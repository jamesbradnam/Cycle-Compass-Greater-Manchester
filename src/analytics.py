"""Local funnel-analytics event log.

A single flexible events table (rather than one table per event type) since
the event shapes here are small and varied (question_viewed, question_answered,
continue_clicked, recommendation_link_clicked, ...) and a rigid per-type
schema would be over-engineering for this data volume. Report text and
profile answers are never stored anywhere else - this is the one place an
answer value is persisted, and only because quantifying the funnel requires it.
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from . import config


def _connect(db_path: Path | None = None) -> sqlite3.Connection:
    return sqlite3.connect(str(db_path or config.ANALYTICS_DB_PATH))


def init_db(db_path: Path | None = None) -> None:
    with _connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                payload TEXT,
                created_at TEXT NOT NULL
            )
            """
        )


def record_event(
    session_id: str,
    event_type: str,
    payload: dict | None = None,
    db_path: Path | None = None,
) -> None:
    with _connect(db_path) as conn:
        conn.execute(
            "INSERT INTO events (session_id, event_type, payload, created_at) VALUES (?, ?, ?, ?)",
            (
                session_id,
                event_type,
                json.dumps(payload) if payload is not None else None,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
