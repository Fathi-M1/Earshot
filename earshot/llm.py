"""Local LLM calls (Ollama) — JSON-schema-constrained, validated, with fallback.

Every call goes through localclient (loopback only, byte-counted), uses
stream:false, format=<schema>, temperature 0, seed 7, num_thread 2, keep_alive
-1, a timeout, and returns None on any failure so callers fall back gracefully
(CLAUDE.md non-negotiable: never block the audio thread; always have a fallback).
"""

from __future__ import annotations

import json

from . import config, localclient

OLLAMA = "http://127.0.0.1:11434"


def chat_json(model: str, system: str, user: str, schema: dict, timeout: float = 8.0) -> dict | None:
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
        "format": schema,
        "keep_alive": -1,
        "options": {"temperature": 0, "seed": 7, "num_thread": 2},
    }
    try:
        resp = localclient.post_json(f"{OLLAMA}/api/chat", body, timeout=timeout)
        content = resp.json()["message"]["content"]
        parsed = json.loads(content)
    except Exception:
        return None
    if not isinstance(parsed, dict):
        return None
    return parsed


_TRANSLATION_SCHEMA = {
    "type": "object",
    "properties": {"translation": {"type": "string"}},
    "required": ["translation"],
}


def prewarm(model: str, timeout: float = 45.0) -> bool:
    """Load a model into memory (keep_alive -1) so the first real call is fast."""
    body = {"model": model, "prompt": "ok", "stream": False, "keep_alive": -1,
            "options": {"num_predict": 1}}
    try:
        localclient.post_json(f"{OLLAMA}/api/generate", body, timeout=timeout)
        return True
    except Exception:
        return False


def translate(text: str, target_lang: str, model: str = config.LLM_HEAVY, timeout: float = 20.0) -> str | None:
    """Translate *text* into the language named by code ``target_lang``.
    Strict: the model returns only the translation. None on failure."""
    target_name = config.LANG_NAMES.get(target_lang, target_lang)
    system = (
        f"You are a translator. Translate the user's text into {target_name}. "
        f"Output JSON only: {{\"translation\": \"...\"}}. "
        f"Return only the {target_name} translation, no notes, no transliteration, no original."
    )
    out = chat_json(model, system, text, _TRANSLATION_SCHEMA, timeout=timeout)
    if not out:
        return None
    t = str(out.get("translation", "")).strip()
    return t or None
