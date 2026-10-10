<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="design/lockup-dark.svg">
    <img src="design/lockup-light.svg" width="440" alt="Earshot">
  </picture>
</p>

<p align="center">
  <strong>Hear what matters. Offline.</strong><br>
  Live captions and alerts on the laptop, the phone, and the watch.<br>
  Speech recognition, the language model, and speech all stay on the machine.
</p>

<p align="center">
  English · Tagalog · Arabic<br>
  Made in Manila for AppBuilders PH 2026 · Team Skip Intro<br>
  <a href="https://earshot-landing.vercel.app">earshot-landing.vercel.app</a><br>
  <a href="https://github.com/Fathi-M1/Earshot">github.com/Fathi-M1/Earshot</a>
</p>

---

Earshot listens through the laptop microphone and puts the words on screens you already have: a caption bar on Windows, a phone page (Safari Media Session, so the iPhone lock screen and a Garmin can show the line), and a laptop dashboard. Cut the Wi-Fi after setup and it keeps listening. The only network the phone needs is the laptop’s own hotspot or LAN.

Raw audio stays in a 30-second memory buffer. It is never written to disk. What is saved is text: transcript lines, alerts, and catch-ups.

Contact: fatximahadpoqor1@gmail.com

## What it does

| | |
|---|---|
| **Captions** | Every line, as it is said, in the spoken language. Arabic is right-to-left. |
| **Listen for me** | Quiet until your name, a keyword, or a deadline. |
| **Translate** | They speak one language. You read another. English, Tagalog, Arabic. |
| **Catch me up** | A two-line recap on screen. Voice plays only when you tap **Hear it**. |
| **Sessions** | Transcript, alerts, and catch-ups save on the laptop. Open one to read it or replay the lines. Calendar export is a separate button inside the session. |
| **Mute** | One press closes the mic on every screen. Tap **Paused — tap to resume** and captions start again. |

Tell people you are captioning. Follow the recording law where you are. Captions can be wrong. This is not for emergencies or legal records.

## Models

Everything below runs on the CPU. This laptop is Windows 11, Intel Iris Xe, 16 GB RAM, no discrete GPU. Weights are not in the git repo. `models\` is git-ignored; Ollama keeps its own copies under your user profile.

| Job | Model | Where it runs |
|---|---|---|
| English partials | faster-whisper `tiny.en`, int8 | `models\whisper` |
| English refine | faster-whisper `base.en`, int8 | same |
| Tagalog and Arabic partials | faster-whisper `tiny`, int8 | same |
| Tagalog and Arabic refine | faster-whisper `small`, int8 | same |
| Voice activity | Silero VAD (bundled with faster-whisper) | in process |
| Alerts, catch-up, notes, English → their language | Ollama `qwen2.5:1.5b` | `127.0.0.1:11434` |
| Recall search | Ollama `nomic-embed-text` | same |
| Hear it | Piper `en_US-lessac-medium`, else the Windows voice | `models\piper` |

Speech recognition goes first. The language model uses two CPU threads and one call at a time, and it unloads after five minutes idle. Tagalog or Arabic to English is Whisper’s translate task. English into the other person’s language is `qwen2.5:1.5b`.

`qwen2.5:3b` was pulled during the hackathon and measured, then taken off the live path. On this machine it was slower (6.3 tok/s, 19 s wall on that call) and it stole CPU from captions. The installer still pulls it so the weights are there; the daemon does not call it. The live model is `qwen2.5:1.5b`.

Measured on this laptop and written into `docs/bench.txt` (do not treat anything else as a benchmark):

| | |
|---|---|
| `qwen2.5:1.5b` | 9.1 tok/s (15 tokens, 1.64 s eval, `num_thread` 2) |
| `qwen2.5:3b` | 6.3 tok/s on the same bench, then removed from the hot path |
| RAM while loaded | Earshot 222 MB + nomic 376 MB + qwen 1.5B 1.2 GB, about 1.85 GB |
| English fast tier | tiny, real-time factor 0.224, word error 0.04 on the clean English clip in that file |

Live caption timings from the same night are appended in `docs/bench.txt`. If a number is not in that file, it has not been measured.

## Set up (Windows 11, PowerShell)

You need internet once, to install tools and download weights. After that, Earshot does not call the public internet.

```powershell
git clone https://github.com/Fathi-M1/Earshot.git
cd Earshot
powershell -ExecutionPolicy Bypass -File scripts\install.ps1
```

`scripts\install.ps1` does this, in order:

1. Installs [uv](https://docs.astral.sh/uv/) and [Ollama](https://ollama.com/) with winget if they are missing.
2. Sets user environment variables `OLLAMA_KEEP_ALIVE=-1` and `OLLAMA_NUM_PARALLEL=1`.
3. Runs `uv sync --extra dev` (Python 3.12).
4. Pulls `qwen2.5:3b`, `qwen2.5:1.5b`, and `nomic-embed-text`.
5. Runs `scripts\fetch-models.ps1`: faster-whisper `tiny`, `base`, and `small` into `models\whisper` (int8, CPU), and the Piper voice `en_US-lessac-medium` into `models\piper`.
6. Adds a Start-menu shortcut named Earshot. The shortcut runs `scripts\start.ps1`, which opens the caption bar and the daemon.

Check the machine before the demo:

```powershell
uv run earshot doctor
```

That checks the mic, the model files, Ollama, ports 7777 and 7778, and whether the offline firewall rules are active.

Start it:

```powershell
uv run earshot serve
```

Or launch **Earshot** from the Start menu. The dashboard is [http://127.0.0.1:7777](http://127.0.0.1:7777). The phone page listens on `0.0.0.0:7778`. The terminal prints a QR code. On the iPhone, join the same Wi-Fi (or the laptop hotspot), open that URL in Safari, tap **Start**, then Add to Home Screen. On the Garmin, use Music → Control Phone so the watch title follows the phone’s Now Playing line.

Other commands:

```powershell
uv run earshot bar                         # caption bar, if the daemon is already running
uv run earshot serve --demo                # warm models, then start live with the QR
uv run earshot bench                       # append ASR and Ollama numbers to docs\bench.txt
uv run earshot wipe --yes                  # delete stored text
uv run earshot net status                  # is the offline firewall rule on?
uv run pytest -q
```

`earshot net cut` and `earshot net restore` need an elevated PowerShell. The same rules are in `scripts\cut-internet.ps1` and `scripts\restore-internet.ps1`. A cut must be restored before you leave the machine. The script restores on exit.

## Privacy

| | |
|---|---|
| Microphone | Open while listening. Mute closes the stream immediately. |
| Raw audio on disk | Never. 30-second RAM ring only. |
| What is stored | Text: lines, alerts, catch-ups, in a local SQLite file under your user profile. |
| Bytes to the public internet | Counted in the privacy panel. Loopback calls to Ollama are local, not internet. |
| Who can open the phone page | A token in the URL. The dashboard stays on `127.0.0.1`. |

## How it was built

AppBuilders PH 2026, local-AI track. Planning notes and the Editorial Forest brand kit were ready before the window. Code started Friday 9 October 2026, 7 PM PHT, on this laptop, and was written to run with the network cut. The log is `docs/BUILDLOG.md`. The spec is `docs/01_SPEC.md`. The plan is `docs/03_BUILD_PLAN.md`.

The order that actually shipped:

1. **Go / no-go.** Dashboard on port 7777, phone page on 7778, a looping silent clip generated in memory so iOS Media Session stays alive, and a firewall cut that restores on exit. The only HTTP client is `earshot/localclient.py`. It refuses public hosts.
2. **Captions.** Microphone audio stays in a RAM ring. faster-whisper on CPU, int8. The first live pass used a larger model on the hot path and captions took tens of seconds. The rewrite split it: `tiny` / `tiny.en` for partials and the instant line, `base.en` or `small` only to refine in the background. The caption never waits on the language model.
3. **Alerts and catch-up.** A fuzzy keyword hit, then `qwen2.5:1.5b` confirms intent. Catch-up prints an extractive recap immediately (last alert, then the last lines) and replaces it if the model answers within 3 seconds. Speech is only the **Hear it** button.
4. **Phone, watch, mute.** One Safari page. Pause closes the mic and every surface says muted. Resume opens the mic again and publishes listening, including from the watch Play control.
5. **Sessions.** Lines, alerts, and catch-ups append to SQLite as they happen. Settings lists them. Opening one replays the transcript in the app. An `.ics` file is built only if you tap add-to-calendar inside that session.
6. **Recall and notes.** `nomic-embed-text` over stored lines, searched when the room is quiet. End-of-session notes stay on the laptop.

Languages in the product are English, Tagalog, and Arabic. The spoken language is chosen. It is not guessed. Spanish showed up in an early detection experiment and was dropped.

## Layout

```
earshot\     daemon, captions, alerts, sessions, phone pages
web\         phone page (one HTML file)
design\      logo, wordmark, tokens, fonts
landing\     product site (Vite). Deploy from the repo root.
scripts\     install, start, model fetch, firewall cut and restore
tests\       pytest
docs\        spec, plan, bench log, build log
```

| Surface | Address |
|---|---|
| Laptop dashboard | `http://127.0.0.1:7777` |
| Phone | `http://<laptop-lan-ip>:7778/?t=<token>` |
| Ollama | `http://127.0.0.1:11434` |

## License

Earshot’s code is MIT. Host Grotesk and Fragment Mono are SIL OFL 1.1. Model and library licenses stay with those projects. The in-app Licenses page reads library licenses from installed package metadata. Whisper weights and faster-whisper are MIT. Qwen2.5-1.5B-Instruct and nomic-embed-text v1.5 are Apache-2.0. The Piper voice used here is `en_US-lessac-medium`.
