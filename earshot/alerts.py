"""Alerts that make sense (committed lines only).

Fire ONLY on:
  - the user's name: fuzzy, Levenshtein <= 1 on a single word ("Fathy", "Fati").
  - user-set keywords: EXACT word match (default: quiz, deadline, exam, midterm),
    so unrelated words like "agents" never fire.

No question detection, no LLM judging. Every hit carries a human reason
("Heard your name" / "Keyword: quiz") and the matched word. Per-reason debounce
is handled by the caller.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class AlertHit:
    reason: str   # "Heard your name" or "Keyword: quiz"
    word: str     # the matched word as spoken


def _words(text: str) -> list[str]:
    return [w for w in re.split(r"\s+", text) if w]


def _bare(w: str) -> str:
    return re.sub(r"[^\w]", "", w).lower()


def _lev(a: str, b: str) -> int:
    try:
        import jellyfish
        return jellyfish.levenshtein_distance(a, b)
    except Exception:
        return 0 if a == b else 99


def check(text: str, names: list[str], keywords: list[str]) -> list[AlertHit]:
    hits: list[AlertHit] = []
    seen: set[str] = set()
    names_l = [n.lower() for n in names if n]
    kw_l = {k.lower() for k in keywords if k}
    for w in _words(text):
        bw = _bare(w)
        if not bw:
            continue
        # name: Levenshtein <= 1 against any configured name
        if any(_lev(bw, n) <= 1 for n in names_l) and ("name:" + bw) not in seen:
            seen.add("name:" + bw)
            hits.append(AlertHit("Heard your name", w.strip(".,?!")))
            continue
        # keyword: exact word match only
        if bw in kw_l and ("kw:" + bw) not in seen:
            seen.add("kw:" + bw)
            hits.append(AlertHit(f"Keyword: {bw}", w.strip(".,?!")))
    return hits
