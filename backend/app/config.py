import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

# SQLite by default so the backend runs with zero setup; point DATABASE_URL
# at a Postgres instance for staging/production (same SQLAlchemy code runs
# against either).
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'backend' / 'glide.db'}")

SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-secret-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24h, fine for a project demo

ML_DIR = BASE_DIR / "ml"
DATA_PATH = ML_DIR / "data" / "earnings.csv"
