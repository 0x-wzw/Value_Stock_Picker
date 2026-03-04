"""
data_service.py
---------------
Fetches real-time and static financial data from open sources:

  1. yfinance  — real-time quotes, historical prices, fundamentals
  2. SEC EDGAR — 10-K / 10-Q filings, XBRL company facts (open government data)
  3. SEC EDGAR full-text search — filing document list

All results are cached in-process with configurable TTLs so repeated requests
within the same server process avoid redundant network calls.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta
from typing import Any, Optional

import requests
import yfinance as yf
from cachetools import TTLCache, cached
from cachetools.keys import hashkey

from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# ---------------------------------------------------------------------------
# In-process caches
# ---------------------------------------------------------------------------
_price_cache: TTLCache = TTLCache(maxsize=500, ttl=settings.price_cache_ttl)
_fundamentals_cache: TTLCache = TTLCache(maxsize=200, ttl=settings.fundamentals_cache_ttl)
_history_cache: TTLCache = TTLCache(maxsize=200, ttl=settings.fundamentals_cache_ttl)
_filings_cache: TTLCache = TTLCache(maxsize=100, ttl=settings.filings_cache_ttl)
_sec_facts_cache: TTLCache = TTLCache(maxsize=100, ttl=settings.filings_cache_ttl)
_screener_cache: TTLCache = TTLCache(maxsize=50, ttl=settings.fundamentals_cache_ttl)

# SEC EDGAR base URLs
_EDGAR_BASE = "https://data.sec.gov"
_EDGAR_SEARCH = "https://efts.sec.gov/LATEST/search-index"
_EDGAR_COMPANY_SEARCH = "https://efts.sec.gov/LATEST/search-index"

_SEC_HEADERS = {
    "User-Agent": settings.sec_user_agent,
    "Accept-Encoding": "gzip, deflate",
    "Host": "data.sec.gov",
}

_SEC_SEARCH_HEADERS = {
    "User-Agent": settings.sec_user_agent,
    "Accept-Encoding": "gzip, deflate",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_float(value: Any) -> Optional[float]:
    """Convert a value to float, returning None on failure."""
    try:
        if value is None:
            return None
        f = float(value)
        return None if (f != f) else f  # filter NaN
    except (TypeError, ValueError):
        return None


def _safe_int(value: Any) -> Optional[int]:
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _pct(numerator: Any, denominator: Any) -> Optional[float]:
    """Return numerator / denominator as a percentage, or None."""
    n, d = _safe_float(numerator), _safe_float(denominator)
    if n is None or d is None or d == 0:
        return None
    return round(n / d * 100, 2)


# ---------------------------------------------------------------------------
# 1. Real-time price & quote data  (yfinance)
# ---------------------------------------------------------------------------

def get_realtime_quote(ticker: str) -> dict:
    """
    Fetch the latest real-time (delayed ~15 min) price data for a ticker.

    Returns a dict with keys:
        ticker, price, open, high, low, volume, prev_close,
        change, change_pct, market_cap, pe_ratio, eps,
        52w_high, 52w_low, avg_volume, currency, exchange,
        fetched_at
    """
    key = hashkey("quote", ticker.upper())
    if key in _price_cache:
        return _price_cache[key]

    try:
        t = yf.Ticker(ticker)
        info = t.info or {}

        quote = {
            "ticker": ticker.upper(),
            "price": _safe_float(info.get("currentPrice") or info.get("regularMarketPrice")),
            "open": _safe_float(info.get("regularMarketOpen")),
            "high": _safe_float(info.get("dayHigh") or info.get("regularMarketDayHigh")),
            "low": _safe_float(info.get("dayLow") or info.get("regularMarketDayLow")),
            "volume": _safe_int(info.get("regularMarketVolume")),
            "prev_close": _safe_float(info.get("previousClose") or info.get("regularMarketPreviousClose")),
            "market_cap": _safe_int(info.get("marketCap")),
            "pe_ratio": _safe_float(info.get("trailingPE")),
            "forward_pe": _safe_float(info.get("forwardPE")),
            "eps": _safe_float(info.get("trailingEps")),
            "52w_high": _safe_float(info.get("fiftyTwoWeekHigh")),
            "52w_low": _safe_float(info.get("fiftyTwoWeekLow")),
            "avg_volume": _safe_int(info.get("averageVolume")),
            "currency": info.get("currency", "USD"),
            "exchange": info.get("exchange", ""),
            "fetched_at": datetime.utcnow().isoformat(),
        }

        price = quote["price"]
        prev = quote["prev_close"]
        if price is not None and prev is not None and prev != 0:
            quote["change"] = round(price - prev, 4)
            quote["change_pct"] = round((price - prev) / prev * 100, 2)
        else:
            quote["change"] = None
            quote["change_pct"] = None

        _price_cache[key] = quote
        return quote

    except Exception as exc:
        logger.warning("get_realtime_quote(%s) failed: %s", ticker, exc)
        return {"ticker": ticker.upper(), "error": str(exc), "fetched_at": datetime.utcnow().isoformat()}


# ---------------------------------------------------------------------------
# 2. Historical price data  (yfinance)
# ---------------------------------------------------------------------------

def get_price_history(ticker: str, period: str = "5y", interval: str = "1d") -> list[dict]:
    """
    Fetch OHLCV price history.

    Args:
        ticker:   Stock ticker symbol
        period:   yfinance period string — "1mo","3mo","6mo","1y","2y","5y","10y","ytd","max"
        interval: yfinance interval — "1d","1wk","1mo"

    Returns list of dicts: {date, open, high, low, close, volume, adj_close}
    """
    key = hashkey("history", ticker.upper(), period, interval)
    if key in _history_cache:
        return _history_cache[key]

    try:
        t = yf.Ticker(ticker)
        df = t.history(period=period, interval=interval, auto_adjust=True)

        if df.empty:
            return []

        records = []
        for ts, row in df.iterrows():
            records.append({
                "date": ts.strftime("%Y-%m-%d"),
                "open": _safe_float(row.get("Open")),
                "high": _safe_float(row.get("High")),
                "low": _safe_float(row.get("Low")),
                "close": _safe_float(row.get("Close")),
                "volume": _safe_int(row.get("Volume")),
            })

        _history_cache[key] = records
        return records

    except Exception as exc:
        logger.warning("get_price_history(%s, %s) failed: %s", ticker, period, exc)
        return []


# ---------------------------------------------------------------------------
# 3. Company fundamentals  (yfinance)
# ---------------------------------------------------------------------------

def get_company_overview(ticker: str) -> dict:
    """
    Fetch static company metadata and key fundamentals.

    Returns a rich dict including sector, industry, description, key ratios,
    dividend yield, beta, etc.
    """
    key = hashkey("overview", ticker.upper())
    if key in _fundamentals_cache:
        return _fundamentals_cache[key]

    try:
        t = yf.Ticker(ticker)
        info = t.info or {}

        overview = {
            "ticker": ticker.upper(),
            "name": info.get("longName") or info.get("shortName", ""),
            "sector": info.get("sector", ""),
            "industry": info.get("industry", ""),
            "exchange": info.get("exchange", ""),
            "currency": info.get("currency", "USD"),
            "country": info.get("country", ""),
            "website": info.get("website", ""),
            "description": info.get("longBusinessSummary", ""),
            "employees": _safe_int(info.get("fullTimeEmployees")),

            # Valuation ratios
            "market_cap": _safe_int(info.get("marketCap")),
            "enterprise_value": _safe_int(info.get("enterpriseValue")),
            "pe_ratio": _safe_float(info.get("trailingPE")),
            "forward_pe": _safe_float(info.get("forwardPE")),
            "peg_ratio": _safe_float(info.get("pegRatio")),
            "price_to_book": _safe_float(info.get("priceToBook")),
            "price_to_sales": _safe_float(info.get("priceToSalesTrailing12Months")),
            "ev_to_ebitda": _safe_float(info.get("enterpriseToEbitda")),
            "ev_to_revenue": _safe_float(info.get("enterpriseToRevenue")),

            # Profitability
            "gross_margin": _safe_float(info.get("grossMargins")),
            "operating_margin": _safe_float(info.get("operatingMargins")),
            "profit_margin": _safe_float(info.get("profitMargins")),
            "roe": _safe_float(info.get("returnOnEquity")),
            "roa": _safe_float(info.get("returnOnAssets")),

            # Growth
            "revenue_growth": _safe_float(info.get("revenueGrowth")),
            "earnings_growth": _safe_float(info.get("earningsGrowth")),
            "earnings_quarterly_growth": _safe_float(info.get("earningsQuarterlyGrowth")),

            # Dividends & buybacks
            "dividend_yield": _safe_float(info.get("dividendYield")),
            "dividend_rate": _safe_float(info.get("dividendRate")),
            "payout_ratio": _safe_float(info.get("payoutRatio")),

            # Balance sheet health
            "current_ratio": _safe_float(info.get("currentRatio")),
            "debt_to_equity": _safe_float(info.get("debtToEquity")),
            "total_cash": _safe_int(info.get("totalCash")),
            "total_debt": _safe_int(info.get("totalDebt")),

            # Per-share metrics
            "eps_ttm": _safe_float(info.get("trailingEps")),
            "eps_forward": _safe_float(info.get("forwardEps")),
            "book_value_per_share": _safe_float(info.get("bookValue")),
            "revenue_per_share": _safe_float(info.get("revenuePerShare")),

            # Risk / market
            "beta": _safe_float(info.get("beta")),
            "52w_high": _safe_float(info.get("fiftyTwoWeekHigh")),
            "52w_low": _safe_float(info.get("fiftyTwoWeekLow")),
            "shares_outstanding": _safe_int(info.get("sharesOutstanding")),
            "float_shares": _safe_int(info.get("floatShares")),
            "short_ratio": _safe_float(info.get("shortRatio")),

            "fetched_at": datetime.utcnow().isoformat(),
        }

        _fundamentals_cache[key] = overview
        return overview

    except Exception as exc:
        logger.warning("get_company_overview(%s) failed: %s", ticker, exc)
        return {"ticker": ticker.upper(), "error": str(exc), "fetched_at": datetime.utcnow().isoformat()}


def get_financial_statements(ticker: str) -> dict:
    """
    Fetch multi-year income statement, balance sheet, and cash flow statement.

    Returns:
    {
        "income_statement":   [ { period, revenue, gross_profit, ... }, ... ],
        "balance_sheet":      [ { period, total_assets, total_debt, ... }, ... ],
        "cash_flow":          [ { period, operating_cf, capex, free_cash_flow, ... }, ... ],
        "fetched_at": "..."
    }
    """
    key = hashkey("financials", ticker.upper())
    if key in _fundamentals_cache:
        return _fundamentals_cache[key]

    try:
        t = yf.Ticker(ticker)

        # ---- Income Statement ----
        income = []
        try:
            df = t.financials  # annual; columns = periods, rows = line items
            if df is not None and not df.empty:
                for col in df.columns:
                    period_str = col.strftime("%Y-%m-%d") if hasattr(col, "strftime") else str(col)
                    row_dict = {str(k): _safe_float(v) for k, v in df[col].items()}
                    income.append({
                        "period": period_str,
                        "revenue": row_dict.get("Total Revenue"),
                        "gross_profit": row_dict.get("Gross Profit"),
                        "operating_income": row_dict.get("Operating Income"),
                        "ebit": row_dict.get("EBIT"),
                        "ebitda": row_dict.get("EBITDA"),
                        "net_income": row_dict.get("Net Income"),
                        "interest_expense": row_dict.get("Interest Expense"),
                        "tax_provision": row_dict.get("Tax Provision"),
                        "diluted_eps": row_dict.get("Diluted EPS"),
                        "basic_shares": row_dict.get("Basic Average Shares"),
                        "diluted_shares": row_dict.get("Diluted Average Shares"),
                    })
        except Exception as e:
            logger.debug("income statement fetch failed for %s: %s", ticker, e)

        # ---- Balance Sheet ----
        balance = []
        try:
            df = t.balance_sheet
            if df is not None and not df.empty:
                for col in df.columns:
                    period_str = col.strftime("%Y-%m-%d") if hasattr(col, "strftime") else str(col)
                    row_dict = {str(k): _safe_float(v) for k, v in df[col].items()}
                    balance.append({
                        "period": period_str,
                        "total_assets": row_dict.get("Total Assets"),
                        "total_liabilities": row_dict.get("Total Liabilities Net Minority Interest"),
                        "total_equity": row_dict.get("Stockholders Equity"),
                        "total_debt": row_dict.get("Total Debt"),
                        "long_term_debt": row_dict.get("Long Term Debt"),
                        "short_term_debt": row_dict.get("Current Debt"),
                        "cash_and_equivalents": row_dict.get("Cash And Cash Equivalents"),
                        "current_assets": row_dict.get("Current Assets"),
                        "current_liabilities": row_dict.get("Current Liabilities"),
                        "goodwill": row_dict.get("Goodwill"),
                        "retained_earnings": row_dict.get("Retained Earnings"),
                    })
        except Exception as e:
            logger.debug("balance sheet fetch failed for %s: %s", ticker, e)

        # ---- Cash Flow ----
        cashflow = []
        try:
            df = t.cashflow
            if df is not None and not df.empty:
                for col in df.columns:
                    period_str = col.strftime("%Y-%m-%d") if hasattr(col, "strftime") else str(col)
                    row_dict = {str(k): _safe_float(v) for k, v in df[col].items()}
                    operating = row_dict.get("Operating Cash Flow") or row_dict.get("Cash From Operating Activities")
                    capex = row_dict.get("Capital Expenditure")
                    fcf = None
                    if operating is not None and capex is not None:
                        fcf = operating + capex  # capex is negative in yfinance
                    cashflow.append({
                        "period": period_str,
                        "operating_cf": operating,
                        "capex": capex,
                        "free_cash_flow": fcf,
                        "investing_cf": row_dict.get("Investing Cash Flow"),
                        "financing_cf": row_dict.get("Financing Cash Flow"),
                        "depreciation_amortization": row_dict.get("Depreciation And Amortization"),
                        "stock_based_compensation": row_dict.get("Stock Based Compensation"),
                        "change_in_working_capital": row_dict.get("Change In Working Capital"),
                        "dividends_paid": row_dict.get("Payment Of Dividends"),
                        "share_repurchases": row_dict.get("Repurchase Of Capital Stock"),
                    })
        except Exception as e:
            logger.debug("cash flow fetch failed for %s: %s", ticker, e)

        result = {
            "ticker": ticker.upper(),
            "income_statement": income,
            "balance_sheet": balance,
            "cash_flow": cashflow,
            "fetched_at": datetime.utcnow().isoformat(),
        }

        _fundamentals_cache[key] = result
        return result

    except Exception as exc:
        logger.warning("get_financial_statements(%s) failed: %s", ticker, exc)
        return {
            "ticker": ticker.upper(),
            "income_statement": [],
            "balance_sheet": [],
            "cash_flow": [],
            "error": str(exc),
            "fetched_at": datetime.utcnow().isoformat(),
        }


def get_key_metrics(ticker: str) -> dict:
    """
    Compute derived value-investing metrics from raw financial data.

    Returns ROIC, FCF yield, owner earnings estimate, debt ratios, etc.
    """
    overview = get_company_overview(ticker)
    financials = get_financial_statements(ticker)

    cf_list = financials.get("cash_flow", [])
    bs_list = financials.get("balance_sheet", [])
    is_list = financials.get("income_statement", [])

    # Latest period data
    latest_cf = cf_list[0] if cf_list else {}
    latest_bs = bs_list[0] if bs_list else {}
    latest_is = is_list[0] if is_list else {}

    market_cap = _safe_float(overview.get("market_cap"))
    total_debt = _safe_float(latest_bs.get("total_debt"))
    cash = _safe_float(latest_bs.get("cash_and_equivalents"))
    fcf = _safe_float(latest_cf.get("free_cash_flow"))
    net_income = _safe_float(latest_is.get("net_income"))
    operating_income = _safe_float(latest_is.get("operating_income"))
    total_equity = _safe_float(latest_bs.get("total_equity"))
    total_assets = _safe_float(latest_bs.get("total_assets"))

    # Enterprise value
    ev = None
    if market_cap is not None and total_debt is not None and cash is not None:
        ev = market_cap + total_debt - cash

    # FCF yield = FCF / Market Cap
    fcf_yield = _pct(fcf, market_cap)

    # EV/FCF
    ev_to_fcf = None
    if ev and fcf and fcf > 0:
        ev_to_fcf = round(ev / fcf, 2)

    # ROIC = EBIT(1-t) / (Equity + Debt - Cash)
    # Approximation using operating income * (1 - 0.21)
    roic = None
    invested_capital = None
    if total_equity is not None and total_debt is not None:
        invested_capital = total_equity + (total_debt or 0) - (cash or 0)
    if operating_income is not None and invested_capital and invested_capital > 0:
        nopat = operating_income * 0.79  # rough after-tax
        roic = round(nopat / invested_capital * 100, 2)

    # Owner earnings = Net Income + D&A - Maintenance CapEx
    # Approximation: use 50% of CapEx as maintenance
    da = _safe_float(latest_cf.get("depreciation_amortization"))
    capex = _safe_float(latest_cf.get("capex"))
    owner_earnings = None
    if net_income is not None and da is not None and capex is not None:
        maintenance_capex = abs(capex) * 0.5
        owner_earnings = net_income + da - maintenance_capex

    # FCF 5-year average
    fcf_values = [
        _safe_float(c.get("free_cash_flow"))
        for c in cf_list[:5]
        if _safe_float(c.get("free_cash_flow")) is not None
    ]
    avg_fcf_5y = round(sum(fcf_values) / len(fcf_values), 0) if fcf_values else None

    # Revenue CAGR (5-year)
    rev_cagr = None
    if len(is_list) >= 2:
        rev_latest = _safe_float(is_list[0].get("revenue"))
        rev_oldest = _safe_float(is_list[-1].get("revenue"))
        years = len(is_list) - 1
        if rev_latest and rev_oldest and rev_oldest > 0 and years > 0:
            rev_cagr = round(((rev_latest / rev_oldest) ** (1 / years) - 1) * 100, 2)

    return {
        "ticker": ticker.upper(),
        "enterprise_value": _safe_int(ev),
        "ev_to_fcf": ev_to_fcf,
        "fcf_yield_pct": fcf_yield,
        "roic_pct": roic,
        "invested_capital": _safe_int(invested_capital),
        "owner_earnings_estimate": _safe_int(owner_earnings),
        "avg_fcf_5y": _safe_int(avg_fcf_5y),
        "revenue_cagr_pct": rev_cagr,
        # Pass through key ratios from overview
        "roe_pct": _safe_float(overview.get("roe")),
        "roa_pct": _safe_float(overview.get("roa")),
        "gross_margin_pct": _safe_float(overview.get("gross_margin")),
        "operating_margin_pct": _safe_float(overview.get("operating_margin")),
        "profit_margin_pct": _safe_float(overview.get("profit_margin")),
        "debt_to_equity": _safe_float(overview.get("debt_to_equity")),
        "current_ratio": _safe_float(overview.get("current_ratio")),
        "fetched_at": datetime.utcnow().isoformat(),
    }


# ---------------------------------------------------------------------------
# 4. Analyst data & news  (yfinance)
# ---------------------------------------------------------------------------

def get_analyst_data(ticker: str) -> dict:
    """Fetch analyst recommendations and earnings estimates."""
    key = hashkey("analyst", ticker.upper())
    if key in _fundamentals_cache:
        return _fundamentals_cache[key]

    try:
        t = yf.Ticker(ticker)
        result: dict = {"ticker": ticker.upper(), "fetched_at": datetime.utcnow().isoformat()}

        # Recommendations summary
        try:
            rec = t.recommendations
            if rec is not None and not rec.empty:
                # Most recent analyst consensus
                recent = rec.tail(10)
                result["recommendations"] = recent.reset_index().to_dict(orient="records")
        except Exception:
            result["recommendations"] = []

        # Earnings calendar
        try:
            cal = t.calendar
            if cal is not None:
                if hasattr(cal, "to_dict"):
                    result["earnings_calendar"] = cal.to_dict()
                elif isinstance(cal, dict):
                    result["earnings_calendar"] = cal
        except Exception:
            result["earnings_calendar"] = {}

        # Earnings estimates
        try:
            earnings_est = t.earnings_estimate
            if earnings_est is not None and not earnings_est.empty:
                result["earnings_estimates"] = earnings_est.to_dict(orient="index")
        except Exception:
            result["earnings_estimates"] = {}

        _fundamentals_cache[key] = result
        return result

    except Exception as exc:
        logger.warning("get_analyst_data(%s) failed: %s", ticker, exc)
        return {"ticker": ticker.upper(), "error": str(exc), "fetched_at": datetime.utcnow().isoformat()}


def get_news(ticker: str, limit: int = 10) -> list[dict]:
    """Fetch recent news headlines for a ticker via yfinance."""
    key = hashkey("news", ticker.upper(), limit)
    if key in _price_cache:
        return _price_cache[key]

    try:
        t = yf.Ticker(ticker)
        raw_news = t.news or []
        news = []
        for item in raw_news[:limit]:
            news.append({
                "title": item.get("title", ""),
                "publisher": item.get("publisher", ""),
                "link": item.get("link", ""),
                "published_at": datetime.utcfromtimestamp(
                    item.get("providerPublishTime", 0)
                ).isoformat() if item.get("providerPublishTime") else None,
                "type": item.get("type", ""),
                "thumbnail": (
                    item.get("thumbnail", {}).get("resolutions", [{}])[0].get("url")
                    if item.get("thumbnail") else None
                ),
            })
        _price_cache[key] = news
        return news

    except Exception as exc:
        logger.warning("get_news(%s) failed: %s", ticker, exc)
        return []


# ---------------------------------------------------------------------------
# 5. SEC EDGAR — CIK lookup & filings  (open government data)
# ---------------------------------------------------------------------------

def _get_cik_for_ticker(ticker: str) -> Optional[str]:
    """
    Resolve a stock ticker to its SEC CIK number using the EDGAR company
    tickers JSON (open data, no auth required).
    """
    key = hashkey("cik", ticker.upper())
    if key in _filings_cache:
        return _filings_cache[key]

    try:
        url = "https://www.sec.gov/files/company_tickers.json"
        resp = requests.get(url, headers=_SEC_SEARCH_HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        target = ticker.upper()
        for _, entry in data.items():
            if entry.get("ticker", "").upper() == target:
                cik = str(entry["cik_str"]).zfill(10)
                _filings_cache[key] = cik
                return cik

        logger.warning("CIK not found for ticker %s", ticker)
        return None

    except Exception as exc:
        logger.warning("_get_cik_for_ticker(%s) failed: %s", ticker, exc)
        return None


def get_sec_filings(ticker: str, form_types: list[str] | None = None, limit: int = 10) -> list[dict]:
    """
    Fetch a list of recent SEC filings from EDGAR for a given ticker.

    Args:
        ticker:     Stock ticker symbol
        form_types: List of form types to filter, e.g. ["10-K", "10-Q", "DEF 14A"]
                    If None, returns all filing types.
        limit:      Maximum number of filings to return

    Returns list of dicts:
    {
        form_type, filing_date, report_date, accession_number,
        document_url, description
    }
    """
    if form_types is None:
        form_types = ["10-K", "10-Q", "DEF 14A", "8-K"]

    key = hashkey("filings", ticker.upper(), tuple(sorted(form_types)), limit)
    if key in _filings_cache:
        return _filings_cache[key]

    cik = _get_cik_for_ticker(ticker)
    if not cik:
        return []

    try:
        url = f"{_EDGAR_BASE}/submissions/CIK{cik}.json"
        resp = requests.get(url, headers=_SEC_HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        filings_data = data.get("filings", {}).get("recent", {})
        forms = filings_data.get("form", [])
        dates = filings_data.get("filingDate", [])
        report_dates = filings_data.get("reportDate", [])
        accessions = filings_data.get("accessionNumber", [])
        descriptions = filings_data.get("primaryDocument", [])

        results = []
        for i, form in enumerate(forms):
            if form not in form_types:
                continue
            if len(results) >= limit:
                break

            acc = accessions[i].replace("-", "") if i < len(accessions) else ""
            doc = descriptions[i] if i < len(descriptions) else ""
            doc_url = (
                f"https://www.sec.gov/Archives/edgar/full-index/{dates[i][:4]}/"
                f"QTR{((int(dates[i][5:7]) - 1) // 3) + 1}/{accessions[i]}-index.htm"
                if acc else ""
            )
            # Direct viewer URL
            viewer_url = (
                f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany"
                f"&CIK={cik}&type={form}&dateb=&owner=include&count=10"
            )

            results.append({
                "form_type": form,
                "filing_date": dates[i] if i < len(dates) else "",
                "report_date": report_dates[i] if i < len(report_dates) else "",
                "accession_number": accessions[i] if i < len(accessions) else "",
                "primary_document": doc,
                "document_url": (
                    f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/"
                    f"{acc}/{doc}"
                    if acc and doc else ""
                ),
                "filing_index_url": (
                    f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/"
                    f"{acc}/{accessions[i]}-index.htm"
                    if acc else ""
                ),
                "edgar_viewer_url": viewer_url,
            })

        _filings_cache[key] = results
        return results

    except Exception as exc:
        logger.warning("get_sec_filings(%s) failed: %s", ticker, exc)
        return []


def get_sec_company_facts(ticker: str) -> dict:
    """
    Fetch XBRL company facts from SEC EDGAR — a structured dataset of all
    reported financial figures across all filings.

    This is the most authoritative source for historical reported numbers
    directly from SEC submissions.

    Returns the raw EDGAR company-facts JSON enriched with ticker + CIK.
    """
    key = hashkey("sec_facts", ticker.upper())
    if key in _sec_facts_cache:
        return _sec_facts_cache[key]

    cik = _get_cik_for_ticker(ticker)
    if not cik:
        return {"ticker": ticker.upper(), "error": "CIK not found"}

    try:
        url = f"{_EDGAR_BASE}/api/xbrl/companyfacts/CIK{cik}.json"
        resp = requests.get(url, headers=_SEC_HEADERS, timeout=20)
        resp.raise_for_status()
        data = resp.json()

        result = {
            "ticker": ticker.upper(),
            "cik": cik,
            "entity_name": data.get("entityName", ""),
            "facts": data.get("facts", {}),
            "fetched_at": datetime.utcnow().isoformat(),
        }
        _sec_facts_cache[key] = result
        return result

    except Exception as exc:
        logger.warning("get_sec_company_facts(%s) failed: %s", ticker, exc)
        return {"ticker": ticker.upper(), "cik": cik, "error": str(exc), "fetched_at": datetime.utcnow().isoformat()}


def get_sec_key_facts(ticker: str) -> dict:
    """
    Extract key financial facts from SEC XBRL data — a curated subset of
    the most useful reported values (revenues, assets, shares, etc.).

    Returns a dict of concept → list of {period, value, unit, form} records,
    filtered to annual (10-K) filings.
    """
    key = hashkey("sec_key_facts", ticker.upper())
    if key in _sec_facts_cache:
        return _sec_facts_cache[key]

    raw = get_sec_company_facts(ticker)
    if "error" in raw:
        return raw

    facts = raw.get("facts", {})
    us_gaap = facts.get("us-gaap", {})

    # Concepts we care about for value investing
    concepts_of_interest = {
        "Revenues": "revenue",
        "RevenueFromContractWithCustomerExcludingAssessedTax": "revenue_alt",
        "NetIncomeLoss": "net_income",
        "OperatingIncomeLoss": "operating_income",
        "EarningsPerShareDiluted": "eps_diluted",
        "CommonStockSharesOutstanding": "shares_outstanding",
        "Assets": "total_assets",
        "Liabilities": "total_liabilities",
        "StockholdersEquity": "stockholders_equity",
        "LongTermDebt": "long_term_debt",
        "CashAndCashEquivalentsAtCarryingValue": "cash",
        "NetCashProvidedByUsedInOperatingActivities": "operating_cf",
        "PaymentsToAcquirePropertyPlantAndEquipment": "capex",
        "DepreciationDepletionAndAmortization": "depreciation",
        "GrossProfit": "gross_profit",
        "ResearchAndDevelopmentExpense": "rd_expense",
        "DividendsCommonStockCash": "dividends_paid",
    }

    extracted: dict = {
        "ticker": ticker.upper(),
        "cik": raw.get("cik"),
        "entity_name": raw.get("entity_name"),
        "fetched_at": datetime.utcnow().isoformat(),
    }

    for gaap_name, friendly_name in concepts_of_interest.items():
        concept_data = us_gaap.get(gaap_name, {})
        units = concept_data.get("units", {})

        # Prefer USD units, fall back to shares
        unit_data = units.get("USD") or units.get("shares") or []

        # Keep only 10-K annual filings; deduplicate by fiscal year end
        annual_records: dict[str, dict] = {}
        for entry in unit_data:
            if entry.get("form") != "10-K":
                continue
            # Use the end date as the period key
            period_end = entry.get("end", "")
            if not period_end:
                continue
            # Keep the most recent filing for each period
            existing = annual_records.get(period_end)
            if existing is None or entry.get("filed", "") > existing.get("filed", ""):
                annual_records[period_end] = {
                    "period_end": period_end,
                    "value": entry.get("val"),
                    "unit": next(iter(units.keys()), ""),
                    "accession": entry.get("accn", ""),
                    "filed": entry.get("filed", ""),
                }

        # Sort descending by period
        records = sorted(annual_records.values(), key=lambda r: r["period_end"], reverse=True)
        extracted[friendly_name] = records[:10]  # last 10 annual periods

    _sec_facts_cache[key] = extracted
    return extracted


# ---------------------------------------------------------------------------
# 6. Bulk ticker search / screener support  (yfinance)
# ---------------------------------------------------------------------------

def search_tickers(query: str, limit: int = 20) -> list[dict]:
    """
    Search for tickers/companies matching a query string.

    Uses yfinance's search functionality, which internally calls the
    Yahoo Finance search API.
    """
    key = hashkey("search", query.lower(), limit)
    if key in _screener_cache:
        return _screener_cache[key]

    try:
        results = []
        # yfinance search
        search = yf.Search(query, max_results=limit)
        quotes = search.quotes or []
        for q in quotes[:limit]:
            results.append({
                "ticker": q.get("symbol", ""),
                "name": q.get("longname") or q.get("shortname", ""),
                "exchange": q.get("exchange", ""),
                "type": q.get("quoteType", ""),
                "sector": q.get("sector", ""),
                "industry": q.get("industry", ""),
            })

        _screener_cache[key] = results
        return results

    except Exception as exc:
        logger.warning("search_tickers(%s) failed: %s", query, exc)
        return []


def get_bulk_quotes(tickers: list[str]) -> dict[str, dict]:
    """
    Fetch real-time quotes for multiple tickers efficiently using
    yfinance's batch download capability.

    Returns: { "AAPL": {price, change_pct, market_cap, ...}, ... }
    """
    if not tickers:
        return {}

    key = hashkey("bulk_quotes", tuple(sorted(t.upper() for t in tickers)))
    if key in _price_cache:
        return _price_cache[key]

    try:
        symbols = " ".join(t.upper() for t in tickers)
        data = yf.download(
            symbols,
            period="2d",
            interval="1d",
            auto_adjust=True,
            progress=False,
            group_by="ticker",
        )

        result: dict[str, dict] = {}
        for ticker in tickers:
            sym = ticker.upper()
            try:
                if len(tickers) == 1:
                    close_series = data["Close"]
                else:
                    close_series = data["Close"][sym]

                closes = close_series.dropna()
                if len(closes) >= 2:
                    prev_close = float(closes.iloc[-2])
                    curr_price = float(closes.iloc[-1])
                    change_pct = round((curr_price - prev_close) / prev_close * 100, 2)
                elif len(closes) == 1:
                    curr_price = float(closes.iloc[-1])
                    prev_close = curr_price
                    change_pct = 0.0
                else:
                    result[sym] = {"ticker": sym, "error": "no data"}
                    continue

                result[sym] = {
                    "ticker": sym,
                    "price": round(curr_price, 4),
                    "prev_close": round(prev_close, 4),
                    "change_pct": change_pct,
                    "fetched_at": datetime.utcnow().isoformat(),
                }
            except Exception as e:
                logger.debug("bulk quote parse failed for %s: %s", sym, e)
                result[sym] = {"ticker": sym, "error": str(e)}

        _price_cache[key] = result
        return result

    except Exception as exc:
        logger.warning("get_bulk_quotes failed: %s", exc)
        return {t.upper(): {"ticker": t.upper(), "error": str(exc)} for t in tickers}


# ---------------------------------------------------------------------------
# 7. Sector & market-wide data  (yfinance)
# ---------------------------------------------------------------------------

# Standard SPDR sector ETFs used as proxies for sector performance
SECTOR_ETFS = {
    "Technology": "XLK",
    "Health Care": "XLV",
    "Financials": "XLF",
    "Consumer Discretionary": "XLY",
    "Consumer Staples": "XLP",
    "Energy": "XLE",
    "Utilities": "XLU",
    "Real Estate": "XLRE",
    "Materials": "XLB",
    "Industrials": "XLI",
    "Communication Services": "XLC",
}

S_AND_P_500_TICKER = "^GSPC"
NASDAQ_TICKER = "^IXIC"
DOW_TICKER = "^DJI"


def get_market_indices() -> dict:
    """Fetch current levels for the major U.S. market indices."""
    key = hashkey("indices")
    if key in _price_cache:
        return _price_cache[key]

    indices = {
        "S&P 500": S_AND_P_500_TICKER,
        "NASDAQ": NASDAQ_TICKER,
        "Dow Jones": DOW_TICKER,
    }
    result = {}
    for name, sym in indices.items():
        quote = get_realtime_quote(sym)
        result[name] = {
            "symbol": sym,
            "price": quote.get("price"),
            "change_pct": quote.get("change_pct"),
            "fetched_at": quote.get("fetched_at"),
        }

    _price_cache[key] = result
    return result


def get_sector_performance(period: str = "1y") -> list[dict]:
    """
    Fetch performance for all major S&P 500 sectors via sector ETFs.

    Returns list of dicts: {sector, etf, ytd_return_pct, pe_ratio, ...}
    """
    key = hashkey("sector_perf", period)
    if key in _screener_cache:
        return _screener_cache[key]

    results = []
    for sector, etf in SECTOR_ETFS.items():
        try:
            t = yf.Ticker(etf)
            info = t.info or {}
            hist = t.history(period=period, interval="1mo", auto_adjust=True)

            perf = None
            if not hist.empty and len(hist) >= 2:
                start_price = float(hist["Close"].iloc[0])
                end_price = float(hist["Close"].iloc[-1])
                if start_price > 0:
                    perf = round((end_price - start_price) / start_price * 100, 2)

            results.append({
                "sector": sector,
                "etf": etf,
                "current_price": _safe_float(info.get("regularMarketPrice")),
                "performance_pct": perf,
                "period": period,
                "pe_ratio": _safe_float(info.get("trailingPE")),
                "ytd_return": _safe_float(info.get("ytdReturn")),
                "three_year_return": _safe_float(info.get("threeYearAverageReturn")),
                "five_year_return": _safe_float(info.get("fiveYearAverageReturn")),
            })
        except Exception as e:
            logger.debug("sector performance failed for %s: %s", etf, e)
            results.append({"sector": sector, "etf": etf, "error": str(e)})

    _screener_cache[key] = results
    return results


# ---------------------------------------------------------------------------
# 8. Institutional holdings & insider data  (yfinance)
# ---------------------------------------------------------------------------

def get_institutional_holders(ticker: str) -> list[dict]:
    """Fetch top institutional holders from yfinance."""
    key = hashkey("inst_holders", ticker.upper())
    if key in _fundamentals_cache:
        return _fundamentals_cache[key]

    try:
        t = yf.Ticker(ticker)
        df = t.institutional_holders
        if df is None or df.empty:
            return []

        records = []
        for _, row in df.iterrows():
            records.append({
                "holder": str(row.get("Holder", "")),
                "shares": _safe_int(row.get("Shares")),
                "date_reported": (
                    row["Date Reported"].strftime("%Y-%m-%d")
                    if hasattr(row.get("Date Reported"), "strftime") else str(row.get("Date Reported", ""))
                ),
                "pct_held": _safe_float(row.get("% Out")),
                "value": _safe_int(row.get("Value")),
            })

        _fundamentals_cache[key] = records
        return records

    except Exception as exc:
        logger.warning("get_institutional_holders(%s) failed: %s", ticker, exc)
        return []


def get_insider_transactions(ticker: str) -> list[dict]:
    """Fetch recent insider buy/sell transactions from yfinance."""
    key = hashkey("insider", ticker.upper())
    if key in _fundamentals_cache:
        return _fundamentals_cache[key]

    try:
        t = yf.Ticker(ticker)
        df = t.insider_transactions
        if df is None or df.empty:
            return []

        records = []
        for _, row in df.iterrows():
            records.append({
                "insider": str(row.get("Insider", "")),
                "relation": str(row.get("Relation", "")),
                "transaction": str(row.get("Transaction", "")),
                "date": (
                    row["Start Date"].strftime("%Y-%m-%d")
                    if hasattr(row.get("Start Date"), "strftime") else str(row.get("Start Date", ""))
                ),
                "shares": _safe_int(row.get("#Shares")),
                "value": _safe_int(row.get("Value")),
                "shares_total": _safe_int(row.get("Shares Total")),
            })

        _fundamentals_cache[key] = records
        return records

    except Exception as exc:
        logger.warning("get_insider_transactions(%s) failed: %s", ticker, exc)
        return []


# ---------------------------------------------------------------------------
# 9. Options data  (yfinance) — useful for implied volatility / market sentiment
# ---------------------------------------------------------------------------

def get_options_summary(ticker: str) -> dict:
    """
    Fetch nearest-term options chain summary for market sentiment analysis.
    Returns implied volatility, put/call ratio, and nearest expiry data.
    """
    key = hashkey("options", ticker.upper())
    if key in _price_cache:
        return _price_cache[key]

    try:
        t = yf.Ticker(ticker)
        expirations = t.options
        if not expirations:
            return {"ticker": ticker.upper(), "available": False}

        # Use nearest expiry
        nearest_exp = expirations[0]
        chain = t.option_chain(nearest_exp)

        calls_df = chain.calls
        puts_df = chain.puts

        total_call_oi = _safe_int(calls_df["openInterest"].sum()) if not calls_df.empty else 0
        total_put_oi = _safe_int(puts_df["openInterest"].sum()) if not puts_df.empty else 0
        put_call_ratio = round(total_put_oi / total_call_oi, 3) if total_call_oi else None

        # ATM implied vol (approximate)
        current_price = get_realtime_quote(ticker).get("price")
        atm_iv = None
        if current_price and not calls_df.empty:
            calls_df = calls_df.copy()
            calls_df["strike_diff"] = abs(calls_df["strike"] - current_price)
            atm_call = calls_df.nsmallest(1, "strike_diff")
            if not atm_call.empty:
                atm_iv = _safe_float(atm_call["impliedVolatility"].iloc[0])

        result = {
            "ticker": ticker.upper(),
            "available": True,
            "nearest_expiry": nearest_exp,
            "total_expirations": len(expirations),
            "put_call_ratio": put_call_ratio,
            "total_call_open_interest": total_call_oi,
            "total_put_open_interest": total_put_oi,
            "atm_implied_volatility": atm_iv,
            "fetched_at": datetime.utcnow().isoformat(),
        }

        _price_cache[key] = result
        return result

    except Exception as exc:
        logger.warning("get_options_summary(%s) failed: %s", ticker, exc)
        return {"ticker": ticker.upper(), "available": False, "error": str(exc)}


# ---------------------------------------------------------------------------
# 10. Cache management utilities
# ---------------------------------------------------------------------------

def clear_ticker_cache(ticker: str) -> None:
    """Evict all cached data for a specific ticker."""
    sym = ticker.upper()
    caches = [_price_cache, _fundamentals_cache, _history_cache, _filings_cache, _sec_facts_cache]
    for cache in caches:
        keys_to_delete = [k for k in list(cache.keys()) if sym in str(k)]
        for k in keys_to_delete:
            cache.pop(k, None)
    logger.info("Cache cleared for %s", sym)


def get_cache_stats() -> dict:
    """Return current cache utilisation statistics."""
    return {
        "price_cache": {"size": len(_price_cache), "maxsize": _price_cache.maxsize, "ttl": _price_cache.ttl},
        "fundamentals_cache": {"size": len(_fundamentals_cache), "maxsize": _fundamentals_cache.maxsize, "ttl": _fundamentals_cache.ttl},
        "history_cache": {"size": len(_history_cache), "maxsize": _history_cache.maxsize, "ttl": _history_cache.ttl},
        "filings_cache": {"size": len(_filings_cache), "maxsize": _filings_cache.maxsize, "ttl": _filings_cache.ttl},
        "sec_facts_cache": {"size": len(_sec_facts_cache), "maxsize": _sec_facts_cache.maxsize, "ttl": _sec_facts_cache.ttl},
        "screener_cache": {"size": len(_screener_cache), "maxsize": _screener_cache.maxsize, "ttl": _screener_cache.ttl},
    }
