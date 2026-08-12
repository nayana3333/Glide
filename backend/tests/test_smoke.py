"""
End-to-end smoke test: register (seeded from a synthetic worker) -> login ->
forecast -> buffer -> alerts -> dashboard. Uses a throwaway SQLite file so it
never touches the real dev database.
"""

import os
import sys
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./test_glide.db"

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture(scope="module")
def auth_headers():
    resp = client.post(
        "/api/auth/register",
        json=dict(
            name="Test Worker",
            phone="9999999999",
            password="testpass123",
            archetype="full_time_driver",
            platform="Ola",
            demo_worker_id=1,
        ),
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _worker_id(headers):
    resp = client.get("/api/earnings/1", headers=headers)
    assert resp.status_code == 200
    return 1


def test_register_and_login(auth_headers):
    # auth_headers fixture performs registration; this confirms login works afterward
    resp = client.post("/api/auth/login", json=dict(phone="9999999999", password="testpass123"))
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_seeded_earnings_present(auth_headers):
    resp = client.get("/api/earnings/1", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) > 50  # seeded from synthetic worker history minus last 8 weeks


def test_forecast(auth_headers):
    resp = client.get("/api/forecast/1", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["model_used"] == "Prophet"
    assert len(body["forecast"]) == 4
    assert body["forecast"][0]["dip_level"] in ("GREEN", "AMBER", "RED")


def test_buffer(auth_headers):
    resp = client.get("/api/buffer/1", headers=auth_headers)
    assert resp.status_code == 200
    assert "balance" in resp.json()


def test_alerts(auth_headers):
    resp = client.get("/api/alerts/1", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_dashboard(auth_headers):
    resp = client.get("/api/dashboard/1", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["worker_id"] == 1
    assert "buffer_balance" in body
