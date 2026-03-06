"""
Tests for macro_service.py and alternative_data_service.py
All external HTTP calls are mocked.
"""

import pytest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Treasury yield curve
# ---------------------------------------------------------------------------

TREASURY_XML_SAMPLE = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:d="http://schemas.microsoft.com/ado/2007/08/dataservices"
      xmlns:m="http://schemas.microsoft.com/ado/2007/08/dataservices/metadata">
  <entry>
    <content type="application/xml">
      <m:properties>
        <d:NEW_DATE m:type="Edm.DateTime">2024-01-15T00:00:00</d:NEW_DATE>
        <d:BC_1MONTH m:type="Edm.Double">5.28</d:BC_1MONTH>
        <d:BC_3MONTH m:type="Edm.Double">5.40</d:BC_3MONTH>
        <d:BC_6MONTH m:type="Edm.Double">5.45</d:BC_6MONTH>
        <d:BC_1YEAR  m:type="Edm.Double">5.02</d:BC_1YEAR>
        <d:BC_2YEAR  m:type="Edm.Double">4.38</d:BC_2YEAR>
        <d:BC_5YEAR  m:type="Edm.Double">4.01</d:BC_5YEAR>
        <d:BC_10YEAR m:type="Edm.Double">4.08</d:BC_10YEAR>
        <d:BC_20YEAR m:type="Edm.Double">4.43</d:BC_20YEAR>
        <d:BC_30YEAR m:type="Edm.Double">4.36</d:BC_30YEAR>
      </m:properties>
    </content>
  </entry>
</feed>"""


@patch("app.services.macro_service.requests.get")
def test_get_treasury_yield_curve(mock_get):
    from app.services.macro_service import get_treasury_yield_curve, _MACRO_CACHE
    _MACRO_CACHE.clear()

    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.text = TREASURY_XML_SAMPLE
    mock_get.return_value = mock_resp

    result = get_treasury_yield_curve()

    assert result["risk_free_rate_10y"] == pytest.approx(4.08)
    assert result["yields"]["10Y"] == pytest.approx(4.08)
    assert result["yields"]["3M"] == pytest.approx(5.40)
    assert "1M" in result["yields"]
    assert result["source"] == "US Treasury"


@patch("app.services.macro_service.requests.get")
def test_get_risk_free_rate(mock_get):
    from app.services.macro_service import get_risk_free_rate, _MACRO_CACHE
    _MACRO_CACHE.clear()

    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.text = TREASURY_XML_SAMPLE
    mock_get.return_value = mock_resp

    rf = get_risk_free_rate()
    # 4.08% → 0.0408
    assert rf == pytest.approx(0.0408, abs=0.001)


@patch("app.services.macro_service.requests.get")
def test_treasury_yields_error_returns_empty(mock_get):
    """Should return empty/error dict on network failure, not raise."""
    from app.services.macro_service import get_treasury_yield_curve, _MACRO_CACHE
    _MACRO_CACHE.clear()

    mock_get.side_effect = ConnectionError("timeout")

    result = get_treasury_yield_curve()
    assert "error" in result
    assert result["yields"] == {}


# ---------------------------------------------------------------------------
# FRED
# ---------------------------------------------------------------------------

FRED_RESP = {
    "observations": [
        {"date": "2024-01-01", "value": "4.35"},
        {"date": "2024-01-08", "value": "4.28"},
        {"date": "2024-01-15", "value": "4.20"},
    ]
}


@patch("app.services.macro_service.requests.get")
def test_get_fred_series(mock_get):
    from app.services.macro_service import get_fred_series, _MACRO_CACHE
    _MACRO_CACHE.clear()

    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = FRED_RESP
    mock_get.return_value = mock_resp

    result = get_fred_series("DGS10", limit=3)

    assert result["series_id"] == "DGS10"
    assert len(result["observations"]) == 3
    # Should be in chronological order (reversed from desc response)
    assert result["observations"][0]["date"] == "2024-01-01"
    assert result["latest_value"] == pytest.approx(4.20)


@patch("app.services.macro_service.requests.get")
def test_fred_handles_dot_values(mock_get):
    """FRED uses '.' for missing values — should return None."""
    from app.services.macro_service import get_fred_series, _MACRO_CACHE
    _MACRO_CACHE.clear()

    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {"observations": [{"date": "2024-01-01", "value": "."}]}
    mock_get.return_value = mock_resp

    result = get_fred_series("DGS10")
    assert result["observations"][0]["value"] is None


# ---------------------------------------------------------------------------
# World Bank
# ---------------------------------------------------------------------------

WB_RESP = [
    {"page": 1, "pages": 1, "per_page": "50", "total": 3},
    [
        {"date": "2021", "value": 5.9, "indicator": {"id": "NY.GDP.MKTP.KD.ZG"}},
        {"date": "2022", "value": 2.1, "indicator": {"id": "NY.GDP.MKTP.KD.ZG"}},
        {"date": "2023", "value": 2.5, "indicator": {"id": "NY.GDP.MKTP.KD.ZG"}},
    ]
]


@patch("app.services.macro_service.requests.get")
def test_get_world_bank_indicator(mock_get):
    from app.services.macro_service import get_world_bank_indicator, _MACRO_CACHE
    _MACRO_CACHE.clear()

    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = WB_RESP
    mock_get.return_value = mock_resp

    result = get_world_bank_indicator("NY.GDP.MKTP.KD.ZG", country="US")

    assert result["indicator"] == "NY.GDP.MKTP.KD.ZG"
    assert result["country"] == "US"
    assert len(result["data"]) == 3
    assert result["data"][0]["year"] == "2021"
    assert result["latest"]["value"] == pytest.approx(2.5)


# ---------------------------------------------------------------------------
# BLS CPI
# ---------------------------------------------------------------------------

BLS_RESP = {
    "status": "REQUEST_SUCCEEDED",
    "Results": {
        "series": [
            {
                "seriesID": "CUSR0000SA0",
                "data": [
                    {"year": "2023", "period": "M12", "periodName": "December", "value": "307.026"},
                    {"year": "2022", "period": "M12", "periodName": "December", "value": "296.797"},
                    {"year": "2021", "period": "M12", "periodName": "December", "value": "278.802"},
                ]
            }
        ]
    }
}


@patch("app.services.macro_service.requests.post")
def test_get_bls_series(mock_post):
    from app.services.macro_service import get_bls_series, _MACRO_CACHE
    _MACRO_CACHE.clear()

    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = BLS_RESP
    mock_post.return_value = mock_resp

    result = get_bls_series(["CUSR0000SA0"])

    assert "CUSR0000SA0" in result
    series = result["CUSR0000SA0"]
    assert len(series["observations"]) == 3


# ---------------------------------------------------------------------------
# alternative_data_service — S&P 500
# ---------------------------------------------------------------------------

def test_sp500_fallback_returned_on_error():
    """If Wikipedia scraping fails, the fallback list should be returned."""
    with patch("app.services.alternative_data_service.requests.get") as mock_get:
        from app.services.alternative_data_service import get_sp500_constituents, _ALT_CACHE
        _ALT_CACHE.clear()

        mock_get.side_effect = ConnectionError("timeout")
        result = get_sp500_constituents()

        assert isinstance(result, list)
        assert len(result) > 0
        assert "ticker" in result[0]


def test_get_industry_peers_not_in_sp500():
    """Ticker not in S&P 500 should return empty peers with a note."""
    with patch("app.services.alternative_data_service.get_sp500_constituents") as mock_sp500:
        from app.services.alternative_data_service import get_industry_peers, _ALT_CACHE
        _ALT_CACHE.clear()

        mock_sp500.return_value = [
            {"ticker": "AAPL", "company": "Apple", "gics_sector": "IT", "gics_sub_industry": "Hardware", "headquarters": "", "date_added": ""},
        ]

        result = get_industry_peers("NFLX")
        assert result["ticker"] == "NFLX"
        assert result["peers"] == []
        assert "note" in result


def test_get_industry_peers_same_sector():
    """Should find peers in same sector."""
    with patch("app.services.alternative_data_service.get_sp500_constituents") as mock_sp500:
        from app.services.alternative_data_service import get_industry_peers, _ALT_CACHE
        _ALT_CACHE.clear()

        mock_sp500.return_value = [
            {"ticker": "AAPL",  "company": "Apple",     "gics_sector": "IT", "gics_sub_industry": "Hardware", "headquarters": "", "date_added": ""},
            {"ticker": "MSFT",  "company": "Microsoft", "gics_sector": "IT", "gics_sub_industry": "Software", "headquarters": "", "date_added": ""},
            {"ticker": "GOOGL", "company": "Alphabet",  "gics_sector": "Communication", "gics_sub_industry": "Internet", "headquarters": "", "date_added": ""},
        ]

        result = get_industry_peers("AAPL")
        assert result["sector"] == "IT"
        # MSFT is same sector
        peer_tickers = [p["ticker"] for p in result["peers"]]
        assert "MSFT" in peer_tickers
        assert "GOOGL" not in peer_tickers


# ---------------------------------------------------------------------------
# Buffett Indicator
# ---------------------------------------------------------------------------

@patch("app.services.alternative_data_service.get_fredservice")
def test_buffett_indicator():
    """Compute ratio = Wilshire / GDP."""
    with patch("app.services.macro_service.get_fred_series") as mock_fred:
        from app.services.alternative_data_service import get_buffett_indicator, _FILING_CACHE
        _FILING_CACHE.clear()

        mock_fred.side_effect = lambda series_id, **kw: {
            "WILL5000PR": {"latest_value": 40_000.0},  # $40T in index points
            "GDP":        {"latest_value": 27_000.0},   # $27T nominal GDP
        }.get(series_id, {"latest_value": None})

        result = get_buffett_indicator()
        # 40000 / 27000 * 100 ≈ 148%
        assert result.get("buffett_indicator_pct") is not None
        assert "interpretation" in result
