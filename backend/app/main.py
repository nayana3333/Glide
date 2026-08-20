from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401  (registers models on Base before create_all)
from app.config import FRONTEND_URL
from app.database import Base, engine
from app.routers import alerts, auth, buffer, dashboard, earnings, forecast

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Glide API", description="Predictive income smoothing for gig workers")

origins = ["http://localhost:5174", "http://localhost:3000"]
if FRONTEND_URL:
    origins.append(FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(earnings.router)
app.include_router(forecast.router)
app.include_router(buffer.router)
app.include_router(alerts.router)
app.include_router(dashboard.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "glide-api"}
