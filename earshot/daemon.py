"""Earshot daemon (Phase 0 scope).

Two servers in one process, sharing one broadcast hub:
- dashboard/API on 127.0.0.1:7777  (laptop counter page + /ws)
- phone server  on 0.0.0.0:7778    (web/index.html + artwork + /ws/phone?t=token)

Phase 0 job: push a server-timestamped counter every 2 s to every client so we
can film the Garmin + iPhone lock screen + laptop clock at 60 fps and measure
refresh latency (03 Phase 0, 07). Later phases replace the counter tick with
real caption/track updates via ``Hub.publish``.

On exit the daemon always restores the internet (netcut.restore) so the laptop
is never left cut off (CLAUDE.md non-negotiable).
"""

from __future__ import annotations

import asyncio
import contextlib
import io
import json
import secrets
import time
import wave
from dataclasses import dataclass, field
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response

from . import brand, netcut
from .localclient import counters as net_counters

REPO_ROOT = Path(__file__).resolve().parent.parent
WEB_DIR = REPO_ROOT / "web"
TILES_DIR = REPO_ROOT / "design" / "tiles"

DASH_HOST, DASH_PORT = "127.0.0.1", 7777
PHONE_HOST, PHONE_PORT = "0.0.0.0", 7778
TICK_SECONDS = 2.0

def _silent_wav(seconds: float = 1.0, rate: int = 8000) -> bytes:
    """A finite silent mono WAV generated in RAM (no disk). Looped by the phone
    page to keep the iOS Media Session alive so the Garmin keeps mirroring."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"\x00\x00" * int(rate * seconds))
    return buf.getvalue()


_SILENT_WAV = _silent_wav()


STATE_TILE_FILES = {
    "LISTENING": "listening.png",
    "ALERT": "alert.png",
    "CATCH_UP": "catch-up.png",
    "MUTED": "muted.png",
    "OFFLINE": "offline.png",
}


@dataclass
class Hub:
    """Holds the latest track payload and fans it out to all websocket clients."""

    token: str = field(default_factory=lambda: secrets.token_urlsafe(8))
    _clients: set[WebSocket] = field(default_factory=set)
    _latest: dict = field(default_factory=dict)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._clients.add(ws)
        if self._latest:
            with contextlib.suppress(Exception):
                await ws.send_text(json.dumps(self._latest))

    async def disconnect(self, ws: WebSocket) -> None:
        async with self._lock:
            self._clients.discard(ws)

    async def broadcast(self, message: dict) -> None:
        async with self._lock:
            self._latest = message
            clients = list(self._clients)
        dead: list[WebSocket] = []
        text = json.dumps(message)
        for ws in clients:
            try:
                await ws.send_text(text)
            except Exception:
                dead.append(ws)
        if dead:
            async with self._lock:
                for ws in dead:
                    self._clients.discard(ws)

    async def publish(
        self,
        *,
        title: str,
        artist: str = "",
        state: str = "LISTENING",
        n: int | None = None,
    ) -> None:
        album = f"{brand.display_name()} · P0"
        await self.broadcast(
            {
                "type": "track",
                "title": title,
                "artist": artist,
                "album": album,
                "state": state,
                "n": n,
                "ts": int(time.time() * 1000),
            }
        )


def _laptop_page(token: str) -> str:
    """Big-counter page for 127.0.0.1:7777 — filmed next to the Garmin."""
    display = brand.display_name()
    phone_url = f"http://&lt;laptop-ip&gt;:{PHONE_PORT}/?t={token}"
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{display} · P0 latency</title>
<style>
  :root {{ color-scheme: dark; }}
  body {{ margin:0; background:#12241A; color:#DDE3D3;
         font-family: ui-sans-serif, system-ui, sans-serif;
         height:100vh; display:flex; flex-direction:column;
         align-items:center; justify-content:center; gap:12px; }}
  #n {{ font-size: 34vh; font-weight:600; line-height:1; letter-spacing:-0.03em;
        font-variant-numeric: tabular-nums; color:#DDE3D3; }}
  #clock {{ font-family: ui-monospace, monospace; font-size:6vh; color:#A9B89C;
            font-variant-numeric: tabular-nums; }}
  #meta {{ font-family: ui-monospace, monospace; font-size:2.2vh; color:#3D5A40; }}
  .dot {{ display:inline-block; width:1.6vh; height:1.6vh; border-radius:50%;
          background:#7FB3D5; margin-right:8px; vertical-align:middle; }}
</style></head>
<body>
  <div id="clock">--:--:--.---</div>
  <div id="n">—</div>
  <div id="meta"><span class="dot"></span><span id="conn">connecting…</span> · phone: {phone_url}</div>
<script>
  const clk = document.getElementById('clock');
  function tickClock() {{
    const d = new Date();
    const p = (v,n=2)=>String(v).padStart(n,'0');
    clk.textContent = p(d.getHours())+':'+p(d.getMinutes())+':'+p(d.getSeconds())+'.'+p(d.getMilliseconds(),3);
    requestAnimationFrame(tickClock);
  }}
  tickClock();
  let ws;
  function connect() {{
    ws = new WebSocket(`ws://${{location.host}}/ws`);
    ws.onopen = () => document.getElementById('conn').textContent = 'live';
    ws.onclose = () => {{ document.getElementById('conn').textContent = 'reconnecting…'; setTimeout(connect, 500); }};
    ws.onmessage = (e) => {{
      const m = JSON.parse(e.data);
      document.getElementById('n').textContent = (m.n ?? m.title);
    }};
  }}
  connect();
</script>
</body></html>"""


def build_apps(hub: Hub) -> tuple[FastAPI, FastAPI]:
    dash = FastAPI(title=f"{brand.display_name()} daemon")
    phone = FastAPI(title=f"{brand.display_name()} phone")

    @dash.get("/", response_class=HTMLResponse)
    async def dash_root() -> str:
        return _laptop_page(hub.token)

    @dash.get("/health")
    async def health() -> JSONResponse:
        c = net_counters()
        return JSONResponse(
            {
                "ok": True,
                "brand": brand.display_name(),
                "bytes_sent": c.bytes_sent,
                "bytes_recv": c.bytes_recv,
                "phone_token": hub.token,
                "net_cut": False,  # P0: reported live in P3
            }
        )

    @dash.websocket("/ws")
    async def dash_ws(ws: WebSocket) -> None:
        await hub.connect(ws)
        try:
            while True:
                await ws.receive_text()  # dashboard may send button events later
        except WebSocketDisconnect:
            await hub.disconnect(ws)
        except Exception:
            await hub.disconnect(ws)

    @phone.get("/", response_class=HTMLResponse)
    async def phone_root() -> HTMLResponse:
        index = WEB_DIR / "index.html"
        if not index.exists():
            return HTMLResponse("<h1>phone page missing</h1>", status_code=500)
        return HTMLResponse(index.read_text(encoding="utf-8"))

    @phone.get("/config")
    async def phone_config() -> JSONResponse:
        return JSONResponse({"brand": brand.name(), "displayName": brand.display_name()})

    @phone.get("/silent.wav")
    async def phone_silent() -> Response:
        return Response(content=_SILENT_WAV, media_type="audio/wav")

    @phone.get("/art/{state}.png")
    async def phone_art(state: str) -> Response:
        fname = STATE_TILE_FILES.get(state.upper())
        if not fname:
            return Response(status_code=404)
        path = TILES_DIR / fname
        if not path.exists():
            return Response(status_code=404)
        return FileResponse(path, media_type="image/png")

    @phone.websocket("/ws/phone")
    async def phone_ws(ws: WebSocket) -> None:
        token = ws.query_params.get("t")
        if token != hub.token:
            await ws.close(code=4401)
            return
        await hub.connect(ws)
        try:
            while True:
                await ws.receive_text()  # phone sends button events later (P3)
        except WebSocketDisconnect:
            await hub.disconnect(ws)
        except Exception:
            await hub.disconnect(ws)

    return dash, phone


async def _tick_loop(hub: Hub) -> None:
    """Phase 0: broadcast an incrementing counter every TICK_SECONDS."""
    n = 0
    while True:
        await hub.publish(title=str(n), artist=f"{brand.display_name()} counter", n=n)
        n += 1
        await asyncio.sleep(TICK_SECONDS)


async def _serve_async(hub: Hub, *, tick: bool) -> None:
    import uvicorn

    dash, phone = build_apps(hub)
    servers = [
        uvicorn.Server(uvicorn.Config(dash, host=DASH_HOST, port=DASH_PORT, log_level="warning")),
        uvicorn.Server(uvicorn.Config(phone, host=PHONE_HOST, port=PHONE_PORT, log_level="warning")),
    ]
    coros = [s.serve() for s in servers]
    if tick:
        coros.append(_tick_loop(hub))
    await asyncio.gather(*coros)


def serve(*, tick: bool = True) -> None:
    """Run the daemon. Always restores internet on exit."""
    hub = Hub()
    display = brand.display_name()
    print(f"{display} daemon")
    print(f"  dashboard : http://{DASH_HOST}:{DASH_PORT}/")
    print(f"  phone     : http://<laptop-ip>:{PHONE_PORT}/?t={hub.token}")
    print(f"  (phone token: {hub.token})")
    if tick:
        print(f"  P0 counter tick every {TICK_SECONDS:g}s — film the Garmin + iPhone + laptop clock")
    try:
        asyncio.run(_serve_async(hub, tick=tick))
    except KeyboardInterrupt:
        pass
    finally:
        res = netcut.restore()
        if res.ok and res.output:
            print("restored internet (removed firewall block rules)")
