"""
Module 2 evaluation harness.

For a sample of workers, holds out the last TEST_WEEKS of their earnings
series, fits every model in MODELS on the remainder, forecasts the held-out
weeks, and reports MAE / RMSE / MAPE plus an Asymmetric Error Cost.

Asymmetric Error Cost penalises over-prediction 2x more than
under-prediction: if the system tells a worker to expect more income than
they'll actually get, they're left financially exposed, which is worse
than being pleasantly surprised. This is the project's methodological
contribution on top of standard forecast metrics.

Usage:
    python evaluate.py            # sample of 30 workers (fast, ~2 min)
    python evaluate.py --full     # all 200 workers
"""

import argparse
import sys
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from forecast_models import MODELS  # noqa: E402

warnings.filterwarnings("ignore")

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "earnings.csv"
ARTIFACT_DIR = Path(__file__).resolve().parents[1] / "artifacts"
TEST_WEEKS = 8
DEFAULT_SAMPLE = 30


def load_worker_series(df: pd.DataFrame, worker_id: int) -> pd.Series:
    w = df[df.worker_id == worker_id].sort_values("week_index")
    s = pd.Series(w.net_earnings.values, index=pd.to_datetime(w.week_start))
    return s.asfreq("7D")  # plain 7-day spacing; "W" would anchor to Sunday and misalign the data


def asymmetric_cost(actual: np.ndarray, predicted: np.ndarray, over_penalty: float = 2.0) -> float:
    error = predicted - actual
    cost = np.where(error > 0, error * over_penalty, -error)
    return float(cost.mean())


def score(actual: np.ndarray, predicted: np.ndarray) -> dict:
    mae = float(np.mean(np.abs(actual - predicted)))
    rmse = float(np.sqrt(np.mean((actual - predicted) ** 2)))
    # sMAPE, not MAPE: shock weeks push actual earnings near zero, which makes
    # plain MAPE (dividing by actual) blow up to absurd values. sMAPE divides
    # by the average of |actual| and |predicted| instead, bounding it to 0-200%.
    smape = float(np.mean(2 * np.abs(actual - predicted) / (np.abs(actual) + np.abs(predicted) + 1e-6)) * 100)
    return dict(MAE=mae, RMSE=rmse, sMAPE=smape, AsymCost=asymmetric_cost(actual, predicted))


def run_evaluation(n_workers: int, seed: int = 42):
    df = pd.read_csv(DATA_PATH)
    worker_ids = df.worker_id.unique()
    rng = np.random.default_rng(seed)
    sample = rng.choice(worker_ids, size=min(n_workers, len(worker_ids)), replace=False)

    per_model_scores = {name: [] for name in MODELS}
    example = None  # forecasts for the first sampled worker, used for the preview chart

    for i, wid in enumerate(sample):
        series = load_worker_series(df, wid)
        train, test = series.iloc[:-TEST_WEEKS], series.iloc[-TEST_WEEKS:]

        forecasts = {}
        for name, fn in MODELS.items():
            try:
                fc = fn(train, TEST_WEEKS)
            except Exception as exc:
                print(f"  [warn] {name} failed on worker {wid}: {exc}; using trailing-mean fallback")
                fallback = train.iloc[-4:].mean()
                fc = pd.DataFrame(
                    {"yhat": fallback, "yhat_lower": np.nan, "yhat_upper": np.nan},
                    index=test.index,
                )
            forecasts[name] = fc
            per_model_scores[name].append(score(test.values, fc["yhat"].values))

        if i == 0:
            example = dict(worker_id=wid, train=train, test=test, forecasts=forecasts)

        print(f"  worker {wid} done ({i + 1}/{len(sample)})")

    summary = pd.DataFrame(
        {name: pd.DataFrame(vals).mean() for name, vals in per_model_scores.items()}
    ).T
    return summary.sort_values("MAE"), example


def plot_example(example: dict, out_path: Path):
    train, test, forecasts = example["train"], example["test"], example["forecasts"]
    history = train.iloc[-16:]  # last 16 weeks of history for context

    fig, ax = plt.subplots(figsize=(11, 6))
    ax.plot(history.index, history.values, color="#333333", label="Actual (history)", linewidth=1.8)
    ax.plot(test.index, test.values, color="#111111", marker="o", label="Actual (held-out)", linewidth=1.8)

    colors = {"Naive": "#9e9e9e", "MovingAvg(4wk)": "#5b8def", "ARIMA": "#e07b39", "Prophet": "#1f9d55"}
    for name, fc in forecasts.items():
        ax.plot(fc.index, fc["yhat"].values, color=colors.get(name, "black"),
                 linestyle="--", marker="x", label=f"{name} forecast", linewidth=1.6)
        if fc["yhat_lower"].notna().all():
            ax.fill_between(fc.index, fc["yhat_lower"], fc["yhat_upper"],
                             color=colors.get(name, "black"), alpha=0.08)

    ax.axvline(train.index[-1], color="grey", linestyle=":", linewidth=1)
    ax.set_title(f"Worker {example['worker_id']} — Actual vs Forecast Weekly Net Earnings")
    ax.set_xlabel("Week")
    ax.set_ylabel("Net earnings (INR)")
    ax.legend(loc="upper left", fontsize=9)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true", help="evaluate all 200 workers instead of a sample")
    args = parser.parse_args()

    n = 200 if args.full else DEFAULT_SAMPLE
    print(f"Evaluating {n} workers, {TEST_WEEKS}-week holdout...\n")

    summary, example = run_evaluation(n_workers=n)

    ARTIFACT_DIR.mkdir(exist_ok=True)
    print("\nModel comparison (lower is better for all columns):\n")
    print(summary.round(2).to_string())

    summary.round(3).to_csv(ARTIFACT_DIR / "model_comparison.csv")
    print(f"\nSaved {ARTIFACT_DIR / 'model_comparison.csv'}")

    chart_path = ARTIFACT_DIR / "forecast_example.png"
    plot_example(example, chart_path)
    print(f"Saved {chart_path}")
