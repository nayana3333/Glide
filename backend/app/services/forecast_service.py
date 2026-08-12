import sys

import pandas as pd

from app.config import BASE_DIR

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ml.models.dip_detector import classify_dip, deficit_ratio  # noqa: E402
from ml.models.forecast_models import prophet_forecast  # noqa: E402

FORECAST_HORIZON = 4
ROLLING_WINDOW = 8
MIN_HISTORY_WEEKS = 10


def _series_from_earnings(earnings_rows) -> pd.Series:
    dates = pd.to_datetime([r.week_start for r in earnings_rows])
    values = [r.net_earnings for r in earnings_rows]
    return pd.Series(values, index=dates).asfreq("7D")


def forecast_worker(earnings_rows, horizon: int = FORECAST_HORIZON) -> dict:
    if len(earnings_rows) < MIN_HISTORY_WEEKS:
        raise ValueError(f"Need at least {MIN_HISTORY_WEEKS} weeks of earnings history to forecast")

    series = _series_from_earnings(earnings_rows)
    rolling_avg = float(series.iloc[-ROLLING_WINDOW:].mean())

    fc = prophet_forecast(series, horizon)

    weeks = []
    for date, row in fc.iterrows():
        weeks.append(
            dict(
                week_start=date.date().isoformat(),
                yhat=float(row["yhat"]),
                yhat_lower=float(row["yhat_lower"]) if pd.notna(row["yhat_lower"]) else None,
                yhat_upper=float(row["yhat_upper"]) if pd.notna(row["yhat_upper"]) else None,
                dip_level=classify_dip(row["yhat"], rolling_avg),
                deficit_ratio=deficit_ratio(row["yhat"], rolling_avg),
            )
        )

    return dict(model_used="Prophet", rolling_avg=rolling_avg, forecast=weeks)
