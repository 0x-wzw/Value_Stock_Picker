from pydantic import BaseModel
from typing import Optional, List


class QuoteResponse(BaseModel):
    ticker: str
    price: Optional[float]
    open: Optional[float]
    high: Optional[float]
    low: Optional[float]
    volume: Optional[int]
    prev_close: Optional[float]
    change: Optional[float]
    change_pct: Optional[float]
    market_cap: Optional[int]
    pe_ratio: Optional[float]
    forward_pe: Optional[float]
    eps: Optional[float]
    week_52_high: Optional[float]
    week_52_low: Optional[float]
    avg_volume: Optional[int]
    currency: Optional[str]
    exchange: Optional[str]
    fetched_at: Optional[str]


class CompanyOverviewResponse(BaseModel):
    ticker: str
    name: Optional[str]
    sector: Optional[str]
    industry: Optional[str]
    exchange: Optional[str]
    currency: Optional[str]
    country: Optional[str]
    website: Optional[str]
    description: Optional[str]
    employees: Optional[int]
    market_cap: Optional[int]
    pe_ratio: Optional[float]
    price_to_book: Optional[float]
    gross_margin: Optional[float]
    operating_margin: Optional[float]
    profit_margin: Optional[float]
    roe: Optional[float]
    debt_to_equity: Optional[float]
    current_ratio: Optional[float]
    dividend_yield: Optional[float]
    beta: Optional[float]
    fetched_at: Optional[str]


class PricePoint(BaseModel):
    date: str
    open: Optional[float]
    high: Optional[float]
    low: Optional[float]
    close: Optional[float]
    volume: Optional[int]


class FilingResponse(BaseModel):
    form_type: str
    filing_date: Optional[str]
    report_date: Optional[str]
    accession_number: Optional[str]
    primary_document: Optional[str]
    document_url: Optional[str]
    filing_index_url: Optional[str]
    edgar_viewer_url: Optional[str]


class NewsItem(BaseModel):
    title: str
    publisher: Optional[str]
    link: Optional[str]
    published_at: Optional[str]
    type: Optional[str]
    thumbnail: Optional[str]


class KeyMetricsResponse(BaseModel):
    ticker: str
    enterprise_value: Optional[int]
    ev_to_fcf: Optional[float]
    fcf_yield_pct: Optional[float]
    roic_pct: Optional[float]
    owner_earnings_estimate: Optional[int]
    avg_fcf_5y: Optional[int]
    revenue_cagr_pct: Optional[float]
    roe_pct: Optional[float]
    gross_margin_pct: Optional[float]
    operating_margin_pct: Optional[float]
    debt_to_equity: Optional[float]
    current_ratio: Optional[float]
    fetched_at: Optional[str]
