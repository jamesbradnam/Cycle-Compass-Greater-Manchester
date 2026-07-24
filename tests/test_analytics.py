import json
import sqlite3

from src import analytics


def test_init_db_creates_events_table(tmp_path):
    db_path = tmp_path / "analytics.db"
    analytics.init_db(db_path)

    conn = sqlite3.connect(str(db_path))
    tables = conn.execute(
        "select name from sqlite_master where type='table' and name='events'"
    ).fetchall()
    conn.close()
    assert tables


def test_record_event_persists_session_type_and_payload(tmp_path):
    db_path = tmp_path / "analytics.db"
    analytics.init_db(db_path)

    analytics.record_event(
        "session-123", "question_answered", {"question_id": "persona", "answer": "fence_sitter"}, db_path=db_path
    )

    conn = sqlite3.connect(str(db_path))
    row = conn.execute(
        "select session_id, event_type, payload, created_at from events"
    ).fetchone()
    conn.close()

    session_id, event_type, payload, created_at = row
    assert session_id == "session-123"
    assert event_type == "question_answered"
    assert json.loads(payload) == {"question_id": "persona", "answer": "fence_sitter"}
    assert created_at  # non-empty timestamp


def test_record_event_allows_null_payload(tmp_path):
    db_path = tmp_path / "analytics.db"
    analytics.init_db(db_path)

    analytics.record_event("session-123", "continue_clicked", db_path=db_path)

    conn = sqlite3.connect(str(db_path))
    row = conn.execute("select event_type, payload from events").fetchone()
    conn.close()

    assert row == ("continue_clicked", None)


def test_multiple_events_accumulate(tmp_path):
    db_path = tmp_path / "analytics.db"
    analytics.init_db(db_path)

    analytics.record_event("s1", "question_viewed", {"question_id": "borough"}, db_path=db_path)
    analytics.record_event("s1", "question_answered", {"question_id": "borough", "answer": "manchester"}, db_path=db_path)
    analytics.record_event("s2", "question_viewed", {"question_id": "borough"}, db_path=db_path)

    conn = sqlite3.connect(str(db_path))
    count = conn.execute("select count(*) from events").fetchone()[0]
    conn.close()
    assert count == 3
