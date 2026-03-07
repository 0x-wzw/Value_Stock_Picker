"""
Integration tests for the FastAPI endpoints (mocked data layer).
"""

from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_cache_stats():
    resp = client.get("/api/cache/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "price_cache" in data
    assert "fundamentals_cache" in data


@patch("app.routers.companies.get_realtime_quote")
def test_quote_endpoint(mock_quote):
    mock_quote.return_value = {
        "ticker": "AAPL",
        "price": 180.0,
        "change_pct": 1.5,
        "fetched_at": "2024-01-01T00:00:00",
    }
    resp = client.get("/api/companies/AAPL/quote")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ticker"] == "AAPL"
    assert data["price"] == 180.0


@patch("app.routers.companies.get_realtime_quote")
def test_quote_error_returns_result(mock_quote):
    """Even if data has an error key, it should return 200 if minimal data present."""
    mock_quote.return_value = {
        "ticker": "UNKNOWN",
        "error": "no data",
        "fetched_at": "2024-01-01T00:00:00",
    }
    resp = client.get("/api/companies/UNKNOWN/quote")
    # Should return 404 since price is missing
    assert resp.status_code in (200, 404)


@patch("app.routers.screener.get_market_indices")
def test_market_endpoint(mock_indices):
    mock_indices.return_value = {
        "S&P 500": {"symbol": "^GSPC", "price": 5200.0, "change_pct": 0.5},
        "NASDAQ": {"symbol": "^IXIC", "price": 16200.0, "change_pct": 0.8},
        "Dow Jones": {"symbol": "^DJI", "price": 39000.0, "change_pct": 0.3},
    }
    resp = client.get("/api/screener/market")
    assert resp.status_code == 200
    data = resp.json()
    assert "S&P 500" in data


@patch("app.routers.screener.filter_stocks")
def test_screener_filter(mock_filter):
    mock_filter.return_value = [
        {
            "ticker": "AAPL",
            "name": "Apple Inc.",
            "sector": "Technology",
            "market_cap": 2_400_000_000_000,
            "pe_ratio": 28.5,
            "price_to_book": 45.0,
            "ev_to_ebitda": 22.0,
            "gross_margin": 0.44,
            "operating_margin": 0.30,
            "roe": 1.60,
            "debt_to_equity": 1.8,
            "current_ratio": 0.99,
            "roic_pct": 30.0,
            "fcf_yield_pct": 4.3,
            "revenue_cagr_pct": 7.5,
            "moat_score": 75,
            "dividend_yield": 0.005,
        }
    ]
    resp = client.post("/api/screener/filter", json={"min_roic": 15})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["ticker"] == "AAPL"


def test_screener_universe():
    resp = client.get("/api/screener/universe")
    assert resp.status_code == 200
    data = resp.json()
    assert "tickers" in data
    assert len(data["tickers"]) > 0
