import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import DATA_PATH
from app.database import get_db
from app.models.earnings import Earnings
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services.auth_service import create_access_token, get_current_user, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _seed_demo_earnings(db: Session, user_id: int, demo_worker_id: int) -> None:
    """Copy a synthetic worker's history (minus the last 8 weeks) into a new
    account so the forecast/buffer/dashboard endpoints have real data to show
    immediately after registration, instead of an empty state."""
    if not DATA_PATH.exists():
        return
    df = pd.read_csv(DATA_PATH)
    worker_rows = df[df.worker_id == demo_worker_id].sort_values("week_index")
    if worker_rows.empty:
        return
    worker_rows = worker_rows.iloc[:-8]  # leave a "future" for /forecast to predict

    for _, row in worker_rows.iterrows():
        db.add(
            Earnings(
                user_id=user_id,
                week_start=row["week_start"],
                week_index=int(row["week_index"]),
                platform=row["platform"],
                hours_worked=float(row["hours_worked"]),
                trips_completed=int(row["trips_completed"]),
                gross_earnings=float(row["gross_earnings"]),
                fuel_cost=float(row["fuel_cost"]),
                net_earnings=float(row["net_earnings"]),
            )
        )
    db.commit()


@router.post("/register", response_model=TokenResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.phone == payload.phone).first():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Phone already registered")

    user = User(
        name=payload.name,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        archetype=payload.archetype,
        platform=payload.platform,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    if payload.demo_worker_id is not None:
        _seed_demo_earnings(db, user.id, payload.demo_worker_id)

    return TokenResponse(access_token=create_access_token(user.id))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone == payload.phone).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid phone or password")
    return TokenResponse(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return user
