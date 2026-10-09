"""Heard-your-name / announcement alerts.

Two stages (01 §3.4):
1. Deterministic, instant: fuzzy keyword match (rapidfuzz partial_ratio) on the
   committed line, plus a phonetic key (jellyfish metaphone) for names whisper
   misspells.
2. Optional LLM intent confirm (qwen2.5:1.5b, 4 s): is this actually addressed to
   the listener / a real announcement? On timeout the keyword hit stands.

Per-keyword cooldown is tracked by the caller.
"""

from __future__ import annotations

from dataclasses import dataclass

from rapidfuzz import fuzz

from . import config, llm


@dataclass
class AlertResult:
    is_alert: bool
    matched: list[str]
    title: str


def _metaphone(word: str) -> str:
    try:
        import jellyfish

        return jellyfish.metaphone(word)
    except Exception:
        return ""


def fuzzy_hits(text: str, keywords: list[str] | None = None, threshold: int | None = None) -> list[str]:
    keywords = keywords if keywords is not None else config.ALERT_KEYWORDS
    threshold = threshold if threshold is not None else config.ALERT_FUZZY_THRESHOLD
    text_l = text.lower()
    tokens = [t.strip(".,?!;:").lower() for t in text.split()]
    token_mph = {t: _metaphone(t) for t in tokens}
    hits: list[str] = []
    for kw in keywords:
        kw_l = kw.lower()
        if kw_l in text_l:
            hits.append(kw)
            continue
        if fuzz.partial_ratio(kw_l, text_l) >= threshold:
            hits.append(kw)
            continue
        kw_mph = _metaphone(kw_l)
        if kw_mph and any(kw_mph == m for m in token_mph.values()):
            hits.append(kw)
    # de-dupe, preserve order
    seen: set[str] = set()
    return [h for h in hits if not (h in seen or seen.add(h))]


_INTENT_SCHEMA = {
    "type": "object",
    "properties": {
        "alert": {"type": "boolean"},
        "type": {"type": "string", "enum": ["name", "quiz", "deadline", "submission", "attendance", "travel", "none"]},
        "title": {"type": "string", "maxLength": 40},
    },
    "required": ["alert", "type", "title"],
}


def intent_confirm(line: str, names: list[str] | None = None) -> tuple[bool, str]:
    """LLM intent check. Returns (is_alert, title). On failure/timeout the caller's
    keyword hit stands (we return True)."""
    names = names or ["Fathi"]
    system = (
        "You check one transcribed sentence from a class or public announcement for "
        "something the listener must act on. Reply JSON only. alert=true only for: the "
        f"listener's name being called ({', '.join(names)}), a quiz/exam/test, a deadline "
        "or due date, a submission, attendance, or a boarding/gate/platform announcement. "
        "title: the key words, max 40 characters, copied from the sentence. Never invent."
    )
    out = llm.chat_json(config.ALERT_LLM_MODEL, system, line, _INTENT_SCHEMA, timeout=config.ALERT_LLM_TIMEOUT)
    if not out:
        return True, line[:40]  # timeout/failure: keyword hit stands
    return bool(out.get("alert", False)), (out.get("title") or line[:40])
