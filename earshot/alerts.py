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


# Known expansions beyond simple plurals (lemma/synonym), tested.
_EXPANSIONS = {
    "exam": {"examination", "examinations"},
    "deadline": {"due"},
    "quiz": {"quizzes"},
}


def _stem(x: str) -> str:
    if x.endswith("ies") and len(x) > 4:
        return x[:-3] + "y"
    if x.endswith("es") and len(x) > 4:
        return x[:-2]
    if x.endswith("s") and len(x) > 3:
        return x[:-1]
    return x


def _kw_match(word: str, kw: str) -> bool:
    """Match a spoken word to a keyword: exact, plural/lemma, known expansion, or
    Levenshtein <= 1 on words of >= 5 chars (close spellings)."""
    if word == kw:
        return True
    if _stem(word) == _stem(kw):
        return True
    if word in _EXPANSIONS.get(kw, set()):
        return True
    if len(word) >= 5 and len(kw) >= 5 and _lev(word, kw) <= 1:
        return True
    return False


def check(text: str, names: list[str], keywords: list[str]) -> list[AlertHit]:
    hits: list[AlertHit] = []
    seen: set[str] = set()
    names_l = [n.lower() for n in names if n]
    kw_l = [k.lower() for k in keywords if k]
    for w in _words(text):
        bw = _bare(w)
        if not bw:
            continue
        # name: Levenshtein <= 1 against any configured name
        if any(_lev(bw, n) <= 1 for n in names_l) and ("name:" + bw) not in seen:
            seen.add("name:" + bw)
            hits.append(AlertHit("Heard your name", w.strip(".,?!")))
            continue
        # keyword: exact / plural / lemma / close spelling
        for kw in kw_l:
            if _kw_match(bw, kw) and ("kw:" + kw) not in seen:
                seen.add("kw:" + kw)
                hits.append(AlertHit(f"Keyword: {kw}", w.strip(".,?!")))
                break
    return hits
