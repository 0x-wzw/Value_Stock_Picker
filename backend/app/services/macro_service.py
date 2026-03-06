"""
macro_service.py
----------------
Pulls macroeconomic context data from open-source, mostly key-free APIs:

  1. US Treasury   — daily yield curve (no key required)
  2. FRED          — Fed funds rate, 10-yr yield, CPI, GDP, unemployment
                     (optional free API key for higher rate limits)
  3. World Bank    — US & global GDP growth (no key required)
  4. BLS           — CPI / inflation details (no key for v1)

All calls are cached with a 6-hour TTL — macro data changes slowly.
"""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from datetime import datetime, date
from typing import Optional

import requests
from cachetools import TTLCache
from cachetools.keys import hashkey

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# 6-hour cache for macro data (changes infrequently)
_MACRO_CACHE: TTLCache = TTLCache(maxsize=100, ttl=21_600)

_TIMEOUT = 15  # seconds

# ---------------------------------------------------------------------------
# 1. US TREASURY  — daily yield curve
#    Source: https://home.treasury.gov  (no API key required)
# ---------------------------------------------------------------------------

TREASURY_YIELD_CURVE_URL = (
    "https://home.treasury.gov/resource-center/data-chart-center"
    "/interest-rates/pages/xml?data=daily_treasury_yield_curve"
    "&field_tdr_date_value={ym}"
)

# Maturities available in Treasury XML feed
TREASURY_MATURITIES = [
    ("BC_1MONTH", "1M"),
    ("BC_2MONTH", "2M"),
    ("BC_3MONTH", "3M"),
    ("BC_4MONTH", "4M"),
    ("BC_6MONTH", "6M"),
    ("BC_1YEAR",  "1Y"),
    ("BC_2YEAR",  "2Y"),
    ("BC_3YEAR",  "3Y"),
    ("BC_5YEAR",  "5Y"),
    ("BC_7YEAR",  "7Y"),
    ("BC_10YEAR", "10Y"),
    ("BC_20YEAR", "20Y"),
    ("BC_30YEAR", "30Y"),
]


def get_treasury_yield_curve(as_of: Optional[date] = None) -> dict:
    """
    Fetch the US Treasury daily yield curve for a given month.

    Args:
        as_of: Date to fetch (uses current month if None).

    Returns:
    {
        "as_of":     "2024-01-15",
        "source":    "US Treasury",
        "yields": {
            "1M": 5.28, "3M": 5.40, "6M": 5.45,
            "1Y": 5.20, "2Y": 4.90, "5Y": 4.50,
            "10Y": 4.35, "30Y": 4.50
        },
        "risk_free_rate_10y": 4.35,   # for DCF discount rate reference
        "fetched_at": "..."
    }
    """
    key = hashkey("treasury_yield", (as_of or date.today()).strftime("%Y-%m"))
    if key in _MACRO_CACHE:
        return _MACRO_CACHE[key]

    try:
        ref_date = as_of or date.today()
        ym = ref_date.strftime("%Y%m")
        url = TREASURY_YIELD_CURVE_URL.format(ym=ym)

        resp = requests.get(url, timeout=_TIMEOUT,
                            headers={"User-Agent": settings.sec_user_agent})
        resp.raise_for_status()

        # Parse XML — Treasury uses Atom feed with d: namespace
        root = ET.fromstring(resp.text)
        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "d":    "http://schemas.microsoft.com/ado/2007/08/dataservices",
            "m":    "http://schemas.microsoft.com/ado/2007/08/dataservices/metadata",
        }

        entries = root.findall(".//atom:entry", ns)
        if not entries:
            return _empty_yield_curve("No data for requested period")

        # Use the most recent entry (last in list)
        latest = entries[-1]
        props = latest.find(".//m:properties", ns)
        if props is None:
            return _empty_yield_curve("Malformed Treasury XML")

        def _get_rate(field: str) -> Optional[float]:
            el = props.find(f"d:{field}", ns)
            if el is None or el.text is None or el.text.strip() == "":
                return None
            try:
                return float(el.text)
            except ValueError:
                return None

        # Extract date
        date_el = props.find("d:NEW_DATE", ns)
        as_of_str = ""
        if date_el is not None and date_el.text:
            as_of_str = date_el.text[:10]

        yields = {}
        for field, label in TREASURY_MATURITIES:
            rate = _get_rate(field)
            if rate is not None:
                yields[label] = rate

        risk_free = yields.get("10Y")

        result = {
            "as_of": as_of_str or ref_date.isoformat(),
            "source": "US Treasury",
            "url": "https://home.treasury.gov/resource-center/data-chart-center/interest-rates",
            "yields": yields,
            "risk_free_rate_10y": risk_free,
            "fetched_at": datetime.utcnow().isoformat(),
        }

        _MACRO_CACHE[key] = result
        return result

    except Exception as exc:
        logger.warning("get_treasury_yield_curve failed: %s", exc)
        return _empty_yield_curve(str(exc))


def _empty_yield_curve(error: str) -> dict:
    return {
        "as_of": date.today().isoformat(),
        "source": "US Treasury",
        "yields": {},
        "risk_free_rate_10y": None,
        "error": error,
        "fetched_at": datetime.utcnow().isoformat(),
    }


def get_risk_free_rate() -> float:
    """
    Return the current 10-year US Treasury yield as a decimal (e.g. 0.043).
    Falls back to 0.04 (4%) if data is unavailable.
    Useful as the default risk-free rate in DCF calculations.
    """
    curve = get_treasury_yield_curve()
    rate = curve.get("risk_free_rate_10y")
    if rate is not None:
        return round(rate / 100, 4)  # convert pct → decimal
    return 0.04  # conservative fallback


# ---------------------------------------------------------------------------
# 2. FRED — Federal Reserve Economic Data
#    Source: https://fred.stlouisfed.org  (free key optional)
# ---------------------------------------------------------------------------

FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"

# Key FRED series for value investors
FRED_SERIES = {
    "DGS10":         "10-Year Treasury Yield (%)",
    "DFF":           "Federal Funds Effective Rate (%)",
    "FEDFUNDS":      "Federal Funds Rate (monthly avg, %)",
    "CPIAUCSL":      "Consumer Price Index (All Urban Consumers)",
    "CPILFESL":      "Core CPI (excl. Food & Energy)",
    "A191RL1Q225SBEA": "Real GDP Growth Rate (quarterly %)",
    "GDPC1":         "Real GDP (billions, chained 2017 $)",
    "UNRATE":        "Unemployment Rate (%)",
    "T10YIE":        "10-Year Breakeven Inflation Rate (%)",
    "BAMLH0A0HYM2":  "High-Yield Spread (BofA, %)",
    "VIXCLS":        "CBOE VIX Volatility Index",
    "DEXUSEU":       "USD/EUR Exchange Rate",
}


def get_fred_series(series_id: str, limit: int = 12) -> dict:
    """
    Fetch recent observations for a FRED series.

    Args:
        series_id: FRED series identifier (e.g. "DGS10", "CPIAUCSL")
        limit:     Number of most recent observations to return

    Returns dict with name, units, and list of {date, value} observations.
    """
    key = hashkey("fred", series_id.upper(), limit)
    if key in _MACRO_CACHE:
        return _MACRO_CACHE[key]

    params: dict = {
        "series_id":  series_id.upper(),
        "file_type":  "json",
        "sort_order": "desc",
        "limit":      limit,
    }
    if settings.fred_api_key:
        params["api_key"] = settings.fred_api_key
    else:
        # FRED allows a small number of keyless requests for public series
        params["api_key"] = "abcdefghijklmnopqrstuvwxyz012345"  # demo key placeholder

    try:
        resp = requests.get(FRED_BASE, params=params, timeout=_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        observations = []
        for obs in data.get("observations", []):
            val_str = obs.get("value", ".")
            try:
                val = float(val_str) if val_str != "." else None
            except ValueError:
                val = None
            observations.append({
                "date":  obs.get("date"),
                "value": val,
            })

        # Reverse to chronological order
        observations.reverse()

        result = {
            "series_id":   series_id.upper(),
            "description": FRED_SERIES.get(series_id.upper(), series_id),
            "source":      "FRED — St. Louis Federal Reserve",
            "url":         f"https://fred.stlouisfed.org/series/{series_id.upper()}",
            "observations": observations,
            "latest_value": observations[-1]["value"] if observations else None,
            "latest_date":  observations[-1]["date"] if observations else None,
            "fetched_at":   datetime.utcnow().isoformat(),
        }

        _MACRO_CACHE[key] = result
        return result

    except Exception as exc:
        logger.warning("get_fred_series(%s) failed: %s", series_id, exc)
        return {
            "series_id":   series_id.upper(),
            "description": FRED_SERIES.get(series_id.upper(), series_id),
            "observations": [],
            "error":       str(exc),
            "fetched_at":  datetime.utcnow().isoformat(),
        }


def get_macro_dashboard() -> dict:
    """
    Fetch a curated set of key macroeconomic indicators in a single call.
    Suitable for displaying a macro context panel for value investors.
    """
    key = hashkey("macro_dashboard")
    if key in _MACRO_CACHE:
        return _MACRO_CACHE[key]

    results: dict = {
        "source":     "FRED + US Treasury",
        "fetched_at": datetime.utcnow().isoformat(),
    }

    # Treasury yield curve (no key needed)
    curve = get_treasury_yield_curve()
    results["yield_curve"] = curve.get("yields", {})
    results["risk_free_rate_10y_pct"] = curve.get("risk_free_rate_10y")

    # FRED series — fetch key indicators
    fred_targets = {
        "fed_funds_rate":   ("DFF", 1),
        "cpi_yoy":          ("CPIAUCSL", 13),   # 13 months to compute YoY
        "core_cpi_yoy":     ("CPILFESL", 13),
        "unemployment":     ("UNRATE", 1),
        "breakeven_inflation": ("T10YIE", 1),
        "high_yield_spread":   ("BAMLH0A0HYM2", 1),
        "vix":              ("VIXCLS", 1),
        "gdp_growth":       ("A191RL1Q225SBEA", 1),
    }

    for metric, (series_id, n) in fred_targets.items():
        try:
            data = get_fred_series(series_id, limit=n)
            obs = data.get("observations", [])
            latest = obs[-1] if obs else {}
            val = latest.get("value")

            # Compute YoY for CPI
            if metric.endswith("_yoy") and len(obs) == 13:
                v_now = obs[-1]["value"]
                v_year_ago = obs[0]["value"]
                if v_now is not None and v_year_ago and v_year_ago > 0:
                    val = round((v_now - v_year_ago) / v_year_ago * 100, 2)
                else:
                    val = None

            results[metric] = {
                "value": val,
                "date":  latest.get("date"),
                "series_id": series_id,
                "label": FRED_SERIES.get(series_id, series_id),
            }
        except Exception as e:
            results[metric] = {"value": None, "error": str(e)}

    _MACRO_CACHE[key] = results
    return results


# ---------------------------------------------------------------------------
# 3. WORLD BANK — global GDP & economic indicators
#    Source: https://api.worldbank.org  (no API key required)
# ---------------------------------------------------------------------------

WB_BASE = "https://api.worldbank.org/v2"

# Useful World Bank indicators
WB_INDICATORS = {
    "NY.GDP.MKTP.KD.ZG": "GDP growth (annual %)",
    "FP.CPI.TOTL.ZG":    "Inflation, CPI (annual %)",
    "SL.UEM.TOTL.ZS":    "Unemployment (% of labor force)",
    "NE.TRD.GNFS.ZS":    "Trade (% of GDP)",
    "GC.DOD.TOTL.GD.ZS": "Central government debt (% of GDP)",
}


def get_world_bank_indicator(
    indicator: str = "NY.GDP.MKTP.KD.ZG",
    country: str = "US",
    years: int = 10,
) -> dict:
    """
    Fetch a World Bank economic indicator time series.

    Args:
        indicator: World Bank indicator code (see WB_INDICATORS)
        country:   ISO 2-letter country code (default: "US")
        years:     Number of most recent years to return

    Returns dict with name, country, and list of {year, value} records.
    """
    key = hashkey("worldbank", indicator, country, years)
    if key in _MACRO_CACHE:
        return _MACRO_CACHE[key]

    try:
        current_year = datetime.utcnow().year
        start_year   = current_year - years

        url = (
            f"{WB_BASE}/country/{country}/indicator/{indicator}"
            f"?format=json&date={start_year}:{current_year}&per_page=50"
        )
        resp = requests.get(url, timeout=_TIMEOUT)
        resp.raise_for_status()
        payload = resp.json()

        # World Bank returns [metadata, data_array]
        if not isinstance(payload, list) or len(payload) < 2:
            raise ValueError("Unexpected World Bank response format")

        records = []
        for entry in payload[1]:
            val = entry.get("value")
            yr  = entry.get("date")
            if yr and val is not None:
                records.append({"year": yr, "value": round(float(val), 3)})

        # Sort ascending
        records.sort(key=lambda r: r["year"])

        result = {
            "indicator":   indicator,
            "description": WB_INDICATORS.get(indicator, indicator),
            "country":     country,
            "source":      "World Bank Open Data",
            "url":         f"https://data.worldbank.org/indicator/{indicator}?locations={country}",
            "data":        records,
            "latest":      records[-1] if records else None,
            "fetched_at":  datetime.utcnow().isoformat(),
        }

        _MACRO_CACHE[key] = result
        return result

    except Exception as exc:
        logger.warning("get_world_bank_indicator(%s, %s) failed: %s", indicator, country, exc)
        return {
            "indicator":  indicator,
            "country":    country,
            "data":       [],
            "error":      str(exc),
            "fetched_at": datetime.utcnow().isoformat(),
        }


def get_us_macro_world_bank() -> dict:
    """
    Convenience: fetch key US macro indicators from World Bank in one call.
    """
    key = hashkey("wb_us_macro")
    if key in _MACRO_CACHE:
        return _MACRO_CACHE[key]

    result = {}
    for code, label in WB_INDICATORS.items():
        data = get_world_bank_indicator(code, country="US", years=10)
        result[code] = {
            "label":  label,
            "latest": data.get("latest"),
            "series": data.get("data", [])[-5:],  # last 5 years only
        }

    result["fetched_at"] = datetime.utcnow().isoformat()
    result["source"] = "World Bank Open Data"
    _MACRO_CACHE[key] = result
    return result


# ---------------------------------------------------------------------------
# 4. BLS — Bureau of Labor Statistics
#    Source: https://api.bls.gov  (v1 = no key, v2 = optional key)
# ---------------------------------------------------------------------------

BLS_BASE_V1 = "https://api.bls.gov/publicAPI/v1/timeseries/data/"
BLS_BASE_V2 = "https://api.bls.gov/publicAPI/v2/timeseries/data/"

BLS_SERIES = {
    "CUUR0000SA0":  "CPI-U All Items (Not Seasonally Adjusted)",
    "CUSR0000SA0":  "CPI-U All Items (Seasonally Adjusted)",
    "CUSR0000SEHF": "CPI-U Energy",
    "CUSR0000SAF1": "CPI-U Food",
    "LNS14000000":  "Unemployment Rate (Seasonally Adjusted)",
    "CES0000000001":"Total Nonfarm Payroll (thousands)",
    "PRS85006092":  "Business Sector: Labor Productivity (quarterly)",
}


def get_bls_series(series_ids: list[str], years: int = 3) -> dict:
    """
    Fetch one or more BLS time series.

    Args:
        series_ids: List of BLS series identifiers (max 25 per request)
        years:      Number of most recent years

    Returns: {series_id: {name, observations: [{year, period, value}]}}
    """
    key = hashkey("bls", tuple(sorted(series_ids)), years)
    if key in _MACRO_CACHE:
        return _MACRO_CACHE[key]

    current_year = datetime.utcnow().year
    payload: dict = {
        "seriesid":  series_ids[:25],
        "startyear": str(current_year - years),
        "endyear":   str(current_year),
    }

    bls_key = getattr(settings, "bls_api_key", "")
    use_v2  = bool(bls_key)
    base    = BLS_BASE_V2 if use_v2 else BLS_BASE_V1
    if use_v2:
        payload["registrationkey"] = bls_key

    try:
        resp = requests.post(base, json=payload, timeout=_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        if data.get("status") != "REQUEST_SUCCEEDED":
            raise ValueError(f"BLS error: {data.get('message', 'unknown')}")

        result: dict = {}
        for series in data.get("Results", {}).get("series", []):
            sid = series.get("seriesID", "")
            observations = []
            for item in series.get("data", []):
                try:
                    observations.append({
                        "year":   item.get("year"),
                        "period": item.get("period"),
                        "label":  item.get("periodName"),
                        "value":  float(item["value"]) if item.get("value") else None,
                    })
                except (KeyError, ValueError):
                    pass
            # Sort ascending
            observations.sort(key=lambda o: (o["year"], o["period"]))
            result[sid] = {
                "series_id":    sid,
                "description":  BLS_SERIES.get(sid, sid),
                "source":       "Bureau of Labor Statistics",
                "url":          f"https://data.bls.gov/timeseries/{sid}",
                "observations": observations,
                "latest":       observations[-1] if observations else None,
            }

        result["fetched_at"] = datetime.utcnow().isoformat()
        _MACRO_CACHE[key] = result
        return result

    except Exception as exc:
        logger.warning("get_bls_series(%s) failed: %s", series_ids, exc)
        return {
            sid: {"series_id": sid, "observations": [], "error": str(exc)}
            for sid in series_ids
        }


def get_cpi_data(years: int = 5) -> dict:
    """
    Fetch Consumer Price Index data from BLS.
    Returns seasonally adjusted CPI + computed 12-month inflation rate.
    """
    raw = get_bls_series(["CUSR0000SA0"], years=years)
    series = raw.get("CUSR0000SA0", {})
    obs = series.get("observations", [])

    # Compute trailing 12-month inflation for each month where possible
    enriched = []
    for i, point in enumerate(obs):
        record = dict(point)
        if i >= 12 and obs[i - 12]["value"] and point["value"]:
            yoy = (point["value"] - obs[i - 12]["value"]) / obs[i - 12]["value"] * 100
            record["yoy_inflation_pct"] = round(yoy, 2)
        enriched.append(record)

    latest_yoy = None
    for r in reversed(enriched):
        if r.get("yoy_inflation_pct") is not None:
            latest_yoy = r["yoy_inflation_pct"]
            break

    return {
        "source":           "Bureau of Labor Statistics",
        "series":           "CPI-U (Seasonally Adjusted)",
        "latest_yoy_pct":   latest_yoy,
        "observations":     enriched,
        "fetched_at":       datetime.utcnow().isoformat(),
    }


# ---------------------------------------------------------------------------
# 5. Convenience: macro context for DCF
# ---------------------------------------------------------------------------

def get_dcf_context() -> dict:
    """
    Return a single dict with the key macro inputs needed for DCF analysis:
    - 10-year risk-free rate (from Treasury)
    - Current CPI / inflation
    - Fed funds rate
    - 10-year breakeven inflation
    - VIX (market fear gauge)

    This is the "macro context" panel shown alongside valuation tools.
    """
    key = hashkey("dcf_context")
    if key in _MACRO_CACHE:
        return _MACRO_CACHE[key]

    curve = get_treasury_yield_curve()
    dashboard = get_macro_dashboard()

    risk_free = curve.get("risk_free_rate_10y")
    rf_decimal = (risk_free / 100) if risk_free else None

    # Equity risk premium: rough estimate = 10yr yield + ~3.5% historical ERP
    erp_estimate = round((rf_decimal or 0.04) + 0.035, 4) if rf_decimal else None

    # Suggested discount rate: risk-free + ERP
    # (simplified — ignores beta; for more accuracy users should add company beta)
    suggested_wacc = erp_estimate

    result = {
        "risk_free_rate_10y_pct": risk_free,
        "risk_free_rate_10y_decimal": rf_decimal,
        "suggested_dcf_discount_rate": suggested_wacc,
        "fed_funds_rate": dashboard.get("fed_funds_rate", {}).get("value"),
        "inflation_yoy_pct": dashboard.get("cpi_yoy", {}).get("value"),
        "breakeven_inflation_pct": dashboard.get("breakeven_inflation", {}).get("value"),
        "unemployment_pct": dashboard.get("unemployment", {}).get("value"),
        "vix": dashboard.get("vix", {}).get("value"),
        "high_yield_spread": dashboard.get("high_yield_spread", {}).get("value"),
        "gdp_growth_pct": dashboard.get("gdp_growth", {}).get("value"),
        "yield_curve": curve.get("yields", {}),
        "yield_curve_date": curve.get("as_of"),
        "sources": ["US Treasury", "FRED — St. Louis Fed"],
        "fetched_at": datetime.utcnow().isoformat(),
    }

    _MACRO_CACHE[key] = result
    return result
