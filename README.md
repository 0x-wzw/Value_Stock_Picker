# Value Stock Picker

A full-stack web application that guides investors through Li Lu's value investing methodology. This tool acts as an investigative workbench for deep fundamental analysis.

## Features Currently Implemented (Foundation)

*   **Backend Structure (FastAPI & PostgreSQL)**
    *   REST API endpoints stubbed out for Authentication.
    *   Database models using SQLAlchemy (`User`, `Company`, `FinancialSnapshot`).
    *   Pydantic schemas and dependency injection rules.
*   **Frontend Structure (React & Vite)**
    *   Basic scaffolding initialized via Vite using the `react-ts` template.

## Getting Started

### Backend Setup

1.  Navigate to `/backend`
2.  Install requirements: `pip install -r requirements.txt` (It's recommended to use a virtual environment).
3.  Configure your PostgreSQL database and set the credentials in a `.env` file based on `app/config.py`.
4.  Run the application: `uvicorn app.main:app --reload`
5.  Access the API docs at `http://localhost:8000/docs`.

### Frontend Setup

1.  Navigate to `/frontend`
2.  Install dependencies: `npm install`
3.  Run the dev server: `npm run dev`

## Methodology

This app codifies the step-by-step research process of finding durable free cash flow, competitive moats, and management integrity, all while demanding a strict margin of safety.