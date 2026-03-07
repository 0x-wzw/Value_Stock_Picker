"""
screener_service.py
-------------------
Stock screener logic built on top of data_service.
Provides multi-criteria filtering and moat signal detection.
"""

from __future__ import annotations

import logging
from typing import Optional

from app.services.data_service import get_company_overview, get_key_metrics

logger = logging.getLogger(__name__)


def screen_stock(ticker: str, criteria: dict) -> dict | None:
    """
    Evaluate a single ticker against screening criteria.

    criteria keys (all optional):
        min_roic, max_pe, max_debt_to_equity, min_gross_margin,
        min_operating_margin, min_market_cap, max_market_cap,
        min_fcf_yield, min_current_ratio, sectors (list of str)

    Returns enriched dict if it passes all criteria, or None if it fails.
    """
    try:
        overview = get_company_overview(ticker)
        metrics = get_key_metrics(ticker)

        if "error" in overview:
            return None

        # Sector filter
        sectors = criteria.get("sectors")
        if sectors and overview.get("sector") not in sectors:
            return None

        # Numerical filters
        def passes(value, min_val=None, max_val=None) -> bool:
            if value is None:
                return True  # don't exclude on missing data
            if min_val is not None and value < min_val:
                return False
            if max_val is not None and value > max_val:
                return False
            return True

        checks = [
            passes(metrics.get("roic_pct"), min_val=criteria.get("min_roic")),
            passes(overview.get("pe_ratio"), max_val=criteria.get("max_pe")),
            passes(overview.get("debt_to_equity"), max_val=criteria.get("max_debt_to_equity")),
            passes(overview.get("gross_margin"), min_val=criteria.get("min_gross_margin")),
            passes(overview.get("operating_margin"), min_val=criteria.get("min_operating_margin")),
            passes(overview.get("market_cap"), min_val=criteria.get("min_market_cap"), max_val=criteria.get("max_market_cap")),
            passes(metrics.get("fcf_yield_pct"), min_val=criteria.get("min_fcf_yield")),
            passes(overview.get("current_ratio"), min_val=criteria.get("min_current_ratio")),
        ]

        if not all(checks):
            return None

        # Compute moat score (0–100)
        moat_score = _compute_moat_score(overview, metrics)

        return {
            "ticker": ticker.upper(),
            "name": overview.get("name"),
            "sector": overview.get("sector"),
            "industry": overview.get("industry"),
            "market_cap": overview.get("market_cap"),
            "pe_ratio": overview.get("pe_ratio"),
            "price_to_book": overview.get("price_to_book"),
            "ev_to_ebitda": overview.get("ev_to_ebitda"),
            "gross_margin": overview.get("gross_margin"),
            "operating_margin": overview.get("operating_margin"),
            "roe": overview.get("roe"),
            "debt_to_equity": overview.get("debt_to_equity"),
            "current_ratio": overview.get("current_ratio"),
            "roic_pct": metrics.get("roic_pct"),
            "fcf_yield_pct": metrics.get("fcf_yield_pct"),
            "revenue_cagr_pct": metrics.get("revenue_cagr_pct"),
            "moat_score": moat_score,
            "dividend_yield": overview.get("dividend_yield"),
        }

    except Exception as exc:
        logger.warning("screen_stock(%s) failed: %s", ticker, exc)
        return None


def _compute_moat_score(overview: dict, metrics: dict) -> int:
    """
    Score 0–100 for moat quality based on:
      - High gross margin (>40% = wide moat signal)
      - High ROIC (>15%)
      - Low D/E ratio (balance sheet strength)
      - Consistent return on equity
      - Positive FCF yield
    """
    score = 0

    gm = overview.get("gross_margin") or 0
    if gm >= 0.60:
        score += 25
    elif gm >= 0.40:
        score += 15
    elif gm >= 0.25:
        score += 8

    roic = metrics.get("roic_pct") or 0
    if roic >= 20:
        score += 25
    elif roic >= 15:
        score += 18
    elif roic >= 10:
        score += 10

    roe = (overview.get("roe") or 0)
    if roe >= 0.20:
        score += 20
    elif roe >= 0.15:
        score += 12
    elif roe >= 0.10:
        score += 6

    de = overview.get("debt_to_equity")
    if de is not None:
        if de < 0.3:
            score += 15
        elif de < 0.8:
            score += 8
        elif de < 1.5:
            score += 3

    fcf_yield = metrics.get("fcf_yield_pct") or 0
    if fcf_yield >= 5:
        score += 15
    elif fcf_yield >= 3:
        score += 8
    elif fcf_yield >= 1:
        score += 4

    return min(score, 100)


def get_value_signals(ticker: str) -> dict:
    """
    Compute value investing signals for a single ticker:
    - Is it undervalued vs. historical P/E?
    - Margin of safety estimate
    - Quick qualitative flags
    """
    overview = get_company_overview(ticker)
    metrics = get_key_metrics(ticker)
    price_history = None

    try:
        from app.services.data_service import get_price_history
        price_history = get_price_history(ticker, period="5y", interval="1mo")
    except Exception:
        pass

    signals = {
        "ticker": ticker.upper(),
        "flags": [],
        "warnings": [],
    }

    # High quality signals
    if (overview.get("gross_margin") or 0) > 0.40:
        signals["flags"].append("High gross margin (>40%) — potential pricing power")
    if (metrics.get("roic_pct") or 0) > 15:
        signals["flags"].append("High ROIC (>15%) — capital-efficient business")
    if (overview.get("debt_to_equity") or 999) < 0.5:
        signals["flags"].append("Low debt — strong balance sheet")
    if (metrics.get("fcf_yield_pct") or 0) > 5:
        signals["flags"].append("High FCF yield (>5%) — potentially undervalued")
    if (overview.get("revenue_growth") or 0) > 0.10:
        signals["flags"].append("Revenue growing >10% YoY")

    # Warning signals
    if (overview.get("debt_to_equity") or 0) > 2.0:
        signals["warnings"].append("High debt-to-equity ratio (>2x)")
    if (overview.get("pe_ratio") or 0) > 50:
        signals["warnings"].append("High P/E ratio (>50) — priced for perfection")
    if (overview.get("current_ratio") or 2) < 1.0:
        signals["warnings"].append("Current ratio <1 — potential liquidity risk")
    if (overview.get("profit_margin") or 0) < 0:
        signals["warnings"].append("Negative profit margins")

    # Simple fair value estimate using FCF-based approach
    fcf = metrics.get("avg_fcf_5y")
    shares = overview.get("shares_outstanding")
    if fcf and shares and shares > 0:
        # Conservative: 15x FCF multiple
        conservative_value = (fcf * 15) / shares
        # Base: 20x FCF multiple
        base_value = (fcf * 20) / shares

        signals["fair_value_conservative"] = round(conservative_value, 2)
        signals["fair_value_base"] = round(base_value, 2)

        from app.services.data_service import get_realtime_quote
        quote = get_realtime_quote(ticker)
        price = quote.get("price")
        if price and price > 0:
            mos_conservative = round((conservative_value - price) / conservative_value * 100, 1)
            mos_base = round((base_value - price) / price * 100, 1)
            signals["margin_of_safety_conservative_pct"] = mos_conservative
            signals["margin_of_safety_base_pct"] = mos_base

            if mos_conservative > 20:
                signals["flags"].append(
                    f"Possible margin of safety: ~{mos_conservative}% below conservative FCF value"
                )

    return signals
