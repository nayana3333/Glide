"""
Module 3: Dip Detection

Classifies a forecast into an actionable alert level by comparing it
against the worker's trailing rolling average. Thresholds are the
blueprint's starting values; tune on a validation split and report the
tuned values in the results section.
"""

GREEN, AMBER, RED = "GREEN", "AMBER", "RED"

AMBER_THRESHOLD = 0.10  # deficit_ratio below this is normal variation
RED_THRESHOLD = 0.25    # deficit_ratio at/above this is a dip worth acting on


def deficit_ratio(predicted: float, rolling_avg: float) -> float:
    if rolling_avg <= 0:
        return 0.0
    return (rolling_avg - predicted) / rolling_avg


def classify_dip(predicted: float, rolling_avg: float) -> str:
    ratio = deficit_ratio(predicted, rolling_avg)
    if ratio < AMBER_THRESHOLD:
        return GREEN
    if ratio < RED_THRESHOLD:
        return AMBER
    return RED


if __name__ == "__main__":
    # sanity check against the blueprint's own boundary examples
    cases = [
        (9500, 10000),  # 5% below avg -> GREEN
        (8500, 10000),  # 15% below avg -> AMBER
        (7000, 10000),  # 30% below avg -> RED
    ]
    for predicted, avg in cases:
        ratio = deficit_ratio(predicted, avg)
        print(f"predicted={predicted}, rolling_avg={avg}, "
              f"deficit_ratio={ratio:.2f} -> {classify_dip(predicted, avg)}")
