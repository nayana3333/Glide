"""
Module 4 evaluation: runs the buffer engine across all 200 workers and
reports the headline result — % reduction in weeks where a worker's income
fell below their essential-expense floor, with vs without the buffer.

Essential-expense floor is a modeling assumption (not in the raw data):
a worker's own subsistence spending is set at ESSENTIAL_FLOOR_RATIO of
their long-run average net earnings. State this explicitly as an
assumption in the report; it is not derived from any ground truth.
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from buffer_engine import simulate_buffer  # noqa: E402

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "earnings.csv"
ARTIFACT_DIR = Path(__file__).resolve().parents[1] / "artifacts"
ESSENTIAL_FLOOR_RATIO = 0.55


def run():
    df = pd.read_csv(DATA_PATH)
    rows = []
    example = None

    for wid, w in df.groupby("worker_id"):
        w = w.sort_values("week_index")
        income = pd.Series(w.net_earnings.values, index=pd.to_datetime(w.week_start))
        floor = ESSENTIAL_FLOOR_RATIO * income.mean()

        sim = simulate_buffer(income)

        shortfalls_without = int((income < floor).sum())
        shortfalls_with = int((sim["smoothed_income"] < floor).sum())

        rows.append(
            dict(
                worker_id=wid,
                floor=floor,
                weeks=len(income),
                shortfalls_without=shortfalls_without,
                shortfalls_with=shortfalls_with,
                avg_buffer_balance=sim["buffer_balance"].mean(),
                max_buffer_balance=sim["buffer_balance"].max(),
            )
        )

        if example is None:
            example = dict(worker_id=wid, income=income, floor=floor, sim=sim)

    result = pd.DataFrame(rows)
    total_without = result["shortfalls_without"].sum()
    total_with = result["shortfalls_with"].sum()
    pct_reduction = (total_without - total_with) / total_without * 100 if total_without else 0.0
    zero_shortfall_workers = int((result["shortfalls_with"] == 0).sum())

    print(f"Workers simulated:                   {len(result)}")
    print(f"Total shortfall weeks (no buffer):   {total_without}")
    print(f"Total shortfall weeks (with buffer): {total_with}")
    print(f"Shortfall reduction:                 {pct_reduction:.1f}%")
    print(f"Avg buffer balance maintained:       Rs.{result['avg_buffer_balance'].mean():,.0f}")
    print(f"Workers with zero remaining shortfalls: {zero_shortfall_workers} / {len(result)}")

    ARTIFACT_DIR.mkdir(exist_ok=True)
    result.to_csv(ARTIFACT_DIR / "buffer_simulation.csv", index=False)
    print(f"\nSaved {ARTIFACT_DIR / 'buffer_simulation.csv'}")

    plot_example(example, ARTIFACT_DIR / "buffer_example.png")
    print(f"Saved {ARTIFACT_DIR / 'buffer_example.png'}")

    return result, pct_reduction


def plot_example(example: dict, out_path: Path):
    income, sim, floor = example["income"], example["sim"], example["floor"]
    weeks = range(len(income))

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 8), sharex=True,
                                    gridspec_kw={"height_ratios": [2, 1]})

    ax1.plot(weeks, sim["actual"], color="#999999", label="Actual (raw) income", linewidth=1.2)
    ax1.plot(weeks, sim["smoothed_income"], color="#1f9d55", label="Smoothed (post-buffer) income", linewidth=1.6)
    ax1.axhline(floor, color="#c0392b", linestyle="--", linewidth=1.2, label="Essential expense floor")
    ax1.set_title(f"Worker {example['worker_id']} — Raw vs Buffer-Smoothed Income")
    ax1.set_ylabel("Net earnings (INR)")
    ax1.legend(loc="upper right", fontsize=9)
    ax1.grid(alpha=0.25)

    ax2.fill_between(weeks, sim["buffer_balance"], color="#5b8def", alpha=0.4)
    ax2.plot(weeks, sim["buffer_balance"], color="#5b8def", linewidth=1.2)
    ax2.set_ylabel("Buffer balance (INR)")
    ax2.set_xlabel("Week")
    ax2.grid(alpha=0.25)

    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    run()
