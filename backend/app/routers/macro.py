from fastapi import APIRouter, Query
from app.services.macro_service import (
    get_treasury_yield_curve,
    get_risk_free_rate,
    get_fred_series,
    get_macro_dashboard,
    get_world_bank_indicator,
    get_us_macro_world_bank,
    get_cpi_data,
    get_dcf_context,
    FRED_SERIES,
    WB_INDICATORS,
)

router = APIRouter(prefix="/api/macro", tags=["macro"])


@router.get("/yields")
def treasury_yields():
    """
    Current US Treasury yield curve from treasury.gov.
    No API key required. Includes the 10-year risk-free rate for DCF use.
    """
    return get_treasury_yield_curve()


@router.get("/risk-free-rate")
def risk_free_rate():
    """Current 10-year Treasury yield as a decimal (e.g. 0.043 = 4.3%)."""
    rf = get_risk_free_rate()
    return {
        "risk_free_rate": rf,
        "risk_free_rate_pct": round(rf * 100, 2),
        "note": "10-year US Treasury Constant Maturity Rate — standard proxy for DCF discount rate baseline",
    }


@router.get("/dashboard")
def macro_dashboard():
    """
    Key macroeconomic indicators in a single call:
    Fed funds rate, CPI inflation, GDP growth, unemployment,
    breakeven inflation, VIX, yield curve.

    Data sources: US Treasury + FRED (St. Louis Fed).
    """
    return get_macro_dashboard()


@router.get("/dcf-context")
def dcf_context():
    """
    Macro inputs for DCF valuation:
    risk-free rate, inflation, Fed rate, VIX, suggested discount rate.
    Use these to inform your valuation assumptions.
    """
    return get_dcf_context()


@router.get("/fred/{series_id}")
def fred_series(
    series_id: str,
    limit: int = Query(24, le=100, description="Number of most recent observations"),
):
    """
    Fetch any FRED economic series by ID.

    Common series:
    - DGS10       — 10-Year Treasury yield
    - DFF         — Federal Funds Rate (daily)
    - CPIAUCSL    — CPI (inflation)
    - UNRATE      — Unemployment rate
    - A191RL1Q225SBEA — Real GDP growth
    - T10YIE      — Breakeven inflation
    - VIXCLS      — VIX volatility index
    - BAMLH0A0HYM2 — High-yield credit spread

    See https://fred.stlouisfed.org for the full catalogue of 800,000+ series.
    """
    return get_fred_series(series_id, limit=limit)


@router.get("/fred")
def fred_series_list():
    """List the pre-configured FRED series most relevant to value investing."""
    return [
        {"series_id": sid, "description": desc}
        for sid, desc in FRED_SERIES.items()
    ]


@router.get("/worldbank/{indicator}")
def worldbank_indicator(
    indicator: str,
    country: str = Query("US", description="ISO 2-letter country code"),
    years: int = Query(10, le=30),
):
    """
    Fetch any World Bank economic indicator for a country.
    No API key required.

    Common indicators:
    - NY.GDP.MKTP.KD.ZG — GDP growth (annual %)
    - FP.CPI.TOTL.ZG    — Inflation (annual %)
    - SL.UEM.TOTL.ZS    — Unemployment (% labor force)
    - GC.DOD.TOTL.GD.ZS — Government debt (% of GDP)
    """
    return get_world_bank_indicator(indicator, country=country, years=years)


@router.get("/worldbank")
def worldbank_us_macro():
    """Key US macroeconomic indicators from the World Bank (no API key required)."""
    return get_us_macro_world_bank()


@router.get("/cpi")
def cpi(years: int = Query(5, le=10)):
    """
    US Consumer Price Index from BLS with computed YoY inflation rate.
    No API key required for BLS v1.
    """
    return get_cpi_data(years=years)
