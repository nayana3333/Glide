"""
Module 1: Synthetic Data Generator

Real platform earnings data is proprietary and not publicly available, so this
generator produces synthetic weekly gig-worker income calibrated to published
Indian gig-economy volatility statistics (~30-40% week-to-week coefficient of
variation), rather than arbitrary noise.

Output: earnings.csv
Columns: worker_id, week_start, week_index, platform, archetype, hours_worked,
         trips_completed, gross_earnings, fuel_cost, net_earnings, is_shock_week

Scale: 200 workers x 156 weeks (3 years) = 31,200 records
"""

from datetime import date, timedelta

import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)

N_WORKERS = 200
N_WEEKS = 156
START_DATE = date(2022, 1, 3)  # 3 years back, still a Monday

# Day-of-week earning multiplier: Mon..Sun (weekend uplift, Mon/Tue dip)
DAY_OF_WEEK_MULT = np.array([0.85, 0.85, 0.95, 1.00, 1.05, 1.25, 1.20])
WEEKDAY_COMPONENT = DAY_OF_WEEK_MULT.mean()

ARCHETYPES = {
    "full_time_driver": dict(
        share=0.35, base_range=(8000, 12000), hours_range=(50, 65),
        cv=0.30, platforms=["Ola", "Uber"],
    ),
    "part_time_delivery": dict(
        share=0.40, base_range=(4000, 7000), hours_range=(20, 35),
        cv=0.40, platforms=["Swiggy", "Zomato"],
    ),
    "multi_platform": dict(
        share=0.25, base_range=(7000, 11000), hours_range=(40, 55),
        cv=0.35, platforms=["Ola", "Uber", "Swiggy", "Zomato", "UrbanCompany"],
    ),
}


def monsoon_mult(week_start: date) -> float:
    """Jun-Sep suppression: fewer rides/deliveries during heavy rain."""
    return 0.85 if week_start.month in (6, 7, 8, 9) else 1.0


def festival_mult(week_start: date) -> float:
    """Oct-Nov (Dussehra/Diwali) and Dec-Jan (New Year/wedding season) surge."""
    if week_start.month in (10, 11):
        return 1.20
    if week_start.month in (12, 1):
        return 1.10
    return 1.0


def assign_archetype() -> str:
    r = RNG.random()
    cum = 0.0
    for name, cfg in ARCHETYPES.items():
        cum += cfg["share"]
        if r <= cum:
            return name
    return name


def build_worker_profile(worker_id: int) -> dict:
    archetype = assign_archetype()
    cfg = ARCHETYPES[archetype]
    return dict(
        worker_id=worker_id,
        archetype=archetype,
        base_weekly_income=RNG.uniform(*cfg["base_range"]),
        base_hours=RNG.uniform(*cfg["hours_range"]),
        cv=cfg["cv"],
        platform=RNG.choice(cfg["platforms"]),
    )


def build_week_record(profile: dict, week_idx: int, week_start: date) -> dict:
    seasonal = monsoon_mult(week_start) * festival_mult(week_start)

    # Mild per-worker trend over the 2-year window so series aren't flat
    trend = 1.0 + (week_idx / N_WEEKS) * RNG.uniform(-0.05, 0.10)

    expected_income = profile["base_weekly_income"] * WEEKDAY_COMPONENT * seasonal * trend

    # Gaussian noise calibrated to the archetype's target coefficient of variation
    noise = max(RNG.normal(loc=1.0, scale=profile["cv"]), 0.05)
    gross_earnings = max(expected_income * noise, 0.0)

    # Rare shock events (~2% of weeks): illness, vehicle breakdown, account suspension
    is_shock = RNG.random() < 0.02
    if is_shock:
        gross_earnings *= RNG.uniform(0.0, 0.15)

    hours_worked = (
        profile["base_hours"] * RNG.uniform(0.0, 0.2)
        if is_shock
        else max(profile["base_hours"] * noise * seasonal, 0.0)
    )
    trips_completed = max(int(hours_worked * RNG.uniform(1.0, 1.8)), 0)

    fuel_rate = RNG.uniform(5, 12) if profile["archetype"] == "part_time_delivery" else RNG.uniform(15, 25)
    fuel_cost = hours_worked * fuel_rate
    net_earnings = max(gross_earnings - fuel_cost, 0.0)

    return dict(
        worker_id=profile["worker_id"],
        week_start=week_start.isoformat(),
        week_index=week_idx,
        platform=profile["platform"],
        archetype=profile["archetype"],
        hours_worked=round(hours_worked, 1),
        trips_completed=trips_completed,
        gross_earnings=round(gross_earnings, 2),
        fuel_cost=round(fuel_cost, 2),
        net_earnings=round(net_earnings, 2),
        is_shock_week=is_shock,
    )


def generate_dataset(n_workers: int = N_WORKERS, n_weeks: int = N_WEEKS,
                      start_date: date = START_DATE) -> pd.DataFrame:
    records = []
    for worker_id in range(1, n_workers + 1):
        profile = build_worker_profile(worker_id)
        for week_idx in range(n_weeks):
            week_start = start_date + timedelta(weeks=week_idx)
            records.append(build_week_record(profile, week_idx, week_start))
    return pd.DataFrame.from_records(records)


def summarize(df: pd.DataFrame) -> None:
    per_worker_cv = df.groupby("worker_id")["net_earnings"].apply(lambda s: s.std() / s.mean())
    print(f"Records:                 {len(df)}")
    print(f"Workers:                 {df['worker_id'].nunique()}")
    print(f"Weeks per worker:        {df.groupby('worker_id').size().iloc[0]}")
    print(f"Mean weekly net earning: Rs.{df['net_earnings'].mean():,.2f}")
    print(f"Mean per-worker CV:      {per_worker_cv.mean():.3f}  (target 0.30-0.40)")
    print(f"Shock weeks:             {int(df['is_shock_week'].sum())} "
          f"({df['is_shock_week'].mean() * 100:.2f}% of records)")
    print("\nArchetype distribution:")
    print(df.drop_duplicates("worker_id")["archetype"].value_counts(normalize=True).round(3))


if __name__ == "__main__":
    dataset = generate_dataset()
    summarize(dataset)
    out_path = "earnings.csv"
    dataset.to_csv(out_path, index=False)
    print(f"\nSaved {out_path}")
