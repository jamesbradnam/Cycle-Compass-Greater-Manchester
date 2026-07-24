import sqlite3

import pytest
from fastapi.testclient import TestClient

from src import config
from src.api import app

_chroma_missing = not config.CHROMA_DIR.exists()


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Isolate each test from the real analytics.db - config is a shared
    # module object, so this monkeypatch is visible to analytics.py too.
    monkeypatch.setattr(config, "ANALYTICS_DB_PATH", tmp_path / "analytics.db")
    with TestClient(app) as test_client:
        yield test_client


def test_get_questions_returns_all_seven_in_stage_order(client):
    response = client.get("/api/questions")
    assert response.status_code == 200

    data = response.json()
    ids = [q["id"] for q in data["questions"]]
    assert ids == [
        "borough",
        "persona",
        "purpose",
        "accessibility_relevant",
        "e_bike_focused",
        "budget_band",
        "employment_required",
    ]
    assert "not affiliated" in data["disclaimer"].lower()


def test_post_event_returns_204_and_persists(client):
    response = client.post(
        "/api/events",
        json={
            "session_id": "s1",
            "event_type": "question_viewed",
            "payload": {"question_id": "borough"},
        },
    )
    assert response.status_code == 204

    conn = sqlite3.connect(str(config.ANALYTICS_DB_PATH))
    row = conn.execute("select session_id, event_type from events").fetchone()
    conn.close()
    assert row == ("s1", "question_viewed")


def test_post_event_without_payload_is_allowed(client):
    response = client.post(
        "/api/events", json={"session_id": "s1", "event_type": "continue_clicked"}
    )
    assert response.status_code == 204


def test_post_overview_rejects_unknown_persona(client):
    response = client.post(
        "/api/overview",
        json={
            "persona": "power_cyclist",
            "purpose": ["commuting"],
            "borough": None,
            "accessibility_relevant": True,
        },
    )
    assert response.status_code == 400


def test_post_recommendations_rejects_missing_stage_2_fields(client):
    # Missing e_bike_focused/budget_band/employment_required entirely -
    # FastAPI/Pydantic should reject this at the request-validation layer.
    response = client.post(
        "/api/recommendations",
        json={
            "persona": "fence_sitter",
            "purpose": ["commuting"],
            "borough": "manchester",
            "accessibility_relevant": True,
        },
    )
    assert response.status_code == 422


@pytest.mark.live
@pytest.mark.skipif(_chroma_missing, reason="no vector store found - run `python -m src.ingest` first")
def test_post_overview_endpoint_returns_overview_and_disclaimer(client):
    response = client.post(
        "/api/overview",
        json={
            "persona": "fence_sitter",
            "purpose": ["commuting"],
            "borough": "manchester",
            "accessibility_relevant": False,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["overview"]
    assert "not affiliated" in data["disclaimer"].lower()


@pytest.mark.live
@pytest.mark.skipif(_chroma_missing, reason="no vector store found - run `python -m src.ingest` first")
def test_post_recommendations_endpoint_returns_recommendations_and_disclaimer(client):
    response = client.post(
        "/api/recommendations",
        json={
            "persona": "fence_sitter",
            "purpose": ["commuting"],
            "borough": "manchester",
            "accessibility_relevant": False,
            "e_bike_focused": True,
            "budget_band": "low_cost",
            "employment_required": False,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["recommendations"] or data["note"]
    assert "not affiliated" in data["disclaimer"].lower()
