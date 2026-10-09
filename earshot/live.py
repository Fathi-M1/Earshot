"""Live capture controller.

Switches the daemon between the P0 counter tick and real multilingual captions.

Live pipeline (VAD endpointing):
  - A worker thread watches the RAM ring buffer. While the speaker is talking it
    emits fast *partials* (beam 1) every ~1.5 s for the laptop bar / phone screen.
  - On a speaker *pause* (trailing silence) or the 12 s cap it *commits* the
    utterance with an accurate pass (beam 5), detecting language among en/tl/ar/es,
    and producing the English translation for the watch.
  - Commits feed:
      * a "caption" event (committed=true) -> dashboard log + phone full-screen
      * the watch chunk queue -> a pacer publishes <=28-char rolling "track"
        updates (~1.5 s) for the lock screen / Garmin.
  - A matched keyword raises an alert that overrides the watch title for 8 s.

The mic is closed the instant we leave live mode (privacy).
"""

from __future__ import annotations

import asyncio
import collections
import threading
import time

import numpy as np

from . import captions, config
from .asr import Transcriber, _clean
from .audio import RingMic


class LiveController:
    def __init__(self, hub):
        self.hub = hub
        self.mode = "counter"
        self._loop: asyncio.AbstractEventLoop | None = None
        self._mic: RingMic | None = None
        self._transcriber = Transcriber(config.ASR_MODEL)
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

        # watch pacing state (read by the pacer on the event loop)
        self.watch_queue: collections.deque[str] = collections.deque()
        self.watch_last = ""
        self.watch_prev = ""
        self.alert_until = 0.0
        self.alert_title = ""
        self.state = "LISTENING"

    def attach_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    # ---- broadcast helpers (worker thread -> event loop) ----
    def _emit(self, message: dict) -> None:
        if self._loop is not None:
            asyncio.run_coroutine_threadsafe(self.hub.broadcast(message), self._loop)

    # ---- mode control ----
    def set_mode(self, mode: str) -> dict:
        if mode not in ("counter", "live"):
            raise ValueError("mode must be 'counter' or 'live'")
        if mode == self.mode:
            return {"mode": self.mode, "mic": bool(self._mic and self._mic.is_open)}
        if mode == "live":
            self._start_live()
        else:
            self._stop_live()
        self.mode = mode
        self._emit({"type": "event", "kind": "mode", "detail": mode, "ts": _ms()})
        return {"mode": self.mode, "mic": bool(self._mic and self._mic.is_open)}

    def _start_live(self) -> None:
        self._stop.clear()
        self.watch_queue.clear()
        self.watch_last = "Listening"
        self.watch_prev = ""
        self.alert_until = 0.0
        try:
            self._mic = RingMic()
            self._mic.start()
        except Exception as exc:
            self._mic = None
            self._emit({"type": "event", "kind": "mic_error", "detail": str(exc), "ts": _ms()})
            return
        self._thread = threading.Thread(target=self._worker, name="earshot-live", daemon=True)
        self._thread.start()

    def _stop_live(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=3.0)
            self._thread = None
        if self._mic is not None:
            self._mic.close()
            self._mic = None

    # ---- VAD helpers ----
    def _has_speech(self, samples: np.ndarray) -> bool:
        from faster_whisper.vad import VadOptions, get_speech_timestamps

        if len(samples) < config.SAMPLE_RATE // 8:
            return False
        opts = VadOptions(
            threshold=config.VAD_THRESHOLD,
            min_speech_duration_ms=config.VAD_MIN_SPEECH_MS,
            min_silence_duration_ms=config.VAD_MIN_SILENCE_MS,
        )
        return bool(get_speech_timestamps(samples, opts, sampling_rate=config.SAMPLE_RATE))

    # ---- worker ----
    def _worker(self) -> None:
        self._emit({"type": "event", "kind": "loading", "detail": config.ASR_MODEL, "ts": _ms()})
        self._transcriber.load()
        self._emit({"type": "event", "kind": "ready", "detail": config.ASR_MODEL, "ts": _ms()})

        active = False
        utt_start = 0.0
        last_partial = 0.0
        last_speech = 0.0
        utt_lang: str | None = None
        last_partial_text = ""

        pause_s = config.PAUSE_SILENCE_MS / 1000.0

        while not self._stop.is_set():
            time.sleep(config.LOOP_TICK_S)
            if self._stop.is_set() or self._mic is None:
                break
            try:
                active, utt_start, last_partial, last_speech, utt_lang, last_partial_text = self._tick(
                    active, utt_start, last_partial, last_speech, utt_lang, last_partial_text, pause_s
                )
            except Exception as exc:  # keep the worker alive on a transient error
                self._emit({"type": "event", "kind": "asr_error", "detail": str(exc), "ts": _ms()})

    def _tick(self, active, utt_start, last_partial, last_speech, utt_lang, last_partial_text, pause_s):
            now = time.monotonic()
            tail = self._mic.snapshot(0.8)
            speaking = self._has_speech(tail)

            if speaking:
                last_speech = now
                if not active:
                    active = True
                    utt_start = now
                    last_partial = 0.0
                    utt_lang = None
                    last_partial_text = ""
                # periodic partial
                if now - last_partial >= config.PARTIAL_INTERVAL_S:
                    dur = min(now - utt_start + 0.3, config.MAX_UTTERANCE_S + 1)
                    samples = self._mic.snapshot(dur)
                    if utt_lang is None:
                        utt_lang, _ = self._transcriber.detect(samples)
                    try:
                        raw, conf = self._transcriber._run(
                            samples, "transcribe", utt_lang, config.ASR_BEAM_PARTIAL
                        )
                        txt = _clean(raw, conf)
                    except Exception:
                        txt = ""
                    last_partial = now
                    if txt and txt != last_partial_text:
                        last_partial_text = txt
                        self._emit({
                            "type": "caption", "committed": False, "original": txt,
                            "english": "", "lang": utt_lang or "", "matched": [],
                            "rtf": None, "ts": _ms(),
                        })
                if now - utt_start >= config.MAX_UTTERANCE_S:
                    self._commit(now, utt_start, utt_lang)
                    active = False
            else:
                if active and (now - last_speech) >= pause_s:
                    self._commit(now, utt_start, utt_lang)
                    active = False
            return active, utt_start, last_partial, last_speech, utt_lang, last_partial_text

    def _commit(self, now: float, utt_start: float, utt_lang: str | None) -> None:
        if self._mic is None:
            return
        dur = min(now - utt_start + 0.5, config.MAX_UTTERANCE_S + 1)
        samples = self._mic.snapshot(dur)
        try:
            cap = self._transcriber.caption(
                samples, beam_size=config.ASR_BEAM_COMMIT, language=utt_lang
            )
        except Exception as exc:
            self._emit({"type": "event", "kind": "asr_error", "detail": str(exc), "ts": _ms()})
            return
        if not cap.original:
            return
        matched = [k for k in config.DEMO_KEYWORDS
                   if k in cap.original.lower() or k in cap.english.lower()]
        self._emit({
            "type": "caption", "committed": True, "original": cap.original,
            "english": cap.english, "lang": cap.language, "matched": matched,
            "rtf": cap.rtf, "conf": cap.confidence, "ts": _ms(),
        })
        # Feed the watch: rolling English chunks; an alert overrides for 8 s.
        for chunk in captions.chunk_for_watch(cap.english):
            self.watch_queue.append(chunk)
        if matched:
            self.alert_title = captions.clip_title(cap.english)
            self.alert_until = time.monotonic() + config.ALERT_HOLD_S

    # ---- watch pacer (runs on the event loop) ----
    async def watch_pacer(self) -> None:
        last_published = None
        while True:
            await asyncio.sleep(config.WATCH_CHUNK_INTERVAL_S)
            if self.mode != "live":
                last_published = None
                continue
            now = time.monotonic()
            if now < self.alert_until:
                title = "⬥ " + self.alert_title  # ⬥
                state = "ALERT"
                artist = ""
            elif self.watch_queue:
                title = self.watch_queue.popleft()
                self.watch_prev = self.watch_last
                self.watch_last = title
                artist = self.watch_prev
                state = "LISTENING"
            else:
                continue  # nothing new; leave the current title up
            if (title, state) == last_published:
                continue
            last_published = (title, state)
            self.state = state
            await self.hub.publish(title=title, artist=artist, state=state)

    def shutdown(self) -> None:
        self._stop_live()


def _ms() -> int:
    return int(time.time() * 1000)
