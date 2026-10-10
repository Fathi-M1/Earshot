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


def _fires(text, kw):
    return any(h.reason == f"Keyword: {kw}" for h in alerts.check(text, NAMES, KW))


def test_smart_keyword_plurals_and_lemmas():
    assert _fires("we have two midterms", "midterm")
    assert _fires("there are three exams", "exam")
    assert _fires("the examination is hard", "exam")
    assert _fires("two deadlines this week", "deadline")
    assert _fires("the project is due", "deadline")       # expansion: due
    assert _fires("surprise quizzes today", "quiz")


def test_smart_keyword_close_spelling():
    assert _fires("the deadlin is tight", "deadline")      # Levenshtein 1, >=5 chars


def test_smart_keyword_no_false_fire():
    assert alerts.check("the agents are ready", NAMES, KW) == []
    assert alerts.check("quizzical look", NAMES, KW) == []
