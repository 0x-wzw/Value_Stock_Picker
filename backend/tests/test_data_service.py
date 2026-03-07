"""
Tests for data_service.py

These tests use mocking to avoid real network calls, which:
 - Makes tests fast and deterministic
 - Works without API keys
 - Doesn't hit rate limits
"""

import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np


# ---------------------------------------------------------------------------
# Unit tests for helper functions
# ---------------------------------------------------------------------------

def test_safe_float():
    from app.services.data_service import _safe_float
    assert _safe_float(1.5) == 1.5
    assert _safe_float("3.14") == 3.14
    assert _safe_float(None) is None
    assert _safe_float(float("nan")) is None
    assert _safe_float("not a number") is None


def test_safe_int():
    from app.services.data_service import _safe_int
    assert _safe_int(42) == 42
    assert _safe_int(3.9) == 3
    assert _safe_int(None) is None
    assert _safe_int("abc") is None


def test_pct():
    from app.services.data_service import _pct
    assert _pct(50, 100) == 50.0
    assert _pct(1, 4) == 25.0
    assert _pct(None, 100) is None
    assert _pct(10, 0) is None


# ---------------------------------------------------------------------------
# get_realtime_quote — mocked yfinance
# ---------------------------------------------------------------------------

def _mock_ticker_info(overrides=None):
    """Build a fake yfinance Ticker info dict."""
    base = {
        "currentPrice": 150.0,
        "regularMarketOpen": 148.0,
        "dayHigh": 155.0,
        "dayLow": 147.0,
        "regularMarketVolume": 50_000_000,
        "previousClose": 145.0,
        "marketCap": 2_400_000_000_000,
        "trailingPE": 28.5,
        "forwardPE": 25.0,
        "trailingEps": 5.26,
        "fiftyTwoWeekHigh": 198.0,
        "fiftyTwoWeekLow": 124.0,
        "averageVolume": 60_000_000,
        "currency": "USD",
        "exchange": "NMS",
    }
    if overrides:
        base.update(overrides)
    return base


@patch("app.services.data_service.yf.Ticker")
def test_get_realtime_quote_basic(mock_ticker_cls):
    from app.services.data_service import get_realtime_quote, _price_cache
    _price_cache.clear()

    mock_ticker = MagicMock()
    mock_ticker.info = _mock_ticker_info()
    mock_ticker_cls.return_value = mock_ticker

    result = get_realtime_quote("AAPL")

    assert result["ticker"] == "AAPL"
    assert result["price"] == 150.0
    assert result["prev_close"] == 145.0
    assert result["change"] == pytest.approx(5.0, abs=0.01)
    assert result["change_pct"] == pytest.approx(3.45, abs=0.1)
    assert result["market_cap"] == 2_400_000_000_000
    assert result["pe_ratio"] == 28.5
    assert result["currency"] == "USD"
    assert "fetched_at" in result


@patch("app.services.data_service.yf.Ticker")
def test_get_realtime_quote_cache(mock_ticker_cls):
    """Second call should hit cache, not yfinance."""
    from app.services.data_service import get_realtime_quote, _price_cache
    _price_cache.clear()

    mock_ticker = MagicMock()
    mock_ticker.info = _mock_ticker_info()
    mock_ticker_cls.return_value = mock_ticker

    get_realtime_quote("MSFT")
    get_realtime_quote("MSFT")  # second call

    # yf.Ticker should only be called once (first call)
    assert mock_ticker_cls.call_count == 1


@patch("app.services.data_service.yf.Ticker")
def test_get_realtime_quote_error_handling(mock_ticker_cls):
    """Should return error dict on failure, not raise."""
    from app.services.data_service import get_realtime_quote, _price_cache
    _price_cache.clear()

    mock_ticker_cls.side_effect = RuntimeError("network error")

    result = get_realtime_quote("BADTICKER")
    assert "error" in result
    assert result["ticker"] == "BADTICKER"


# ---------------------------------------------------------------------------
# get_company_overview
# ---------------------------------------------------------------------------

@patch("app.services.data_service.yf.Ticker")
def test_get_company_overview(mock_ticker_cls):
    from app.services.data_service import get_company_overview, _fundamentals_cache
    _fundamentals_cache.clear()

    mock_ticker = MagicMock()
    mock_ticker.info = {
        "longName": "Apple Inc.",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "exchange": "NMS",
        "currency": "USD",
        "country": "United States",
        "website": "https://www.apple.com",
        "longBusinessSummary": "Apple designs and sells consumer electronics.",
        "fullTimeEmployees": 164_000,
        "marketCap": 2_400_000_000_000,
        "trailingPE": 28.5,
        "priceToBook": 45.0,
        "grossMargins": 0.44,
        "operatingMargins": 0.30,
        "profitMargins": 0.26,
        "returnOnEquity": 1.60,
        "returnOnAssets": 0.20,
        "debtToEquity": 180.0,
        "currentRatio": 0.99,
        "dividendYield": 0.005,
        "beta": 1.2,
    }
    mock_ticker_cls.return_value = mock_ticker

    result = get_company_overview("AAPL")

    assert result["name"] == "Apple Inc."
    assert result["sector"] == "Technology"
    assert result["gross_margin"] == 0.44
    assert result["pe_ratio"] == 28.5


# ---------------------------------------------------------------------------
# get_financial_statements
# ---------------------------------------------------------------------------

def _make_df(periods, rows):
    """Helper to create a fake yfinance financial DataFrame."""
    cols = pd.to_datetime(periods)
    return pd.DataFrame(rows, columns=cols)


@patch("app.services.data_service.yf.Ticker")
def test_get_financial_statements_income(mock_ticker_cls):
    from app.services.data_service import get_financial_statements, _fundamentals_cache
    _fundamentals_cache.clear()

    periods = ["2023-09-30", "2022-09-30", "2021-09-30"]

    income_df = _make_df(
        periods,
        {
            "Total Revenue": [394_330_000_000, 365_817_000_000, 274_515_000_000],
            "Gross Profit":  [169_148_000_000, 152_836_000_000, 104_956_000_000],
            "Net Income":    [ 96_995_000_000,  99_803_000_000,  94_680_000_000],
            "Operating Income": [114_301_000_000, 119_437_000_000, 108_949_000_000],
            "EBITDA": [125_000_000_000, 130_000_000_000, 115_000_000_000],
            "Diluted EPS": [6.13, 6.11, 5.61],
        }
    )

    mock_ticker = MagicMock()
    mock_ticker.financials = income_df
    mock_ticker.balance_sheet = pd.DataFrame()
    mock_ticker.cashflow = pd.DataFrame()
    mock_ticker_cls.return_value = mock_ticker

    result = get_financial_statements("AAPL")

    assert "income_statement" in result
    assert len(result["income_statement"]) == 3
    first = result["income_statement"][0]
    assert first["revenue"] == pytest.approx(394_330_000_000)
    assert first["net_income"] == pytest.approx(96_995_000_000)


# ---------------------------------------------------------------------------
# get_key_metrics — integration of overview + financials
# ---------------------------------------------------------------------------

@patch("app.services.data_service.get_company_overview")
@patch("app.services.data_service.get_financial_statements")
def test_get_key_metrics(mock_financials, mock_overview):
    from app.services.data_service import get_key_metrics, _fundamentals_cache
    _fundamentals_cache.clear()

    mock_overview.return_value = {
        "ticker": "AAPL",
        "market_cap": 2_400_000_000_000,
        "shares_outstanding": 15_700_000_000,
        "total_cash": 62_000_000_000,
        "total_debt": 110_000_000_000,
        "roe": 1.60,
        "roa": 0.20,
        "gross_margin": 0.44,
        "operating_margin": 0.30,
        "profit_margin": 0.26,
        "debt_to_equity": 180.0,
        "current_ratio": 0.99,
    }

    mock_financials.return_value = {
        "ticker": "AAPL",
        "income_statement": [
            {"revenue": 394e9, "gross_profit": 169e9, "net_income": 97e9,
             "operating_income": 114e9, "ebit": 114e9, "period": "2023-09-30"},
        ],
        "balance_sheet": [
            {"total_equity": 62e9, "total_debt": 110e9,
             "cash_and_equivalents": 30e9, "total_assets": 352e9,
             "total_liabilities": 290e9, "period": "2023-09-30"},
        ],
        "cash_flow": [
            {"operating_cf": 114e9, "capex": -11e9, "free_cash_flow": 103e9,
             "depreciation_amortization": 11e9, "period": "2023-09-30"},
        ],
        "fetched_at": "2024-01-01T00:00:00",
    }

    result = get_key_metrics("AAPL")

    assert result["ticker"] == "AAPL"
    assert result["avg_fcf_5y"] == pytest.approx(103e9, rel=0.01)
    assert result["roic_pct"] is not None
    assert result["owner_earnings_estimate"] is not None


# ---------------------------------------------------------------------------
# SEC EDGAR — CIK lookup (mocked HTTP)
# ---------------------------------------------------------------------------

@patch("app.services.data_service.requests.get")
def test_get_cik_for_ticker(mock_get):
    from app.services.data_service import _get_cik_for_ticker, _filings_cache
    _filings_cache.clear()

    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {
        "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
        "1": {"cik_str": 789019, "ticker": "MSFT", "title": "Microsoft Corp"},
    }
    mock_get.return_value = mock_resp

    cik = _get_cik_for_ticker("AAPL")
    assert cik == "0000320193"

    cik_msft = _get_cik_for_ticker("MSFT")
    assert cik_msft == "0000789019"


@patch("app.services.data_service.requests.get")
def test_get_sec_filings(mock_get):
    from app.services.data_service import get_sec_filings, _filings_cache
    _filings_cache.clear()

    # First call: company_tickers.json
    cik_resp = MagicMock()
    cik_resp.raise_for_status.return_value = None
    cik_resp.json.return_value = {
        "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."}
    }

    # Second call: EDGAR submissions
    filings_resp = MagicMock()
    filings_resp.raise_for_status.return_value = None
    filings_resp.json.return_value = {
        "filings": {
            "recent": {
                "form": ["10-K", "10-Q", "8-K"],
                "filingDate": ["2023-11-03", "2023-08-05", "2023-05-05"],
                "reportDate": ["2023-09-30", "2023-07-01", "2023-04-01"],
                "accessionNumber": [
                    "0000320193-23-000106",
                    "0000320193-23-000077",
                    "0000320193-23-000050",
                ],
                "primaryDocument": [
                    "aapl-20230930.htm",
                    "aapl-20230701.htm",
                    "aapl-20230401.htm",
                ],
            }
        }
    }
    mock_get.side_effect = [cik_resp, filings_resp]

    result = get_sec_filings("AAPL", form_types=["10-K", "10-Q"])

    assert len(result) == 2
    assert result[0]["form_type"] == "10-K"
    assert result[0]["filing_date"] == "2023-11-03"
    assert "document_url" in result[0]


# ---------------------------------------------------------------------------
# screener_service
# ---------------------------------------------------------------------------

@patch("app.services.screener_service.get_company_overview")
@patch("app.services.screener_service.get_key_metrics")
def test_screen_stock_passes(mock_metrics, mock_overview):
    from app.services.screener_service import screen_stock

    mock_overview.return_value = {
        "ticker": "AAPL",
        "name": "Apple Inc.",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "market_cap": 2_400_000_000_000,
        "pe_ratio": 28.5,
        "price_to_book": 45.0,
        "ev_to_ebitda": 22.0,
        "gross_margin": 0.44,
        "operating_margin": 0.30,
        "profit_margin": 0.26,
        "roe": 1.60,
        "debt_to_equity": 1.8,
        "current_ratio": 0.99,
        "dividend_yield": 0.005,
    }
    mock_metrics.return_value = {
        "roic_pct": 30.0,
        "fcf_yield_pct": 4.3,
        "revenue_cagr_pct": 7.5,
        "roic_pct": 30.0,
    }

    # Should pass these relaxed criteria
    result = screen_stock("AAPL", {"min_roic": 15, "min_gross_margin": 0.3})
    assert result is not None
    assert result["ticker"] == "AAPL"
    assert result["moat_score"] is not None
    assert result["moat_score"] > 0


@patch("app.services.screener_service.get_company_overview")
@patch("app.services.screener_service.get_key_metrics")
def test_screen_stock_fails(mock_metrics, mock_overview):
    from app.services.screener_service import screen_stock

    mock_overview.return_value = {
        "ticker": "JUNK",
        "name": "Junk Corp",
        "sector": "Energy",
        "industry": "Coal",
        "market_cap": 100_000_000,
        "pe_ratio": 80.0,
        "price_to_book": 2.0,
        "ev_to_ebitda": 40.0,
        "gross_margin": 0.05,
        "operating_margin": 0.01,
        "profit_margin": -0.02,
        "roe": 0.02,
        "debt_to_equity": 5.0,
        "current_ratio": 0.5,
        "dividend_yield": None,
    }
    mock_metrics.return_value = {"roic_pct": 2.0, "fcf_yield_pct": -1.0}

    # Should fail min_roic = 15
    result = screen_stock("JUNK", {"min_roic": 15})
    assert result is None


# ---------------------------------------------------------------------------
# valuation_service
# ---------------------------------------------------------------------------

@patch("app.services.valuation_service.get_key_metrics")
@patch("app.services.valuation_service.get_company_overview")
@patch("app.services.valuation_service.get_realtime_quote")
def test_run_dcf(mock_quote, mock_overview, mock_metrics):
    from app.services.valuation_service import run_dcf

    mock_quote.return_value = {"price": 175.0}
    mock_overview.return_value = {
        "shares_outstanding": 15_700_000_000,
        "total_cash": 62_000_000_000,
        "total_debt": 110_000_000_000,
    }
    mock_metrics.return_value = {
        "avg_fcf_5y": 100_000_000_000,  # $100B FCF
    }

    result = run_dcf("AAPL", growth_rate_yr1_5=0.08, growth_rate_yr6_10=0.05,
                     terminal_growth_rate=0.03, discount_rate=0.10, safety_margin=0.25)

    assert result["method"] == "dcf"
    assert result["intrinsic_value_per_share"] is not None
    assert result["intrinsic_value_per_share"] > 0
    assert result["margin_of_safety_pct"] is not None
    assert "inputs" in result


@patch("app.services.valuation_service.get_key_metrics")
@patch("app.services.valuation_service.get_company_overview")
@patch("app.services.valuation_service.get_realtime_quote")
def test_run_dcf_no_fcf(mock_quote, mock_overview, mock_metrics):
    """Should return error when no FCF data available."""
    from app.services.valuation_service import run_dcf

    mock_quote.return_value = {"price": 50.0}
    mock_overview.return_value = {"shares_outstanding": 1_000_000_000, "total_cash": 0, "total_debt": 0}
    mock_metrics.return_value = {"avg_fcf_5y": None}

    result = run_dcf("NODATA")
    assert "error" in result
