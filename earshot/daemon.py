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

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from starlette.concurrency import run_in_threadpool

from . import brand, netcut
from .live import LiveController
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


TOKEN_FILE = REPO_ROOT / "phone.token"


def _load_or_create_token() -> str:
    """Stable phone token across daemon restarts, so an installed PWA / open tab
    keeps working. Stored in a git-ignored file."""
    try:
        if TOKEN_FILE.exists():
            existing = TOKEN_FILE.read_text(encoding="utf-8").strip()
            if existing:
                return existing
    except Exception:
        pass
    token = secrets.token_urlsafe(8)
    try:
        TOKEN_FILE.write_text(token, encoding="utf-8")
    except Exception:
        pass
    return token


@dataclass
class Hub:
    """Holds the latest track payload and fans it out to all websocket clients."""

    token: str = field(default_factory=_load_or_create_token)
    _clients: set[WebSocket] = field(default_factory=set)
    _latest: dict = field(default_factory=dict)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def connect(self, ws: WebSocket, accept: bool = True) -> None:
        if accept:
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


def _live_page(token: str) -> str:
    """Dashboard live log (127.0.0.1:7777/live): captions, detected language,
    events, and the counter/live mode toggle. Confirms capture during testing."""
    display = brand.display_name()
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{display} · live</title>
<style>
  :root{{ color-scheme:dark; --fd:#12241A; --f:#1F3A24; --moss:#3D5A40; --sage:#A9B89C;
         --beige:#DDE3D3; --needs:#C9A45C; --fern:#8FA876; --glow:#7FB3D5; }}
  *{{ box-sizing:border-box; }}
  body{{ margin:0; background:var(--fd); color:var(--beige);
        font-family:ui-sans-serif,system-ui,sans-serif; }}
  header{{ display:flex; align-items:center; gap:14px; padding:14px 20px;
          border-bottom:1px solid rgba(169,184,156,.2); }}
  header .mark{{ width:22px; height:22px; border-radius:7px; background:var(--f);
               display:flex; align-items:center; justify-content:center; }}
  header .mark .d{{ width:7px; height:7px; border-radius:50%; background:var(--glow); }}
  h1{{ font-size:17px; font-weight:600; margin:0; }}
  .pill{{ font:400 11px/1 ui-monospace,monospace; letter-spacing:.08em; text-transform:uppercase;
         border:1px solid rgba(169,184,156,.4); border-radius:6px; padding:5px 8px; color:var(--sage); }}
  .pill.live{{ color:var(--fern); border-color:var(--fern); }}
  .pill.alert{{ color:var(--needs); border-color:var(--needs); }}
  .spacer{{ flex:1; }}
  button{{ height:32px; padding:0 14px; border-radius:8px; border:1px solid rgba(169,184,156,.4);
          background:transparent; color:var(--beige); font-size:13px; font-weight:500; cursor:pointer; }}
  button.on{{ background:var(--beige); color:var(--fd); border-color:var(--beige); }}
  .wrap{{ display:grid; grid-template-columns:1fr 340px; gap:20px; padding:20px; max-width:1200px; }}
  .card{{ background:var(--f); border-radius:14px; padding:18px; }}
  .card h2{{ font:400 11px/1 ui-monospace,monospace; letter-spacing:.1em; text-transform:uppercase;
            color:var(--sage); margin:0 0 12px; }}
  #log{{ display:flex; flex-direction:column; gap:8px; max-height:72vh; overflow:auto; }}
  .row{{ display:grid; grid-template-columns:72px 44px 1fr; gap:10px; align-items:baseline;
        padding:8px 0; border-bottom:1px solid rgba(169,184,156,.12); }}
  .t{{ font:400 12px/1.3 ui-monospace,monospace; color:var(--sage); }}
  .lang{{ font:400 11px/1 ui-monospace,monospace; text-transform:uppercase; color:var(--fd);
         background:var(--sage); border-radius:5px; padding:3px 5px; text-align:center; }}
  .orig{{ font-size:15px; font-weight:600; }}
  .eng{{ font-size:13px; color:var(--sage); }}
  .row.match .orig{{ color:var(--needs); }}
  .row.match .lang{{ background:var(--needs); }}
  .evt .orig{{ color:var(--sage); font-weight:400; font-style:normal; }}
  .np .big{{ font-size:22px; font-weight:600; min-height:1.3em; }}
  .np .sub{{ font-size:13px; color:var(--sage); margin-top:4px; }}
  .kv{{ display:flex; justify-content:space-between; font:400 13px/1.8 ui-monospace,monospace; }}
  .kv .k{{ color:var(--sage); }}
  .cv{{ border:1px solid rgba(169,184,156,.4); border-radius:8px; padding:6px 10px; font-size:13px;
        background:transparent; color:var(--beige); cursor:pointer; }}
  .cv.on{{ background:var(--moss); border-color:var(--moss); }}
  .row .eng[dir="rtl"], .orig[dir="rtl"]{{ direction:rtl; text-align:right;
        font-family:"Geeza Pro","Noto Naskh Arabic",system-ui,sans-serif; }}
</style></head>
<body>
  <header>
    <div class="mark"><div class="d"></div></div>
    <h1>{display} · live</h1>
    <span class="pill" id="statePill">—</span>
    <span class="pill" id="connPill">connecting…</span>
    <div class="spacer"></div>
    <button id="counterBtn">Counter (film)</button>
    <button id="liveBtn">Go live (mic)</button>
  </header>
  <div class="wrap">
    <div class="card">
      <h2>Live log — every caption, detected language, event</h2>
      <div id="partial" class="prev" style="min-height:1.4em; color:var(--sage); font-style:italic; margin-bottom:8px"></div>
      <div id="log"></div>
    </div>
    <div>
      <div class="card">
        <h2>Now playing (sent to watch / lock screen)</h2>
        <div class="np"><div class="big" id="npTitle">—</div><div class="sub" id="npArtist"></div></div>
      </div>
      <div class="card" style="margin-top:16px">
        <h2>Conversation</h2>
        <div style="font:400 11px/1 ui-monospace,monospace;color:var(--sage);text-transform:uppercase;margin-bottom:6px">They speak</div>
        <div id="theirChips" style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px">
          <button class="cv" data-their="ar">Arabic</button><button class="cv" data-their="tl">Tagalog</button>
          <button class="cv" data-their="es">Spanish</button><button class="cv" data-their="en">English</button>
        </div>
        <div style="font:400 11px/1 ui-monospace,monospace;color:var(--sage);text-transform:uppercase;margin-bottom:6px">I speak</div>
        <div id="mineChips" style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px">
          <button class="cv" data-mine="en">English</button><button class="cv" data-mine="tl">Tagalog</button>
          <button class="cv" data-mine="es">Spanish</button><button class="cv" data-mine="ar">Arabic</button>
        </div>
        <div style="display:flex;gap:8px;margin-bottom:8px">
          <button class="cv turn" data-turn="them" style="flex:1;height:40px">Them</button>
          <button class="cv turn" data-turn="me" style="flex:1;height:40px">Me</button>
        </div>
        <div style="display:flex;gap:8px">
          <button class="cv" id="catchBtn" style="flex:1;height:40px">Catch me up</button>
          <button class="cv" id="muteBtn" style="flex:1;height:40px">Mute</button>
        </div>
      </div>
      <div class="card" style="margin-top:16px">
        <h2>Privacy / status</h2>
        <div class="kv"><span class="k">mode</span><span id="kMode">—</span></div>
        <div class="kv"><span class="k">bytes to internet</span><span id="kBytes">—</span></div>
        <div class="kv"><span class="k">internet cut</span><span id="kCut">—</span></div>
      </div>
    </div>
  </div>
<script>
  const token = "{token}";
  const log = document.getElementById('log');
  function pad(v,n=2){{ return String(v).padStart(n,'0'); }}
  function hhmmss(ts){{ const d = ts ? new Date(ts) : new Date();
    return pad(d.getHours())+':'+pad(d.getMinutes())+':'+pad(d.getSeconds()); }}
  function addRow(html, cls){{
    const div = document.createElement('div');
    div.className = 'row ' + (cls||'');
    div.innerHTML = html;
    log.prepend(div);
    while (log.childElementCount > 200) log.removeChild(log.lastChild);
  }}
  function setState(state){{
    const p = document.getElementById('statePill');
    p.textContent = state; p.className = 'pill' + (state==='ALERT'?' alert':(state==='LISTENING'?' live':''));
  }}
  function onMsg(m){{
    if (m.type === 'track'){{
      document.getElementById('npTitle').textContent = m.title || '';
      document.getElementById('npArtist').textContent = m.artist || '';
      setState(m.state || '');
      curMuted = (m.state === 'MUTED'); syncConv();
    }} else if (m.type === 'caption'){{
      if (!m.committed){{
        document.getElementById('partial').textContent =
          (m.lang? '['+m.lang+'] ' : '') + '… ' + (m.original||'');
        return;
      }}
      document.getElementById('partial').textContent = '';
      const match = (m.alert || (m.matched && m.matched.length)) ? 'match' : '';
      const who = (m.speaker==='me'?'You':'Them');
      const p = m.primary||{{text:m.original}}, s = m.secondary||{{}};
      const pd = p.rtl? ' dir="rtl"':''; const sd = s.rtl? ' dir="rtl"':'';
      const sec = s.text ? `<div class="eng"${{sd}}>${{s.text}}</div>` : '';
      addRow(`<div class="t">${{hhmmss(m.ts)}}</div><div class="lang">${{m.lang||'?'}}·${{who}}</div>`+
             `<div><div class="orig"${{pd}}>${{p.text||''}}</div>${{sec}}`+
             (match?` <div class="eng">⬥ ${{(m.matched||[]).join(', ')}}</div>`:'')+`</div>`, match);
    }} else if (m.type === 'conv'){{
      curConv = {{their:m.their, mine:m.mine, turn:m.turn}}; syncConv();
    }} else if (m.type === 'event'){{
      addRow(`<div class="t">${{hhmmss(m.ts)}}</div><div class="lang">·</div>`+
             `<div class="orig">[${{m.kind}}] ${{m.detail||''}}</div>`, 'evt');
    }}
  }}
  let ws;
  function connect(){{
    ws = new WebSocket(`ws://${{location.host}}/ws`);
    ws.onopen = () => document.getElementById('connPill').textContent = 'live';
    ws.onclose = () => {{ document.getElementById('connPill').textContent = 'reconnecting…'; setTimeout(connect, 600); }};
    ws.onmessage = (e) => {{ try {{ onMsg(JSON.parse(e.data)); }} catch(_){{}} }};
  }}
  connect();
  async function setMode(mode){{
    await fetch('/mode', {{ method:'POST', headers:{{'content-type':'application/json'}}, body: JSON.stringify({{mode}}) }});
  }}
  document.getElementById('liveBtn').onclick = () => setMode('live');
  document.getElementById('counterBtn').onclick = () => setMode('counter');

  // conversation controls
  let curConv = {{their:'ar', mine:'en', turn:'them'}}, curMuted=false;
  function post(path, body){{ return fetch(path, {{method:'POST', headers:{{'content-type':'application/json'}}, body:JSON.stringify(body||{{}})}}); }}
  function syncConv(){{
    document.querySelectorAll('[data-their]').forEach(b=>b.classList.toggle('on', b.dataset.their===curConv.their));
    document.querySelectorAll('[data-mine]').forEach(b=>b.classList.toggle('on', b.dataset.mine===curConv.mine));
    document.querySelectorAll('[data-turn]').forEach(b=>b.classList.toggle('on', b.dataset.turn===curConv.turn));
    const mb=document.getElementById('muteBtn'); mb.classList.toggle('on',curMuted); mb.textContent=curMuted?'Muted':'Mute';
  }}
  document.querySelectorAll('[data-their]').forEach(b=>b.onclick=()=>{{ post('/conv',{{their:b.dataset.their}}); curConv.their=b.dataset.their; syncConv(); }});
  document.querySelectorAll('[data-mine]').forEach(b=>b.onclick=()=>{{ post('/conv',{{mine:b.dataset.mine}}); curConv.mine=b.dataset.mine; syncConv(); }});
  document.querySelectorAll('[data-turn]').forEach(b=>b.onclick=()=>{{ post('/conv',{{turn:b.dataset.turn}}); curConv.turn=b.dataset.turn; syncConv(); }});
  document.getElementById('catchBtn').onclick=()=>post('/catchup');
  document.getElementById('muteBtn').onclick=()=>post(curMuted?'/unmute':'/mute');
  fetch('/conv').then(r=>r.json()).then(c=>{{ curConv={{their:c.their,mine:c.mine,turn:c.turn}}; curMuted=!!c.muted; syncConv(); }}).catch(()=>{{}});

  async function poll(){{
    try {{
      const h = await (await fetch('/health')).json();
      document.getElementById('kMode').textContent = h.mode;
      document.getElementById('kBytes').textContent = h.bytes_sent;
      document.getElementById('kCut').textContent = h.net_cut ? 'yes' : 'no';
      document.getElementById('liveBtn').classList.toggle('on', h.mode==='live');
      document.getElementById('counterBtn').classList.toggle('on', h.mode==='counter');
    }} catch(_){{}}
    setTimeout(poll, 1500);
  }}
  poll();
</script>
</body></html>"""


def build_apps(hub: Hub, controller: "LiveController | None" = None) -> tuple[FastAPI, FastAPI]:
    dash = FastAPI(title=f"{brand.display_name()} daemon")
    phone = FastAPI(title=f"{brand.display_name()} phone")
    if controller is None:
        controller = LiveController(hub)

    @dash.get("/", response_class=HTMLResponse)
    async def dash_root() -> str:
        return _laptop_page(hub.token)

    @dash.get("/live", response_class=HTMLResponse)
    async def dash_live() -> str:
        return _live_page(hub.token)

    @dash.get("/health")
    async def health() -> JSONResponse:
        c = net_counters()
        net_cut = await run_in_threadpool(netcut.is_cut_cached)  # may spawn PowerShell
        return JSONResponse(
            {
                "ok": True,
                "brand": brand.display_name(),
                "bytes_sent": c.bytes_sent,
                "bytes_recv": c.bytes_recv,
                "phone_token": hub.token,
                "mode": controller.mode,
                "net_cut": net_cut,
            }
        )

    @dash.post("/mode")
    async def set_mode(request: Request) -> JSONResponse:
        body = await request.json()
        mode = body.get("mode", "")
        try:
            # set_mode blocks (mic open/close, thread join, model load) — offload.
            result = await run_in_threadpool(controller.set_mode, mode)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        return JSONResponse(result)

    async def _conv(request: Request) -> JSONResponse:
        body = await request.json()
        return JSONResponse(
            controller.set_conv(body.get("their"), body.get("mine"), body.get("turn"))
        )

    async def _get_conv() -> JSONResponse:
        return JSONResponse({**controller.conv, "muted": controller.muted, "state": controller.state})

    async def _catchup() -> JSONResponse:
        return JSONResponse(await run_in_threadpool(controller.catch_up))

    async def _mute() -> JSONResponse:
        return JSONResponse(await run_in_threadpool(controller.mute, True))

    async def _unmute() -> JSONResponse:
        return JSONResponse(await run_in_threadpool(controller.mute, False))

    for app in (dash, phone):
        app.add_api_route("/conv", _conv, methods=["POST"])
        app.add_api_route("/conv", _get_conv, methods=["GET"])
        app.add_api_route("/catchup", _catchup, methods=["POST"])
        app.add_api_route("/mute", _mute, methods=["POST"])
        app.add_api_route("/unmute", _unmute, methods=["POST"])

    async def _route_button(raw: str) -> None:
        try:
            msg = json.loads(raw)
        except Exception:
            return
        if msg.get("type") != "button":
            return
        action = msg.get("action")
        if action == "catchup":
            await run_in_threadpool(controller.catch_up)
        elif action == "mute":
            await run_in_threadpool(controller.mute, True)
        elif action == "unmute":
            await run_in_threadpool(controller.mute, False)
        # 'bookmark' is a later phase (P3); ignore for now.

    @dash.websocket("/ws")
    async def dash_ws(ws: WebSocket) -> None:
        await hub.connect(ws)
        try:
            while True:
                await _route_button(await ws.receive_text())
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
        # token is returned so the page can always match phone.token, even when a
        # Home-Screen PWA launch drops the ?t= query (start_url=".").
        return JSONResponse(
            {"brand": brand.name(), "displayName": brand.display_name(), "token": hub.token}
        )

    @phone.get("/manifest.webmanifest")
    async def phone_manifest() -> JSONResponse:
        disp = brand.display_name()
        return JSONResponse(
            {
                "name": f"{disp} remote",
                "short_name": disp,
                "display": "standalone",
                "orientation": "portrait",
                "background_color": brand.color("forest-deep"),
                "theme_color": brand.color("forest-deep"),
                "start_url": ".",
                "icons": [
                    {"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
                    {"src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
                ],
            },
            media_type="application/manifest+json",
        )

    def _design_file(name: str, media: str):
        path = REPO_ROOT / "design" / name
        if not path.exists():
            return Response(status_code=404)
        return FileResponse(path, media_type=media)

    @phone.get("/apple-touch-icon.png")
    async def phone_apple_icon() -> Response:
        return _design_file("apple-touch-icon.png", "image/png")

    @phone.get("/icon-192.png")
    async def phone_icon192() -> Response:
        return _design_file("icon-192.png", "image/png")

    @phone.get("/icon-512.png")
    async def phone_icon512() -> Response:
        return _design_file("icon-512.png", "image/png")

    @phone.get("/font/host-grotesk.ttf")
    async def phone_font() -> Response:
        path = REPO_ROOT / "design" / "fonts" / "HostGrotesk-VariableFont_wght.ttf"
        if not path.exists():
            return Response(status_code=404)
        return FileResponse(path, media_type="font/ttf")

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
        # Accept FIRST so we can send a readable error + close reason on a bad
        # token (a pre-accept close only gives the browser a generic 1006).
        await ws.accept()
        token = ws.query_params.get("t")
        if token != hub.token:
            with contextlib.suppress(Exception):
                await ws.send_text(json.dumps({
                    "type": "auth", "ok": False,
                    "reason": "token mismatch — reopen the link",
                    "got": (token or "")[:4], "want": hub.token[:4],
                }))
                await ws.close(code=4401, reason="token mismatch")
            return
        await hub.connect(ws, accept=False)  # already accepted above
        try:
            while True:
                await _route_button(await ws.receive_text())
        except WebSocketDisconnect:
            await hub.disconnect(ws)
        except Exception:
            await hub.disconnect(ws)

    return dash, phone


async def _tick_loop(hub: Hub, controller: LiveController) -> None:
    """Phase 0: broadcast an incrementing counter every TICK_SECONDS — but only
    while in counter mode. In live mode the mic worker drives the surfaces."""
    n = 0
    while True:
        if controller.mode == "counter":
            await hub.publish(title=str(n), artist=f"{brand.display_name()} counter", n=n)
            n += 1
        await asyncio.sleep(TICK_SECONDS)


async def _serve_async(hub: Hub, controller: LiveController, *, tick: bool, start_live: bool) -> None:
    import uvicorn

    dash, phone = build_apps(hub, controller)
    controller.attach_loop(asyncio.get_running_loop())
    if start_live:
        controller.set_mode("live")
    servers = [
        uvicorn.Server(uvicorn.Config(dash, host=DASH_HOST, port=DASH_PORT, log_level="warning")),
        uvicorn.Server(uvicorn.Config(phone, host=PHONE_HOST, port=PHONE_PORT, log_level="warning")),
    ]
    coros = [s.serve() for s in servers]
    if tick:
        coros.append(_tick_loop(hub, controller))
    coros.append(controller.watch_pacer())  # drives the watch in live mode
    await asyncio.gather(*coros)


def serve(*, tick: bool = True, start_live: bool = False) -> None:
    """Run the daemon. Always restores internet + releases the mic on exit."""
    hub = Hub()
    controller = LiveController(hub)
    display = brand.display_name()
    print(f"{display} daemon")
    print(f"  dashboard : http://{DASH_HOST}:{DASH_PORT}/        (counter page for the latency film)")
    print(f"  live log  : http://{DASH_HOST}:{DASH_PORT}/live    (captions + detected language + events)")
    print(f"  phone     : http://<laptop-ip>:{PHONE_PORT}/?t={hub.token}")
    print(f"  (phone token: {hub.token})")
    print(f"  mode      : {'live (mic open)' if start_live else 'counter (film) — toggle on /live'}")
    try:
        asyncio.run(_serve_async(hub, controller, tick=tick, start_live=start_live))
    except KeyboardInterrupt:
        pass
    finally:
        controller.shutdown()
        res = netcut.restore()
        if res.ok and res.output:
            print("restored internet (removed firewall block rules)")
