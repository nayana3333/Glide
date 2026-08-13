import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "models"))

from dip_detector import AMBER, AMBER_THRESHOLD, GREEN, RED, RED_THRESHOLD, classify_dip, deficit_ratio


def test_deficit_ratio_basic():
    assert deficit_ratio(9500, 10000) == 0.05
    assert deficit_ratio(10000, 10000) == 0.0
    assert deficit_ratio(11000, 10000) == -0.1  # surplus -> negative ratio


def test_deficit_ratio_guards_against_nonpositive_rolling_avg():
    assert deficit_ratio(500, 0) == 0.0
    assert deficit_ratio(500, -100) == 0.0


def test_classify_dip_surplus_is_green():
    assert classify_dip(11000, 10000) == GREEN


def test_classify_dip_normal_variation_is_green():
    assert classify_dip(9500, 10000) == GREEN  # 5% below, under the AMBER threshold


def test_classify_dip_amber_lower_boundary_is_amber_not_green():
    # exactly at AMBER_THRESHOLD: spec is "< AMBER_THRESHOLD -> GREEN", so the
    # boundary itself must NOT be green
    predicted = 10000 * (1 - AMBER_THRESHOLD)
    assert deficit_ratio(predicted, 10000) == AMBER_THRESHOLD
    assert classify_dip(predicted, 10000) == AMBER


def test_classify_dip_mid_amber_range():
    assert classify_dip(8500, 10000) == AMBER  # 15% below


def test_classify_dip_red_lower_boundary_is_red_not_amber():
    # exactly at RED_THRESHOLD: spec is "< RED_THRESHOLD -> AMBER", so the
    # boundary itself must already be RED
    predicted = 10000 * (1 - RED_THRESHOLD)
    assert deficit_ratio(predicted, 10000) == RED_THRESHOLD
    assert classify_dip(predicted, 10000) == RED


def test_classify_dip_deep_red():
    assert classify_dip(7000, 10000) == RED  # 30% below


def test_classify_dip_zero_rolling_avg_defaults_green():
    # deficit_ratio guards to 0.0 when rolling_avg <= 0, which is < AMBER_THRESHOLD
    assert classify_dip(500, 0) == GREEN
