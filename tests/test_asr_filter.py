"""Hallucination filter (01 §3.3, R-6): drop whisper's silence hallucinations,
collapse repeats, drop very short low-confidence blips, keep real text."""

from earshot.asr import _clean, _collapse_repeats


def test_drops_known_hallucinations():
    assert _clean("Thank you for watching.", 0.0) == ""
    assert _clean("Thanks for watching!", 0.0) == ""
    assert _clean("see you in the next video.", 0.0) == ""
    assert _clean("[BLANK_AUDIO]", 0.0) == ""
    assert _clean("you", 0.0) == ""


def test_collapses_repeats():
    assert _collapse_repeats("the the the quiz") == "the quiz"
    assert _collapse_repeats("see you see you see you") == "see you"
    assert _collapse_repeats("normal sentence here") == "normal sentence here"


def test_drops_short_lowconf_keeps_short_highconf():
    # 1 word + low confidence -> noise blip, dropped
    assert _clean("ok", -2.0) == ""
    # 1 word but confident (e.g. a called name) -> kept
    assert _clean("Fathi", -0.2) == "Fathi"


def test_keeps_real_line():
    assert _clean("the quiz is on Monday", -0.4) == "the quiz is on Monday"
