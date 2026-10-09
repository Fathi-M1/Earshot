# 06 · README template (copy to repo README.md; fill every <>; delete unused rows)

<p align="center"><img src="design/lockup-light.svg" width="360" alt="Earshot"></p>

# Earshot
**Hear what matters. Offline.** A private listening companion that runs entirely on your laptop and puts live captions, "heard your name" alerts and a spoken catch-up on screens you already own: your watch, your phone's lock screen, Windows, your earbuds. No new app. No cloud.
Built solo by Fathi <surname> for **AppBuildersPH 2026 — Local AI** (Oct 9–10, 2026). Video: <link> · Post: <link>

![Garmin, iPhone lock screen and caption bar](docs/screens/hero.jpg)  ← real photo, not the mock

## Why local AI?
<the 120-word answer from 05_PITCH>

## What it does
| Feature | Model / method (local) | Status |
|---|---|---|
| Live captions (bar, Windows lock screen, iPhone lock screen, Garmin) | faster-whisper `<base.en>` int8 CPU + Silero VAD | <shipped> |
| Heard-your-name / deadline alerts | rapidfuzz + Double Metaphone; intent check `qwen2.5:<1.5b>` via Ollama | |
| Catch me up (2 lines, spoken) | `qwen2.5:3b` via Ollama → Piper `<voice>` | |
| Tagalog → English | faster-whisper `<base/small>` task=translate | <shipped / cut> |
| Recall (exact quote + time) | `nomic-embed-text` + SQLite, quote validated | <shipped / cut> |
| Class notes, to-dos, .ics | `qwen2.5:3b` + dateparser | <shipped / cut> |
| Safe Word (stretch) | keyword match; saves last 2 min text; optional send after confirmation | <shipped / cut> |
| Privacy: mute, text-only, auto-expire, bytes-sent counter, cut-internet toggle | — | |

## Measured performance (this laptop, `earshot bench`, raw output in docs/bench.txt)
| Metric | Value | How measured |
|---|---|---|
| ASR real-time factor (base.en, int8) | <x> | 5 recordings of my voice, <n> s total |
| WER on my recordings | <x %> | jiwer vs my hand transcript |
| Caption delay: bar / iPhone / Garmin (p50, p90) | <> | 60 fps video, 20 samples |
| Catch-up time (warm) | <s> | 10 runs |
| Bytes sent to internet during demo | <0> | localclient counter + psutil |
Only measured numbers. Blank = not measured.

## What runs locally vs needs internet
| Part | Local | Internet |
|---|---|---|
| Speech recognition, translation, alerts, summaries, recall, notes, TTS | ✅ all | never |
| Caption bar, SMTC (Windows), dashboard | ✅ | never |
| iPhone page + Garmin | ✅ over local Wi-Fi/hotspot (LAN only; laptop's internet is blocked by firewall) | never |
| One-time: install packages + download models | — | yes, at setup |
| Safe Word message (optional, off by default) | evidence saved locally | sends only when online **and** you press Next to confirm |

## Hardware tested
Windows 11 <build>, Intel Core <i5/i7 model>, Intel Iris Xe, 16 GB RAM, no NVIDIA GPU · iPhone <model>, iOS <ver>, Safari · Garmin Forerunner 165 (Control Phone) · Apple EarPods (wired) · mic: <laptop / USB>.

## Setup (Windows 11, PowerShell)
```powershell
winget install astral-sh.uv Ollama.Ollama Git.Git
git clone <repo> ; cd earshot
uv sync
ollama pull qwen2.5:3b ; ollama pull qwen2.5:1.5b ; ollama pull nomic-embed-text
.\scripts\fetch-models.ps1        # whisper + piper voice into models\
uv run earshot doctor             # checks mic, models, ports, firewall
uv run earshot serve              # admin PowerShell if you want the Cut internet toggle
```
iPhone: join the same network/hotspot → Safari → `http://<laptop-ip>:7778/?t=<token shown in terminal>` → tap Start → lock. Garmin: Music → Control Phone.
Cut internet manually: `.\scripts\cut-internet.ps1` · undo: `.\scripts\restore-internet.ps1` (or `Remove-NetFirewallRule -Group "EarshotOffline"`).

## Privacy
Raw audio exists only in a 30-second RAM buffer and is never written to disk. Only text is stored (`%LOCALAPPDATA%\Earshot\earshot.db`), auto-deleted after <24 h> (configurable), `earshot wipe` deletes everything. One press mutes the mic. **Consent:** recording conversations may be restricted where you live (in the Philippines, RA 4200). Ask before using it around others; use mute. This isn't legal advice.

## Disclosures (required)
**Models:** faster-whisper/CTranslate2 conversions of OpenAI Whisper `<tiny.en, base.en, base>` (MIT) · `<sapinsapin/whisper-small-fsc>` (<license>, if used) · Qwen2.5 3B/1.5B Instruct (Qwen license / Apache-2.0 for 1.5B — verify) via Ollama · nomic-embed-text v1.5 (Apache-2.0) · Piper voice `<en_US-…>` (<license>) · Silero VAD (MIT).
**Frameworks/libraries:** Ollama, faster-whisper, CTranslate2, FastAPI, uvicorn, sounddevice, rapidfuzz, jellyfish, dateparser, psutil, pywinrt (winrt 3.2.1), piper-tts, React, Vite, Tailwind, shadcn/ui, pytest, jiwer.
**External APIs / cloud:** none in the core. Optional Safe Word send: <Telegram Bot API / SMTP>, off by default, only after confirmation.
**Existing code:** none. Built Oct 9 7 PM – Oct 10 <time>. Before the build I wrote planning docs/spec and a brand kit; earlier throwaway spikes (Oct 8) were not reused <confirm>.
**Existing assets:** logo: <Fathi's own mark, created <when/with what>>; traced to SVG before the event (`design/_src`). Fonts: Host Grotesk, Fragment Mono (SIL OFL 1.1, `design/fonts/`).
**AI dev tools:** Claude Code (Opus 5.5) wrote most code from my specs; Grok Bot helped plan the docs and brand kit; <Cursor / Codex / Devin if used>. Every model call in the product is local.
**My work:** architecture, Now Playing caption approach, button map, privacy design, alert logic, prompts, design system, testing, demo.

## Limitations
Small models make mistakes, especially in noise and Taglish. The watch shows text but doesn't vibrate. iOS can suspend the Safari page; the caption bar and Windows lock screen keep working. It's laptop-based: it only hears what the laptop's mic hears. Not a medical, accessibility-certified or safety device.

## License
MIT (code). Fonts OFL. Models under their own licenses.
