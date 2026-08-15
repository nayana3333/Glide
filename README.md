# Glide

**Predictive Income Smoothing for Gig Economy Workers Using Machine Learning**

Gig workers (Ola, Uber, Swiggy, Zomato, Urban Company) earn irregularly — strong weeks followed by weak ones — with no salary floor and no savings cushion. Glide forecasts a worker's weekly income, detects an incoming dip before it happens, and recommends an adaptive micro-savings buffer to absorb it.

## The gap this fills

| Prior work | What it does | What it misses |
|---|---|---|
| Kandavel et al., ICDSAAI 2025 | Predicts hourly wage from static worker attributes (Random Forest, R² = 0.85) | Cross-sectional — can't forecast *when* income will fall |
| Weytjens et al., Springer 2021 | Forecasts cash flow over time (ARIMA/Prophet/LSTM) | Corporate cash flows, not individual gig income |
| **Glide** | Forecasts individual gig income temporally **and** converts the forecast into a savings action | — |

## Three-part approach

1. **Forecast** — model weekly gig income as a seasonal time series (weekday cycles, monsoon, festivals) using Prophet/ARIMA
2. **Detect** — flag weeks predicted to fall materially below the worker's rolling average
3. **Act** — a buffer engine recommends how much to save during surplus weeks and how much to release during deficit weeks

## Architecture

```
React (TypeScript) Frontend  →  FastAPI Backend  →  ML Service Layer (Prophet/ARIMA, Dip Detector, Buffer Engine, SHAP)
                                        │
                                   PostgreSQL
```

## Repo structure

```
glide/
├── backend/       FastAPI app (auth, earnings, forecast, buffer, alerts)
├── ml/            data generator, forecasting models, evaluation, notebooks
├── frontend/      React + TypeScript dashboard (Tailwind, shadcn/ui)
└── docs/          literature review, architecture notes, paper draft
```

## Status

All 7 modules built and verified end-to-end:

1. **Synthetic data generator** — 200 workers × 156 weeks (3 years), calibrated to ~30–40% week-to-week coefficient of variation, matching published Indian gig-economy volatility statistics. Real platform earnings data isn't public, so this is a documented, calibrated stand-in, not arbitrary noise.
2. **Forecast engine** — Naive / Moving Average / ARIMA / Prophet, evaluated on MAE / RMSE / sMAPE / Asymmetric Error Cost. On the full 200-worker set, ARIMA and Prophet both clearly beat the baselines.
3. **Dip detector** — classifies a forecast into GREEN / AMBER / RED against the worker's rolling average.
4. **Buffer engine** — reactive save/release rules. Full simulation across all 200 workers: **34.5% reduction** in weeks where income fell below the essential-expense floor.
5. **SHAP explainability** — pooled Random Forest on seasonal + lag features, explained per-prediction.
6. **FastAPI backend** — JWT auth, SQLite by default (swap to Postgres via `DATABASE_URL`), routes wired directly to the ML modules above.
7. **React frontend** — TypeScript, Tailwind CSS + shadcn/ui, react-hook-form + zod validation, toast notifications and skeleton loading states, responsive mobile nav, dark/light theme toggle. Screens: dashboard, forecast (confidence bands + SHAP panel), buffer, income log, insights.

## Running it locally

```bash
# ML modules (from ml/)
pip install -r requirements.txt
python data/generator.py
python models/evaluate.py --full
python models/buffer_simulation.py
python models/explain.py

# Backend (from backend/)
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
# Swagger docs at http://localhost:8000/docs

# Frontend (from frontend/)
npm install
npm run dev
# App at http://localhost:5174 (or whatever port Vite reports)
```

Register with an optional `demo_worker_id` (1–200) to seed a new account with a synthetic worker's earnings history, so the dashboard has real data immediately instead of an empty state.

## Stack

Python · scikit-learn · Prophet · SHAP · FastAPI · SQLAlchemy · SQLite/PostgreSQL · React 19 · TypeScript · Tailwind CSS · shadcn/ui · Recharts
