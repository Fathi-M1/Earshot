"""Laptop caption bar — the primary surface (02 §10).

Frameless, always-on-top, bottom-centre, draggable. Shows the ORIGINAL-language
caption (previous line muted, current line bold), a state dot, language + mode,
and a live 'bytes sent' counter. Global hotkey Ctrl+Alt+C toggles visibility.

Captions arrive over the daemon WS (ws://127.0.0.1:7777/ws). The websocket runs
in a background thread; the Tk UI is updated via a thread-safe queue.
"""

from __future__ import annotations

import asyncio
import ctypes
import queue
import threading
from pathlib import Path

from . import brand, config

REPO_ROOT = Path(__file__).resolve().parent.parent
FONT_PATH = REPO_ROOT / "design" / "fonts" / "HostGrotesk-VariableFont_wght.ttf"
WS_URL = "ws://127.0.0.1:7777/ws"
HEALTH_URL = "http://127.0.0.1:7777/health"


def _register_font() -> str:
    """Register Host Grotesk for this session; return the family name to use."""
    try:
        FR_PRIVATE = 0x10
        ctypes.windll.gdi32.AddFontResourceExW(str(FONT_PATH), FR_PRIVATE, 0)
        return "Host Grotesk"
    except Exception:
        return "Segoe UI"


def _ws_thread(q: "queue.Queue[dict]", stop: threading.Event) -> None:
    import websockets

    async def run():
        backoff = 0.5
        while not stop.is_set():
            try:
                async with websockets.connect(WS_URL) as ws:
                    backoff = 0.5
                    q.put({"_conn": True})
                    while not stop.is_set():
                        raw = await asyncio.wait_for(ws.recv(), timeout=30)
                        import json

                        q.put(json.loads(raw))
            except Exception:
                q.put({"_conn": False})
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 8.0)

    asyncio.new_event_loop().run_until_complete(run())


class CaptionBar:
    def __init__(self):
        import tkinter as tk

        self.tk = tk
        self.family = _register_font()
        self.c = {k: brand.color(k) for k in ("forest-deep", "forest", "sage", "beige", "needs-you", "listen-glow")}
        self.prev_line = ""
        self.cur_line = ""
        self.partial = ""
        self.lang = ""
        self.state = "LISTENING"
        self.connected = False
        self.visible = True
        self._hotkey_down = False

        self.q: "queue.Queue[dict]" = queue.Queue()
        self.stop = threading.Event()

        root = tk.Tk()
        self.root = root
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        try:
            root.attributes("-alpha", 0.96)
        except Exception:
            pass
        w = min(960, int(root.winfo_screenwidth() * 0.7))
        h = 112
        x = (root.winfo_screenwidth() - w) // 2
        y = root.winfo_screenheight() - h - 60
        root.geometry(f"{w}x{h}+{x}+{y}")
        root.configure(bg=self.c["forest-deep"])

        wrap = tk.Frame(root, bg=self.c["forest-deep"])
        wrap.pack(fill="both", expand=True, padx=18, pady=12)

        self.row1 = tk.Label(wrap, text="", bg=self.c["forest-deep"], fg=self.c["sage"],
                             font=("Consolas", 9), anchor="w")
        self.row1.pack(fill="x")
        self.row2 = tk.Label(wrap, text="", bg=self.c["forest-deep"], fg=self.c["sage"],
                             font=(self.family, 11), anchor="w")
        self.row2.pack(fill="x")
        self.row3 = tk.Label(wrap, text="", bg=self.c["forest-deep"], fg=self.c["beige"],
                             font=(self.family, 18, "bold"), anchor="w", justify="left")
        self.row3.pack(fill="x")

        # drag to move
        for wdg in (root, wrap, self.row1, self.row2, self.row3):
            wdg.bind("<Button-1>", self._start_drag)
            wdg.bind("<B1-Motion>", self._on_drag)
        root.bind("<Escape>", lambda e: self._toggle(False))

    # ---- drag ----
    def _start_drag(self, e):
        self._dx, self._dy = e.x_root - self.root.winfo_x(), e.y_root - self.root.winfo_y()

    def _on_drag(self, e):
        self.root.geometry(f"+{e.x_root - self._dx}+{e.y_root - self._dy}")

    # ---- visibility / hotkey ----
    def _toggle(self, show=None):
        self.visible = (not self.visible) if show is None else show
        if self.visible:
            self.root.deiconify()
        else:
            self.root.withdraw()

    def _poll_hotkey(self):
        # Ctrl+Alt+C global toggle via GetAsyncKeyState (rising edge).
        try:
            gaks = ctypes.windll.user32.GetAsyncKeyState
            down = (gaks(0x11) & 0x8000) and (gaks(0x12) & 0x8000) and (gaks(0x43) & 0x8000)
            if down and not self._hotkey_down:
                self._toggle()
            self._hotkey_down = bool(down)
        except Exception:
            pass
        self.root.after(120, self._poll_hotkey)

    # ---- render ----
    def _dot(self) -> str:
        return {"ALERT": "◆", "MUTED": "‖"}.get(self.state, "◉")

    def _refresh(self):
        self.row1.config(
            text=f"{self._dot()} {self.state} · {(self.lang or '—').upper()} · {('LIVE' if self.connected else '—')}"
        )
        self.row3.config(fg=self.c["needs-you"] if self.state == "ALERT" else self.c["beige"])
        self.row2.config(text=self.prev_line[:80])
        cur = self.cur_line
        if self.partial:
            cur = (self.cur_line + "  " if self.cur_line else "") + "… " + self.partial
        self.row3.config(text=cur[:90])

    def _drain(self):
        try:
            while True:
                m = self.q.get_nowait()
                if "_conn" in m:
                    self.connected = m["_conn"]
                elif m.get("type") == "caption":
                    if m.get("committed"):
                        self.partial = ""
                        if m.get("original"):
                            self.prev_line = self.cur_line
                            self.cur_line = m["original"]
                            self.lang = m.get("lang", self.lang)
                            self.state = "ALERT" if m.get("matched") else "LISTENING"
                    else:
                        self.partial = m.get("original", "")
                        self.lang = m.get("lang", self.lang)
                elif m.get("type") == "track":
                    self.state = m.get("state", self.state)
                elif m.get("type") == "event" and m.get("kind") == "mode":
                    if m.get("detail") == "counter":
                        self.prev_line = self.cur_line = self.partial = ""
        except queue.Empty:
            pass
        self._refresh()
        self.root.after(150, self._drain)

    def run(self):
        t = threading.Thread(target=_ws_thread, args=(self.q, self.stop), daemon=True)
        t.start()
        self.root.after(150, self._drain)
        self.root.after(120, self._poll_hotkey)
        try:
            self.root.mainloop()
        finally:
            self.stop.set()


def run():
    print(f"{brand.display_name()} caption bar — Ctrl+Alt+C toggles, Esc hides, drag to move.")
    CaptionBar().run()
