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

from . import alerts, captions, config, llm, voice
from .asr import Transcriber, _clean
from .audio import RingMic

# Common Tagalog function words — if whisper's "English" still contains these,
# its translate pass stayed in Tagalog and we fall back to the local LLM.
_TAGALOG_MARKERS = {"ang", "ng", "sa", "ka", "mo", "ba", "ako", "ikaw", "kasama", "saan", "sino", "pupunta"}


def _looks_tagalog(text: str) -> bool:
    words = {w.strip(".,?!").lower() for w in text.split()}
    return len(words & _TAGALOG_MARKERS) >= 2


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

        # app mode: ambient (default) | captions | translate
        self.app_mode = "ambient"
        self.read_lang = "en"   # language the user reads (captions/ambient)
        # conversation mode (explicit languages, turn-based) — used by TRANSLATE
        self.conv = dict(config.CONV_DEFAULT)
        self.muted = False

        # committed transcript history (English) for catch-up; alert cooldowns
        self.history: collections.deque[tuple[float, str]] = collections.deque(maxlen=400)
        self._alert_cooldown: dict[str, float] = {}

    def attach_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    # ---- conversation settings ----
    def set_conv(self, their: str | None = None, mine: str | None = None, turn: str | None = None) -> dict:
        if their in config.ASR_LANGS:
            self.conv["their"] = their
        if mine in config.ASR_LANGS:
            self.conv["mine"] = mine
        if turn in ("them", "me"):
            self.conv["turn"] = turn
        self._emit({"type": "conv", **self.conv, "ts": _ms()})
        return dict(self.conv)

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
        # Prewarm the LLMs (translation 3b, alerts/catch-up 1.5b) in the background
        # so the first conversation turn / alert / catch-up isn't a cold-load timeout.
        threading.Thread(
            target=lambda: (llm.prewarm(config.LLM_HEAVY), llm.prewarm(config.LLM_DEFAULT)),
            name="earshot-prewarm", daemon=True,
        ).start()

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
                    utt_lang = self._turn_asr_lang()  # explicit, no detection
                    last_partial_text = ""
                # periodic partial (transcribe in the forced turn language)
                if now - last_partial >= config.PARTIAL_INTERVAL_S:
                    dur = min(now - utt_start + 0.3, config.MAX_UTTERANCE_S + 1)
                    samples = self._mic.snapshot(dur)
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

    def _turn_asr_lang(self) -> str:
        """The language whisper is forced to for the current turn (no detection)."""
        return self.conv["their"] if self.conv["turn"] == "them" else self.conv["mine"]

    def _rtl(self, lang: str) -> bool:
        return lang in config.RTL_LANGS

    def _commit(self, now: float, utt_start: float, utt_lang: str | None) -> None:
        if self._mic is None:
            return
        dur = min(now - utt_start + 0.5, config.MAX_UTTERANCE_S + 1)
        samples = self._mic.snapshot(dur)
        turn = self.conv["turn"]
        their, mine = self.conv["their"], self.conv["mine"]
        beam = config.ASR_BEAM_COMMIT
        try:
            if turn == "them":
                original, conf = self._transcriber._run(samples, "transcribe", their, beam)
                original = _clean(original, conf)
                if not original:
                    return
                english = self._to_english(samples, their, original, beam)
                primary = {"text": english, "lang": "en", "rtl": False}
                secondary = {"text": original, "lang": their, "rtl": self._rtl(their)}
                watch_en = english
            else:  # my turn: transcribe my language, translate -> their language (big)
                original, conf = self._transcriber._run(samples, "transcribe", mine, beam)
                original = _clean(original, conf)
                if not original:
                    return
                translated = llm.translate(original, their, model=config.LLM_HEAVY) or original
                primary = {"text": translated, "lang": their, "rtl": self._rtl(their)}
                secondary = {"text": original, "lang": mine, "rtl": self._rtl(mine)}
                watch_en = original if mine == "en" else self._to_english(samples, mine, original, beam)
        except Exception as exc:
            self._emit({"type": "event", "kind": "asr_error", "detail": str(exc), "ts": _ms()})
            return

        # record English history for catch-up
        self.history.append((time.time(), watch_en))

        # alerts: fuzzy keyword hit -> cooldown -> optional LLM intent confirm
        is_alert, matched, alert_title = self._check_alert(watch_en, original)

        self._emit({
            "type": "caption", "committed": True, "speaker": turn,
            "original": original, "english": watch_en, "lang": self._turn_asr_lang(),
            "primary": primary, "secondary": secondary,
            "matched": matched, "alert": is_alert, "ts": _ms(),
        })
        # Watch: rolling English chunks; an alert overrides for 8 s + chime.
        for chunk in captions.chunk_for_watch(watch_en):
            self.watch_queue.append(chunk)
        if is_alert:
            self.alert_title = captions.clip_title(alert_title or watch_en)
            self.alert_until = time.monotonic() + config.ALERT_HOLD_S
            voice.chime()
            self._emit({"type": "event", "kind": "alert", "detail": self.alert_title,
                        "matched": matched, "ts": _ms()})

    def _check_alert(self, english: str, original: str) -> tuple[bool, list[str], str]:
        hits = alerts.fuzzy_hits(f"{english} {original}")
        if not hits:
            return False, [], ""
        now = time.monotonic()
        fresh = [k for k in hits if now - self._alert_cooldown.get(k.lower(), -1e9) >= config.ALERT_COOLDOWN_S]
        if not fresh:
            return False, hits, ""  # all on cooldown
        for k in fresh:
            self._alert_cooldown[k.lower()] = now
        if config.ALERT_USE_LLM:
            is_alert, title = alerts.intent_confirm(english)
        else:
            is_alert, title = True, english[:40]
        return is_alert, hits, title

    def _to_english(self, samples, lang: str, original: str, beam: int) -> str:
        """English for the watch. Whisper translate; for Tagalog, fall back to the
        local LLM if whisper's output is still Tagalog."""
        if lang == "en":
            return original
        raw_en, conf_en = self._transcriber._run(samples, "translate", lang, beam)
        english = _clean(raw_en, conf_en) or original
        if lang == "tl" and _looks_tagalog(english):
            english = llm.translate(original, "en", model=config.LLM_HEAVY) or english
        return english

    # ---- mute (privacy) ----
    def mute(self, muted: bool) -> dict:
        if self.mode != "live":
            return {"muted": self.muted, "mode": self.mode}
        if muted and not self.muted:
            self._stop_live()          # closes the mic immediately
            self.muted = True
            self.state = "MUTED"
            self._emit({"type": "event", "kind": "mute", "detail": "on", "ts": _ms()})
            if self._loop is not None:
                asyncio.run_coroutine_threadsafe(
                    self.hub.publish(title="Muted · not listening", artist="", state="MUTED"),
                    self._loop,
                )
        elif not muted and self.muted:
            self.muted = False
            self.state = "LISTENING"
            self._start_live()          # reopens the mic + worker
            self._emit({"type": "event", "kind": "mute", "detail": "off", "ts": _ms()})
        return {"muted": self.muted, "mode": self.mode}

    # ---- catch me up ----
    def catch_up(self) -> dict:
        cutoff = time.time() - config.CATCHUP_MINUTES * 60
        recent = [t for (ts, t) in self.history if ts >= cutoff and t]
        if not recent:
            summary = {"line1": "Nothing to catch up on yet.", "line2": "", "source": "empty"}
            self._announce_catchup(summary)
            return summary
        words: list[str] = []
        for line in reversed(recent):  # newest first, cap words
            words = line.split() + words
            if len(words) >= config.CATCHUP_MAX_WORDS:
                break
        transcript = " ".join(words[-config.CATCHUP_MAX_WORDS:])
        schema = {
            "type": "object",
            "properties": {
                "line1": {"type": "string", "maxLength": 60},
                "line2": {"type": "string", "maxLength": 60},
                "important": {"type": "boolean"},
            },
            "required": ["line1", "line2", "important"],
        }
        system = (
            "Summarize what the listener missed in exactly two short lines, max 60 "
            "characters each, plain words, using only facts in the transcript. Mention "
            "deadlines, names and numbers exactly as said. If nothing important was said, say so."
        )
        out = llm.chat_json(config.CATCHUP_MODEL, system, transcript, schema, timeout=config.CATCHUP_TIMEOUT)
        if out and (out.get("line1") or out.get("line2")):
            summary = {"line1": out.get("line1", ""), "line2": out.get("line2", ""), "source": "llm"}
        else:
            # extractive fallback: the last couple of committed lines
            tail = recent[-2:]
            summary = {
                "line1": tail[-1][:60] if tail else "",
                "line2": (tail[-2][:60] if len(tail) > 1 else "(quick recap — no summary)"),
                "source": "extractive",
            }
        self._announce_catchup(summary)
        return summary

    def _announce_catchup(self, summary: dict) -> None:
        if self._loop is not None:
            asyncio.run_coroutine_threadsafe(
                self.hub.publish(title=summary["line1"], artist=summary["line2"], state="CATCH_UP"),
                self._loop,
            )
        self._emit({"type": "event", "kind": "catchup", "detail": summary["source"],
                    "line1": summary["line1"], "line2": summary["line2"], "ts": _ms()})
        spoken = f"In the last five minutes. {summary['line1']}. {summary['line2']}"
        voice.speak(spoken)

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
