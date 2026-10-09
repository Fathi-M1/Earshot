"""User settings persisted locally (name, alert keywords, auto-expire).

Stored as JSON in %LOCALAPPDATA%/<Brand>/settings.json (text only, no secrets).
"""

from __future__ import annotations

import json
import os
import threading

from . import brand

_lock = threading.Lock()

DEFAULTS = {
    "name": "Fathi",
    "keywords": ["quiz", "deadline", "exam", "midterm"],
    "auto_expire": "24h",
}


def _path() -> str:
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    d = os.path.join(base, brand.display_name())
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "settings.json")


def load() -> dict:
    with _lock:
        try:
            with open(_path(), encoding="utf-8") as f:
                data = json.load(f)
            return {**DEFAULTS, **data}
        except Exception:
            return dict(DEFAULTS)


def save(patch: dict) -> dict:
    with _lock:
        cur = DEFAULTS.copy()
        try:
            with open(_path(), encoding="utf-8") as f:
                cur.update(json.load(f))
        except Exception:
            pass
        if "name" in patch and isinstance(patch["name"], str):
            cur["name"] = patch["name"].strip() or cur["name"]
        if "keywords" in patch:
            kw = patch["keywords"]
            if isinstance(kw, str):
                kw = [k.strip() for k in kw.split(",")]
            cur["keywords"] = [k for k in (kw or []) if k][:20] or DEFAULTS["keywords"]
        if "auto_expire" in patch and patch["auto_expire"] in ("1h", "24h", "7d", "keep"):
            cur["auto_expire"] = patch["auto_expire"]
        with open(_path(), "w", encoding="utf-8") as f:
            json.dump(cur, f)
        return cur


def names() -> list[str]:
    s = load()
    return [s["name"]]


def keywords() -> list[str]:
    return load()["keywords"]
