# CLAUDE.md · Earshot project rules

## What this is
Earshot (working name; read it from `design/tokens.json → brand.name` via `earshot/brand.py`, never hard-code it in UI text) is a private, fully offline listening companion on a Windows laptop. Mic → local speech recognition (faster-whisper) → caption lines → OS **Now Playing** session (Windows SMTC + an iPhone Safari Media Session page mirrored to a Garmin) + a laptop caption bar. Local LLM (Ollama qwen2.5) for alert intent, catch-up summaries, recall answers and notes; Piper for speech; nomic-embed-text for recall.
**Hackathon rule that drives everything:** meaningful inference runs locally; everything must work with the internet cut. Judges may read the code.
Spec docs/01_SPEC.md · Plan docs/03_BUILD_PLAN.md · Risks docs/08_RISK_REGISTER.md · Design docs/02_DESIGN.md · Demo docs/04_DEMO_SCRIPT.md · Tests docs/07_TEST_CHECKLIST.md.

## Phases (strict order; cutoffs in 03)
P0 go/no-go (Garmin refresh latency, ASR bench, Ollama speed, hotspot + firewall cut) → P1 captions core → P2 alerts (+ offline pass) → P3 buttons + privacy + net toggle → P4 catch-up + Piper → P5 dashboard → P6 translate → P7 recall → (P8 notes/.ics, P9 Safe Word: only if early). Cut from the bottom.

## Environment
Windows 11, **PowerShell** only, `\` paths. Python 3.12 via **uv**. Ollama `127.0.0.1:11434`. Daemon `127.0.0.1:7777`, phone page `0.0.0.0:7778`. Models in `models\` (git-ignored). Iris Xe + 16 GB, CPU inference: ASR has priority, LLM `num_thread: 2`, one LLM call in flight.

## Stack (don't add others without asking)
FastAPI + uvicorn · sounddevice · faster-whisper (CTranslate2, int8 CPU) [fallback: whisper.cpp binaries] · silero VAD (bundled) · rapidfuzz + jellyfish · httpx (Ollama only, via `localclient.py`) · pydantic · dateparser · numpy · psutil · Pillow · Tkinter (caption bar) · `winrt-*` **3.2.1** (`winrt-runtime`, `-Windows.Media`, `-Windows.Media.Playback`, `-Windows.Media.Core`, `-Windows.Storage`, `-Windows.Storage.Streams`, `-Windows.Foundation`, `-Windows.Foundation.Collections`; NOT `winsdk`) · `piper-tts==1.3.0` (→ Piper binary → pyttsx3) · pytest + respx + jiwer. Phone page = one static HTML + vanilla JS. Dashboard = Vite + React + Tailwind + shadcn. No LangChain, no vector DB, no cloud SDKs (Safe Word's one optional send is the only exception, and only online after an explicit Next).
WinRT enums UPPER case; SMTC = MediaPlayer + `command_manager.is_enabled=False` + looping silent WAV.

## Layout
```
earshot/  brand.py  daemon.py  audio.py  asr.py  captions.py  alerts.py  catchup.py  recall.py  notes.py
          buttons.py  state.py  smtc.py  bar.py  cards.py  voice.py  privacy.py  netcut.py  localclient.py
          safeword.py (stretch)  prompts/*.md  cli.py (serve, bench, net cut|restore|status, doctor, wipe)
web/index.html  web/dashboard/   design/ (tokens, logo, tiles, fonts — use as is)
scripts/ cut-internet.ps1 restore-internet.ps1 fetch-models.ps1   tests/   docs/ BUILDLOG.md README.md bench.txt
```

## Non-negotiables
- **Raw audio never touches disk** (no WAV/temp files); RAM ring buffer 30 s. Tests assert it.
- **Privacy mute** closes the mic stream immediately and shows MUTED on every surface.
- `localclient.py` is the only HTTP client: loopback/private hosts only, counts bytes; the privacy panel shows real counters or "—".
- Every Ollama call: `stream:false`, `format` = JSON schema (01 §4), `temperature 0`, timeout, validated, fallback on failure. Never block the audio thread.
- Button debounce: 500 ms same-action filter, 1.5 s per-action lockout, drop events older than 3 s; phone client one reconnect in flight + backoff, never queue logs; server drops duplicate logs.
- Never claim or display unmeasured numbers. Never script/cache model output for the demo.
- `earshot net cut` must always be undone on exit (`restore` in a finally/atexit).
- Commit `pN: <what>` after each working step; BUILDLOG line; `uv run pytest -q` and show the result; ask Fathi for device checks (watch, iPhone, mic, Wi-Fi off).

## Design
Tokens only (`design/tokens.json`, Editorial Forest v3). Host Grotesk + Fragment Mono from `design/fonts/`. Logo files from `design/` (never redraw). Tiles: render with `cards.py` matching `design/tiles/*.png`. Every state = colour + shape + word. Glow `listen-glow` only for LISTENING.
