from pydantic import BaseModel, Field
from typing import Optional


class DCFRequest(BaseModel):
    growth_rate_yr1_5: float = Field(0.10, ge=0, le=1, description="FCF growth rate years 1-5 (0-1)")
    growth_rate_yr6_10: float = Field(0.07, ge=0, le=1, description="FCF growth rate years 6-10 (0-1)")
    terminal_growth_rate: float = Field(0.03, ge=0, le=0.10, description="Perpetual terminal growth rate")
    discount_rate: float = Field(0.10, ge=0.05, le=0.30, description="Discount rate / WACC")
    safety_margin: float = Field(0.25, ge=0, le=0.75, description="Margin of safety to apply to result")


class OwnerEarningsRequest(BaseModel):
    growth_rate: float = Field(0.08, ge=0, le=1)
    discount_rate: float = Field(0.10, ge=0.05, le=0.30)
    years: int = Field(10, ge=5, le=20)
    terminal_multiple: float = Field(15.0, ge=5, le=30)
    safety_margin: float = Field(0.25, ge=0, le=0.75)


class ValuationResponse(BaseModel):
    ticker: str
    method: str
    intrinsic_value_per_share: Optional[float]
    intrinsic_with_margin_of_safety: Optional[float]
    current_price: Optional[float]
    margin_of_safety_pct: Optional[float]
    upside_pct: Optional[float]
    inputs: Optional[dict]
    error: Optional[str] = None
