"""
Wraps the pooled Random Forest + SHAP explainer from ml.models.explain.
Trained once (on the synthetic population) and cached in memory; used to
explain the *next* week's prediction for any worker — including a real
registered user — from their own recent earnings.
"""

import sys

import pandas as pd

from app.config import BASE_DIR, DATA_PATH

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ml.models.explain import FEATURE_COLS, LABELS, train_model  # noqa: E402

MIN_HISTORY_WEEKS = 4
_cache: dict = {}


def _get_trained():
    if "model" not in _cache:
        raw = pd.read_csv(DATA_PATH)
        model, explainer, _features, archetype_enc, platform_enc = train_model(raw)
        _cache.update(model=model, explainer=explainer, archetype_enc=archetype_enc, platform_enc=platform_enc)
    return _cache["model"], _cache["explainer"], _cache["archetype_enc"], _cache["platform_enc"]


def explain_worker(earnings_rows, archetype: str, platform: str) -> dict:
    if len(earnings_rows) < MIN_HISTORY_WEEKS:
        raise ValueError(f"Need at least {MIN_HISTORY_WEEKS} weeks of earnings history to explain a prediction")

    model, explainer, archetype_enc, platform_enc = _get_trained()

    rows = sorted(earnings_rows, key=lambda r: r.week_index)
    last = rows[-1]
    last4 = rows[-4:]
    next_week_start = pd.to_datetime(last.week_start) + pd.Timedelta(weeks=1)

    feature_row = pd.DataFrame(
        [
            dict(
                month=next_week_start.month,
                is_monsoon=int(next_week_start.month in (6, 7, 8, 9)),
                is_festival=int(next_week_start.month in (10, 11, 12, 1)),
                week_index=last.week_index + 1,
                lag_1_earnings=last.net_earnings,
                lag_4wk_avg_earnings=sum(r.net_earnings for r in last4) / len(last4),
                lag_1_hours=last.hours_worked,
                archetype_enc=int(archetype_enc.transform([archetype])[0]),
                platform_enc=int(platform_enc.transform([platform])[0]),
            )
        ]
    )[FEATURE_COLS]

    predicted = float(model.predict(feature_row)[0])
    rolling_avg = float(feature_row["lag_4wk_avg_earnings"].iloc[0])
    deficit_ratio = (rolling_avg - predicted) / rolling_avg if rolling_avg else 0.0

    shap_values = explainer.shap_values(feature_row)[0]
    contributions = {LABELS.get(feat, feat): float(val) for feat, val in zip(FEATURE_COLS, shap_values)}

    return dict(
        predicted=predicted,
        rolling_avg_4wk=rolling_avg,
        deficit_ratio=float(deficit_ratio),
        contributions=contributions,
    )
