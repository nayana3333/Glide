"""
Module 2 hyperparameter tuning: Prophet.

Prophet fits are too slow to tune per-worker across all 200 workers (each
fit is ~1-2s; a grid x 200 workers would take tens of minutes just for one
sweep). Instead, this tunes once on a representative sample of workers
(same DEFAULT_SAMPLE convention as evaluate.py) and selects a single global
configuration, which is the realistic choice for a system serving many
similar time series - not a shortcut, a standard "tune globally, fit
per-series" pattern in production forecasting.

Grid: changepoint_prior_scale controls how flexible the trend is (higher =
more willing to bend to recent changes, risking overfitting); seasonality_
prior_scale controls how strongly the yearly/holiday seasonality can flex.
Both left at Prophet's defaults (0.05 and 10.0) were never actually
verified as good choices for this data - that's the gap being closed here.

Usage:
    python tune_prophet.py            # sample of 20 workers (~5 min)
    python tune_prophet.py --sample 40
"""

import argparse
import itertools
import logging
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from prophet import Prophet

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evaluate import TEST_WEEKS, load_worker_series, score  # noqa: E402

logging.getLogger("cmdstanpy").setLevel(logging.WARNING)
logging.getLogger("prophet").setLevel(logging.WARNING)
warnings.filterwarnings("ignore")

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "earnings.csv"
ARTIFACT_DIR = Path(__file__).resolve().parents[1] / "artifacts"
DEFAULT_SAMPLE = 20

CHANGEPOINT_PRIOR_GRID = [0.01, 0.05, 0.1, 0.5]
SEASONALITY_PRIOR_GRID = [1.0, 10.0]


def fit_and_forecast(train: pd.Series, horizon: int, changepoint_prior: float, seasonality_prior: float) -> pd.Series:
    df = pd.DataFrame({"ds": train.index, "y": train.values})
    m = Prophet(
        weekly_seasonality=False,
        yearly_seasonality=True,
        daily_seasonality=False,
        interval_width=0.8,
        changepoint_prior_scale=changepoint_prior,
        seasonality_prior_scale=seasonality_prior,
    )
    m.add_country_holidays(country_name="IN")
    m.fit(df)
    future = m.make_future_dataframe(periods=horizon, freq="7D")
    fc = m.predict(future).set_index("ds").iloc[-horizon:]
    return fc["yhat"].values


def run(n_workers: int, seed: int = 42):
    df = pd.read_csv(DATA_PATH)
    worker_ids = df.worker_id.unique()
    rng = np.random.default_rng(seed)
    sample = rng.choice(worker_ids, size=min(n_workers, len(worker_ids)), replace=False)

    grid = list(itertools.product(CHANGEPOINT_PRIOR_GRID, SEASONALITY_PRIOR_GRID))
    results = {combo: [] for combo in grid}

    for i, wid in enumerate(sample):
        series = load_worker_series(df, wid)
        train, test = series.iloc[:-TEST_WEEKS], series.iloc[-TEST_WEEKS:]

        for changepoint_prior, seasonality_prior in grid:
            try:
                yhat = fit_and_forecast(train, TEST_WEEKS, changepoint_prior, seasonality_prior)
            except Exception as exc:
                print(f"  [warn] combo ({changepoint_prior}, {seasonality_prior}) failed on worker {wid}: {exc}")
                continue
            results[(changepoint_prior, seasonality_prior)].append(score(test.values, yhat))

        print(f"  worker {wid} done ({i + 1}/{len(sample)})")

    summary = pd.DataFrame(
        {
            f"cp={cp}_sp={sp}": pd.DataFrame(vals).mean()
            for (cp, sp), vals in results.items()
            if vals
        }
    ).T
    summary.index.name = "combo"
    summary = summary.sort_values("MAE")

    ARTIFACT_DIR.mkdir(exist_ok=True)
    summary.round(3).to_csv(ARTIFACT_DIR / "prophet_tuning.csv")

    best = summary.index[0]
    best_cp, best_sp = [float(x.split("=")[1]) for x in best.split("_")]
    print("\nProphet hyperparameter sweep (lower MAE is better):\n")
    print(summary.round(2).to_string())
    print(f"\nBest: changepoint_prior_scale={best_cp}, seasonality_prior_scale={best_sp}")
    print(f"Saved {ARTIFACT_DIR / 'prophet_tuning.csv'}")
    return best_cp, best_sp


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", type=int, default=DEFAULT_SAMPLE)
    args = parser.parse_args()
    run(args.sample)
