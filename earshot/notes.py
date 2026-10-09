"""Session notes + .ics (01 §3.8).

On End session: qwen2.5:1.5b produces a summary, key points, tasks, and deadlines
(what + the date *phrase* as said + a supporting quote). Dates are resolved
DETERMINISTICALLY with dateparser (offline); unresolved ones are listed as
"date unclear" and left out of the .ics. Notes (Markdown) and the .ics are
written to %USERPROFILE%/Documents/<Brand>/notes/<date>-<session>.md|.ics.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import os
import re

from . import brand, config, llm

NOTES_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "array", "items": {"type": "string", "maxLength": 160}, "maxItems": 6},
        "key_points": {"type": "array", "items": {"type": "string", "maxLength": 160}, "maxItems": 8},
        "tasks": {"type": "array", "items": {"type": "string", "maxLength": 120}, "maxItems": 10},
        "deadlines": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "what": {"type": "string"}, "when_text": {"type": "string"}, "quote": {"type": "string"},
            },
            "required": ["what", "when_text", "quote"],
        }, "maxItems": 8},
    },
    "required": ["summary", "key_points", "tasks", "deadlines"],
}

_SYSTEM = (
    "Summarize this session transcript. Return JSON with: summary (a few lines), "
    "key_points, tasks (action items), and deadlines (each with what, when_text = the "
    "date phrase exactly as said e.g. 'next Friday' or 'Oct 17', and a short supporting "
    "quote). Use only facts in the transcript. Never invent dates."
)


def _notes_dir() -> str:
    base = os.environ.get("USERPROFILE") or os.path.expanduser("~")
    d = os.path.join(base, "Documents", brand.display_name(), "notes")
    os.makedirs(d, exist_ok=True)
    return d


def _resolve_date(when_text: str, base: _dt.datetime) -> _dt.date | None:
    try:
        import dateparser
    except Exception:
        return None
    settings = {"RELATIVE_BASE": base, "PREFER_DATES_FROM": "future"}
    candidates = [when_text]
    # dateparser doesn't handle "next Friday"/"this Friday"; strip the modifier and
    # let PREFER_DATES_FROM=future pick the coming weekday.
    stripped = re.sub(r"^\s*(next|this|coming|on|by|due)\s+", "", when_text, flags=re.IGNORECASE)
    if stripped != when_text:
        candidates.append(stripped)
    for c in candidates:
        try:
            dt = dateparser.parse(c, settings=settings)
        except Exception:
            dt = None
        if dt:
            return dt.date()
    return None


def _ics(events: list[dict], now: _dt.datetime) -> str:
    """Hand-written RFC 5545 VCALENDAR with all-day VEVENTs."""
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", f"PRODID:-//{brand.display_name()}//EN", "CALSCALE:GREGORIAN"]
    for i, ev in enumerate(events):
        d = ev["date"].strftime("%Y%m%d")
        uid = hashlib.sha1(f"{ev['what']}{d}{i}".encode()).hexdigest()[:16]
        desc = (ev.get("quote", "") or "").replace("\n", " ").replace(",", r"\,").replace(";", r"\;")
        summ = ev["what"].replace("\n", " ").replace(",", r"\,")
        lines += [
            "BEGIN:VEVENT",
            f"UID:{uid}@{brand.name()}",
            f"DTSTAMP:{stamp}",
            f"DTSTART;VALUE=DATE:{d}",
            f"SUMMARY:{summ}",
            f"DESCRIPTION:{desc}",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


def _markdown(notes: dict, deadlines: list[dict], session: str, now: _dt.datetime) -> str:
    out = [f"# {brand.display_name()} session — {session}", "", now.strftime("%Y-%m-%d %H:%M"), ""]
    if notes.get("summary"):
        out += ["## Summary", *[f"- {s}" for s in notes["summary"]], ""]
    if notes.get("key_points"):
        out += ["## Key points", *[f"- {s}" for s in notes["key_points"]], ""]
    if notes.get("tasks"):
        out += ["## Tasks", *[f"- [ ] {s}" for s in notes["tasks"]], ""]
    if deadlines:
        out += ["## Deadlines", "", "| What | When (said) | Resolved | Quote |", "|---|---|---|---|"]
        for d in deadlines:
            resolved = d["date"].isoformat() if d.get("date") else "date unclear"
            out.append(f"| {d['what']} | {d['when_text']} | {resolved} | {d.get('quote','')} |")
        out.append("")
    return "\n".join(out)


def end_session(lines: list[str], session: str | None = None, now: _dt.datetime | None = None) -> dict:
    now = now or _dt.datetime.now()
    session = session or now.strftime("%Y-%m-%d")
    transcript = " ".join(l for l in lines if l)[-6000:]
    notes = llm.chat_json(config.LLM_DEFAULT, _SYSTEM, transcript or "(no speech)", NOTES_SCHEMA, timeout=30) or {
        "summary": [], "key_points": [], "tasks": [], "deadlines": []
    }
    # Resolve deadline dates deterministically.
    deadlines = []
    for d in notes.get("deadlines", []):
        date = _resolve_date(d.get("when_text", ""), now)
        deadlines.append({**d, "date": date})
    events = [{"what": d["what"], "quote": d.get("quote", ""), "date": d["date"]} for d in deadlines if d.get("date")]

    md = _markdown(notes, deadlines, session, now)
    ics = _ics(events, now)
    safe = re.sub(r"[^A-Za-z0-9_-]", "-", session)
    d = _notes_dir()
    md_path = os.path.join(d, f"{safe}.md")
    ics_path = os.path.join(d, f"{safe}.ics")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)
    with open(ics_path, "w", encoding="utf-8", newline="") as f:
        f.write(ics)
    return {
        "session": session, "md_path": md_path, "ics_path": ics_path,
        "events": len(events), "notes": notes,
        "deadlines": [{**d, "date": (d["date"].isoformat() if d.get("date") else None)} for d in deadlines],
        "markdown": md,
    }


def list_sessions() -> list[dict]:
    d = _notes_dir()
    out = []
    for name in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        if name.endswith(".md"):
            out.append({"session": name[:-3], "md_path": os.path.join(d, name),
                        "ics_path": os.path.join(d, name[:-3] + ".ics")})
    return out
