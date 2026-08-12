"""
Module 4: Buffer Allocation Engine — the project's core novelty.

Converts a worker's income stream into a savings action every week: sweep
part of a surplus into a buffer, release part of the buffer during a
deficit, so the *experienced* (post-buffer) income is smoother than the
raw income. Reactive by design — driven by a trailing rolling average, not
a forecast — so it runs directly on observed earnings.

Parameters match the blueprint's starting values.
"""

import numpy as np
import pandas as pd

ALPHA = 0.4              # fraction of a surplus week swept into the buffer
SAVE_CAP_RATIO = 0.15    # never save more than 15% of a week's income
ROLLING_WINDOW = 8       # weeks used to compute the rolling-average baseline
BUFFER_CEILING_WEEKS = 4  # stop accumulating beyond 4 weeks of average income


def simulate_buffer(income: pd.Series) -> pd.DataFrame:
    """
    income: one worker's weekly net earnings, chronological order.

    Returns a DataFrame indexed like `income` with columns:
      actual, rolling_avg, save, release, buffer_balance, smoothed_income
    """
    n = len(income)
    rolling_avg = income.rolling(ROLLING_WINDOW, min_periods=1).mean().shift(1)
    rolling_avg.iloc[0] = income.iloc[0]  # no prior history for week 1

    buffer_balance = 0.0
    saves = np.zeros(n)
    releases = np.zeros(n)
    balances = np.zeros(n)
    smoothed = np.zeros(n)

    for i in range(n):
        actual = income.iloc[i]
        avg = rolling_avg.iloc[i]
        ceiling = BUFFER_CEILING_WEEKS * avg

        if actual > avg:
            surplus = actual - avg
            save = min(surplus * ALPHA, actual * SAVE_CAP_RATIO)
            save = min(save, max(ceiling - buffer_balance, 0.0))  # respect the ceiling
            buffer_balance += save
            saves[i] = save
            smoothed[i] = actual - save
        else:
            gap = avg - actual
            release = min(gap, buffer_balance)
            buffer_balance -= release
            releases[i] = release
            smoothed[i] = actual + release

        balances[i] = buffer_balance

    return pd.DataFrame(
        {
            "actual": income.values,
            "rolling_avg": rolling_avg.values,
            "save": saves,
            "release": releases,
            "buffer_balance": balances,
            "smoothed_income": smoothed,
        },
        index=income.index,
    )
