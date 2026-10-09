"""Caption segmentation.

- ``chunk_for_watch`` splits a committed line into short rolling chunks (<=28 chars,
  ~6 words) for the lock screen / Garmin title, which only fits a few words.
- ``clip_title`` hard-caps a single title string.
"""

from __future__ import annotations

from . import config


def chunk_for_watch(
    text: str,
    max_chars: int = config.WATCH_CHUNK_MAXCHARS,
    max_words: int = config.WATCH_CHUNK_WORDS,
) -> list[str]:
    """Split text into word-boundary chunks that each fit the watch title."""
    words = text.split()
    chunks: list[str] = []
    cur: list[str] = []
    for w in words:
        trial = " ".join(cur + [w])
        if cur and (len(trial) > max_chars or len(cur) >= max_words):
            chunks.append(" ".join(cur))
            cur = [w]
        else:
            cur.append(w)
        # A single word longer than the cap still goes out on its own.
        if len(cur) == 1 and len(cur[0]) > max_chars:
            chunks.append(cur[0][:max_chars])
            cur = []
    if cur:
        chunks.append(" ".join(cur))
    return chunks or [""]


def clip_title(text: str, max_chars: int = config.WATCH_CHUNK_MAXCHARS) -> str:
    text = text.strip()
    return text if len(text) <= max_chars else text[: max_chars - 1].rstrip() + "…"
