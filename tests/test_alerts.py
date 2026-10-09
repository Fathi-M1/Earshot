"""Alert keyword matching (01 §3.4): fuzzy + phonetic hits, no false positives."""

from earshot import alerts


def test_exact_and_fuzzy_name():
    assert "Fathi" in alerts.fuzzy_hits("please welcome Fathi to the stage")
    assert "quiz" in alerts.fuzzy_hits("there is a quiz tomorrow")


def test_tagalog_keyword():
    assert "pagsusulit" in alerts.fuzzy_hits("may pagsusulit tayo bukas")


def test_no_false_positive():
    assert alerts.fuzzy_hits("the weather is very nice today") == []


def test_dedupes():
    hits = alerts.fuzzy_hits("quiz quiz quiz deadline")
    assert hits.count("quiz") == 1
