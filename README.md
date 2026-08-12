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
React Frontend  →  FastAPI Backend  →  ML Service Layer (Prophet/ARIMA, Dip Detector, Buffer Engine, SHAP)
                          │
                     PostgreSQL
```

## Repo structure

```
glide/
├── backend/       FastAPI app (auth, earnings, forecast, buffer, alerts)
├── ml/            data generator, forecasting models, evaluation, notebooks
├── frontend/      React dashboard
└── docs/          literature review, architecture notes, paper draft
```

## Status

Module 1 (synthetic data generator) — in progress. See `ml/data/generator.py`.

Real platform earnings data isn't public, so the dataset is synthetically generated with volatility parameters calibrated to published Indian gig-economy income-volatility statistics (~30–40% week-to-week coefficient of variation), not arbitrary noise.

## Stack

Python · scikit-learn · Prophet · SHAP · FastAPI · React + Recharts · PostgreSQL
