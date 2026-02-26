# Value Stock Picker

A value investing research web app inspired by Li Lu's methodology. Screen for undervalued companies, conduct deep fundamental analysis, estimate intrinsic value, and manage a concentrated portfolio — all guided by the principles of ownership mentality, margin of safety, and circle of competence.

## Features

### Stock Screener
- Multi-criteria filtering (ROIC, debt/equity, FCF yield, margins, market cap, sector)
- Moat indicator flags for companies with durable competitive advantages
- Valuation signals highlighting stocks trading below intrinsic value
- Sector heatmap to visualize where opportunities concentrate
- Watchlist with quick notes

### Analysis Workbench
- **Company dashboard** — price chart, key ratios, 5-year financials, business description
- **Financial deep-dive** — income statement, balance sheet, and cash flow with 5–10 year history
- **Research notebook** — structured notes organized by: business model, moat, management, risks, field notes
- **Li Lu checklist** — score companies across 8 criteria: owner economics, competitive moat, management integrity, financial strength, margin of safety, circle of competence, long-term compounding, downside protection
- **DCF / Owner earnings calculator** — intrinsic value estimation with adjustable assumptions
- **Comparative valuation** — side-by-side comparison of multiple companies
- **SEC filings links** — direct access to 10-K, 10-Q, and proxy statements

### Portfolio Tracker
- Holdings overview with cost basis, current value, gain/loss, and allocation
- Investment thesis tracker linked to research notes
- Performance charting vs. S&P 500 benchmark
- Configurable alerts for price and fundamental changes

### Learning & Circle of Competence
- Industry study tracker to log research progress
- Reading list and reading log

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Tailwind CSS, Recharts |
| Backend | FastAPI (Python) |
| Database | PostgreSQL |
| ORM | SQLAlchemy 2.0 + Alembic |
| Financial Data | yfinance, SEC EDGAR API |
| Auth | JWT + bcrypt |
| Build | Vite (frontend), uvicorn (backend) |
| Testing | pytest (backend), Vitest (frontend) |

## Project Structure

```
Value_Stock_Picker/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Settings / env vars
│   │   ├── database.py          # DB engine + session
│   │   ├── models/              # SQLAlchemy models
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── routers/             # API route handlers
│   │   ├── services/            # Business logic
│   │   └── utils/               # Security, dependency injection
│   ├── alembic/                 # DB migrations
│   ├── requirements.txt
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── api/                 # API client functions
│   │   ├── components/          # Reusable UI components
│   │   ├── pages/               # Route-level pages
│   │   ├── context/             # React Context providers
│   │   ├── hooks/               # Custom hooks
│   │   ├── types/               # TypeScript types
│   │   └── utils/
│   ├── package.json
│   └── vite.config.ts
├── PLAN.md                      # Detailed architecture and implementation plan
└── README.md
```

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

The frontend dev server runs at `http://localhost:5173` and the API at `http://localhost:8000`.

## Philosophy

This tool is built around Li Lu's core value investing principles:

- **Think like an owner** — stocks represent fractional ownership of a business
- **Margin of safety** — buy well below estimated intrinsic value
- **Mr. Market serves you** — market volatility creates opportunity, not guidance
- **Circle of competence** — invest only in what you genuinely understand
- **Concentrate and hold** — a few high-conviction positions held for the long term
- **Stay curious** — broad reading and investigative research uncover what others miss

See [PLAN.md](PLAN.md) for the full architecture and implementation plan.

## License

MIT
