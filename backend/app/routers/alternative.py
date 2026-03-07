from fastapi import APIRouter, Query
from app.services.alternative_data_service import (
    get_sp500_constituents,
    get_sp500_by_sector,
    get_13f_holdings,
    get_guru_list,
    get_industry_peers,
    get_buffett_indicator,
)
from app.services.data_service import (
    get_av_company_overview,
    get_av_earnings,
    get_av_income_statement,
)

router = APIRouter(prefix="/api/alternative", tags=["alternative-data"])


# ---- S&P 500 ----------------------------------------------------------------

@router.get("/sp500")
def sp500_constituents():
    """
    Current S&P 500 constituent list with GICS sector/sub-industry.
    Source: Wikipedia (open, no API key required).
    """
    return get_sp500_constituents()


@router.get("/sp500/sectors")
def sp500_by_sector():
    """S&P 500 constituents grouped by GICS sector."""
    return get_sp500_by_sector()


# ---- Industry peers ---------------------------------------------------------

@router.get("/peers/{ticker}")
def industry_peers(
    ticker: str,
    max_peers: int = Query(10, le=20),
):
    """
    Find S&P 500 peer companies in the same GICS sector/sub-industry.
    """
    return get_industry_peers(ticker.upper(), max_peers=max_peers)


# ---- SEC 13F institutional holdings -----------------------------------------

@router.get("/gurus")
def guru_list():
    """
    List of well-known value investors whose 13F filings are indexed.
    Use the 'key' field in the /13f/{fund} endpoint.
    """
    return get_guru_list()


@router.get("/13f/{fund}")
def institutional_13f(
    fund: str,
    limit: int = Query(50, le=100, description="Max number of holdings to return"),
):
    """
    Fetch the most recent 13F-HR institutional holdings for a fund.

    Use a guru key (e.g. 'berkshire_hathaway') or a 10-digit SEC CIK number.
    All data from SEC EDGAR — no API key required.

    Available guru keys:
    berkshire_hathaway, sequoia_fund, fairfax_financial, markel_corp,
    davis_advisors, first_eagle, greenlight_capital, baupost_group,
    third_point, pershing_square
    """
    return get_13f_holdings(fund, limit=limit)


# ---- Buffett Indicator ------------------------------------------------------

@router.get("/buffett-indicator")
def buffett_indicator():
    """
    Buffett Indicator: US total stock market cap / GDP.

    > 150% = significantly overvalued
    115–150% = moderately overvalued
    90–115% = fair value
    70–90% = moderately undervalued
    < 70% = significantly undervalued

    Source: FRED (Wilshire 5000 + GDP).
    """
    return get_buffett_indicator()


# ---- Alpha Vantage (optional key) -------------------------------------------

@router.get("/av/{ticker}/overview")
def av_overview(ticker: str):
    """
    Company overview from Alpha Vantage (cross-check data source).
    Requires ALPHA_VANTAGE_API_KEY in .env. Returns empty dict if no key.
    Free tier: 25 premium req/day, 500 standard req/day.
    """
    return get_av_company_overview(ticker.upper())


@router.get("/av/{ticker}/earnings")
def av_earnings(ticker: str):
    """
    Annual and quarterly EPS history from Alpha Vantage with beat/miss data.
    Requires ALPHA_VANTAGE_API_KEY in .env.
    """
    return get_av_earnings(ticker.upper())


@router.get("/av/{ticker}/income")
def av_income(ticker: str):
    """
    Annual income statement from Alpha Vantage.
    Requires ALPHA_VANTAGE_API_KEY in .env.
    """
    return get_av_income_statement(ticker.upper())
