from fastapi import APIRouter
from app.schemas.valuation import DCFRequest, OwnerEarningsRequest, ValuationResponse
from app.services.valuation_service import run_dcf, run_owner_earnings

router = APIRouter(prefix="/api/valuation", tags=["valuation"])


@router.post("/{ticker}/dcf", response_model=ValuationResponse)
def dcf_valuation(ticker: str, req: DCFRequest):
    """
    Run a two-stage DCF model using average 5-year free cash flow.

    Adjustable inputs: growth rates, discount rate, terminal growth, margin of safety.
    """
    return run_dcf(
        ticker.upper(),
        growth_rate_yr1_5=req.growth_rate_yr1_5,
        growth_rate_yr6_10=req.growth_rate_yr6_10,
        terminal_growth_rate=req.terminal_growth_rate,
        discount_rate=req.discount_rate,
        safety_margin=req.safety_margin,
    )


@router.post("/{ticker}/owner-earnings", response_model=ValuationResponse)
def owner_earnings_valuation(ticker: str, req: OwnerEarningsRequest):
    """
    Run a Buffett-style owner earnings valuation.

    Owner Earnings = Net Income + D&A - estimated maintenance CapEx.
    """
    return run_owner_earnings(
        ticker.upper(),
        growth_rate=req.growth_rate,
        discount_rate=req.discount_rate,
        years=req.years,
        terminal_multiple=req.terminal_multiple,
        safety_margin=req.safety_margin,
    )


@router.get("/{ticker}/quick")
def quick_valuation(ticker: str):
    """
    Run both DCF and owner earnings with default assumptions for a quick snapshot.
    Returns both results side by side.
    """
    dcf = run_dcf(ticker.upper())
    oe = run_owner_earnings(ticker.upper())
    return {
        "ticker": ticker.upper(),
        "dcf": dcf,
        "owner_earnings": oe,
    }
