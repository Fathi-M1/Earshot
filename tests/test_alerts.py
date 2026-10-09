"""Alerts fire only on name (Levenshtein<=1) + exact keywords, with reasons.
Required: 'agents' doesn't fire; a plain question doesn't fire; 'Fathy, the quiz'
fires with BOTH reasons (Phase 3)."""

from earshot import alerts

NAMES = ["Fathi"]
KW = ["quiz", "deadline", "exam", "midterm"]


def test_name_and_keyword_both_fire():
    hits = alerts.check("Fathy, the quiz is Monday", NAMES, KW)
    reasons = {h.reason for h in hits}
    assert "Heard your name" in reasons
    assert "Keyword: quiz" in reasons


def test_name_fuzzy_variants():
    assert any(h.reason == "Heard your name" for h in alerts.check("hey Fati", NAMES, KW))
    assert any(h.reason == "Heard your name" for h in alerts.check("Fathy!", NAMES, KW))


def test_agents_does_not_fire():
    assert alerts.check("the agents are ready", NAMES, KW) == []


def test_plain_question_does_not_fire():
    assert alerts.check("What are you doing today?", NAMES, KW) == []


def test_keyword_exact_only():
    assert alerts.check("there is a quiz", NAMES, KW)        # exact 'quiz'
    assert alerts.check("quizzical remark", NAMES, KW) == []  # not an exact word


def test_reason_carries_matched_word():
    hits = alerts.check("the deadline is near", NAMES, KW)
    assert hits[0].reason == "Keyword: deadline" and hits[0].word == "deadline"
