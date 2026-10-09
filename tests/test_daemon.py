"""P0 daemon smoke tests: both apps build and serve the right surfaces; the phone
WS rejects a bad token; the hub fans out a published track."""

import asyncio
import json

from fastapi.testclient import TestClient

from earshot import daemon


def _apps():
    hub = daemon.Hub()
    dash, phone = daemon.build_apps(hub)
    return hub, dash, phone


def test_dashboard_serves_counter_page_and_health():
    hub, dash, _ = _apps()
    client = TestClient(dash)
    r = client.get("/")
    assert r.status_code == 200
    assert "<html" in r.text.lower()
    h = client.get("/health").json()
    assert h["ok"] is True
    assert h["brand"] == "Earshot"
    assert h["phone_token"] == hub.token


def test_dashboard_live_page_renders():
    _, dash, _ = _apps()
    client = TestClient(dash)
    r = client.get("/live")
    assert r.status_code == 200
    assert "Live log" in r.text
    assert "Go live" in r.text


def test_mode_endpoint_validates_and_defaults_counter():
    hub = daemon.Hub()
    controller = daemon.LiveController(hub)
    dash, _phone = daemon.build_apps(hub, controller)
    client = TestClient(dash)
    bad = client.post("/mode", json={"mode": "banana"})
    assert bad.status_code == 400
    ok = client.post("/mode", json={"mode": "counter"})
    assert ok.status_code == 200
    assert ok.json()["mode"] == "counter"


def test_phone_serves_config_silent_wav_and_art():
    _, _, phone = _apps()
    client = TestClient(phone)
    cfg = client.get("/config").json()
    assert cfg["brand"] == "earshot" and cfg["displayName"] == "Earshot"

    wav = client.get("/silent.wav")
    assert wav.status_code == 200
    assert wav.headers["content-type"] == "audio/wav"
    assert wav.content[:4] == b"RIFF"

    art = client.get("/art/LISTENING.png")
    assert art.status_code == 200
    assert art.headers["content-type"] == "image/png"

    assert client.get("/art/NOPE.png").status_code == 404


def test_phone_pwa_assets():
    _, _, phone = _apps()
    client = TestClient(phone)
    man = client.get("/manifest.webmanifest")
    assert man.status_code == 200
    j = man.json()
    assert j["display"] == "standalone"
    assert j["short_name"] == "Earshot"
    assert client.get("/apple-touch-icon.png").status_code == 200
    assert client.get("/icon-512.png").status_code == 200
    font = client.get("/font/host-grotesk.ttf")
    assert font.status_code == 200


def test_phone_ws_rejects_bad_token_with_reason():
    hub, _, phone = _apps()
    client = TestClient(phone)
    import pytest
    from starlette.websockets import WebSocketDisconnect

    with client.websocket_connect("/ws/phone?t=wrong") as ws:
        msg = json.loads(ws.receive_text())
        assert msg["type"] == "auth" and msg["ok"] is False
        assert "token mismatch" in msg["reason"]
        with pytest.raises(WebSocketDisconnect):
            ws.receive_text()


def test_phone_ws_accepts_good_token():
    hub, _, phone = _apps()
    client = TestClient(phone)
    with client.websocket_connect(f"/ws/phone?t={hub.token}"):
        pass  # handshake accepted, no immediate close


def test_config_exposes_token():
    hub, _, phone = _apps()
    client = TestClient(phone)
    cfg = client.get("/config").json()
    assert cfg["token"] == hub.token


def test_conv_endpoint_sets_and_gets():
    hub = daemon.Hub()
    controller = daemon.LiveController(hub)
    dash, _ = daemon.build_apps(hub, controller)
    client = TestClient(dash)
    r = client.post("/conv", json={"their": "tl", "turn": "me"})
    assert r.json()["their"] == "tl" and r.json()["turn"] == "me"
    g = client.get("/conv").json()
    assert g["their"] == "tl" and g["turn"] == "me" and "muted" in g


def test_qr_and_lan_ip():
    png = daemon.qr_png("http://172.20.10.3:7778/")
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    ip = daemon.lan_ip()
    assert isinstance(ip, str) and ip.count(".") == 3
    assert daemon.phone_url().startswith("http://") and daemon.phone_url().endswith(":7778/")


def test_qr_endpoint_served():
    hub, dash, _ = _apps()
    client = TestClient(dash)
    r = client.get("/qr.png")
    assert r.status_code == 200 and r.headers["content-type"] == "image/png"


def test_appmode_endpoint():
    hub = daemon.Hub()
    controller = daemon.LiveController(hub)
    dash, _ = daemon.build_apps(hub, controller)
    client = TestClient(dash)
    r = client.post("/appmode", json={"app_mode": "captions", "read_lang": "ar", "src_lang": "tl"})
    assert r.json() == {"app_mode": "captions", "read_lang": "ar", "src_lang": "tl"}
    g = client.get("/conv").json()
    assert g["app_mode"] == "captions" and g["src_lang"] == "tl"


def test_question_to_me_detection():
    from earshot.live import _is_question_to_me
    assert _is_question_to_me("Fathi, can you answer the question?")
    assert _is_question_to_me("where are you going?")
    assert not _is_question_to_me("the sky is blue")


def test_mute_noop_when_not_live():
    hub = daemon.Hub()
    controller = daemon.LiveController(hub)
    dash, _ = daemon.build_apps(hub, controller)
    client = TestClient(dash)
    # mode is counter (not live) -> mute is a no-op, stays unmuted
    assert client.post("/mute", json={}).json()["muted"] is False


class _FakeWS:
    def __init__(self):
        self.sent = []
        self.accepted = False

    async def accept(self):
        self.accepted = True

    async def send_text(self, text):
        self.sent.append(json.loads(text))


def test_hub_publish_builds_track_payload():
    hub = daemon.Hub()

    async def go():
        ws = _FakeWS()
        await hub.connect(ws)
        assert ws.accepted
        await hub.publish(title="7", artist="Earshot counter", n=7)
        return ws.sent[-1]

    msg = asyncio.run(go())
    assert msg["type"] == "track"
    assert msg["title"] == "7"
    assert msg["n"] == 7
    assert msg["state"] == "LISTENING"
    assert msg["album"].startswith("Earshot")


def test_hub_connect_replays_latest():
    hub = daemon.Hub()

    async def go():
        first = _FakeWS()
        await hub.connect(first)
        await hub.publish(title="3", n=3)
        late = _FakeWS()
        await hub.connect(late)  # should immediately receive the latest payload
        return late.sent

    sent = asyncio.run(go())
    assert sent and sent[-1]["n"] == 3
