from pydantic import BaseModel, Field
from typing import Optional, List


class ScreenerFilter(BaseModel):
    tickers: Optional[List[str]] = None  # explicit list, OR use filters below

    # Profitability
    min_roic: Optional[float] = Field(None, description="Minimum ROIC (%)")
    min_gross_margin: Optional[float] = Field(None, description="Minimum gross margin (0-1)")
    min_operating_margin: Optional[float] = Field(None, description="Minimum operating margin (0-1)")

    # Valuation
    max_pe: Optional[float] = Field(None, description="Maximum P/E ratio")
    min_fcf_yield: Optional[float] = Field(None, description="Minimum FCF yield (%)")

    # Balance sheet
    max_debt_to_equity: Optional[float] = Field(None, description="Maximum debt/equity")
    min_current_ratio: Optional[float] = Field(None, description="Minimum current ratio")

    # Size
    min_market_cap: Optional[int] = Field(None, description="Minimum market cap (USD)")
    max_market_cap: Optional[int] = Field(None, description="Maximum market cap (USD)")

    # Classification
    sectors: Optional[List[str]] = Field(None, description="Filter by sector(s)")


class ScreenerResult(BaseModel):
    ticker: str
    name: Optional[str]
    sector: Optional[str]
    industry: Optional[str]
    market_cap: Optional[int]
    pe_ratio: Optional[float]
    price_to_book: Optional[float]
    ev_to_ebitda: Optional[float]
    gross_margin: Optional[float]
    operating_margin: Optional[float]
    roe: Optional[float]
    debt_to_equity: Optional[float]
    current_ratio: Optional[float]
    roic_pct: Optional[float]
    fcf_yield_pct: Optional[float]
    revenue_cagr_pct: Optional[float]
    moat_score: Optional[int]
    dividend_yield: Optional[float]
