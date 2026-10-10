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
import os
import secrets
import time
import wave
from dataclasses import dataclass, field
from pathlib import Path

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from starlette.concurrency import run_in_threadpool

from . import brand, config, netcut
from .live import LiveController
from .localclient import counters as net_counters

REPO_ROOT = Path(__file__).resolve().parent.parent
WEB_DIR = REPO_ROOT / "web"
TILES_DIR = REPO_ROOT / "design" / "tiles"

DASH_HOST, DASH_PORT = "127.0.0.1", 7777
PHONE_HOST, PHONE_PORT = "0.0.0.0", 7778
TICK_SECONDS = 2.0

def lan_ip() -> str:
    """Best-guess LAN IP for the phone URL: prefer the iPhone hotspot subnet."""
    import socket

    candidates: list[str] = []
    try:
        import psutil

        for addrs in psutil.net_if_addrs().values():
            for a in addrs:
                if a.family == socket.AF_INET and not a.address.startswith("127."):
                    candidates.append(a.address)
    except Exception:
        pass
    for ip in candidates:
        if ip.startswith("172.20.10."):  # iPhone Personal Hotspot
            return ip
    for ip in candidates:
        if ip.startswith(("192.168.", "10.", "172.")):
            return ip
    # fallback: primary outbound interface (no packet actually sent)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def phone_url() -> str:
    return f"http://{lan_ip()}:{PHONE_PORT}/"


def qr_png(data: str, scale: int = 6) -> bytes:
    import segno

    buf = io.BytesIO()
    segno.make(data, error="m").save(buf, kind="png", scale=scale, border=2,
                                     dark="#12241A", light="#EEF1E8")
    return buf.getvalue()


def qr_terminal(data: str) -> str:
    import segno

    buf = io.StringIO()
    segno.make(data, error="m").terminal(out=buf, border=2)
    return buf.getvalue()


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
    latest_proof: dict = field(default_factory=dict)
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


def _live_page(token: str, dev: bool = True) -> str:
    """Laptop dashboard. At / it's the main app (dev widgets hidden); at /live the
    developer view (counter, timings, now-playing) is shown."""
    display = brand.display_name()
    devcss = "inline-flex" if dev else "none"
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{display}{' · dev' if dev else ''}</title>
<style>
  :root{{ color-scheme:dark; --fd:#12241A; --f:#1F3A24; --moss:#3D5A40; --sage:#A9B89C;
         --beige:#DDE3D3; --paper:#EEF1E8; --needs:#C9A45C; --fern:#8FA876; --glow:#7FB3D5; }}
  .devonly{{ display:{devcss} !important; }}
  footer{{ padding:18px 20px 32px; color:var(--sage); font:400 13px/1 ui-monospace,monospace; border-top:1px solid rgba(169,184,156,.2); margin-top:24px; }}
  footer a{{ color:var(--sage); margin-right:16px; text-decoration:none; }}
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
  .row.pending .orig{{ opacity:.55; }}
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
    <img src="/icon-192.png" alt="" style="width:26px;height:26px;border-radius:8px">
    <h1>{display}{' · dev' if dev else ''}</h1>
    <span class="pill" id="statePill">—</span>
    <span class="pill" id="connPill">connecting…</span>
    <span class="pill devonly" id="timingPill" title="partial / commit / translate latency">—</span>
    <div class="spacer"></div>
    <button class="devonly" id="counterBtn">Counter (film)</button>
    <button class="devonly" id="liveBtn">Go live (mic)</button>
  </header>
  <div class="wrap">
    <div class="card">
      <h2>Live log — every caption, detected language, event</h2>
      <div id="partial" class="prev" style="min-height:1.4em; color:var(--sage); font-style:italic; margin-bottom:8px"></div>
      <div id="log"></div>
    </div>
    <div>
      <div class="card" style="display:flex;gap:16px;align-items:center">
        <img src="/qr.png" alt="phone QR" style="width:120px;height:120px;border-radius:12px;background:var(--paper)">
        <div><h2>Pair your phone</h2>
          <div class="kv"><span class="k">Scan with iPhone camera, open in Safari, tap Start.</span></div>
          <div class="kv"><span class="k" id="phoneUrl">—</span></div>
        </div>
      </div>
      <div class="card" style="margin-top:16px">
        <h2>Recall — search today's transcript</h2>
        <div style="display:flex;gap:8px">
          <input id="recallQ" placeholder="what did they say about the deadline?"
            style="flex:1;height:36px;border-radius:8px;border:1px solid rgba(169,184,156,.4);background:var(--fd);color:var(--beige);padding:0 10px;font-size:14px">
          <button class="cv" id="recallBtn" style="height:36px">Search</button>
        </div>
        <div id="recallOut" style="margin-top:10px"></div>
      </div>
      <div class="card devonly" style="margin-top:16px">
        <h2>Now playing (sent to watch / lock screen)</h2>
        <div class="np"><div class="big" id="npTitle">—</div><div class="sub" id="npArtist"></div></div>
      </div>
      <div class="card" style="margin-top:16px">
        <h2>Mode</h2>
        <div id="modeChips" style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px">
          <button class="cv" data-mode="ambient">Listen for me</button><button class="cv" data-mode="captions">Captions</button>
          <button class="cv" data-mode="translate">Translate</button>
        </div>
        <div id="readWrap">
        <div style="font:400 11px/1 ui-monospace,monospace;color:var(--sage);text-transform:uppercase;margin-bottom:6px">Spoken</div>
        <div id="srcChips" style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px">
          <button class="cv" data-src="en">English</button><button class="cv" data-src="tl">Tagalog</button>
          <button class="cv" data-src="ar">Arabic</button>
        </div>
        <div style="font:400 11px/1 ui-monospace,monospace;color:var(--sage);text-transform:uppercase;margin-bottom:6px">I read</div>
        <div id="readChips" style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px">
          <button class="cv" data-read="en">English</button><button class="cv" data-read="tl">Tagalog</button>
          <button class="cv" data-read="ar">Arabic</button>
        </div></div>
      </div>
      <div class="card" style="margin-top:16px" id="insightCard">
        <h2>Insight cards <button class="cv" id="insightBtn" style="float:right;height:28px">Insight now</button></h2>
        <div id="insights" style="display:flex;flex-direction:column;gap:10px;max-height:40vh;overflow:auto"></div>
      </div>
      <div class="card" style="margin-top:16px">
        <h2>Sessions <button class="cv" id="endBtn" style="float:right;height:28px">End session</button></h2>
        <div id="sessions" style="display:flex;flex-direction:column;gap:6px"></div>
      </div>
      <div class="card" style="margin-top:16px" id="convCard">
        <h2>Conversation (Translate)</h2>
        <div style="font:400 11px/1 ui-monospace,monospace;color:var(--sage);text-transform:uppercase;margin-bottom:6px">They speak</div>
        <div id="theirChips" style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px">
          <button class="cv" data-their="ar">Arabic</button><button class="cv" data-their="tl">Tagalog</button>
          <button class="cv" data-their="en">English</button>
        </div>
        <div style="font:400 11px/1 ui-monospace,monospace;color:var(--sage);text-transform:uppercase;margin-bottom:6px">I speak</div>
        <div id="mineChips" style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px">
          <button class="cv" data-mine="en">English</button><button class="cv" data-mine="tl">Tagalog</button>
          <button class="cv" data-mine="ar">Arabic</button>
        </div>
        <div style="display:flex;gap:8px;margin-bottom:8px">
          <button class="cv turn" data-turn="them" style="flex:1;height:40px">Them</button>
          <button class="cv turn" data-turn="me" style="flex:1;height:40px">Me</button>
        </div>
        <div style="display:flex;gap:8px">
          <button class="cv" id="catchBtn" style="flex:1;height:40px">Catch me up</button>
          <button class="cv" id="muteBtn" style="flex:1;height:40px">Mute</button>
        </div>
        <div id="catchCard" style="display:none;margin-top:10px;padding:10px;border:1px solid rgba(169,184,156,.35);border-radius:10px">
          <div id="catchBody" style="font-size:15px;font-weight:600"></div>
          <div style="display:flex;justify-content:space-between;margin-top:8px">
            <span id="catchSrc" style="color:var(--sage);font-size:12px"></span>
            <button class="cv" id="hearBtn" style="height:32px">Hear it</button>
          </div>
        </div>
      </div>
      <div class="card" style="margin-top:16px">
        <h2>Privacy / status · measured live</h2>
        <div class="kv"><span class="k">engine</span><span id="kMode">—</span></div>
        <div class="kv"><span class="k">bytes to internet</span><span id="kBytes">—</span></div>
        <div class="kv"><span class="k">internet connections</span><span id="kConn">—</span></div>
        <div class="kv"><span class="k">local bytes (Ollama)</span><span id="kLocal">—</span></div>
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
    return div;
  }}
  function capRowHtml(m){{
    const match = (m.alert || (m.matched && m.matched.length)) ? 'match' : '';
    const who = m.speaker ? ('·' + (m.speaker==='me'?'You':'Them')) : '';
    const p = m.primary||{{text:m.original}}, s = m.secondary||{{}};
    const pd = p.rtl? ' dir="rtl"':''; const sd = s.rtl? ' dir="rtl"':'';
    const sec = s.text ? `<div class="eng"${{sd}}>${{s.text}}</div>` : '';
    return {{html:`<div class="t">${{hhmmss(m.ts)}}</div><div class="lang">${{m.lang||'?'}}${{who}}</div>`+
           `<div><div class="orig"${{pd}}>${{esc2(p.text||'')}}</div>${{sec}}`+
           (match?` <div class="eng">⬥ ${{(m.matched||[]).join(', ')}}</div>`:'')+`</div>`, match:match}};
  }}
  function esc2(s){{ return (s||'').replace(/[&<>]/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;'}}[c])); }}
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
      const r = capRowHtml(m);
      const row = addRow(r.html, r.match + (m.pending?' pending':''));
      if (m.id) row.setAttribute('data-id', m.id);
    }} else if (m.type === 'caption_update'){{
      const row = log.querySelector('[data-id="'+m.id+'"]');
      if (row){{ const r = capRowHtml(m); row.innerHTML = r.html; row.className = 'row ' + r.match; }}
    }} else if (m.type === 'timing'){{
      document.getElementById('timingPill').textContent =
        'p'+(m.partial_ms||'–')+' c'+(m.commit_ms||'–')+' t'+(m.translate_ms||'–')+'ms';
    }} else if (m.type === 'conv'){{
      curConv = {{their:m.their, mine:m.mine, turn:m.turn}}; syncConv();
    }} else if (m.type === 'appmode'){{
      curMode = m.app_mode; curRead = m.read_lang; curSrc = m.src_lang || curSrc; syncConv();
    }} else if (m.type === 'catchup'){{
      showCatch(m);
    }} else if (m.type === 'insight'){{
      window._insights = (window._insights||[]); window._insights.push(m); renderInsights();
    }} else if (m.type === 'event'){{
      if (m.kind === 'mute') {{ curMuted = m.detail === 'on'; syncConv(); }}
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

  // conversation + mode controls
  let curConv = {{their:'ar', mine:'en', turn:'them'}}, curMuted=false, curMode='ambient', curRead='en', curSrc='en';
  function post(path, body){{ return fetch(path, {{method:'POST', headers:{{'content-type':'application/json'}}, body:JSON.stringify(body||{{}})}}); }}
  function esc(s){{ return (s||'').replace(/[&<>]/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;'}}[c])); }}
  function syncConv(){{
    document.querySelectorAll('[data-mode]').forEach(b=>b.classList.toggle('on', b.dataset.mode===curMode));
    document.querySelectorAll('[data-read]').forEach(b=>b.classList.toggle('on', b.dataset.read===curRead));
    document.querySelectorAll('[data-src]').forEach(b=>b.classList.toggle('on', b.dataset.src===curSrc));
    document.querySelectorAll('[data-their]').forEach(b=>b.classList.toggle('on', b.dataset.their===curConv.their));
    document.querySelectorAll('[data-mine]').forEach(b=>b.classList.toggle('on', b.dataset.mine===curConv.mine));
    document.querySelectorAll('[data-turn]').forEach(b=>b.classList.toggle('on', b.dataset.turn===curConv.turn));
    const mb=document.getElementById('muteBtn'); mb.classList.toggle('on',curMuted); mb.textContent=curMuted?'Paused — tap to resume':'Mute';
    document.getElementById('convCard').style.display = (curMode==='translate')?'block':'none';
    document.getElementById('readWrap').style.display = (curMode==='translate')?'none':'block';
    document.getElementById('insightCard').style.display = (curMode==='ambient')?'block':'none';
  }}
  function renderInsights(){{
    const el=document.getElementById('insights'); el.innerHTML='';
    (window._insights||[]).slice(-10).reverse().forEach(c=>{{
      const d=document.createElement('div'); d.className='card'; d.style.padding='12px';
      const li=a=>(a&&a.length)?'<ul style="margin:2px 0 8px;padding-left:18px">'+a.map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul>':'<div class="kv"><span class="k">—</span></div>';
      d.innerHTML='<h2>'+esc(c.time||'')+'</h2>'+
        '<div class="kv"><span class="k">topics</span></div>'+li((c.topics||[]).map(esc))+
        '<div class="kv"><span class="k">questions</span></div>'+li((c.questions||[]).map(q=>esc(q.who)+': '+esc(q.what)))+
        '<div class="kv"><span class="k">dates</span></div>'+li((c.dates||[]).map(x=>esc(x.what)+' — '+esc(x.when)))+
        '<div class="kv"><span class="k">tasks</span></div>'+li((c.tasks||[]).map(esc));
      el.appendChild(d);
    }});
  }}
  document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>{{ post('/appmode',{{app_mode:b.dataset.mode}}); curMode=b.dataset.mode; syncConv(); }});
  document.querySelectorAll('[data-read]').forEach(b=>b.onclick=()=>{{ post('/appmode',{{read_lang:b.dataset.read}}); curRead=b.dataset.read; syncConv(); }});
  document.querySelectorAll('[data-src]').forEach(b=>b.onclick=()=>{{ post('/appmode',{{src_lang:b.dataset.src}}); curSrc=b.dataset.src; syncConv(); }});
  document.querySelectorAll('[data-their]').forEach(b=>b.onclick=()=>{{ post('/conv',{{their:b.dataset.their}}); curConv.their=b.dataset.their; syncConv(); }});
  document.querySelectorAll('[data-mine]').forEach(b=>b.onclick=()=>{{ post('/conv',{{mine:b.dataset.mine}}); curConv.mine=b.dataset.mine; syncConv(); }});
  document.querySelectorAll('[data-turn]').forEach(b=>b.onclick=()=>{{ post('/conv',{{turn:b.dataset.turn}}); curConv.turn=b.dataset.turn; syncConv(); }});
  let catchTimer=null;
  function showCatchSkeleton(){{
    const card=document.getElementById('catchCard'); card.style.display='block';
    document.getElementById('catchBody').textContent='…';
    document.getElementById('catchSrc').textContent='';
    clearTimeout(catchTimer);
    catchTimer=setTimeout(()=>{{
      if(document.getElementById('catchBody').textContent==='…')
        showCatch({{line1:'Nothing to catch up on yet.', line2:'', source:'extractive'}});
    }}, 3000);
  }}
  function showCatch(m){{
    clearTimeout(catchTimer);
    document.getElementById('catchCard').style.display='block';
    document.getElementById('catchBody').textContent=(m.line1||'')+(m.line2?(' — '+m.line2):'');
    document.getElementById('catchSrc').textContent=m.source==='llm'?'summary':'quick recap';
  }}
  document.getElementById('catchBtn').onclick=()=>{{ showCatchSkeleton(); post('/catchup'); }};
  document.getElementById('hearBtn').onclick=()=>post('/catchup/say');
  document.getElementById('insightBtn').onclick=()=>post('/insight');
  document.getElementById('muteBtn').onclick=async()=>{{
    const r = await post(curMuted?'/unmute':'/mute');
    try {{ const j = await r.json(); curMuted = !!j.muted; }} catch(_) {{ curMuted = !curMuted; }}
    syncConv();
  }};
  fetch('/conv').then(r=>r.json()).then(c=>{{ curConv={{their:c.their,mine:c.mine,turn:c.turn}}; curMuted=!!c.muted; curMode=c.app_mode||curMode; curRead=c.read_lang||curRead; curSrc=c.src_lang||curSrc; syncConv(); }}).catch(()=>{{}});
  fetch('/insights').then(r=>r.json()).then(j=>{{ window._insights=j.insights||[]; renderInsights(); }}).catch(()=>{{}});

  async function doRecall(){{
    const q = document.getElementById('recallQ').value.trim();
    const out = document.getElementById('recallOut');
    if (!q) return;
    out.innerHTML = '<div class="kv"><span class="k">searching…</span></div>';
    try {{
      const r = await (await fetch('/recall?q='+encodeURIComponent(q))).json();
      let h = '<div style="font-size:15px;font-weight:600;margin-bottom:8px">'+esc(r.answer||'')+'</div>';
      (r.results||[]).forEach(res=>{{
        const t = new Date((res.ts||0)*1000); const hhmm = String(t.getHours()).padStart(2,'0')+':'+String(t.getMinutes()).padStart(2,'0');
        h += '<div class="row" style="cursor:pointer" data-ts="'+(res.ts||0)+'"><div class="t">'+hhmm+'</div><div class="lang">'+(res.score||'')+'</div><div class="orig">'+esc(res.text)+'</div></div>';
      }});
      out.innerHTML = h || '<div class="kv"><span class="k">no results</span></div>';
    }} catch(e) {{ out.innerHTML = '<div class="kv"><span class="k">error</span></div>'; }}
  }}
  document.getElementById('recallBtn').onclick = doRecall;
  document.getElementById('recallQ').addEventListener('keydown', e=>{{ if(e.key==='Enter') doRecall(); }});

  function renderSessions(list){{
    const el=document.getElementById('sessions'); el.innerHTML='';
    (list||[]).forEach(s=>{{
      const row=document.createElement('div'); row.className='kv';
      row.innerHTML='<span class="k">'+esc(s.session)+'</span>'+
        '<a href="/session/ics?session='+encodeURIComponent(s.session)+'" style="color:var(--beige)">Download .ics</a>';
      el.appendChild(row);
    }});
  }}
  async function refreshSessions(){{ try {{ const j=await (await fetch('/sessions')).json(); renderSessions(j.sessions); }} catch(_){{}} }}
  document.getElementById('endBtn').onclick=async()=>{{
    document.getElementById('endBtn').textContent='Saving…';
    try {{ const r=await (await fetch('/session/end',{{method:'POST'}})).json();
      addRow('<div class="t">now</div><div class="lang">·</div><div class="orig">[session saved] '+esc(r.session)+' · '+r.events+' dates</div>','evt'); }} catch(_){{}}
    document.getElementById('endBtn').textContent='End session'; refreshSessions();
  }};
  refreshSessions();

  async function poll(){{
    try {{
      const h = await (await fetch('/health')).json();
      document.getElementById('kMode').textContent = h.mode + ' · ' + (h.app_mode||'');
      document.getElementById('kBytes').textContent = h.bytes_sent;
      document.getElementById('kConn').textContent = h.internet_connections;
      document.getElementById('kLocal').textContent = h.local_bytes_sent;
      document.getElementById('kCut').textContent = h.net_cut ? 'yes' : 'no';
      if (h.phone_url) document.getElementById('phoneUrl').textContent = h.phone_url;
      document.getElementById('liveBtn').classList.toggle('on', h.mode==='live');
      document.getElementById('counterBtn').classList.toggle('on', h.mode==='counter');
    }} catch(_){{}}
    setTimeout(poll, 1500);
  }}
  poll();
</script>
<footer>
  <a href="/about">About</a><a href="/privacy">Privacy</a><a href="/terms">Terms</a>
  <a href="/faq">FAQ</a><a href="/licenses">Licenses</a><a href="/accessibility">Accessibility</a>
  <a href="/live">Developer</a>
  <span style="margin-left:8px">· local-only · 0 bytes to the internet</span>
</footer>
</body></html>"""


def build_apps(hub: Hub, controller: "LiveController | None" = None) -> tuple[FastAPI, FastAPI]:
    dash = FastAPI(title=f"{brand.display_name()} daemon")
    phone = FastAPI(title=f"{brand.display_name()} phone")
    if controller is None:
        controller = LiveController(hub)

    _nocache = {"Cache-Control": "no-cache, no-store, must-revalidate"}

    @dash.get("/", response_class=HTMLResponse)
    async def dash_root() -> HTMLResponse:
        return HTMLResponse(_live_page(hub.token, dev=False), headers=_nocache)

    @dash.get("/live", response_class=HTMLResponse)
    async def dash_live() -> HTMLResponse:
        return HTMLResponse(_live_page(hub.token, dev=True), headers=_nocache)

    @dash.get("/counter", response_class=HTMLResponse)
    async def dash_counter() -> HTMLResponse:
        return HTMLResponse(_laptop_page(hub.token), headers=_nocache)

    @dash.get("/health")
    async def health() -> JSONResponse:
        net_cut = await run_in_threadpool(netcut.is_cut_cached)  # cached; may spawn PowerShell
        pr = hub.latest_proof or {}  # refreshed on a background timer (instant read)
        return JSONResponse(
            {
                "ok": True,
                "brand": brand.display_name(),
                "bytes_sent": pr.get("internet_bytes_sent", 0),   # to the internet (0)
                "local_bytes_sent": pr.get("local_bytes_sent", 0),  # loopback (Ollama)
                "internet_connections": pr.get("internet_connections", 0),
                "phone_token": hub.token,
                "phone_url": phone_url(),
                "mode": controller.mode,
                "app_mode": controller.app_mode,
                "net_cut": net_cut,
            }
        )

    @dash.get("/proof")
    async def proof_endpoint() -> JSONResponse:
        return JSONResponse(hub.latest_proof or {})

    @dash.get("/qr.png")
    async def qr_endpoint() -> Response:
        return Response(content=qr_png(phone_url()), media_type="image/png")

    @dash.get("/qr.svg")
    async def qr_svg_endpoint() -> Response:
        import segno

        buf = io.BytesIO()
        segno.make(phone_url(), error="m").save(buf, kind="svg", scale=5, border=2,
                                                dark=brand.color("forest-deep"), light=brand.color("paper"))
        return Response(content=buf.getvalue(), media_type="image/svg+xml")

    # product pages (About / Privacy / Terms / Accessibility / Licenses / FAQ)
    from . import pages

    def _make_page_route(renderer):
        async def _route() -> HTMLResponse:
            return HTMLResponse(await run_in_threadpool(renderer))
        return _route

    for _slug, _renderer in pages.RENDERERS.items():
        dash.add_api_route(f"/{_slug}", _make_page_route(_renderer),
                           methods=["GET"], response_class=HTMLResponse)
        phone.add_api_route(f"/{_slug}", _make_page_route(_renderer),
                            methods=["GET"], response_class=HTMLResponse)

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
        return JSONResponse({
            **controller.conv, "muted": controller.muted, "state": controller.state,
            "app_mode": controller.app_mode, "read_lang": controller.read_lang,
            "src_lang": controller.src_lang,
        })

    async def _appmode(request: Request) -> JSONResponse:
        body = await request.json()
        return JSONResponse(controller.set_app_mode(
            body.get("app_mode"), body.get("read_lang"), body.get("src_lang")))

    async def _insight() -> JSONResponse:
        return JSONResponse(await run_in_threadpool(controller.make_insight))

    async def _insights() -> JSONResponse:
        return JSONResponse({"insights": controller.insights[-20:]})

    async def _get_settings() -> JSONResponse:
        from . import settings

        return JSONResponse(settings.load())

    async def _post_settings(request: Request) -> JSONResponse:
        from . import settings

        body = await request.json()
        return JSONResponse(settings.save(body))

    async def _recall(request: Request) -> JSONResponse:
        q = request.query_params.get("q", "").strip()
        if not q:
            return JSONResponse({"answer": "", "results": []})
        return JSONResponse(await run_in_threadpool(controller.recall.answer, q))

    async def _session_end() -> JSONResponse:
        return JSONResponse(await run_in_threadpool(controller.end_session))

    async def _wipe() -> JSONResponse:
        return JSONResponse(await run_in_threadpool(controller.wipe))

    async def _sessions() -> JSONResponse:
        from . import notes

        return JSONResponse({"sessions": notes.list_sessions()})

    async def _session_ics(request: Request) -> Response:
        from . import notes

        name = request.query_params.get("session", "")
        for s in notes.list_sessions():
            if s["session"] == name and os.path.exists(s["ics_path"]):
                return FileResponse(s["ics_path"], media_type="text/calendar",
                                    filename=f"{name}.ics")
        return Response(status_code=404)

    async def _catchup() -> JSONResponse:
        return JSONResponse(await run_in_threadpool(controller.catch_up))

    async def _catchup_say() -> JSONResponse:
        return JSONResponse(await run_in_threadpool(controller.say_catchup))

    async def _mute() -> JSONResponse:
        return JSONResponse(await run_in_threadpool(controller.mute, True))

    async def _unmute() -> JSONResponse:
        return JSONResponse(await run_in_threadpool(controller.mute, False))

    for app in (dash, phone):
        app.add_api_route("/conv", _conv, methods=["POST"])
        app.add_api_route("/conv", _get_conv, methods=["GET"])
        app.add_api_route("/appmode", _appmode, methods=["POST"])
        app.add_api_route("/catchup", _catchup, methods=["POST"])
        app.add_api_route("/catchup/say", _catchup_say, methods=["POST"])
        app.add_api_route("/insight", _insight, methods=["POST"])
        app.add_api_route("/insights", _insights, methods=["GET"])
        app.add_api_route("/recall", _recall, methods=["GET"])
        app.add_api_route("/settings", _get_settings, methods=["GET"])
        app.add_api_route("/settings", _post_settings, methods=["POST"])
        app.add_api_route("/session/end", _session_end, methods=["POST"])
        app.add_api_route("/wipe", _wipe, methods=["POST"])
        app.add_api_route("/sessions", _sessions, methods=["GET"])
        app.add_api_route("/session/ics", _session_ics, methods=["GET"])
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


async def _insight_timer(controller: LiveController) -> None:
    """Every 10 min in AMBIENT live mode, auto-create an insight card."""
    while True:
        await asyncio.sleep(600)
        idle = (time.monotonic() - controller._last_speech_end) >= config.IDLE_SECONDS
        # only when idle >10s (never while speaking) — insights must not steal CPU from ASR
        if (controller.mode == "live" and controller.app_mode == "ambient"
                and not controller.muted and not controller._speaking and idle):
            await run_in_threadpool(controller.make_insight)


async def _proof_refresher(hub: Hub) -> None:
    """Refresh the privacy proof (psutil is slow) off the request path."""
    from . import privacy

    while True:
        try:
            hub.latest_proof = await run_in_threadpool(privacy.proof)
        except Exception:
            pass
        await asyncio.sleep(5.0)


async def _rss_logger(hub: Hub) -> None:
    """Log Earshot+Ollama resident memory every 30 s (target < 3 GB total)."""
    from . import privacy

    while True:
        try:
            r = await run_in_threadpool(privacy.rss_mb)
            hub.latest_proof = {**(hub.latest_proof or {}), **r}
            flag = "" if r["total_mb"] < 3000 else "  !! OVER 3GB"
            print(f"[rss] earshot {r['earshot_mb']}MB + ollama {r['ollama_mb']}MB = {r['total_mb']}MB{flag}")
        except Exception:
            pass
        await asyncio.sleep(30.0)


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
    coros.append(_proof_refresher(hub))      # privacy counters off the request path
    coros.append(_insight_timer(controller)) # 10-min ambient insight cards
    coros.append(_rss_logger(hub))           # RAM watch (<3 GB)
    await asyncio.gather(*coros)


def serve(*, tick: bool = True, start_live: bool = False, demo: bool = False) -> None:
    """Run the daemon. Always restores internet + releases the mic on exit."""
    hub = Hub()
    controller = LiveController(hub)
    display = brand.display_name()
    if demo:
        print("=" * 60)
        print(f"  {display} — DEMO MODE (models preloading, live mic)")
        print("=" * 60)
    print(f"{display} daemon")
    print(f"  dashboard : http://{DASH_HOST}:{DASH_PORT}/        (counter page for the latency film)")
    print(f"  live log  : http://{DASH_HOST}:{DASH_PORT}/live    (captions + detected language + events)")
    url = phone_url()
    print(f"  phone     : {url}   (scan the QR below on your iPhone)")
    print(f"  (phone token auto; manual: {url}?t={hub.token})")
    print(f"  mode      : {'live (mic open)' if start_live else 'counter (film) — toggle on /live'}")
    if demo:
        print("  warming models (one dummy inference each)…")
        wt = controller.warmup()
        print(f"  warm: fast {wt.get('fast')}ms · accurate {wt.get('accurate')}ms · llm1.5b {wt.get('llm_1.5b')}ms")
        try:
            from . import privacy
            r = privacy.rss_mb()
            print(f"  RAM : earshot {r['earshot_mb']}MB + ollama {r['ollama_mb']}MB = {r['total_mb']}MB (target <3000)")
        except Exception:
            pass
    try:
        print(qr_terminal(url))
    except Exception:
        pass
    try:
        asyncio.run(_serve_async(hub, controller, tick=tick, start_live=start_live))
    except KeyboardInterrupt:
        pass
    finally:
        controller.shutdown()
        res = netcut.restore()
        if res.ok and res.output:
            print("restored internet (removed firewall block rules)")
