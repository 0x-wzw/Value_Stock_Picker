# Value Stock Picker — Web App Plan
## A Value Investing Research Tool Inspired by Li Lu's Methodology

---

## 1. Product Vision

A web application that guides investors through Li Lu's value investing methodology — from idea generation and screening through deep fundamental analysis, intrinsic value estimation, and long-term portfolio monitoring. The app codifies the step-by-step research process described in the methodology while keeping the investigative, curiosity-driven spirit at its core.

---

## 2. Tech Stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| **Frontend** | React 18 + TypeScript | Component-based UI, strong typing, large ecosystem |
| **Styling** | Tailwind CSS | Rapid, consistent styling without CSS bloat |
| **Charts** | Recharts | Lightweight React-native charting for financial data |
| **State Management** | React Context + useReducer | Sufficient for this app's complexity without extra deps |
| **Backend** | FastAPI (Python) | Async, fast, excellent for data-heavy financial APIs |
| **Database** | PostgreSQL | Relational data (companies, financials, notes, portfolios) |
| **ORM** | SQLAlchemy 2.0 + Alembic | Mature Python ORM with migration support |
| **Financial Data** | yfinance + SEC EDGAR API | Free tickers, fundamentals, and filings |
| **Auth** | JWT (python-jose) + bcrypt | Simple token-based auth |
| **Build / Dev** | Vite (frontend), uvicorn (backend) | Fast dev servers for both layers |
| **Testing** | pytest (backend), Vitest (frontend) | Fast, modern test runners |

---

## 3. Architecture Overview

```
┌─────────────────────────────────────────────────┐
│                   Frontend (React)               │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │ Screener │ │ Analysis │ │ Portfolio Tracker │ │
│  │  Module  │ │ Workbench│ │     Module        │ │
│  └────┬─────┘ └────┬─────┘ └────────┬─────────┘ │
│       │             │                │           │
│       └─────────────┼────────────────┘           │
│                     │ REST API                   │
└─────────────────────┼───────────────────────────-┘
                      │
┌─────────────────────┼───────────────────────────-┐
│                Backend (FastAPI)                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │ Screening│ │ Analysis │ │   Portfolio       │ │
│  │  Service │ │  Service │ │   Service         │ │
│  └────┬─────┘ └────┬─────┘ └────────┬─────────┘ │
│       │             │                │           │
│  ┌────┴─────────────┴────────────────┴─────────┐ │
│  │          Data Layer (SQLAlchemy)             │ │
│  └────┬──────────────────────────┬─────────────┘ │
│       │                          │               │
│  ┌────┴─────┐           ┌───────┴────────┐      │
│  │PostgreSQL│           │ External APIs  │      │
│  │          │           │ (yfinance/SEC) │      │
│  └──────────┘           └────────────────┘      │
└──────────────────────────────────────────────────┘
```

---

## 4. Data Model (Core Entities)

### `users`
- `id` (PK), `email`, `password_hash`, `name`, `created_at`

### `companies`
- `id` (PK), `ticker`, `name`, `sector`, `industry`, `exchange`, `description`
- Cached from external APIs; refreshed periodically

### `financial_snapshots`
- `id` (PK), `company_id` (FK), `period` (year/quarter), `revenue`, `net_income`, `free_cash_flow`, `total_debt`, `total_equity`, `shares_outstanding`, `roic`, `roe`, `gross_margin`, `operating_margin`, `current_ratio`, `debt_to_equity`, `fetched_at`

### `watchlist_items`
- `id` (PK), `user_id` (FK), `company_id` (FK), `added_at`, `notes`

### `research_notes`
- `id` (PK), `user_id` (FK), `company_id` (FK), `category` (enum: business_model, moat, management, valuation, risks, field_notes), `title`, `content` (rich text), `created_at`, `updated_at`

### `valuations`
- `id` (PK), `user_id` (FK), `company_id` (FK), `method` (enum: dcf, owner_earnings, asset_based, comparative), `assumptions` (JSON), `intrinsic_value_per_share`, `margin_of_safety_pct`, `created_at`

### `portfolio_holdings`
- `id` (PK), `user_id` (FK), `company_id` (FK), `shares`, `avg_cost_basis`, `date_acquired`, `thesis_summary`, `status` (active/exited)

### `checklist_results`
- `id` (PK), `user_id` (FK), `company_id` (FK), `checklist_data` (JSON — scored Li Lu checklist items), `overall_score`, `created_at`

---

## 5. Feature Breakdown by Module

### Module A: Stock Screener (Li Lu Step 1–2)
_Idea generation and preliminary screening_

| Feature | Description |
|---------|-------------|
| **A1. Multi-criteria screener** | Filter stocks by: ROIC > threshold, debt/equity < threshold, free-cash-flow yield, gross margin, market cap range, sector/industry |
| **A2. Moat indicators** | Flag companies with high gross margins (>40%), high ROIC consistency (5+ years), and low capital intensity as potential moat candidates |
| **A3. Valuation signals** | Show P/E, P/FCF, EV/EBIT, P/B ratios; highlight stocks trading below historical averages or sector medians |
| **A4. Watchlist** | Save interesting companies for deeper research; add quick notes |
| **A5. Sector heatmap** | Visual overview of sectors by valuation and quality metrics to "fish where the fish are" |

### Module B: Analysis Workbench (Li Lu Step 3–4)
_Deep fundamental analysis and investigative research_

| Feature | Description |
|---------|-------------|
| **B1. Company dashboard** | Overview page: price chart, key ratios, 5-year financials summary, business description |
| **B2. Financial deep-dive** | Detailed tables and charts for income statement, balance sheet, cash flow — with 5-10 year history |
| **B3. Research notebook** | Structured note-taking organized by Li Lu's categories: business model, competitive advantage/moat, management quality, risks, field notes |
| **B4. Li Lu checklist** | Interactive checklist scoring a company across Li Lu's criteria: owner economics, margin of safety, moat durability, management integrity, circle of competence fit, long-term compounding potential |
| **B5. DCF / Owner earnings calculator** | Built-in intrinsic value calculator with adjustable assumptions (growth rate, discount rate, terminal value); shows margin of safety vs. current price |
| **B6. Comparative valuation** | Side-by-side comparison of 2-4 companies on key metrics |
| **B7. SEC filings links** | Direct links to 10-K, 10-Q, proxy statements on SEC EDGAR for investigative research |

### Module C: Portfolio Tracker (Li Lu Step 6–7)
_Concentrated portfolio management and monitoring_

| Feature | Description |
|---------|-------------|
| **C1. Holdings overview** | Dashboard showing current holdings, cost basis, current value, gain/loss, and portfolio allocation |
| **C2. Thesis tracker** | Each holding linked to its investment thesis; visual indicator if thesis assumptions still hold |
| **C3. Alerts & monitoring** | Configurable alerts: price drops below margin-of-safety threshold, earnings surprises, debt ratio changes |
| **C4. Performance tracking** | Portfolio return over time vs. benchmark (S&P 500); per-holding performance |

### Module D: Learning & Circle of Competence (Li Lu Step 5)

| Feature | Description |
|---------|-------------|
| **D1. Industry study tracker** | Track which industries/sectors the user has studied; log reading and research hours |
| **D2. Reading list** | Curated resources on value investing, plus user's own reading log |

---

## 6. API Endpoints

### Auth
- `POST /api/auth/register` — Create account
- `POST /api/auth/login` — Get JWT token
- `GET  /api/auth/me` — Current user profile

### Screener
- `GET  /api/screener/search` — Search companies by name/ticker
- `POST /api/screener/filter` — Apply multi-criteria screen (body: filter params)
- `GET  /api/screener/sectors` — Sector heatmap data

### Companies
- `GET  /api/companies/{ticker}` — Company overview + latest financials
- `GET  /api/companies/{ticker}/financials` — Multi-year financial data
- `GET  /api/companies/{ticker}/filings` — SEC filing links

### Watchlist
- `GET    /api/watchlist` — User's watchlist
- `POST   /api/watchlist` — Add company to watchlist
- `DELETE /api/watchlist/{id}` — Remove from watchlist

### Research
- `GET    /api/research/{ticker}` — All notes for a company
- `POST   /api/research/{ticker}` — Create research note
- `PUT    /api/research/{id}` — Update note
- `DELETE /api/research/{id}` — Delete note
- `POST   /api/research/{ticker}/checklist` — Save checklist evaluation
- `GET    /api/research/{ticker}/checklist` — Get latest checklist

### Valuation
- `POST /api/valuation/{ticker}/dcf` — Run DCF calculation
- `POST /api/valuation/{ticker}/owner-earnings` — Run owner earnings calc
- `GET  /api/valuation/{ticker}` — Get saved valuations
- `POST /api/valuation/compare` — Compare multiple tickers

### Portfolio
- `GET    /api/portfolio` — All holdings
- `POST   /api/portfolio` — Add holding
- `PUT    /api/portfolio/{id}` — Update holding
- `DELETE /api/portfolio/{id}` — Remove/exit holding
- `GET    /api/portfolio/performance` — Performance over time

---

## 7. Page / Route Structure (Frontend)

```
/                          → Landing / login
/dashboard                 → Portfolio overview (Module C)
/screener                  → Stock screener (Module A)
/screener/sectors          → Sector heatmap
/watchlist                 → Watchlist with quick notes
/company/:ticker           → Company dashboard (Module B)
/company/:ticker/financials→ Detailed financials
/company/:ticker/research  → Research notebook
/company/:ticker/checklist → Li Lu checklist
/company/:ticker/valuation → DCF & valuation tools
/compare                   → Side-by-side comparison
/portfolio                 → Holdings tracker (Module C)
/learning                  → Circle of competence tracker (Module D)
/settings                  → User settings
```

---

## 8. Implementation Plan (Phases)

### Phase 1: Foundation (Backend + DB + Auth)
1. Initialize Python project (FastAPI, SQLAlchemy, Alembic, pytest)
2. Set up PostgreSQL schema and migrations for all entities
3. Implement user auth (register, login, JWT middleware)
4. Build company data service (yfinance integration to fetch & cache fundamentals)
5. Create screener API endpoints with filtering logic
6. Write unit tests for data models and screener logic

### Phase 2: Foundation (Frontend Shell)
7. Initialize React + TypeScript + Vite project
8. Set up Tailwind CSS, routing (React Router), and auth context
9. Build layout shell (sidebar navigation, header, responsive design)
10. Create login/register pages
11. Build screener page with filter controls and results table

### Phase 3: Analysis Workbench
12. Build company dashboard page (price chart, key metrics, description)
13. Implement financial deep-dive page (multi-year tables + charts)
14. Create research notebook UI (categorized notes with rich text)
15. Build Li Lu checklist — interactive scoring form
16. Implement DCF/owner-earnings calculator with adjustable inputs
17. Add comparative valuation page
18. Add SEC filings links integration
19. Backend endpoints for research notes, checklists, and valuations

### Phase 4: Portfolio & Monitoring
20. Build portfolio holdings page
21. Implement thesis tracker tied to research notes
22. Add performance charting vs. benchmark
23. Build alert configuration and notification system

### Phase 5: Learning & Polish
24. Build circle-of-competence / industry study tracker
25. Add reading list feature
26. Responsive design polish and accessibility review
27. Error handling, loading states, and edge cases
28. End-to-end testing

---

## 9. Directory Structure

```
Value_Stock_Picker/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI app entry
│   │   ├── config.py                # Settings / env vars
│   │   ├── database.py              # DB engine + session
│   │   ├── models/                  # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── company.py
│   │   │   ├── financial.py
│   │   │   ├── watchlist.py
│   │   │   ├── research.py
│   │   │   ├── valuation.py
│   │   │   └── portfolio.py
│   │   ├── schemas/                 # Pydantic request/response schemas
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── company.py
│   │   │   ├── screener.py
│   │   │   ├── research.py
│   │   │   ├── valuation.py
│   │   │   └── portfolio.py
│   │   ├── routers/                 # API route handlers
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── screener.py
│   │   │   ├── companies.py
│   │   │   ├── watchlist.py
│   │   │   ├── research.py
│   │   │   ├── valuation.py
│   │   │   └── portfolio.py
│   │   ├── services/                # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── data_service.py      # yfinance / SEC integration
│   │   │   ├── screener_service.py
│   │   │   ├── valuation_service.py
│   │   │   └── portfolio_service.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── security.py          # JWT + password hashing
│   │       └── deps.py              # Dependency injection
│   ├── alembic/                     # DB migrations
│   │   └── versions/
│   ├── alembic.ini
│   ├── requirements.txt
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_auth.py
│       ├── test_screener.py
│       ├── test_valuation.py
│       └── test_portfolio.py
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── api/                     # API client functions
│   │   │   ├── client.ts
│   │   │   ├── auth.ts
│   │   │   ├── screener.ts
│   │   │   ├── companies.ts
│   │   │   ├── research.ts
│   │   │   ├── valuation.ts
│   │   │   └── portfolio.ts
│   │   ├── components/              # Reusable UI components
│   │   │   ├── Layout/
│   │   │   ├── Charts/
│   │   │   ├── Tables/
│   │   │   └── Forms/
│   │   ├── pages/                   # Route-level page components
│   │   │   ├── Login.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Screener.tsx
│   │   │   ├── SectorHeatmap.tsx
│   │   │   ├── Watchlist.tsx
│   │   │   ├── CompanyDashboard.tsx
│   │   │   ├── Financials.tsx
│   │   │   ├── ResearchNotebook.tsx
│   │   │   ├── Checklist.tsx
│   │   │   ├── Valuation.tsx
│   │   │   ├── Compare.tsx
│   │   │   ├── Portfolio.tsx
│   │   │   └── Learning.tsx
│   │   ├── context/                 # React Context providers
│   │   │   └── AuthContext.tsx
│   │   ├── hooks/                   # Custom hooks
│   │   ├── types/                   # TypeScript type definitions
│   │   └── utils/
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   └── vite.config.ts
├── README.md
└── PLAN.md
```

---

## 10. Li Lu Checklist — Scoring Criteria

The interactive checklist (Feature B4) scores each company on these dimensions, each rated 1–5:

| # | Criterion | What to evaluate |
|---|-----------|-----------------|
| 1 | **Owner Economics** | Does the business generate durable free cash flow? Are returns on capital consistently high? |
| 2 | **Competitive Moat** | Is the advantage durable — network effects, cost advantages, brand, switching costs? Can competitors erode it? |
| 3 | **Management Integrity** | Is management honest, competent, and shareholder-aligned? Track record of capital allocation? |
| 4 | **Financial Strength** | Low debt, strong balance sheet, ability to weather downturns without dilution? |
| 5 | **Margin of Safety** | Is the current price meaningfully below conservative intrinsic value estimate? |
| 6 | **Circle of Competence** | Do I genuinely understand this business, its industry, and its risks? |
| 7 | **Long-term Compounding** | Can this business compound value for 10+ years? Is the runway long? |
| 8 | **Downside Protection** | What's the worst case? Can I quantify and accept the potential loss? |

Overall score = weighted average. A score ≥ 4.0 suggests a strong candidate for concentrated investment.

---

## 11. Key Design Principles

1. **Research-first UX** — The app is a research workbench, not a trading platform. Prioritize depth of analysis over speed of execution.
2. **Structured thinking** — Guide users through Li Lu's methodology with clear categories and checklists rather than free-form exploration.
3. **Data integrity** — Cache financial data with clear timestamps; never present stale data as current without indication.
4. **Simplicity** — Clean, distraction-free interface. No gamification, no social features, no real-time tickers. This is for patient, focused investors.
5. **Investor's journal** — The research notebook is central. Every insight, question, and source should be capturable and searchable.
