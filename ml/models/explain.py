"""
Module 5: Explainability (SHAP)

Trains a single pooled Random Forest on engineered seasonal + lag features
across all workers, then uses SHAP to explain individual predictions in
plain language, e.g. "predicted low because -> monsoon season (-Rs.1,200),
recent hours declining (-Rs.400)".

Scope note: this model is a *one-step-ahead* predictor (each test-week
prediction is allowed to see the true previous week's actuals as lag
features), evaluated separately from Module 2's Naive/MA/ARIMA/Prophet
comparison, which forecasts the full 8-week horizon from training data
alone. The two are not directly comparable on the same table. Prophet's
own trend/yearly/holiday decomposition remains the interpretability path
for the primary forecasting model; this module gives a complementary,
feature-level explanation for individual dip alerts, since Prophet/ARIMA
don't expose a SHAP-friendly internal structure.
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "earnings.csv"
ARTIFACT_DIR = Path(__file__).resolve().parents[1] / "artifacts"

LAG_WINDOW = 4
TEST_WEEKS = 8

FEATURE_COLS = [
    "month", "is_monsoon", "is_festival", "week_index",
    "lag_1_earnings", "lag_4wk_avg_earnings", "lag_1_hours",
    "archetype_enc", "platform_enc",
]

LABELS = {
    "is_monsoon": "monsoon season",
    "is_festival": "festival season",
    "lag_1_earnings": "last week's earnings",
    "lag_4wk_avg_earnings": "recent 4-week trend",
    "lag_1_hours": "hours worked last week",
    "week_index": "long-term trend",
    "month": "time of year",
    "archetype_enc": "worker type",
    "platform_enc": "platform",
}


def build_features(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()
    df["week_start"] = pd.to_datetime(df["week_start"])
    df["month"] = df["week_start"].dt.month
    df["is_monsoon"] = df["month"].isin([6, 7, 8, 9]).astype(int)
    df["is_festival"] = df["month"].isin([10, 11, 12, 1]).astype(int)
    df["archetype_enc"] = LabelEncoder().fit_transform(df["archetype"])
    df["platform_enc"] = LabelEncoder().fit_transform(df["platform"])

    rows = []
    for wid, w in df.groupby("worker_id"):
        w = w.sort_values("week_index").reset_index(drop=True)
        earnings = w["net_earnings"].values
        hours = w["hours_worked"].values
        n = len(w)
        for i in range(LAG_WINDOW, n):
            rows.append(dict(
                worker_id=wid,
                week_index=int(w.loc[i, "week_index"]),
                month=int(w.loc[i, "month"]),
                is_monsoon=int(w.loc[i, "is_monsoon"]),
                is_festival=int(w.loc[i, "is_festival"]),
                lag_1_earnings=earnings[i - 1],
                lag_4wk_avg_earnings=earnings[i - 4:i].mean(),
                lag_1_hours=hours[i - 1],
                archetype_enc=int(w.loc[i, "archetype_enc"]),
                platform_enc=int(w.loc[i, "platform_enc"]),
                target=earnings[i],
                is_test=(n - i) <= TEST_WEEKS,
            ))
    return pd.DataFrame(rows)


def train_and_explain():
    raw = pd.read_csv(DATA_PATH)
    features = build_features(raw)

    train = features[~features.is_test]
    test = features[features.is_test].reset_index(drop=True)

    model = RandomForestRegressor(n_estimators=300, max_depth=10, random_state=42, n_jobs=-1)
    model.fit(train[FEATURE_COLS], train["target"])

    pred = model.predict(test[FEATURE_COLS])
    actual = test["target"].values
    mae = np.mean(np.abs(actual - pred))
    rmse = np.sqrt(np.mean((actual - pred) ** 2))
    smape = np.mean(2 * np.abs(actual - pred) / (np.abs(actual) + np.abs(pred) + 1e-6)) * 100
    print(f"Random Forest (1-step-ahead, pooled across all workers, {len(test)} test rows):")
    print(f"  MAE={mae:.2f}  RMSE={rmse:.2f}  sMAPE={smape:.2f}%")

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(test[FEATURE_COLS])

    test["pred"] = pred
    test["deficit_ratio"] = (
        (test["lag_4wk_avg_earnings"] - test["pred"]) / test["lag_4wk_avg_earnings"].clip(lower=1)
    )
    example_idx = int(test["deficit_ratio"].idxmax())
    example_row = test.loc[example_idx]

    print(f"\nExample dip explanation - worker {int(example_row.worker_id)}, "
          f"week_index {int(example_row.week_index)}:")
    print(f"  predicted=Rs.{example_row.pred:.0f}  4wk_avg=Rs.{example_row.lag_4wk_avg_earnings:.0f}  "
          f"deficit_ratio={example_row.deficit_ratio:.2f}")

    contributions = pd.Series(shap_values[example_idx], index=FEATURE_COLS).sort_values()
    print("\n  Why this prediction:")
    for feat, val in contributions.items():
        if abs(val) < 1:
            continue
        sign = "-" if val < 0 else "+"
        print(f"    {LABELS.get(feat, feat):<24} {sign}Rs.{abs(val):,.0f}")

    ARTIFACT_DIR.mkdir(exist_ok=True)
    plot_explanation(contributions, example_row, ARTIFACT_DIR / "shap_explanation.png")
    print(f"\nSaved {ARTIFACT_DIR / 'shap_explanation.png'}")


def plot_explanation(contributions: pd.Series, example_row: pd.Series, out_path: Path):
    labels = [LABELS.get(f, f) for f in contributions.index]
    values = contributions.values
    colors = ["#c0392b" if v < 0 else "#1f9d55" for v in values]

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(labels, values, color=colors)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_xlabel("SHAP contribution relative to average prediction (INR)")
    ax.set_title(
        f"Worker {int(example_row.worker_id)} — why the model predicts a low week\n"
        f"(predicted Rs.{example_row.pred:,.0f} vs recent avg Rs.{example_row.lag_4wk_avg_earnings:,.0f})"
    )
    ax.grid(alpha=0.25, axis="x")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    train_and_explain()
