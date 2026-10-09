"""Live capture controller: switches the daemon between the P0 counter tick and
real multilingual captions from the mic.

In live mode a background thread snapshots the RAM ring buffer every
LIVE_INTERVAL_S, transcribes the recent window (original + detected language +
English translation), and broadcasts:
  - a "track" update  -> Now Playing (watch/lock screen show the ENGLISH title)
  - a "caption" event -> dashboard live log (original, language, English, matched keywords)

The mic is closed the instant we leave live mode (privacy).
"""

from __future__ import annotations

import asyncio
import threading
import time

from . import config
from .asr import Transcriber
from .audio import RingMic


class LiveController:
    def __init__(self, hub):
        self.hub = hub
        self.mode = "counter"  # "counter" | "live"
        self._loop: asyncio.AbstractEventLoop | None = None
        self._mic: RingMic | None = None
        self._transcriber = Transcriber(config.ASR_MODEL)
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    def attach_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    # ---- broadcast helper (thread -> event loop) ----
    def _emit(self, message: dict) -> None:
        if self._loop is None:
            return
        asyncio.run_coroutine_threadsafe(self.hub.broadcast(message), self._loop)

    def _emit_track(self, *, title: str, artist: str, state: str = "LISTENING") -> None:
        if self._loop is None:
            return
        asyncio.run_coroutine_threadsafe(
            self.hub.publish(title=title, artist=artist, state=state), self._loop
        )

    # ---- mode control ----
    def set_mode(self, mode: str) -> dict:
        if mode not in ("counter", "live"):
            raise ValueError("mode must be 'counter' or 'live'")
        if mode == self.mode:
            return {"mode": self.mode, "mic": self._mic.is_open if self._mic else False}
        if mode == "live":
            self._start_live()
        else:
            self._stop_live()
        self.mode = mode
        self._emit({"type": "event", "kind": "mode", "detail": mode, "ts": int(time.time() * 1000)})
        return {"mode": self.mode, "mic": self._mic.is_open if self._mic else False}

    def _start_live(self) -> None:
        self._stop.clear()
        try:
            self._mic = RingMic()
            self._mic.start()
        except Exception as exc:  # no mic / device busy
            self._mic = None
            self._emit({"type": "event", "kind": "mic_error", "detail": str(exc), "ts": int(time.time() * 1000)})
            return
        self._thread = threading.Thread(target=self._worker, name="earshot-live", daemon=True)
        self._thread.start()

    def _stop_live(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        if self._mic is not None:
            self._mic.close()  # privacy: release mic immediately
            self._mic = None

    def _worker(self) -> None:
        # Warm the model (first load is slow) and announce readiness.
        self._emit({"type": "event", "kind": "loading", "detail": config.ASR_MODEL, "ts": int(time.time() * 1000)})
        self._transcriber.load()
        self._emit({"type": "event", "kind": "ready", "detail": config.ASR_MODEL, "ts": int(time.time() * 1000)})
        last_original = ""
        while not self._stop.is_set():
            time.sleep(config.LIVE_INTERVAL_S)
            if self._stop.is_set() or self._mic is None:
                break
            samples = self._mic.snapshot(config.LIVE_WINDOW_S)
            if len(samples) < config.SAMPLE_RATE // 2:  # <0.5 s captured
                continue
            try:
                cap = self._transcriber.caption(samples)
            except Exception as exc:
                self._emit({"type": "event", "kind": "asr_error", "detail": str(exc), "ts": int(time.time() * 1000)})
                continue
            if not cap.original or cap.original == last_original:
                continue
            last_original = cap.original
            matched = [k for k in config.DEMO_KEYWORDS if k in cap.original.lower() or k in cap.english.lower()]
            ts = int(time.time() * 1000)
            # Now Playing: English on the watch/lock screen; original as the sub-line.
            self._emit_track(title=cap.english, artist=cap.original, state="ALERT" if matched else "LISTENING")
            # Dashboard live log row.
            self._emit(
                {
                    "type": "caption",
                    "original": cap.original,
                    "english": cap.english,
                    "lang": cap.language,
                    "matched": matched,
                    "rtf": cap.rtf,
                    "ts": ts,
                }
            )

    def shutdown(self) -> None:
        self._stop_live()
