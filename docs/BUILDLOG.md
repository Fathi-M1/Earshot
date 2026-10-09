# Earshot build log

All code written in the AppBuildersPH 2026 build window (started Fri Oct 9, 7 PM PHT).
Planning docs and brand kit were prepared before the build (disclosed in README).

## Phase 0 — go/no-go (target cutoff 8:00 PM)
- Scaffolded repo: moved `design/` to root, copied docs to `docs/`, created `web/ scripts/ tests/ earshot/`; `git init`; `uv init` (flat layout, pinned Python 3.12); `.gitignore` (models, *.db, *.wav except tests/audio, secrets).
- Started downloads in background: Ollama (installed 0.40.1) + `qwen2.5:3b/1.5b` + `nomic-embed-text`; faster-whisper `tiny.en/base.en/base` (done); set `OLLAMA_KEEP_ALIVE=-1`, `OLLAMA_NUM_PARALLEL=1`.
- `brand.py`: reads name/colors/state tiles from `design/tokens.json` (name is a variable).
- `localclient.py`: the only HTTP client — refuses non-local/non-private hosts before any socket opens; byte counters. Unit-tested (public hosts refused, bytes stay 0; local calls counted via respx).
- `netcut.py` + `scripts/cut-internet.ps1` / `restore-internet.ps1`: firewall cut/restore reproducing 01 §3.11 verbatim; rule-builder unit-tested against the exact command strings.
- `daemon.py`: dashboard app (127.0.0.1:7777, big-counter page + /ws + /health) and phone app (0.0.0.0:7778, web/index.html + /config + /silent.wav generated in RAM + /art tiles + token-gated /ws/phone). Shared Hub broadcasts a server-timestamped counter every 2 s for the Garmin/iPhone latency film. Smoke-tested live: both ports serve, WS tick increments.
- `web/index.html`: phone page — Start→silent looping audio holds the iOS Media Session; metadata/title from WS; play/pause/next/previous handlers (no seek); token WS with backoff + visibilitychange resync; tap-to-resume. Brand name fetched from /config (not hard-coded).
- `bench.py` + `earshot bench`: ASR RTF/WER over `tests/audio/*.wav` decoded into RAM (warm model, VAD on, cpu_threads=4); Ollama tokens/s via localclient; appends real numbers to `docs/bench.txt`.
- `cli.py`: `serve · bench · net cut|restore|status · doctor · wipe`.
- Tests: 20 passing (`uv run pytest -q`) — brand, localclient, netcut, no-audio-on-disk, daemon smoke/hub.
- Pending for Fathi (device checks): record `tests/audio/*.wav` then run `earshot bench`; film Garmin + iPhone latency; run `cut-internet.ps1` from admin PowerShell; try both button maps. Numbers → `docs/bench.txt`.

## P1 (pulled forward for the P0 confirm test)
- Languages = English/Tagalog/Arabic: multilingual whisper `base` (auto-detect), caption bar shows original, Now Playing (watch/lock) shows English (task=translate). LLM default `qwen2.5:1.5b`. Downloaded whisper `small` (use if RTF allows).
- `audio.py` RAM ring mic, `asr.py` multilingual transcriber, `live.py` controller; daemon `/live` dashboard shows every caption + detected language + events, with a Counter↔Live toggle. Smoke-tested: mic opens, model warms (loading→ready), events stream over WS, mode toggles, bytes-to-internet stays 0, /health responsive (43 ms/3 calls after offloading blocking calls to a threadpool).
- `earshot serve --live` starts in live mode; default stays counter (for the latency film).

## P1 quality pass
- Languages restricted to en/tl/ar/es (detect highest-prob among them); whisper small (fallback base), beam 5 commit / beam 1 partial; Taglish initial_prompt; anti-repetition + hallucination filter. VAD endpointing: partials while speaking, commit on pause / 12 s cap. Smoke-tested live: loading→ready, 22 s silence with no false captions, worker survives errors.
- Phone is one installable PWA (manifest + Host Grotesk + icons from design/). Foreground = full-screen captions (last 3 lines, English under original, Wake Lock); background/locked = Media Session rolling ≤28-char chunks, alert override 8 s. On-page diagnostic reports standalone/tab + Media Session presence — **Fathi to verify iOS standalone Media Session; fall back to a Safari tab if it dies (I can't test iOS from here).**
- Laptop caption bar `earshot bar` (frameless, topmost, draggable, Ctrl+Alt+C global toggle, WS-driven).
- bench mirrors the live commit pass with per-language RTF incl. Spanish. 31 tests passing.

## P2 — conversation mode, alerts, catch-up, mute
- Conversation mode: explicit language pair + Them/Me turn, no auto-detection. Them = force whisper to their language, show original + English. Me = transcribe English, translate EN→their language with qwen2.5:3b (strict JSON via llm.py). Arabic RTL + Arabic font fallback. Tagalog forced + tl→en LLM fallback. Real translations verified (AR/ES good; TL weak on 3b — honest limit).
- Phone layout fixed: scrollable full-height caption column, newest at bottom, auto-scroll pauses on scroll-up, Jump-to-live pill, safe-area insets. Controls on phone + /live (language pair, Them/Me, Catch up, Mute).
- Alerts: rapidfuzz + metaphone keyword match → qwen2.5:1.5b intent confirm (4s, keyword stands on timeout), 20s cooldown; amber row + watch ⬥ title 8s + laptop chime.
- Catch me up: qwen2.5:1.5b 2-line summary of last 5 min → local TTS (pyttsx3 SAPI; Piper hook) + extractive fallback; LLMs prewarmed on live start (fixes cold-load timeout).
- Mute: Pause → mic closed instantly, MUTED on every surface. Persistent phone token + WS auth fix (token from /config, close code/reason shown). 42 tests passing.

## P2 big build — modes, recall, notes, privacy, install
- **Privacy fix (D):** localclient now separates internet (public, 0 by construction) from local (loopback/Ollama) bytes; HF_HUB_OFFLINE/TRANSFORMERS_OFFLINE set at import; psutil egress proof on a 5s background timer. Verified live: after Ollama prewarm, internet_bytes=0, internet_connections=0, local_bytes=212/924. Arabic "安娜" bug fixed with a foreign-script sanitizer (rejects drifted translations). Garmin chunks ≤28 (unit-tested).
- **Modes (A):** ambient (auto-detect→read language, announcements + questions-to-me alerts, 10-min + on-demand insight cards via 1.5b), captions (read-language translate, A-/A+ size, speaker-changed divider), translate (unchanged Them/Me). Switchers on phone + /live.
- **Recall (B):** nomic-embed-text + SQLite semantic search; /recall → top-3 quotes + 1-line answer; verified top hit cosine 0.726 for "when is the quiz?". Search box on phone + /live.
- **Notes (C):** End session → 1.5b notes + dateparser (handles "next Friday" via modifier-strip) + hand-written .ics (validated with icalendar). Sessions list + .ics download.
- **Install/QR (E):** scripts/install.ps1 (uv, Ollama, models, Start-menu shortcut) + start.ps1; QR of the phone URL on /live (/qr.png) and printed to the terminal on serve.
- 56 tests passing. All new endpoints smoke-tested live.
