"""Local semantic recall over today's transcript (01 §3.7).

Committed English lines are embedded with nomic-embed-text (via Ollama, through
localclient) and stored in SQLite (TEXT only — no audio, privacy). A query
embeds with the search_query prefix, cosine-ranks the stored lines, returns the
top 3 quotes + timestamps, and a 1-line answer from qwen2.5:1.5b whose quote
must come from a retrieved line.

DB: %LOCALAPPDATA%/<Brand>/earshot.db  (git-ignored location).
"""

from __future__ import annotations

import os
import sqlite3
import struct
import threading
import time

from . import brand, config, llm, localclient

OLLAMA = "http://127.0.0.1:11434"
EMBED_MODEL = "nomic-embed-text"


def _db_path() -> str:
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    d = os.path.join(base, brand.display_name())
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "earshot.db")


def _pack(vec: list[float]) -> bytes:
    return struct.pack(f"{len(vec)}f", *vec)


def _unpack(blob: bytes) -> list[float]:
    return list(struct.unpack(f"{len(blob)//4}f", blob))


def _embed(text: str, prefix: str) -> list[float] | None:
    """nomic-embed-text embedding via Ollama. Tries /api/embed then /api/embeddings."""
    payload = f"{prefix}{text}"
    try:
        r = localclient.post_json(f"{OLLAMA}/api/embed", {"model": EMBED_MODEL, "input": payload}, timeout=15)
        data = r.json()
        if "embeddings" in data and data["embeddings"]:
            return list(data["embeddings"][0])
        if "embedding" in data:
            return list(data["embedding"])
    except Exception:
        pass
    try:
        r = localclient.post_json(f"{OLLAMA}/api/embeddings", {"model": EMBED_MODEL, "prompt": payload}, timeout=15)
        return list(r.json().get("embedding") or []) or None
    except Exception:
        return None


def _cosine(a: list[float], b: list[float]) -> float:
    import math

    if not a or not b or len(a) != len(b):
        return -1.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else -1.0


class Recall:
    def __init__(self, session: str | None = None):
        self.session = session or time.strftime("%Y-%m-%d")
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(_db_path(), check_same_thread=False)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS chunks(id INTEGER PRIMARY KEY, session TEXT, ts REAL, text TEXT, emb BLOB)"
        )
        self._conn.commit()

    def add_line(self, text: str, ts: float | None = None) -> None:
        text = (text or "").strip()
        if not text:
            return
        emb = _embed(text, "search_document: ")
        if emb is None:
            return
        with self._lock:
            self._conn.execute(
                "INSERT INTO chunks(session, ts, text, emb) VALUES(?,?,?,?)",
                (self.session, ts or time.time(), text, _pack(emb)),
            )
            self._conn.commit()

    def search(self, query: str, k: int = 3) -> list[dict]:
        qemb = _embed(query, "search_query: ")
        if qemb is None:
            return []
        with self._lock:
            rows = self._conn.execute(
                "SELECT ts, text, emb FROM chunks WHERE session=?", (self.session,)
            ).fetchall()
        scored = [
            {"ts": ts, "text": text, "score": round(_cosine(qemb, _unpack(emb)), 3)}
            for (ts, text, emb) in rows
        ]
        scored.sort(key=lambda r: r["score"], reverse=True)
        return scored[:k]

    def answer(self, query: str, k: int = 3) -> dict:
        results = self.search(query, k)
        if not results:
            return {"answer": "No transcript yet.", "results": []}
        excerpts = "\n".join(f"[{i}] {r['text']}" for i, r in enumerate(results))
        schema = {
            "type": "object",
            "properties": {
                "found": {"type": "boolean"},
                "answer": {"type": "string", "maxLength": 160},
            },
            "required": ["found", "answer"],
        }
        system = (
            "Answer the question in one short line using ONLY the excerpts. "
            "If the answer isn't in them, found=false and answer='Not found'. Reply JSON only."
        )
        out = llm.chat_json(config.LLM_DEFAULT, system, f"Q: {query}\nExcerpts:\n{excerpts}", schema, timeout=10)
        answer = (out or {}).get("answer", "").strip()
        found = bool((out or {}).get("found"))
        # The retrieval is the ground truth; if the small model whiffs, surface the
        # best-matching quote so the user always gets something useful.
        if not found or not answer or answer.lower().startswith("not found"):
            answer = results[0]["text"]
        return {"answer": answer, "results": results}

    def count(self) -> int:
        with self._lock:
            return self._conn.execute(
                "SELECT COUNT(*) FROM chunks WHERE session=?", (self.session,)
            ).fetchone()[0]

    def close(self) -> None:
        with self._lock:
            self._conn.close()
