"""Latency-pass invariants: only en/tl/ar, language is always forced (never
detected), and refine is latest-wins (stale lines are dropped)."""

from earshot import config
from earshot.daemon import Hub, LiveController


def test_only_en_tl_ar_no_spanish():
    assert config.ASR_LANGS == ["en", "tl", "ar"]
    assert "es" not in config.ASR_LANGS
    assert "es" not in config.LANG_NAMES


def test_language_always_forced_per_mode():
    c = LiveController(Hub())
    # AMBIENT / CAPTIONS: forced to the user-selected spoken language, never detected
    c.set_app_mode("ambient", src_lang="ar")
    assert c._asr_lang_for_mode() == "ar"
    c.set_app_mode("captions", src_lang="tl")
    assert c._asr_lang_for_mode() == "tl"
    # TRANSLATE: forced to their/mine by turn
    c.set_app_mode("translate")
    c.set_conv(their="ar", mine="en", turn="them")
    assert c._asr_lang_for_mode() == "ar"
    c.set_conv(turn="me")
    assert c._asr_lang_for_mode() == "en"


def test_set_app_mode_rejects_unknown_language():
    c = LiveController(Hub())
    c.set_app_mode("ambient", src_lang="en")
    c.set_app_mode("ambient", src_lang="es")  # Spanish gone -> ignored
    assert c.src_lang == "en"


def test_refine_latest_wins_drops_stale():
    c = LiveController(Hub())
    emitted = []
    c._emit = lambda m: emitted.append(m)  # capture
    c._refine_gen = 5                       # newest committed line is id 5
    # a stale refine (id 3) must bail before emitting any caption_update
    c._refine(samples=None, lang="en", original_fast="hi", cid=3, ctx={"announcements": False})
    assert not any(m.get("type") == "caption_update" for m in emitted)
