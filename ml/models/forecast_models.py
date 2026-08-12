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


def arima_forecast(train: pd.Series, horizon: int, order=(2, 1, 1)) -> pd.DataFrame:
    """Classical benchmark. Falls back to a simpler order if the fit fails to converge."""
    dates = _future_dates(train, horizon)
    try:
        fit = ARIMA(train.values, order=order).fit()
    except Exception:
        fit = ARIMA(train.values, order=(1, 1, 0)).fit()
    fc = fit.get_forecast(steps=horizon)
    ci = fc.conf_int(alpha=0.2)  # 80% interval, matches Prophet's default
    return pd.DataFrame(
        {"yhat": fc.predicted_mean, "yhat_lower": ci[:, 0], "yhat_upper": ci[:, 1]},
        index=dates,
    )


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
