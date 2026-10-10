"""Product pages return 200 with real content (phase 11); audio far-field helpers."""

from fastapi.testclient import TestClient

from earshot import audio, daemon


def _dash():
    hub = daemon.Hub()
    dash, _ = daemon.build_apps(hub, daemon.LiveController(hub))
    return TestClient(dash)


def test_product_pages_200():
    client = _dash()
    for slug in ("about", "privacy", "terms", "accessibility", "licenses", "faq"):
        r = client.get(f"/{slug}")
        assert r.status_code == 200, slug
        assert "Earshot" in r.text


def test_privacy_page_mentions_no_audio():
    client = _dash()
    assert "never" in client.get("/privacy").text.lower()


def test_qr_svg_served():
    client = _dash()
    r = client.get("/qr.svg")
    assert r.status_code == 200 and "svg" in r.headers["content-type"]


def test_agc_off_by_default():
    mic = audio.RingMic()
    assert mic.agc is False


def test_apply_agc_static_boosts_quiet():
    import numpy as np
    quiet = (0.01 * np.sin(np.linspace(0, 100, 16000))).astype(np.float32)
    out = audio.apply_agc_static(quiet)
    assert float(np.sqrt((out ** 2).mean())) > float(np.sqrt((quiet ** 2).mean()))


def test_pick_input_device_returns_tuple():
    idx, name = audio.pick_input_device()
    assert isinstance(name, str)
