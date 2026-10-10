"""Continuous session log. Text only — transcript lines, alerts, catch-ups. Never audio.

Stored in SQLite next to the recall database. Opening a session in the app reads
this log. A calendar file is written only when the user asks to add deadlines.
"""

from __future__ import annotations

import datetime as _dt
import os
import sqlite3
import threading

from . import brand

_lock = threading.Lock()
_conn: sqlite3.Connection | None = None


def _db_path() -> str:
    override = os.environ.get("EARSHOT_SESSIONS_DB")
    if override:
        parent = os.path.dirname(override)
        if parent:
            os.makedirs(parent, exist_ok=True)
        return override
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    d = os.path.join(base, brand.display_name())
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "sessions.db")


def _db() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(_db_path(), check_same_thread=False)
        _conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS sessions(
              id INTEGER PRIMARY KEY,
              started REAL NOT NULL,
              updated REAL NOT NULL,
              topic TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS events(
              id INTEGER PRIMARY KEY,
              session_id INTEGER NOT NULL,
              ts REAL NOT NULL,
              kind TEXT NOT NULL,
              text TEXT NOT NULL
            );
            """
        )
        _conn.commit()
    return _conn


def reset_connection() -> None:
    """Close the cached connection (tests point EARSHOT_SESSIONS_DB at a temp file)."""
    global _conn
    if _conn is not None:
        _conn.close()
        _conn = None


def _label(started: float, topic: str) -> str:
    dt = _dt.datetime.fromtimestamp(started)
    day = f"{dt.strftime('%a')} {dt.day} {dt.strftime('%b')}"
    return f"{day} · {topic or 'session'}"


def _hhmm(ts: float) -> str:
    return _dt.datetime.fromtimestamp(ts).strftime("%H:%M")


def _current(now: float) -> int:
    db = _db()
    row = db.execute("SELECT id, started FROM sessions ORDER BY id DESC LIMIT 1").fetchone()
    if row and now - row[1] < 12 * 3600:
        return int(row[0])
    topic = ""
    cur = db.execute(
        "INSERT INTO sessions(started, updated, topic) VALUES(?,?,?)", (now, now, topic)
    )
    db.commit()
    return int(cur.lastrowid)


def add_event(kind: str, text: str, ts: float | None = None, topic: str | None = None) -> None:
    text = (text or "").strip()
    if not text or kind not in ("line", "alert", "catchup"):
        return
    now = ts if ts is not None else _dt.datetime.now().timestamp()
    with _lock:
        db = _db()
        sid = _current(now)
        db.execute(
            "INSERT INTO events(session_id, ts, kind, text) VALUES(?,?,?,?)",
            (sid, now, kind, text),
        )
        word = (topic or "").strip()[:24]
        if word:
            db.execute(
                "UPDATE sessions SET topic=CASE WHEN topic='' THEN ? ELSE topic END, updated=? WHERE id=?",
                (word, now, sid),
            )
        else:
            db.execute("UPDATE sessions SET updated=? WHERE id=?", (now, sid))
        db.commit()


def list_saved() -> list[dict]:
    with _lock:
        db = _db()
        rows = db.execute(
            "SELECT id, started, updated, topic FROM sessions ORDER BY started DESC"
        ).fetchall()
        out = []
        for sid, started, updated, topic in rows:
            n = db.execute(
                "SELECT COUNT(*) FROM events WHERE session_id=? AND kind='line'", (sid,)
            ).fetchone()[0]
            if not topic:
                first = db.execute(
                    "SELECT text FROM events WHERE session_id=? AND kind='line' ORDER BY ts LIMIT 1",
                    (sid,),
                ).fetchone()
                topic = (first[0].split()[0][:24] if first else "session")
            out.append({
                "id": sid,
                "label": _label(started, topic),
                "start": _hhmm(started),
                "end": _hhmm(updated),
                "lines": n,
            })
        return out


def get_session(session_id: int) -> dict | None:
    with _lock:
        db = _db()
        row = db.execute(
            "SELECT id, started, updated, topic FROM sessions WHERE id=?", (session_id,)
        ).fetchone()
        if not row:
            return None
        sid, started, updated, topic = row
        events = [
            {"ts": ts, "time": _hhmm(ts), "kind": kind, "text": text}
            for ts, kind, text in db.execute(
                "SELECT ts, kind, text FROM events WHERE session_id=? ORDER BY ts, id", (sid,)
            )
        ]
        return {
            "id": sid,
            "label": _label(started, topic or "session"),
            "start": _hhmm(started),
            "end": _hhmm(updated),
            "lines": sum(1 for e in events if e["kind"] == "line"),
            "events": events,
        }


def wipe() -> None:
    with _lock:
        db = _db()
        db.execute("DELETE FROM events")
        db.execute("DELETE FROM sessions")
        db.commit()
