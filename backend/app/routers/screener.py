from fastapi import APIRouter, Query, HTTPException
from typing import List

from app.services.data_service import (
    get_bulk_quotes,
    get_market_indices,
    get_sector_performance,
    search_tickers,
)
from app.services.screener_service import screen_stock
from app.schemas.screener import ScreenerFilter, ScreenerResult

router = APIRouter(prefix="/api/screener", tags=["screener"])

# A curated list of large-cap tickers for screener demos
# In production this would come from a database of all traded companies
DEFAULT_UNIVERSE = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "BRK-B", "LLY",
    "V", "JPM", "UNH", "MA", "XOM", "JNJ", "PG", "HD", "ABBV", "MRK",
    "AVGO", "CVX", "COST", "PEP", "KO", "ADBE", "CRM", "TMO", "ACN",
    "MCD", "CSCO", "ABT", "DHR", "TXN", "NEE", "LIN", "QCOM", "INTU",
    "AMD", "UPS", "LOW", "AMGN", "SBUX", "GILD", "CB", "BLK", "MDT",
    "ADP", "ISRG", "VRTX", "REGN", "SYK", "ZTS", "MMC", "ITW", "PLD",
    "WM", "ECL", "APH", "KLAC", "LRCX", "CDNS", "SNPS", "MCHP", "ADI",
    "ORCL", "SAP", "NOW", "WDAY", "SNOW", "PANW", "CRWD", "ZS", "DDOG",
    "NKE", "DIS", "NFLX", "PYPL", "SQ", "SPOT", "UBER", "LYFT", "ABNB",
    "TSLA", "F", "GM", "TM", "HMC", "WMT", "TGT", "DLTR", "DG", "BKNG",
]


@router.get("/universe")
def get_universe():
    """Return the list of tickers in the default screener universe."""
    return {"tickers": DEFAULT_UNIVERSE, "count": len(DEFAULT_UNIVERSE)}


@router.post("/filter", response_model=List[ScreenerResult])
def filter_stocks(filters: ScreenerFilter):
    """
    Apply multi-criteria screening to find value stocks.

    Pass a list of tickers to screen, or leave empty to use the default universe.
    All filter criteria are optional — omit any to skip that filter.
    """
    tickers = filters.tickers or DEFAULT_UNIVERSE

    criteria = filters.model_dump(exclude={"tickers"}, exclude_none=True)

    results = []
    for ticker in tickers:
        result = screen_stock(ticker, criteria)
        if result:
            results.append(result)

    # Sort by moat score descending
    results.sort(key=lambda r: r.get("moat_score", 0) or 0, reverse=True)
    return results


@router.get("/quotes")
def bulk_quotes(tickers: str = Query(..., description="Comma-separated ticker symbols")):
    """
    Fetch real-time quotes for multiple tickers at once.
    Example: ?tickers=AAPL,MSFT,GOOGL
    """
    ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    if not ticker_list:
        raise HTTPException(status_code=400, detail="No tickers provided")
    if len(ticker_list) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 tickers per request")
    return get_bulk_quotes(ticker_list)


@router.get("/market")
def market_overview():
    """Current levels for S&P 500, NASDAQ, and Dow Jones."""
    return get_market_indices()


@router.get("/sectors")
def sectors(period: str = Query("1y", description="Performance period: 1mo,3mo,6mo,1y,3y,5y")):
    """Sector performance heatmap data via SPDR ETFs."""
    return get_sector_performance(period=period)


@router.get("/search")
def search(q: str = Query(..., min_length=1), limit: int = Query(20, le=50)):
    """Search for companies by name or ticker."""
    return search_tickers(q, limit=limit)
