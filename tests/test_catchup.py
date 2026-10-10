"""Catch me up (0c): instant extractive card even if the LLM is slow/unavailable,
never auto-voices, 'Hear it' speaks."""

import time

import earshot.live as L
from earshot.daemon import Hub, LiveController


def _controller(monkeypatch):
    c = LiveController(Hub())
    c._loop = None
    emitted = []
    c._emit = lambda m: emitted.append(m)
    return c, emitted


def test_catchup_instant_extractive_when_llm_down(monkeypatch):
    c, emitted = _controller(monkeypatch)
    said = []
    monkeypatch.setattr(L.voice, "speak", lambda t: said.append(t))
    monkeypatch.setattr(L.llm, "chat_json", lambda *a, **k: None)  # LLM unavailable
    for i in range(10):
        c.history.append((time.time(), f"committed line number {i}"))
    res = c.catch_up()
    cards = [m for m in emitted if m.get("type") == "catchup"]
    assert cards and cards[0]["line1"]           # instant card has text
    assert cards[0]["source"] == "extractive"
    assert res["line1"]
    assert said == []                            # NEVER auto-voice


def test_catchup_llm_replaces_card(monkeypatch):
    c, emitted = _controller(monkeypatch)
    monkeypatch.setattr(L.voice, "speak", lambda t: None)
    monkeypatch.setattr(L.llm, "chat_json",
                        lambda *a, **k: {"line1": "Quiz Monday", "line2": "Submit ch.3", "important": True})
    for i in range(10):
        c.history.append((time.time(), f"line {i}"))
    c.catch_up()
    cards = [m for m in emitted if m.get("type") == "catchup"]
    assert any(m["source"] == "extractive" for m in cards)   # instant first
    assert any(m["source"] == "llm" and m["line1"] == "Quiz Monday" for m in cards)  # replaced


def test_extractive_uses_last_alert_and_two_lines(monkeypatch):
    c, _emitted = _controller(monkeypatch)
    monkeypatch.setattr(L.llm, "chat_json", lambda *a, **k: None)
    monkeypatch.setattr(L.voice, "speak", lambda t: (_ for _ in ()).throw(AssertionError("tts")))
    c._last_alert_line = "Fathi, the quiz is Monday"
    c.history.append((time.time(), "chapter three is due"))
    c.history.append((time.time(), "bring the notes"))
    res = c.catch_up()
    assert "quiz" in res["line1"].lower()
    assert "chapter" in res["line2"] and "notes" in res["line2"]


def test_hear_it_speaks(monkeypatch):
    c, emitted = _controller(monkeypatch)
    said = []
    monkeypatch.setattr(L.voice, "speak", lambda t: said.append(t))
    monkeypatch.setattr(L.llm, "chat_json", lambda *a, **k: None)
    c.history.append((time.time(), "the quiz is Monday"))
    c.catch_up()
    assert said == []
    c.say_catchup()
    assert said and "quiz" in said[0].lower()
