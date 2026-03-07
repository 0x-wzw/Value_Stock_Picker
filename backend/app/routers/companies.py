from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from app.services.data_service import (
    get_realtime_quote,
    get_company_overview,
    get_financial_statements,
    get_key_metrics,
    get_price_history,
    get_sec_filings,
    get_sec_key_facts,
    get_news,
    get_analyst_data,
    get_institutional_holders,
    get_insider_transactions,
    get_options_summary,
    search_tickers,
)
from app.services.screener_service import get_value_signals

router = APIRouter(prefix="/api/companies", tags=["companies"])


@router.get("/search")
def search(q: str = Query(..., min_length=1), limit: int = Query(20, le=50)):
    """Search for companies by name or ticker symbol."""
    return search_tickers(q, limit=limit)


@router.get("/{ticker}/quote")
def quote(ticker: str):
    """Real-time (15-min delayed) price quote."""
    data = get_realtime_quote(ticker.upper())
    if "error" in data and "price" not in data:
        raise HTTPException(status_code=404, detail=f"No data found for {ticker}")
    return data


@router.get("/{ticker}/overview")
def overview(ticker: str):
    """Company overview: description, sector, key ratios."""
    data = get_company_overview(ticker.upper())
    if "error" in data and "name" not in data:
        raise HTTPException(status_code=404, detail=f"No data found for {ticker}")
    return data


@router.get("/{ticker}/financials")
def financials(ticker: str):
    """Multi-year income statement, balance sheet, and cash flow."""
    return get_financial_statements(ticker.upper())


@router.get("/{ticker}/metrics")
def key_metrics(ticker: str):
    """Derived value-investing metrics: ROIC, FCF yield, owner earnings, etc."""
    return get_key_metrics(ticker.upper())


@router.get("/{ticker}/signals")
def value_signals(ticker: str):
    """Value investing signals and quick fair value estimates."""
    return get_value_signals(ticker.upper())


@router.get("/{ticker}/history")
def price_history(
    ticker: str,
    period: str = Query("5y", description="1mo,3mo,6mo,1y,2y,5y,10y,max"),
    interval: str = Query("1d", description="1d,1wk,1mo"),
):
    """Historical OHLCV price data."""
    data = get_price_history(ticker.upper(), period=period, interval=interval)
    return {"ticker": ticker.upper(), "period": period, "interval": interval, "data": data}


@router.get("/{ticker}/filings")
def sec_filings(
    ticker: str,
    forms: str = Query("10-K,10-Q,DEF 14A,8-K", description="Comma-separated form types"),
    limit: int = Query(10, le=40),
):
    """SEC EDGAR filings (10-K, 10-Q, proxy statements, 8-K)."""
    form_types = [f.strip() for f in forms.split(",")]
    return get_sec_filings(ticker.upper(), form_types=form_types, limit=limit)


@router.get("/{ticker}/sec-facts")
def sec_facts(ticker: str):
    """Curated SEC XBRL facts: reported revenues, earnings, assets, etc."""
    return get_sec_key_facts(ticker.upper())


@router.get("/{ticker}/news")
def news(ticker: str, limit: int = Query(10, le=30)):
    """Recent news headlines for the company."""
    return get_news(ticker.upper(), limit=limit)


@router.get("/{ticker}/analysts")
def analysts(ticker: str):
    """Analyst recommendations and earnings estimates."""
    return get_analyst_data(ticker.upper())


@router.get("/{ticker}/holders")
def institutional_holders(ticker: str):
    """Top institutional shareholders."""
    return get_institutional_holders(ticker.upper())


@router.get("/{ticker}/insiders")
def insider_transactions(ticker: str):
    """Recent insider buy/sell transactions."""
    return get_insider_transactions(ticker.upper())


@router.get("/{ticker}/options")
def options_summary(ticker: str):
    """Options chain summary: put/call ratio, implied volatility."""
    return get_options_summary(ticker.upper())


@router.get("/{ticker}")
def company_full(ticker: str):
    """
    Combined endpoint: quote + overview + key metrics in a single call.
    Useful for the company dashboard page.
    """
    quote_data = get_realtime_quote(ticker.upper())
    overview_data = get_company_overview(ticker.upper())
    metrics_data = get_key_metrics(ticker.upper())
    signals_data = get_value_signals(ticker.upper())
    news_data = get_news(ticker.upper(), limit=5)

    return {
        "quote": quote_data,
        "overview": overview_data,
        "metrics": metrics_data,
        "signals": signals_data,
        "recent_news": news_data,
    }
