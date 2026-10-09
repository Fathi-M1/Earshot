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
