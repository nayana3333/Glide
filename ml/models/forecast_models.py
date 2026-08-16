"""
Module 2: Forecast Engine

Model stack, weakest to strongest baseline:
Naive -> Moving Average -> ARIMA -> Prophet (primary model)

Each *_forecast function takes a training pd.Series indexed by weekly
timestamps and a forecast horizon (in weeks), and returns a DataFrame
with columns ['yhat', 'yhat_lower', 'yhat_upper'] indexed by the
forecast dates. Lower/upper bounds are NaN for models that don't
produce an uncertainty interval (Naive, Moving Average).
"""

import logging

import numpy as np
import pandas as pd
from prophet import Prophet
from statsmodels.tsa.arima.model import ARIMA

logging.getLogger("cmdstanpy").setLevel(logging.WARNING)
logging.getLogger("prophet").setLevel(logging.WARNING)


def _future_dates(train: pd.Series, horizon: int) -> pd.DatetimeIndex:
    # plain 7-day spacing to match the source data's Monday-anchored weeks;
    # pandas' "W" alias anchors to Sunday and would misalign the index
    return pd.date_range(train.index[-1] + pd.Timedelta(weeks=1), periods=horizon, freq="7D")


def naive_forecast(train: pd.Series, horizon: int) -> pd.DataFrame:
    """Baseline: next week = last observed week."""
    last_value = train.iloc[-1]
    dates = _future_dates(train, horizon)
    return pd.DataFrame(
        {"yhat": last_value, "yhat_lower": np.nan, "yhat_upper": np.nan}, index=dates
    )


def moving_average_forecast(train: pd.Series, horizon: int, window: int = 4) -> pd.DataFrame:
    """Baseline: flat forecast at the trailing `window`-week average."""
    avg = train.iloc[-window:].mean()
    dates = _future_dates(train, horizon)
    return pd.DataFrame(
        {"yhat": avg, "yhat_lower": np.nan, "yhat_upper": np.nan}, index=dates
    )


# (p, d, q) candidates for the order search. Small and deliberately bounded -
# weekly earnings series here run ~100-150 points, so higher orders risk
# overfitting the noise rather than capturing real structure. Excludes
# (0, d, 0), which is just a random walk and never worth grid-searching.
ARIMA_ORDER_GRID = [
    (p, d, q) for p in (0, 1, 2) for d in (0, 1) for q in (0, 1, 2) if not (p == 0 and q == 0)
]


def select_arima_order(train_values: np.ndarray, candidates=ARIMA_ORDER_GRID):
    """
    AIC-based order search: fits every candidate order and keeps the one
    with the lowest Akaike Information Criterion (lower AIC = better fit
    per model parameter spent, penalising unnecessary complexity). Replaces
    a single hardcoded order with a per-series selection, since each
    worker's earnings series has its own autocorrelation structure.

    Falls back to (1, 1, 0) if every candidate fails to converge - rare,
    but happens on short or unusually flat series.
    """
    best_order, best_aic, best_fit = None, np.inf, None
    for order in candidates:
        try:
            fit = ARIMA(train_values, order=order).fit()
        except Exception:
            continue
        if fit.aic < best_aic:
            best_order, best_aic, best_fit = order, fit.aic, fit

    if best_fit is None:
        best_order = (1, 1, 0)
        best_fit = ARIMA(train_values, order=best_order).fit()

    return best_order, best_fit


def arima_forecast(train: pd.Series, horizon: int) -> pd.DataFrame:
    """Classical benchmark. Order selected per-series via AIC grid search
    (see select_arima_order) rather than a single fixed order."""
    dates = _future_dates(train, horizon)
    _, fit = select_arima_order(train.values)
    fc = fit.get_forecast(steps=horizon)
    ci = fc.conf_int(alpha=0.2)  # 80% interval, matches Prophet's default
    return pd.DataFrame(
        {"yhat": fc.predicted_mean, "yhat_lower": ci[:, 0], "yhat_upper": ci[:, 1]},
        index=dates,
    )


# Selected via grid search over changepoint_prior_scale x seasonality_prior_scale
# on a 20-worker sample (see tune_prophet.py, ml/artifacts/prophet_tuning.csv).
# These happen to match Prophet's own defaults - the search confirmed that
# rather than finding something better, which is itself a useful result: the
# defaults weren't an unexamined assumption, they were checked.
PROPHET_CHANGEPOINT_PRIOR_SCALE = 0.05
PROPHET_SEASONALITY_PRIOR_SCALE = 10.0


def prophet_forecast(train: pd.Series, horizon: int) -> pd.DataFrame:
    """
    Primary model. Uses Indian holiday regressors (proxy for festival demand
    surges) and yearly seasonality (proxy for the monsoon dip). Produces a
    genuine uncertainty interval, which the buffer engine needs downstream.
    """
    df = pd.DataFrame({"ds": train.index, "y": train.values})
    m = Prophet(
        weekly_seasonality=False,
        yearly_seasonality=True,
        daily_seasonality=False,
        interval_width=0.8,
        changepoint_prior_scale=PROPHET_CHANGEPOINT_PRIOR_SCALE,
        seasonality_prior_scale=PROPHET_SEASONALITY_PRIOR_SCALE,
    )
    m.add_country_holidays(country_name="IN")
    m.fit(df)
    future = m.make_future_dataframe(periods=horizon, freq="7D")
    fc = m.predict(future).set_index("ds").iloc[-horizon:]
    return fc[["yhat", "yhat_lower", "yhat_upper"]]


MODELS = {
    "Naive": naive_forecast,
    "MovingAvg(4wk)": moving_average_forecast,
    "ARIMA": arima_forecast,
    "Prophet": prophet_forecast,
}
