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

from . import alerts, captions, config, llm, recall, voice
from .asr import Transcriber, _clean
from .audio import RingMic

# Common Tagalog function words — if whisper's "English" still contains these,
# its translate pass stayed in Tagalog and we fall back to the local LLM.
_TAGALOG_MARKERS = {"ang", "ng", "sa", "ka", "mo", "ba", "ako", "ikaw", "kasama", "saan", "sino", "pupunta"}


def _looks_tagalog(text: str) -> bool:
    words = {w.strip(".,?!").lower() for w in text.split()}
    return len(words & _TAGALOG_MARKERS) >= 2


_QUESTION_WORDS = ("what", "where", "when", "who", "why", "how", "did", "do", "are", "is", "can", "could", "will")


def _is_question_to_me(text: str) -> bool:
    """Heuristic: a question that mentions the listener's name or 'you'."""
    t = text.strip().lower()
    if "?" not in t and not t.startswith(_QUESTION_WORDS):
        return False
    names = [n.lower() for n in config.ALERT_KEYWORDS if n.istitle() or n == "Fathi"]
    mentions_me = ("you" in t.split()) or any(n in t for n in ["fathi"] + names)
    return mentions_me


class LiveController:
    def __init__(self, hub):
        self.hub = hub
        self.mode = "counter"
        self._loop: asyncio.AbstractEventLoop | None = None
        self._mic: RingMic | None = None
        # two-tier ASR: fast base for partials + instant commit, small to refine
        self._fast = Transcriber(config.ASR_FAST)
        self._accurate = Transcriber(config.ASR_ACCURATE)
        self._transcriber = self._fast  # back-compat alias
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._cid = 0                    # committed-line id (for background replace)
        self._speaking = False           # gates recall/insight work to idle time
        self._pending_recall: collections.deque[str] = collections.deque()
        self.timing: dict = {}           # last per-stage latency (ms)
        self._last_bench = 0.0

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
        self._last_commit_mono = 0.0
        self.insights: list[dict] = []   # ambient INSIGHT CARDS
        self.recall = recall.Recall()    # semantic search over today's lines

    def attach_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    # ---- app mode (ambient | captions | translate) + reading language ----
    def set_app_mode(self, app_mode: str | None = None, read_lang: str | None = None) -> dict:
        if app_mode in ("ambient", "captions", "translate"):
            self.app_mode = app_mode
        if read_lang in config.ASR_LANGS:
            self.read_lang = read_lang
        self._emit({"type": "appmode", "app_mode": self.app_mode, "read_lang": self.read_lang, "ts": _ms()})
        return {"app_mode": self.app_mode, "read_lang": self.read_lang}

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
        threading.Thread(target=self._recall_worker, name="earshot-recall", daemon=True).start()

    def _stop_live(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=3.0)
            self._thread = None
        if self._mic is not None:
            self._mic.close()
            self._mic = None

    def _recall_worker(self) -> None:
        """Embed committed lines for recall ONLY when idle (never while speaking)."""
        while not self._stop.is_set():
            time.sleep(0.5)
            if self._speaking or not self._pending_recall:
                continue
            try:
                self.recall.add_line(self._pending_recall.popleft())
            except Exception:
                pass

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

    # ---- worker (two-tier: fast captions now, accurate refine in background) ----
    def _worker(self) -> None:
        self._emit({"type": "event", "kind": "loading", "detail": config.ASR_FAST, "ts": _ms()})
        self._fast.load()
        self._emit({"type": "event", "kind": "ready", "detail": config.ASR_FAST, "ts": _ms()})
        threading.Thread(target=self._warm_background, name="earshot-warm", daemon=True).start()

        st = {"active": False, "utt_start": 0.0, "last_partial": 0.0, "last_speech": 0.0,
              "lang": None, "last_text": "", "first_partial": False}
        pause_s = config.PAUSE_SILENCE_MS / 1000.0
        while not self._stop.is_set():
            time.sleep(config.LOOP_TICK_S)
            if self._stop.is_set() or self._mic is None:
                break
            try:
                self._tick(st, pause_s)
            except Exception as exc:
                self._emit({"type": "event", "kind": "asr_error", "detail": str(exc), "ts": _ms()})

    def _warm_background(self) -> None:
        # Only warm what the live path uses (1.5b for translate/alerts/catch-up +
        # nomic for recall). 3b is NOT on the hot path — prewarming it stole CPU
        # from ASR and caused multi-second partial spikes at session start.
        llm.prewarm(config.LLM_DEFAULT)
        try:
            recall._embed("warm", "search_document: ")
        except Exception:
            pass
        try:
            self._accurate.load()  # small, for background refine (load last)
        except Exception:
            pass
        self._emit({"type": "event", "kind": "warm", "detail": "models ready", "ts": _ms()})

    def _tick(self, st: dict, pause_s: float) -> None:
        now = time.monotonic()
        speaking = self._has_speech(self._mic.snapshot(0.8))
        if speaking:
            st["last_speech"] = now
            self._speaking = True
            if not st["active"]:
                st.update(active=True, utt_start=now, last_partial=0.0, last_text="",
                          first_partial=False, lang=self._asr_lang_for_mode())
            # AMBIENT/CAPTIONS: detect language once (on ~LANG_LOCK_S of speech), then lock
            if st["lang"] is None and (now - st["utt_start"]) >= 0.6:
                win = self._mic.snapshot(min(now - st["utt_start"] + 0.3, config.LANG_LOCK_S))
                st["lang"], _ = self._fast.detect(win)
            if now - st["last_partial"] >= config.PARTIAL_INTERVAL_S:
                dur = min(now - st["utt_start"] + 0.2, config.MAX_UTTERANCE_S + 1)
                samples = self._mic.snapshot(dur)
                try:
                    raw, conf = self._fast._run(samples, "transcribe", st["lang"], config.ASR_BEAM_PARTIAL)
                    txt = _clean(raw, conf)
                except Exception:
                    txt = ""
                st["last_partial"] = now
                if txt and txt != st["last_text"]:
                    st["last_text"] = txt
                    if not st["first_partial"]:
                        self.timing["partial_ms"] = int((now - st["utt_start"]) * 1000)
                        st["first_partial"] = True
                    self._emit({"type": "caption", "committed": False, "original": txt,
                                "english": "", "lang": st["lang"] or "", "ts": _ms()})
            if now - st["utt_start"] >= config.MAX_UTTERANCE_S:
                self._commit(now, st["utt_start"], st["lang"]); st["active"] = False
        else:
            self._speaking = False
            if st["active"] and (now - st["last_speech"]) >= pause_s:
                self._commit(now, st["utt_start"], st["lang"]); st["active"] = False

    def _turn_asr_lang(self) -> str:
        return self.conv["their"] if self.conv["turn"] == "them" else self.conv["mine"]

    def _asr_lang_for_mode(self) -> str | None:
        """Forced language (TRANSLATE turn) or None to auto-detect+lock (AMBIENT/CAPTIONS)."""
        return self._turn_asr_lang() if self.app_mode == "translate" else None

    def _rtl(self, lang: str) -> bool:
        return lang in config.RTL_LANGS

    def _commit(self, now: float, utt_start: float, utt_lang: str | None) -> None:
        if self._mic is None:
            return
        if (now - utt_start) < config.MIN_SEGMENT_S:  # drop sub-0.6s blips
            return
        samples = self._mic.snapshot(min(now - utt_start + 0.4, config.MAX_UTTERANCE_S + 1))
        lang = utt_lang or self._fast.detect(samples)[0]
        t0 = time.perf_counter()
        try:
            raw, conf = self._fast._run(samples, "transcribe", lang, config.ASR_BEAM_COMMIT)
        except Exception as exc:
            self._emit({"type": "event", "kind": "asr_error", "detail": str(exc), "ts": _ms()})
            return
        original = _clean(raw, conf)
        if not original:
            return
        commit_ms = int((time.perf_counter() - t0) * 1000)
        self._cid += 1
        cid = self._cid
        divider = (now - self._last_commit_mono) > 1.5
        self._last_commit_mono = now
        speaker = self.conv["turn"] if self.app_mode == "translate" else "them"
        self.timing.update(commit_ms=commit_ms, e2e_ms=commit_ms)
        # Emit the FAST line immediately — captions never wait on refine/LLM.
        self._emit({
            "type": "caption", "committed": True, "id": cid, "speaker": speaker,
            "original": original, "english": "", "lang": lang, "pending": True,
            "primary": {"text": original, "lang": lang, "rtl": self._rtl(lang)}, "secondary": {},
            "matched": [], "alert": False, "divider": divider,
            "timing": {"commit_ms": commit_ms, "partial_ms": self.timing.get("partial_ms")}, "ts": _ms(),
        })
        ctx = {"app_mode": self.app_mode, "read_lang": self.read_lang, "conv": dict(self.conv),
               "announcements": (self.app_mode == "ambient")}
        threading.Thread(target=self._refine, args=(samples, lang, original, cid, ctx),
                         name="earshot-refine", daemon=True).start()

    def _refine(self, samples, lang: str, original_fast: str, cid: int, ctx: dict) -> None:
        t0 = time.perf_counter()
        try:  # accurate re-transcribe (small, beam 1)
            raw, conf = self._accurate._run(samples, "transcribe", lang, 1)
            original = _clean(raw, conf) or original_fast
        except Exception:
            original = original_fast
        # English via whisper translate (xx->en) — no LLM on this path
        tr_ms = None
        if lang == "en":
            watch_en = original
        else:
            tt = time.perf_counter()
            try:
                en_raw, en_conf = self._fast._run(samples, "translate", lang, 1)
                watch_en = _clean(en_raw, en_conf) or original
            except Exception:
                watch_en = original
            tr_ms = int((time.perf_counter() - tt) * 1000)
        primary, secondary = self._display_for(ctx, original, watch_en, lang)
        is_alert, matched, alert_title = self._check_alert(watch_en, original, ctx["announcements"])
        self._emit({
            "type": "caption_update", "id": cid, "original": original, "english": watch_en,
            "lang": lang, "primary": primary, "secondary": secondary,
            "matched": matched, "alert": is_alert,
            "timing": {"translate_ms": tr_ms, "refine_ms": int((time.perf_counter() - t0) * 1000)}, "ts": _ms(),
        })
        for chunk in captions.chunk_for_watch(watch_en):
            self.watch_queue.append(chunk)
        if is_alert:
            self.alert_title = captions.clip_title(alert_title or watch_en)
            self.alert_until = time.monotonic() + config.ALERT_HOLD_S
            voice.chime()
            self._emit({"type": "event", "kind": "alert", "detail": self.alert_title, "matched": matched, "ts": _ms()})
        self.history.append((time.time(), watch_en))
        self._pending_recall.append(watch_en)  # embedded when idle (recall worker)
        self.timing["translate_ms"] = tr_ms
        self._emit({"type": "timing", **self.timing, "ts": _ms()})
        self._maybe_write_bench()

    def _display_for(self, ctx: dict, original: str, watch_en: str, lang: str) -> tuple[dict, dict]:
        """Compute the on-screen primary/secondary per mode. qwen is used ONLY for
        English->their-language (short, capped); xx->English used whisper above."""
        mode = ctx["app_mode"]
        if mode == "translate":
            conv = ctx["conv"]
            if conv["turn"] == "them":
                return ({"text": watch_en, "lang": "en", "rtl": False},
                        {"text": original, "lang": lang, "rtl": self._rtl(lang)})
            their = conv["their"]
            src_en = original if lang == "en" else watch_en
            translated = llm.translate(src_en, their, model=config.LLM_DEFAULT) or src_en
            return ({"text": translated, "lang": their, "rtl": self._rtl(their)},
                    {"text": original, "lang": lang, "rtl": self._rtl(lang)})
        read = ctx["read_lang"]
        if lang == read:
            shown = original
        elif read == "en":
            shown = watch_en
        else:
            shown = llm.translate(watch_en, read, model=config.LLM_DEFAULT) or watch_en
        secondary = {"text": original, "lang": lang, "rtl": self._rtl(lang)} if lang != read else {}
        return {"text": shown, "lang": read, "rtl": self._rtl(read)}, secondary

    def _maybe_write_bench(self) -> None:
        now = time.time()
        if now - self._last_bench < 8.0:
            return
        self._last_bench = now
        try:
            from pathlib import Path
            p = Path(__file__).resolve().parent.parent / "docs" / "bench.txt"
            t = self.timing
            line = (f"latency  partial={t.get('partial_ms')}ms commit={t.get('commit_ms')}ms "
                    f"translate={t.get('translate_ms')}ms e2e={t.get('e2e_ms')}ms "
                    f"({time.strftime('%H:%M:%S')})\n")
            with p.open("a", encoding="utf-8") as f:
                f.write(line)
        except Exception:
            pass

    def _check_alert(self, english: str, original: str, announcements: bool = False) -> tuple[bool, list[str], str]:
        kws = list(config.ALERT_KEYWORDS)
        if announcements:
            kws += config.ANNOUNCEMENT_KEYWORDS
        text = f"{english} {original}"
        hits = alerts.fuzzy_hits(text, kws)
        question = announcements and _is_question_to_me(english)
        if not hits and not question:
            return False, [], ""
        now = time.monotonic()
        key = (hits[0] if hits else "question?")
        fresh = [k for k in hits if now - self._alert_cooldown.get(k.lower(), -1e9) >= config.ALERT_COOLDOWN_S]
        if not fresh and not (question and now - self._alert_cooldown.get("question?", -1e9) >= config.ALERT_COOLDOWN_S):
            return False, hits, ""
        for k in (fresh or [key]):
            self._alert_cooldown[k.lower()] = now
        if config.ALERT_USE_LLM:
            is_alert, title = alerts.intent_confirm(english)
        else:
            is_alert, title = True, english[:40]
        if question:
            is_alert = True
        return is_alert, (hits or ["question"]), title

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

    # ---- session notes ----
    def end_session(self) -> dict:
        from . import notes

        lines = [t for _ts, t in self.history]
        result = notes.end_session(lines)
        self._emit({"type": "event", "kind": "session_saved", "detail": result["session"],
                    "events": result["events"], "ts": _ms()})
        return result

    # ---- insight cards (AMBIENT) ----
    def make_insight(self, minutes: int = 10) -> dict:
        cutoff = time.time() - minutes * 60
        recent = [(ts, t) for (ts, t) in self.history if ts >= cutoff and t]
        if not recent:
            return {"ok": False, "reason": "nothing yet"}
        transcript = " ".join(t for _ts, t in recent)[-4000:]
        schema = {
            "type": "object",
            "properties": {
                "topics": {"type": "array", "items": {"type": "string"}, "maxItems": 6},
                "questions": {"type": "array", "items": {"type": "object",
                    "properties": {"who": {"type": "string"}, "what": {"type": "string"}},
                    "required": ["who", "what"]}, "maxItems": 6},
                "dates": {"type": "array", "items": {"type": "object",
                    "properties": {"what": {"type": "string"}, "when": {"type": "string"}},
                    "required": ["what", "when"]}, "maxItems": 6},
                "tasks": {"type": "array", "items": {"type": "string"}, "maxItems": 8},
            },
            "required": ["topics", "questions", "dates", "tasks"],
        }
        system = (
            "From the transcript, extract: topics discussed; questions asked and who asked "
            "(use 'someone' if unknown); dates/deadlines (what + when as said); and tasks/action "
            "items. Use only facts in the transcript. Reply JSON only."
        )
        out = llm.chat_json(config.LLM_DEFAULT, system, transcript, schema, timeout=config.CATCHUP_TIMEOUT)
        if not out:
            return {"ok": False, "reason": "llm unavailable"}
        card = {
            "ok": True,
            "ts": _ms(),
            "window_min": minutes,
            "time": time.strftime("%H:%M"),
            "topics": out.get("topics", []),
            "questions": out.get("questions", []),
            "dates": out.get("dates", []),
            "tasks": out.get("tasks", []),
        }
        self.insights.append(card)
        self._emit({"type": "insight", **card})
        return card

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
