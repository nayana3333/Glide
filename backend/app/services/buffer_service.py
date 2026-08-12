"""
Buffer ledger built from two independent components summed at read time:

  1. Auto schedule — fully deterministic, recomputed from the worker's whole
     earnings history via ml.models.buffer_engine.simulate_buffer(). Each new
     week is materialized once as an auto_save/auto_release row; existing
     rows are never rewritten.
  2. Manual adjustments — deposit/withdraw rows the worker confirms directly
     (per the blueprint: "all recommendations are advisory, worker confirms
     every transaction").

current_balance = latest auto row's balance_after + net of all manual rows.

Known simplification: the automatic schedule itself doesn't yet react to
manual deposits/withdrawals (e.g. a manual withdrawal doesn't reduce what
the engine is willing to auto-save next week). Documented here rather than
silently shipped; a natural extension for a production version.
"""

import sys

import pandas as pd
from sqlalchemy.orm import Session

from app.config import BASE_DIR
from app.models.buffer import BufferTransaction
from app.models.earnings import Earnings

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ml.models.buffer_engine import simulate_buffer  # noqa: E402

AUTO_KINDS = ("auto_save", "auto_release")


def _sync_auto_schedule(db: Session, user_id: int) -> None:
    rows = (
        db.query(Earnings)
        .filter(Earnings.user_id == user_id)
        .order_by(Earnings.week_index)
        .all()
    )
    if not rows:
        return

    dates = pd.to_datetime([r.week_start for r in rows])
    income = pd.Series([r.net_earnings for r in rows], index=dates)
    sim = simulate_buffer(income)

    already_synced = {
        week_start
        for (week_start,) in db.query(BufferTransaction.week_start)
        .filter(BufferTransaction.user_id == user_id, BufferTransaction.kind.in_(AUTO_KINDS))
        .all()
    }

    for date, row in sim.iterrows():
        week_start = date.date().isoformat()
        if week_start in already_synced:
            continue
        if row["save"] > 0:
            kind, amount = "auto_save", float(row["save"])
        elif row["release"] > 0:
            kind, amount = "auto_release", float(row["release"])
        else:
            continue
        db.add(
            BufferTransaction(
                user_id=user_id,
                week_start=week_start,
                kind=kind,
                amount=amount,
                balance_after=float(row["buffer_balance"]),
            )
        )
    db.commit()


def _latest_auto_balance(db: Session, user_id: int) -> float:
    latest = (
        db.query(BufferTransaction)
        .filter(BufferTransaction.user_id == user_id, BufferTransaction.kind.in_(AUTO_KINDS))
        .order_by(BufferTransaction.week_start.desc())
        .first()
    )
    return latest.balance_after if latest else 0.0


def _manual_net(db: Session, user_id: int) -> float:
    deposits = (
        db.query(BufferTransaction)
        .filter(BufferTransaction.user_id == user_id, BufferTransaction.kind == "manual_deposit")
        .all()
    )
    withdrawals = (
        db.query(BufferTransaction)
        .filter(BufferTransaction.user_id == user_id, BufferTransaction.kind == "manual_withdraw")
        .all()
    )
    return sum(t.amount for t in deposits) - sum(t.amount for t in withdrawals)


def get_balance(db: Session, user_id: int) -> float:
    _sync_auto_schedule(db, user_id)
    return _latest_auto_balance(db, user_id) + _manual_net(db, user_id)


def get_state(db: Session, user_id: int):
    balance = get_balance(db, user_id)
    transactions = (
        db.query(BufferTransaction)
        .filter(BufferTransaction.user_id == user_id)
        .order_by(BufferTransaction.week_start.desc())
        .all()
    )
    return balance, transactions


def manual_deposit(db: Session, user_id: int, amount: float) -> BufferTransaction:
    from datetime import date

    balance = get_balance(db, user_id)
    txn = BufferTransaction(
        user_id=user_id,
        week_start=date.today().isoformat(),
        kind="manual_deposit",
        amount=amount,
        balance_after=balance + amount,
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return txn


def manual_withdraw(db: Session, user_id: int, amount: float) -> BufferTransaction:
    from datetime import date

    balance = get_balance(db, user_id)
    if amount > balance:
        raise ValueError(f"Insufficient buffer balance: requested {amount}, available {balance:.2f}")
    txn = BufferTransaction(
        user_id=user_id,
        week_start=date.today().isoformat(),
        kind="manual_withdraw",
        amount=amount,
        balance_after=balance - amount,
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return txn
