"""Session notes: deterministic date resolution + valid .ics (01 §3.8, §10)."""

import datetime as dt

from earshot import notes


def test_resolve_relative_date_future():
    base = dt.datetime(2026, 10, 10, 9, 0)  # a Saturday
    d = notes._resolve_date("next Friday", base)
    assert d is not None and d > base.date()


def test_resolve_unparseable_is_none():
    assert notes._resolve_date("sometime maybe", dt.datetime(2026, 10, 10)) is None


def test_ics_is_valid_and_has_event():
    now = dt.datetime(2026, 10, 10, 9, 0)
    ics = notes._ics([{"what": "Midterm quiz", "quote": "the quiz is Friday", "date": dt.date(2026, 10, 16)}], now)
    assert ics.startswith("BEGIN:VCALENDAR")
    assert "DTSTART;VALUE=DATE:20261016" in ics
    # parse back with icalendar to prove validity
    from icalendar import Calendar

    cal = Calendar.from_ical(ics)
    events = [c for c in cal.walk() if c.name == "VEVENT"]
    assert len(events) == 1
    assert str(events[0]["SUMMARY"]) == "Midterm quiz"


def test_end_session_writes_files(monkeypatch, tmp_path):
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setattr(notes.llm, "chat_json", lambda *a, **k: {
        "summary": ["We discussed the midterm."],
        "key_points": ["Room 304"],
        "tasks": ["Submit chapter 3"],
        "deadlines": [{"what": "Midterm quiz", "when_text": "next Friday", "quote": "quiz next Friday"}],
    })
    res = notes.end_session(["the quiz is next Friday"], session="2026-10-10",
                            now=dt.datetime(2026, 10, 10, 9, 0))
    assert res["events"] == 1
    import os
    assert os.path.exists(res["md_path"]) and os.path.exists(res["ics_path"])
    assert "Midterm quiz" in open(res["md_path"], encoding="utf-8").read()
    assert notes.list_sessions()[0]["session"] == "2026-10-10"
