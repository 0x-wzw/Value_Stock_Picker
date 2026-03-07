"""
valuation_service.py
--------------------
Intrinsic value calculators:
  - DCF (Discounted Cash Flow)
  - Owner Earnings (Buffett/Munger method)
  - Asset-based (book value with adjustments)
"""

from __future__ import annotations

import math
from typing import Optional

from app.services.data_service import get_key_metrics, get_company_overview, get_financial_statements


def run_dcf(
    ticker: str,
    growth_rate_yr1_5: float = 0.10,   # annual FCF growth rate, years 1-5
    growth_rate_yr6_10: float = 0.07,  # annual FCF growth rate, years 6-10
    terminal_growth_rate: float = 0.03,
    discount_rate: float = 0.10,       # WACC / required return
    safety_margin: float = 0.25,       # margin of safety to apply to result
) -> dict:
    """
    Two-stage DCF model using free cash flow.

    Returns per-share intrinsic value and margin of safety vs current price.
    """
    metrics = get_key_metrics(ticker)
    overview = get_company_overview(ticker)

    base_fcf = metrics.get("avg_fcf_5y")
    shares = overview.get("shares_outstanding")

    if not base_fcf or base_fcf <= 0:
        return {
            "ticker": ticker,
            "error": "Insufficient free cash flow data for DCF",
            "inputs": _dcf_inputs(ticker, growth_rate_yr1_5, growth_rate_yr6_10, terminal_growth_rate, discount_rate, safety_margin),
        }

    # Stage 1: Years 1-5
    stage1_pv = 0.0
    fcf = base_fcf
    for year in range(1, 6):
        fcf *= (1 + growth_rate_yr1_5)
        pv = fcf / ((1 + discount_rate) ** year)
        stage1_pv += pv

    # Stage 2: Years 6-10
    stage2_pv = 0.0
    for year in range(6, 11):
        fcf *= (1 + growth_rate_yr6_10)
        pv = fcf / ((1 + discount_rate) ** year)
        stage2_pv += pv

    # Terminal value (Gordon Growth Model)
    terminal_fcf = fcf * (1 + terminal_growth_rate)
    terminal_value = terminal_fcf / (discount_rate - terminal_growth_rate)
    terminal_pv = terminal_value / ((1 + discount_rate) ** 10)

    total_intrinsic_value = stage1_pv + stage2_pv + terminal_pv

    # Add cash, subtract debt (net cash)
    cash = overview.get("total_cash") or 0
    debt = overview.get("total_debt") or 0
    net_cash = cash - debt
    equity_value = total_intrinsic_value + net_cash

    intrinsic_per_share = equity_value / shares if shares else None
    intrinsic_with_mos = (intrinsic_per_share * (1 - safety_margin)) if intrinsic_per_share else None

    # Current price for MoS calc
    from app.services.data_service import get_realtime_quote
    quote = get_realtime_quote(ticker)
    current_price = quote.get("price")

    mos_pct = None
    if current_price and intrinsic_per_share and intrinsic_per_share > 0:
        mos_pct = round((intrinsic_per_share - current_price) / intrinsic_per_share * 100, 1)

    return {
        "ticker": ticker.upper(),
        "method": "dcf",
        "base_fcf": round(base_fcf, 0),
        "stage1_pv": round(stage1_pv, 0),
        "stage2_pv": round(stage2_pv, 0),
        "terminal_pv": round(terminal_pv, 0),
        "total_enterprise_value": round(total_intrinsic_value, 0),
        "net_cash_adjustment": round(net_cash, 0),
        "total_equity_value": round(equity_value, 0),
        "shares_outstanding": shares,
        "intrinsic_value_per_share": round(intrinsic_per_share, 2) if intrinsic_per_share else None,
        "intrinsic_with_margin_of_safety": round(intrinsic_with_mos, 2) if intrinsic_with_mos else None,
        "current_price": current_price,
        "margin_of_safety_pct": mos_pct,
        "upside_pct": round((intrinsic_per_share / current_price - 1) * 100, 1) if (intrinsic_per_share and current_price) else None,
        "inputs": _dcf_inputs(ticker, growth_rate_yr1_5, growth_rate_yr6_10, terminal_growth_rate, discount_rate, safety_margin),
    }


def _dcf_inputs(ticker, g1, g2, tgr, dr, sm):
    return {
        "ticker": ticker,
        "growth_rate_yr1_5_pct": round(g1 * 100, 1),
        "growth_rate_yr6_10_pct": round(g2 * 100, 1),
        "terminal_growth_rate_pct": round(tgr * 100, 1),
        "discount_rate_pct": round(dr * 100, 1),
        "safety_margin_pct": round(sm * 100, 1),
    }


def run_owner_earnings(
    ticker: str,
    growth_rate: float = 0.08,
    discount_rate: float = 0.10,
    years: int = 10,
    terminal_multiple: float = 15.0,
    safety_margin: float = 0.25,
) -> dict:
    """
    Owner earnings valuation (Buffett method).
    Owner Earnings = Net Income + D&A - Maintenance CapEx (est.)
    """
    metrics = get_key_metrics(ticker)
    overview = get_company_overview(ticker)

    owner_earnings = metrics.get("owner_earnings_estimate")
    shares = overview.get("shares_outstanding")

    if not owner_earnings or owner_earnings <= 0:
        # Fall back to FCF
        owner_earnings = metrics.get("avg_fcf_5y")
        if not owner_earnings or owner_earnings <= 0:
            return {"ticker": ticker, "error": "Insufficient earnings data", "method": "owner_earnings"}

    # Present value of owner earnings over projection period
    pv_sum = 0.0
    oe = owner_earnings
    for year in range(1, years + 1):
        oe *= (1 + growth_rate)
        pv_sum += oe / ((1 + discount_rate) ** year)

    # Terminal value at year N using a price/earnings multiple
    terminal_value_pv = (oe * terminal_multiple) / ((1 + discount_rate) ** years)
    total_value = pv_sum + terminal_value_pv

    # Adjust for net cash
    cash = overview.get("total_cash") or 0
    debt = overview.get("total_debt") or 0
    net_cash = cash - debt
    equity_value = total_value + net_cash

    intrinsic_per_share = equity_value / shares if shares else None
    intrinsic_with_mos = (intrinsic_per_share * (1 - safety_margin)) if intrinsic_per_share else None

    from app.services.data_service import get_realtime_quote
    quote = get_realtime_quote(ticker)
    current_price = quote.get("price")

    mos_pct = None
    if current_price and intrinsic_per_share and intrinsic_per_share > 0:
        mos_pct = round((intrinsic_per_share - current_price) / intrinsic_per_share * 100, 1)

    return {
        "ticker": ticker.upper(),
        "method": "owner_earnings",
        "base_owner_earnings": round(owner_earnings, 0),
        "pv_projection": round(pv_sum, 0),
        "terminal_value_pv": round(terminal_value_pv, 0),
        "total_equity_value": round(equity_value, 0),
        "shares_outstanding": shares,
        "intrinsic_value_per_share": round(intrinsic_per_share, 2) if intrinsic_per_share else None,
        "intrinsic_with_margin_of_safety": round(intrinsic_with_mos, 2) if intrinsic_with_mos else None,
        "current_price": current_price,
        "margin_of_safety_pct": mos_pct,
        "upside_pct": round((intrinsic_per_share / current_price - 1) * 100, 1) if (intrinsic_per_share and current_price) else None,
        "inputs": {
            "growth_rate_pct": round(growth_rate * 100, 1),
            "discount_rate_pct": round(discount_rate * 100, 1),
            "projection_years": years,
            "terminal_multiple": terminal_multiple,
            "safety_margin_pct": round(safety_margin * 100, 1),
        },
    }
