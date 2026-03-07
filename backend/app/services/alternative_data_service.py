"""
alternative_data_service.py
---------------------------
Supplementary open-source financial data:

  1. SEC EDGAR 13F    — institutional holdings from any fund's quarterly 13F
  2. S&P 500 list     — current constituents via Wikipedia (open, no key)
  3. Industry peers   — find peers via shared GICS sector/industry
  4. Guru holdings    — well-known value investors' 13F portfolios
                        (Berkshire Hathaway, Sequoia Fund, etc.)
  5. Buffett Indicator — total market cap / GDP ratio (Wilshire 5000 / GDP)
"""

from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional

import requests
from cachetools import TTLCache
from cachetools.keys import hashkey

from app.config import get_settings
from app.services.data_service import _get_cik_for_ticker, _EDGAR_BASE, _SEC_HEADERS

logger = logging.getLogger(__name__)
settings = get_settings()

_ALT_CACHE: TTLCache  = TTLCache(maxsize=100, ttl=86_400)   # 24h for static lists
_FILING_CACHE: TTLCache = TTLCache(maxsize=50, ttl=21_600)  # 6h for 13F data

_TIMEOUT = 15

# ---------------------------------------------------------------------------
# 1. S&P 500 constituents  — Wikipedia (open, no key)
# ---------------------------------------------------------------------------

SP500_WIKI_URL = (
    "https://en.wikipedia.org/w/api.php?action=parse&page=List_of_S%26P_500_companies"
    "&prop=wikitext&format=json"
)


def get_sp500_constituents() -> list[dict]:
    """
    Fetch the current S&P 500 constituent list from Wikipedia.

    Returns list of dicts:
    {ticker, company, gics_sector, gics_sub_industry, headquarters, date_added}
    """
    key = hashkey("sp500")
    if key in _ALT_CACHE:
        return _ALT_CACHE[key]

    try:
        resp = requests.get(SP500_WIKI_URL, timeout=_TIMEOUT)
        resp.raise_for_status()
        wikitext = resp.json().get("parse", {}).get("wikitext", {}).get("*", "")

        # Parse wiki table — each row: | ticker || company || GICS sector || ...
        rows = []
        in_table = False
        current_cells: list[str] = []

        for line in wikitext.split("\n"):
            if "|-" in line and in_table:
                if current_cells:
                    rows.append(current_cells)
                current_cells = []
            elif line.startswith("|") and not line.startswith("|-") and not line.startswith("|+"):
                in_table = True
                # Strip wiki markup
                cell = re.sub(r"\[\[([^\]|]+\|)?([^\]]+)\]\]", r"\2", line[1:]).strip()
                cell = re.sub(r"\{\{.*?\}\}", "", cell)
                cell = re.sub(r"<[^>]+>", "", cell).strip()
                cell = cell.strip("|").strip()
                if cell:
                    current_cells.append(cell)

        if current_cells:
            rows.append(current_cells)

        constituents = []
        for row in rows:
            if len(row) >= 4:
                ticker_raw = row[0].replace(".", "-")  # BRK.B → BRK-B
                ticker = re.sub(r"\s+.*", "", ticker_raw).strip()
                if not ticker or not re.match(r"^[A-Z\-\.]{1,6}$", ticker):
                    continue
                constituents.append({
                    "ticker":           ticker,
                    "company":          row[1].strip() if len(row) > 1 else "",
                    "gics_sector":      row[2].strip() if len(row) > 2 else "",
                    "gics_sub_industry": row[3].strip() if len(row) > 3 else "",
                    "headquarters":     row[4].strip() if len(row) > 4 else "",
                    "date_added":       row[5].strip() if len(row) > 5 else "",
                })

        if not constituents:
            # Fallback: hardcoded representative list
            constituents = _SP500_FALLBACK

        _ALT_CACHE[key] = constituents
        return constituents

    except Exception as exc:
        logger.warning("get_sp500_constituents failed: %s", exc)
        return _SP500_FALLBACK


def get_sp500_by_sector() -> dict[str, list[dict]]:
    """Group S&P 500 constituents by GICS sector."""
    key = hashkey("sp500_sectors")
    if key in _ALT_CACHE:
        return _ALT_CACHE[key]

    constituents = get_sp500_constituents()
    by_sector: dict[str, list] = {}
    for c in constituents:
        sector = c.get("gics_sector", "Unknown")
        by_sector.setdefault(sector, []).append(c)

    _ALT_CACHE[key] = by_sector
    return by_sector


# ---------------------------------------------------------------------------
# 2. SEC 13F — institutional holdings
#    Source: https://data.sec.gov  (no key required)
# ---------------------------------------------------------------------------

# Well-known value investor CIK numbers for convenient access
GURU_CIKS = {
    "berkshire_hathaway":  "0001067983",
    "sequoia_fund":        "0000083377",
    "fairfax_financial":   "0001005985",
    "markel_corp":         "0001096343",
    "davis_advisors":      "0000310485",
    "first_eagle":         "0000036270",
    "greenlight_capital":  "0001079114",
    "baupost_group":       "0001061768",
    "third_point":         "0001040273",
    "pershing_square":     "0001336528",
}

GURU_LABELS = {
    "berkshire_hathaway":  "Berkshire Hathaway (Warren Buffett)",
    "sequoia_fund":        "Sequoia Fund (Ruane, Cunniff)",
    "fairfax_financial":   "Fairfax Financial (Prem Watsa)",
    "markel_corp":         "Markel Corp (Tom Gayner)",
    "davis_advisors":      "Davis Advisors (Christopher Davis)",
    "first_eagle":         "First Eagle Investments",
    "greenlight_capital":  "Greenlight Capital (David Einhorn)",
    "baupost_group":       "Baupost Group (Seth Klarman)",
    "third_point":         "Third Point (Dan Loeb)",
    "pershing_square":     "Pershing Square (Bill Ackman)",
}


def get_13f_holdings(cik_or_fund: str, limit: int = 50) -> dict:
    """
    Fetch the most recent 13F-HR institutional holdings for a fund.

    Args:
        cik_or_fund: CIK number (10 digits) OR a key from GURU_CIKS
                     (e.g. "berkshire_hathaway")
        limit:       Maximum number of holdings to return

    Returns:
    {
        "fund":        "Berkshire Hathaway (Warren Buffett)",
        "filing_date": "2024-11-14",
        "period":      "2024-09-30",
        "holdings": [
            {"cusip", "ticker", "company", "shares", "value_usd", "pct_portfolio"},
            ...
        ],
        "total_value_usd": 300_000_000_000
    }
    """
    key = hashkey("13f", cik_or_fund, limit)
    if key in _FILING_CACHE:
        return _FILING_CACHE[key]

    # Resolve CIK
    if cik_or_fund in GURU_CIKS:
        cik = GURU_CIKS[cik_or_fund]
        fund_label = GURU_LABELS.get(cik_or_fund, cik_or_fund)
    else:
        cik = str(cik_or_fund).zfill(10)
        fund_label = cik

    try:
        # 1. Get filing list for this CIK
        submissions_url = f"{_EDGAR_BASE}/submissions/CIK{cik}.json"
        resp = requests.get(submissions_url, headers=_SEC_HEADERS, timeout=_TIMEOUT)
        resp.raise_for_status()
        sub_data = resp.json()

        fund_label = sub_data.get("name", fund_label)

        # 2. Find most recent 13F-HR filing
        recent = sub_data.get("filings", {}).get("recent", {})
        forms      = recent.get("form", [])
        dates      = recent.get("filingDate", [])
        report_dates = recent.get("reportDate", [])
        accessions = recent.get("accessionNumber", [])

        filing_idx = next(
            (i for i, f in enumerate(forms) if "13F-HR" in f),
            None
        )
        if filing_idx is None:
            return {"fund": fund_label, "cik": cik, "error": "No 13F-HR filing found"}

        acc = accessions[filing_idx]
        filing_date = dates[filing_idx] if filing_idx < len(dates) else ""
        period_date = report_dates[filing_idx] if filing_idx < len(report_dates) else ""
        acc_clean   = acc.replace("-", "")

        # 3. Fetch the filing index to find the XML document
        index_url = (
            f"https://www.sec.gov/Archives/edgar/data/{int(cik)}"
            f"/{acc_clean}/{acc}-index.htm"
        )

        # Try to find the infotable XML directly
        # EDGAR 13F documents follow a naming pattern
        doc_resp = requests.get(
            f"https://www.sec.gov/cgi-bin/browse-edgar"
            f"?action=getcompany&CIK={cik}&type=13F-HR&dateb=&owner=include&count=5&search_text=",
            headers=_SEC_HEADERS,
            timeout=_TIMEOUT,
        )

        # 4. Fetch the primary document — try known filename patterns
        holdings = _parse_13f_xml(cik, acc_clean, acc)

        if not holdings:
            return {
                "fund":         fund_label,
                "cik":          cik,
                "filing_date":  filing_date,
                "period":       period_date,
                "holdings":     [],
                "error":        "Could not parse 13F holdings XML",
                "edgar_url":    f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=13F-HR",
            }

        # Compute portfolio percentages
        total_value = sum(h.get("value_usd", 0) or 0 for h in holdings)
        for h in holdings:
            v = h.get("value_usd") or 0
            h["pct_portfolio"] = round(v / total_value * 100, 2) if total_value else None

        # Sort by value descending, take top N
        holdings.sort(key=lambda h: h.get("value_usd") or 0, reverse=True)

        result = {
            "fund":           fund_label,
            "cik":            cik,
            "filing_date":    filing_date,
            "period":         period_date,
            "total_holdings": len(holdings),
            "total_value_usd": total_value,
            "holdings":        holdings[:limit],
            "source":          "SEC EDGAR",
            "edgar_url":       f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=13F-HR",
            "fetched_at":      datetime.utcnow().isoformat(),
        }

        _FILING_CACHE[key] = result
        return result

    except Exception as exc:
        logger.warning("get_13f_holdings(%s) failed: %s", cik_or_fund, exc)
        return {
            "fund":      fund_label,
            "cik":       cik,
            "holdings":  [],
            "error":     str(exc),
            "fetched_at": datetime.utcnow().isoformat(),
        }


def _parse_13f_xml(cik: str, acc_clean: str, acc: str) -> list[dict]:
    """
    Attempt to fetch and parse the 13F infotable XML from EDGAR.
    Tries common filename patterns used by EDGAR filers.
    """
    cik_int = int(cik)

    # Try to get the filing index page to find the infotable document
    candidates = [
        f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc_clean}/infotable.xml",
        f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc_clean}/form13fInfoTable.xml",
        f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc_clean}/0001{acc_clean[-12:]}.xml",
    ]

    # Also try fetching the filing index to find the actual document
    try:
        idx_url = (
            f"https://www.sec.gov/Archives/edgar/data/{cik_int}"
            f"/{acc_clean}/{acc}-index.json"
        )
        idx_resp = requests.get(idx_url, headers=_SEC_HEADERS, timeout=_TIMEOUT)
        if idx_resp.ok:
            idx_data = idx_resp.json()
            for doc in idx_data.get("directory", {}).get("item", []):
                name = doc.get("name", "")
                if "infotable" in name.lower() or "13f" in name.lower():
                    if name.endswith(".xml"):
                        candidates.insert(0,
                            f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc_clean}/{name}"
                        )
    except Exception:
        pass

    for url in candidates:
        try:
            resp = requests.get(url, headers=_SEC_HEADERS, timeout=_TIMEOUT)
            if not resp.ok:
                continue
            return _parse_13f_holdings_xml(resp.text)
        except Exception:
            continue

    return []


def _parse_13f_holdings_xml(xml_text: str) -> list[dict]:
    """Parse SEC 13F infotable XML into a list of holding dicts."""
    try:
        # SEC 13F XML has a namespace we need to handle
        # Strip namespaces for simpler parsing
        xml_clean = re.sub(r' xmlns[^"]*"[^"]*"', "", xml_text)
        xml_clean = re.sub(r"ns\d+:", "", xml_clean)

        root = ET.fromstring(xml_clean)

        holdings = []
        for entry in root.iter("infoTable"):
            def _txt(tag: str) -> str:
                el = entry.find(tag)
                return el.text.strip() if el is not None and el.text else ""

            shares_el = entry.find(".//sshPrnamt")
            shares = int(shares_el.text.replace(",", "")) if shares_el is not None and shares_el.text else None

            value_el = entry.find("value")
            # 13F values are in thousands of dollars
            value_usd = int(value_el.text.replace(",", "")) * 1000 if value_el is not None and value_el.text else None

            holdings.append({
                "cusip":         _txt("cusip"),
                "company":       _txt("nameOfIssuer"),
                "title":         _txt("titleOfClass"),
                "shares":        shares,
                "value_usd":     value_usd,
                "option_type":   _txt("putCall") or None,
                "investment_discretion": _txt("investmentDiscretion"),
            })

        return holdings

    except Exception as exc:
        logger.debug("_parse_13f_holdings_xml failed: %s", exc)
        return []


def get_guru_list() -> list[dict]:
    """Return the list of value investor gurus available for 13F lookup."""
    return [
        {"key": k, "label": v, "cik": GURU_CIKS[k]}
        for k, v in GURU_LABELS.items()
    ]


# ---------------------------------------------------------------------------
# 3. Industry peers — find peers via S&P 500 sector/industry data
# ---------------------------------------------------------------------------

def get_industry_peers(ticker: str, max_peers: int = 10) -> dict:
    """
    Find peer companies in the same GICS sector/sub-industry as the given ticker.
    Uses the S&P 500 constituent list as the universe.

    Returns:
    {
        "ticker": "AAPL",
        "sector": "Information Technology",
        "sub_industry": "Technology Hardware...",
        "peers": [{"ticker", "company", "gics_sub_industry"}, ...]
    }
    """
    key = hashkey("peers", ticker.upper(), max_peers)
    if key in _ALT_CACHE:
        return _ALT_CACHE[key]

    constituents = get_sp500_constituents()
    sym = ticker.upper()

    # Find the target company's sector
    target = next((c for c in constituents if c["ticker"].upper() == sym), None)

    if not target:
        return {
            "ticker": sym,
            "peers":  [],
            "note":   f"{sym} not found in S&P 500 constituent list",
        }

    # Find peers: same sub-industry first, then same sector
    sub_peers  = [c for c in constituents
                  if c["ticker"].upper() != sym
                  and c.get("gics_sub_industry") == target.get("gics_sub_industry")]

    sector_peers = [c for c in constituents
                    if c["ticker"].upper() != sym
                    and c.get("gics_sector") == target.get("gics_sector")
                    and c not in sub_peers]

    peers = (sub_peers + sector_peers)[:max_peers]

    result = {
        "ticker":       sym,
        "company":      target.get("company", ""),
        "sector":       target.get("gics_sector", ""),
        "sub_industry": target.get("gics_sub_industry", ""),
        "peers":        [{"ticker": p["ticker"], "company": p["company"],
                          "gics_sub_industry": p["gics_sub_industry"]} for p in peers],
        "total_peers":  len(sub_peers) + len(sector_peers),
        "fetched_at":   datetime.utcnow().isoformat(),
    }

    _ALT_CACHE[key] = result
    return result


# ---------------------------------------------------------------------------
# 4. Buffett Indicator — total market cap / US GDP
#    Uses Wilshire 5000 (WILL5000PR) / GDP from FRED
# ---------------------------------------------------------------------------

def get_buffett_indicator() -> dict:
    """
    Compute the Buffett Indicator: total US stock market cap / GDP.
    Values > 100% historically suggest overvaluation;
    values < 75% suggest undervaluation.

    Uses FRED series:
    - WILL5000PR — Wilshire 5000 Total Market Full Cap Index
    - GDP        — Nominal GDP (quarterly, billions)
    """
    key = hashkey("buffett_indicator")
    if key in _FILING_CACHE:
        return _FILING_CACHE[key]

    try:
        from app.services.macro_service import get_fred_series

        wilshire = get_fred_series("WILL5000PR", limit=5)
        gdp      = get_fred_series("GDP", limit=5)

        w_latest = wilshire.get("latest_value")
        g_latest = gdp.get("latest_value")

        # Wilshire 5000 is in billions of USD
        ratio = None
        if w_latest and g_latest and g_latest > 0:
            ratio = round(w_latest / g_latest * 100, 1)

        # Qualitative interpretation
        interpretation = None
        if ratio is not None:
            if ratio > 150:
                interpretation = "Significantly Overvalued"
            elif ratio > 115:
                interpretation = "Moderately Overvalued"
            elif ratio > 90:
                interpretation = "Fair Value"
            elif ratio > 70:
                interpretation = "Moderately Undervalued"
            else:
                interpretation = "Significantly Undervalued"

        result = {
            "buffett_indicator_pct": ratio,
            "interpretation":        interpretation,
            "wilshire_5000_bn":      w_latest,
            "gdp_bn":                g_latest,
            "note": (
                "Ratio > 100% = market larger than GDP. "
                "Buffett considers ratios of 70–80% as 'buying opportunity.'"
            ),
            "source": "FRED (Wilshire 5000 + GDP)",
            "fetched_at": datetime.utcnow().isoformat(),
        }

        _FILING_CACHE[key] = result
        return result

    except Exception as exc:
        logger.warning("get_buffett_indicator failed: %s", exc)
        return {"error": str(exc), "fetched_at": datetime.utcnow().isoformat()}


# ---------------------------------------------------------------------------
# Fallback S&P 500 list (used if Wikipedia scraping fails)
# ---------------------------------------------------------------------------

_SP500_FALLBACK = [
    {"ticker": "AAPL",  "company": "Apple Inc.",           "gics_sector": "Information Technology", "gics_sub_industry": "Technology Hardware", "headquarters": "Cupertino, CA", "date_added": ""},
    {"ticker": "MSFT",  "company": "Microsoft Corp",        "gics_sector": "Information Technology", "gics_sub_industry": "Systems Software", "headquarters": "Redmond, WA", "date_added": ""},
    {"ticker": "AMZN",  "company": "Amazon.com Inc.",       "gics_sector": "Consumer Discretionary", "gics_sub_industry": "Internet & Direct Marketing Retail", "headquarters": "Seattle, WA", "date_added": ""},
    {"ticker": "NVDA",  "company": "NVIDIA Corp",           "gics_sector": "Information Technology", "gics_sub_industry": "Semiconductors", "headquarters": "Santa Clara, CA", "date_added": ""},
    {"ticker": "GOOGL", "company": "Alphabet Inc. (Class A)","gics_sector": "Communication Services", "gics_sub_industry": "Interactive Media & Services", "headquarters": "Mountain View, CA", "date_added": ""},
    {"ticker": "META",  "company": "Meta Platforms Inc.",   "gics_sector": "Communication Services", "gics_sub_industry": "Interactive Media & Services", "headquarters": "Menlo Park, CA", "date_added": ""},
    {"ticker": "BRK-B", "company": "Berkshire Hathaway",    "gics_sector": "Financials", "gics_sub_industry": "Multi-Sector Holdings", "headquarters": "Omaha, NE", "date_added": ""},
    {"ticker": "LLY",   "company": "Eli Lilly and Co",      "gics_sector": "Health Care", "gics_sub_industry": "Pharmaceuticals", "headquarters": "Indianapolis, IN", "date_added": ""},
    {"ticker": "TSLA",  "company": "Tesla Inc",             "gics_sector": "Consumer Discretionary", "gics_sub_industry": "Automobile Manufacturers", "headquarters": "Austin, TX", "date_added": ""},
    {"ticker": "V",     "company": "Visa Inc.",             "gics_sector": "Financials", "gics_sub_industry": "Transaction & Payment Processing", "headquarters": "San Francisco, CA", "date_added": ""},
    {"ticker": "JPM",   "company": "JPMorgan Chase",        "gics_sector": "Financials", "gics_sub_industry": "Diversified Banks", "headquarters": "New York, NY", "date_added": ""},
    {"ticker": "UNH",   "company": "UnitedHealth Group",    "gics_sector": "Health Care", "gics_sub_industry": "Managed Health Care", "headquarters": "Minnetonka, MN", "date_added": ""},
    {"ticker": "XOM",   "company": "Exxon Mobil",           "gics_sector": "Energy", "gics_sub_industry": "Integrated Oil & Gas", "headquarters": "Spring, TX", "date_added": ""},
    {"ticker": "MA",    "company": "Mastercard Inc.",       "gics_sector": "Financials", "gics_sub_industry": "Transaction & Payment Processing", "headquarters": "Purchase, NY", "date_added": ""},
    {"ticker": "JNJ",   "company": "Johnson & Johnson",     "gics_sector": "Health Care", "gics_sub_industry": "Pharmaceuticals", "headquarters": "New Brunswick, NJ", "date_added": ""},
    {"ticker": "PG",    "company": "Procter & Gamble",      "gics_sector": "Consumer Staples", "gics_sub_industry": "Household Products", "headquarters": "Cincinnati, OH", "date_added": ""},
    {"ticker": "HD",    "company": "Home Depot",            "gics_sector": "Consumer Discretionary", "gics_sub_industry": "Home Improvement Retail", "headquarters": "Atlanta, GA", "date_added": ""},
    {"ticker": "AVGO",  "company": "Broadcom Inc.",         "gics_sector": "Information Technology", "gics_sub_industry": "Semiconductors", "headquarters": "San Jose, CA", "date_added": ""},
    {"ticker": "CVX",   "company": "Chevron Corp",          "gics_sector": "Energy", "gics_sub_industry": "Integrated Oil & Gas", "headquarters": "San Ramon, CA", "date_added": ""},
    {"ticker": "COST",  "company": "Costco Wholesale",      "gics_sector": "Consumer Staples", "gics_sub_industry": "Hypermarkets & Super Centers", "headquarters": "Issaquah, WA", "date_added": ""},
]
