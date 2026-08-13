import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "models"))

import pandas as pd
import pytest
from buffer_engine import BUFFER_CEILING_WEEKS, simulate_buffer


def test_first_week_never_saves_or_releases():
    # week 0's rolling_avg is defined to equal week 0's own actual value, so
    # it can never register as a surplus or deficit week
    for first_value in [0, 500, 999999]:
        income = pd.Series([first_value, first_value + 100])
        sim = simulate_buffer(income)
        assert sim["save"].iloc[0] == 0
        assert sim["release"].iloc[0] == 0
        assert sim["buffer_balance"].iloc[0] == 0
        assert sim["smoothed_income"].iloc[0] == first_value


def test_surplus_then_deficit_hand_verified():
    # income: flat 1000, one spike to 2000, then back to flat 1000
    income = pd.Series([1000, 2000, 1000, 1000])
    sim = simulate_buffer(income)

    # week 0: no history yet -> no transaction (see test above)
    assert sim["rolling_avg"].iloc[0] == 1000

    # week 1: rolling_avg = mean(income[:1]) = 1000, actual = 2000
    # surplus = 1000; save = min(1000*0.4, 2000*0.15) = min(400, 300) = 300
    assert sim["rolling_avg"].iloc[1] == pytest.approx(1000)
    assert sim["save"].iloc[1] == pytest.approx(300)
    assert sim["release"].iloc[1] == 0
    assert sim["buffer_balance"].iloc[1] == pytest.approx(300)
    assert sim["smoothed_income"].iloc[1] == pytest.approx(1700)

    # week 2: rolling_avg = mean(income[:2]) = mean(1000, 2000) = 1500, actual = 1000
    # gap = 500; release = min(500, buffer=300) = 300 (buffer only has 300 to give)
    assert sim["rolling_avg"].iloc[2] == pytest.approx(1500)
    assert sim["save"].iloc[2] == 0
    assert sim["release"].iloc[2] == pytest.approx(300)
    assert sim["buffer_balance"].iloc[2] == pytest.approx(0)
    assert sim["smoothed_income"].iloc[2] == pytest.approx(1300)

    # week 3: buffer is already empty, so a further deficit gets no cushion at all
    # rolling_avg = mean(income[:3]) = mean(1000, 2000, 1000) = 1333.33, actual = 1000
    assert sim["release"].iloc[3] == 0
    assert sim["buffer_balance"].iloc[3] == pytest.approx(0)
    assert sim["smoothed_income"].iloc[3] == pytest.approx(1000)


def test_buffer_balance_never_negative():
    # one big week followed by a long string of low weeks: repeated releases
    # must never overdraw the buffer below zero
    income = pd.Series([5000] + [100] * 15)
    sim = simulate_buffer(income)
    assert (sim["buffer_balance"] >= 0).all()


def test_buffer_never_exceeds_ceiling():
    # alternating low/high weeks keep offering surplus to save; the ceiling
    # (BUFFER_CEILING_WEEKS x that week's rolling average) must always hold
    income = pd.Series([1000, 20000] * 20)
    sim = simulate_buffer(income)
    ceiling = BUFFER_CEILING_WEEKS * sim["rolling_avg"]
    assert (sim["buffer_balance"] <= ceiling + 1e-6).all()


def test_save_never_exceeds_cap_ratio_of_actual_income():
    income = pd.Series([1000, 50000, 1000, 1000, 1000])
    sim = simulate_buffer(income)
    # SAVE_CAP_RATIO = 0.15, so no single week should save more than 15% of
    # that week's own actual earnings, no matter how large the surplus is
    ratios = sim["save"] / sim["actual"].replace(0, pd.NA)
    assert (ratios.dropna() <= 0.15 + 1e-9).all()
