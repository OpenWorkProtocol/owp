from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


class ClosingConnection(sqlite3.Connection):
    """A sqlite connection whose context manager also closes the file handle."""

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            return super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.close()


def _tighten_file_permissions(db_path: str | Path) -> None:
    """Restrictive local file permissions for the database and SQLite sidecars."""
    path = Path(db_path)
    for candidate in (path, Path(str(path) + "-wal"), Path(str(path) + "-shm")):
        if candidate.exists():
            try:
                os.chmod(candidate, 0o600)
            except OSError:
                pass


def connect(db_path: str | Path) -> sqlite3.Connection:
    db_path = str(db_path)
    conn = sqlite3.connect(
        db_path,
        timeout=10.0,
        isolation_level=None,
        factory=ClosingConnection,
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 10000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    _tighten_file_permissions(db_path)
    return conn


SCHEMA = """
CREATE TABLE IF NOT EXISTS submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    public_id TEXT NOT NULL UNIQUE,
    token_hash TEXT NOT NULL,
    work_kind TEXT NOT NULL CHECK (work_kind IN ('github_pr','idea')),
    source_key TEXT,
    idea_title TEXT NOT NULL DEFAULT '',
    context_url TEXT NOT NULL DEFAULT '',
    pr_url TEXT NOT NULL DEFAULT '',
    repo_owner TEXT NOT NULL,
    repo_name TEXT NOT NULL,
    pr_number INTEGER NOT NULL,
    pr_title TEXT NOT NULL,
    pr_author TEXT NOT NULL,
    head_sha TEXT NOT NULL,
    head_ref TEXT NOT NULL,
    base_ref TEXT NOT NULL,
    additions INTEGER NOT NULL,
    deletions INTEGER NOT NULL,
    changed_files INTEGER NOT NULL,
    commits INTEGER NOT NULL,
    size_band TEXT NOT NULL,
    bid_cents INTEGER NOT NULL CHECK (bid_cents > 0),
    outcome TEXT NOT NULL,
    state TEXT NOT NULL,
    provider_decision TEXT,
    validation_status TEXT,
    attempt_number INTEGER NOT NULL DEFAULT 0,
    terminal INTEGER NOT NULL DEFAULT 0 CHECK (terminal IN (0, 1)),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_active_source_unique
ON submissions(source_key) WHERE terminal = 0 AND source_key IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_submissions_active
ON submissions(terminal, created_at);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    submission_id INTEGER NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,
    seq INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    actor TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    prev_hash TEXT,
    event_hash TEXT NOT NULL,
    UNIQUE(submission_id, seq)
);

CREATE TABLE IF NOT EXISTS questions (
    id TEXT PRIMARY KEY,
    submission_id INTEGER NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    options_json TEXT NOT NULL,
    evidence_json TEXT NOT NULL,
    answer_json TEXT,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    answered_at TEXT
);
"""


def init_db(db_path: str | Path) -> None:
    path = Path(db_path)
    parent_existed = path.parent.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    if not parent_existed:
        try:
            os.chmod(path.parent, 0o700)
        except OSError:
            pass
    with connect(path) as conn:
        conn.executescript(SCHEMA)
    _tighten_file_permissions(path)


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def append_event(
    conn: sqlite3.Connection,
    submission_id: int,
    event_type: str,
    actor: str,
    payload: dict[str, Any],
) -> sqlite3.Row:
    sub = conn.execute(
        "SELECT public_id FROM submissions WHERE id = ?", (submission_id,)
    ).fetchone()
    if not sub:
        raise KeyError(submission_id)

    last = conn.execute(
        "SELECT seq, event_hash FROM events WHERE submission_id = ? ORDER BY seq DESC LIMIT 1",
        (submission_id,),
    ).fetchone()
    seq = 1 if not last else int(last["seq"]) + 1
    prev_hash = None if not last else last["event_hash"]
    created_at = utc_now()
    body = {
        "work_ref": sub["public_id"],
        "seq": seq,
        "event_type": event_type,
        "actor": actor,
        "payload": payload,
        "created_at": created_at,
        "prev_hash": prev_hash,
    }
    event_hash = hashlib.sha256(canonical_json(body).encode("utf-8")).hexdigest()
    conn.execute(
        """INSERT INTO events
        (submission_id, seq, event_type, actor, payload_json, created_at, prev_hash, event_hash)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            submission_id,
            seq,
            event_type,
            actor,
            canonical_json(payload),
            created_at,
            prev_hash,
            event_hash,
        ),
    )
    return conn.execute(
        "SELECT * FROM events WHERE submission_id = ? AND seq = ?",
        (submission_id, seq),
    ).fetchone()


def verify_event_chain(conn: sqlite3.Connection, submission_id: int) -> tuple[bool, str]:
    sub = conn.execute(
        "SELECT public_id FROM submissions WHERE id = ?", (submission_id,)
    ).fetchone()
    if not sub:
        return False, "submission not found"

    prev = None
    rows = conn.execute(
        "SELECT * FROM events WHERE submission_id = ? ORDER BY seq", (submission_id,)
    ).fetchall()
    expected_seq = 1
    for row in rows:
        if row["seq"] != expected_seq:
            return False, f"expected seq {expected_seq}, got {row['seq']}"
        if row["prev_hash"] != prev:
            return False, f"prev_hash mismatch at seq {row['seq']}"
        payload = json.loads(row["payload_json"])
        body = {
            "work_ref": sub["public_id"],
            "seq": row["seq"],
            "event_type": row["event_type"],
            "actor": row["actor"],
            "payload": payload,
            "created_at": row["created_at"],
            "prev_hash": row["prev_hash"],
        }
        digest = hashlib.sha256(canonical_json(body).encode("utf-8")).hexdigest()
        if digest != row["event_hash"]:
            return False, f"event_hash mismatch at seq {row['seq']}"
        prev = row["event_hash"]
        expected_seq += 1
    return True, f"{len(rows)} events verified"
