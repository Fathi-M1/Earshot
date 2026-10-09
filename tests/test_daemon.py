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


def test_phone_ws_rejects_bad_token():
    hub, _, phone = _apps()
    client = TestClient(phone)
    import pytest
    from starlette.websockets import WebSocketDisconnect

    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws/phone?t=wrong") as ws:
            ws.receive_text()


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
