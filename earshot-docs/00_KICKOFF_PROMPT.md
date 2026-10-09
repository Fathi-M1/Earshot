# 00 · Kickoff prompt (paste into Claude Code, Opus 5.5, Fri Oct 9 ~7:00 PM)
Before: downloads from 01 §8 started; `mkdir C:\dev\earshot; cd C:\dev\earshot; git init`; copy docs into `docs\` and `design\` to the repo root, CLAUDE.md to the root; `claude`, `/model` → Opus 5.5.
```
You are building Earshot from scratch for AppBuildersPH 2026 (build started Fri 7 PM; deadline Sat 10 AM). All code is written now.
THEME: "Build an AI product that remains genuinely useful when the cloud disappears." Meaningful inference must run locally; the core must work without any cloud AI API; disclose every model/tool; fake benchmarks disqualify; judges may read the code.
PRODUCT: a private, fully offline listening companion on this Windows laptop: mic → faster-whisper → caption lines published as the OS Now Playing track (Windows SMTC + an iPhone Safari Media Session page that a Garmin mirrors) + a laptop caption bar; name/deadline alerts; Previous = 2-line catch-up (Ollama qwen2.5:3b → Piper); Next = bookmark; Play/Pause = privacy mute. The product name is a variable (design/tokens.json brand.name).
Read in order and follow strictly: CLAUDE.md, docs/01_SPEC.md, docs/03_BUILD_PLAN.md, docs/08_RISK_REGISTER.md, docs/07_TEST_CHECKLIST.md, docs/02_DESIGN.md (§9–§12), docs/04_DEMO_SCRIPT.md, docs/06_README_TEMPLATE.md.
Start with PHASE 0 (go/no-go) only: (1) a minimal daemon + web/index.html that pushes a changing title every 2 s so I can film the Garmin and measure delay; (2) `earshot bench` that times tiny.en/base.en/base on WAVs I record (record into memory, never to disk except these explicit bench files I create in tests/audio/) and prints real-time factor; (3) Ollama tokens/s for qwen2.5:3b and 1.5b; (4) scripts/cut-internet.ps1 + restore-internet.ps1 exactly as in 01 §3.11.
Reply first with a 10-line Phase 0 plan and any contradictions you found. Wait for "go".
Rules: commit "pN: <what>" after each working step, BUILDLOG line, run `uv run pytest -q` and show it. At a cutoff, take the fallback and move on. Never write audio to disk in the product. Never show unmeasured numbers. Never claim the watch vibrates.
```
