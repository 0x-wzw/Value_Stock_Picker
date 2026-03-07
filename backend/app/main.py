"""
main.py — FastAPI application entry point for Value Stock Picker.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import companies, screener, valuation, macro, alternative
from app.services.data_service import get_cache_stats

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description=(
        "Value investing research tool — pulls financial data from multiple open sources: "
        "yfinance (quotes/fundamentals), SEC EDGAR (filings/XBRL/13F), "
        "US Treasury (yield curve), FRED (macroeconomic data), "
        "World Bank (GDP/economic indicators), BLS (CPI/inflation), "
        "and optionally Alpha Vantage."
    ),
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Allow the React frontend dev server to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite default
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(companies.router)
app.include_router(screener.router)
app.include_router(valuation.router)
app.include_router(macro.router)
app.include_router(alternative.router)


@app.get("/api/health")
def health():
    """Health check endpoint."""
    return {"status": "ok", "app": settings.app_name}


@app.get("/api/cache/stats")
def cache_stats():
    """Diagnostic: view in-process cache utilisation."""
    return get_cache_stats()
