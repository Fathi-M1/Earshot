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


def test_tagalog_exact_word_fixes():
    from earshot.live import _apply_tl_fixes
    assert _apply_tl_fixes("Ponsusta po") == "Kumusta po"
    assert _apply_tl_fixes("Magandan umaarga") == "Magandang umaga"
    assert _apply_tl_fixes("walang pagbabago") == "walang pagbabago"  # untouched


def test_captions_mode_shows_only_transcript_no_translation():
    c = LiveController(Hub())
    c.set_app_mode("captions", src_lang="ar")
    primary, secondary = c._display_for(
        {"app_mode": "captions", "read_lang": "en", "conv": dict(c.conv)},
        original="مرحبا", watch_en="hello", lang="ar",
    )
    assert primary["text"] == "مرحبا" and primary["lang"] == "ar"  # spoken transcript
    assert secondary == {}  # NO translation line


def test_translate_mode_has_translation_and_speaker():
    c = LiveController(Hub())
    c.set_app_mode("translate")
    c.set_conv(their="ar", mine="en", turn="them")
    primary, secondary = c._display_for(
        {"app_mode": "translate", "read_lang": "en", "conv": dict(c.conv)},
        original="مرحبا", watch_en="hello", lang="ar",
    )
    assert primary["text"] == "hello" and secondary["text"] == "مرحبا"


class _FakeMic:
    is_open = True
    def snapshot(self, s):
        import numpy as np
        return np.zeros(int(s * 16000), dtype="float32")
    def close(self):
        self.is_open = False


def test_mute_stops_captions():
    c = LiveController(Hub())
    emitted = []
    c._emit = lambda m: emitted.append(m)
    c.mode = "live"; c._mic = _FakeMic(); c._thread = None; c.muted = False
    c.mute(True)
    assert c.muted is True and c.state == "MUTED"
    # a commit attempt while muted must emit ZERO captions
    caps_before = sum(1 for m in emitted if m.get("type") in ("caption", "caption_update"))
    c._mic = _FakeMic()  # pretend audio is flowing again
    c._commit(2.0, 0.0, "en")
    caps_after = sum(1 for m in emitted if m.get("type") in ("caption", "caption_update"))
    assert caps_after == caps_before  # nothing new while muted


def test_refine_latest_wins_drops_stale():
    c = LiveController(Hub())
    emitted = []
    c._emit = lambda m: emitted.append(m)  # capture
    c._refine_gen = 5                       # newest committed line is id 5
    # a stale refine (id 3) must bail before emitting any caption_update
    c._refine(samples=None, lang="en", original_fast="hi", cid=3, ctx={"announcements": False})
    assert not any(m.get("type") == "caption_update" for m in emitted)
