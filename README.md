<p align="center"><img src="design/lockup-light.svg" width="320" alt="Earshot"></p>

# Earshot

**Hear what matters. Fully offline.** Earshot turns your laptop mic into live captions
on the screens you already own — your phone, your watch's Now Playing, a caption bar —
with name/keyword alerts and a spoken catch-up. Every bit of inference runs locally
(faster-whisper + Ollama + Piper). Cut the internet and it still works.

Built for **AppBuildersPH 2026 — Local AI**. All model calls are on-device.

## Three modes
- **Captions** — *Every word, as it's said.* Live transcript in the spoken language (en / tl / ar).
- **Translate** — *Two people, two languages.* "They speak / I read", turn toggle.
- **Listen for me** — *Stays quiet. Tells you when it matters.* Only alerts + a spoken catch-up.

Plus: **name/keyword alerts** (fires on your name or your keywords, with the reason shown),
**Catch me up** (2-line local summary spoken via Piper), **Recall** (search today's transcript),
and **session notes + .ics**.

## One-line install (Windows, PowerShell)
```powershell
powershell -ExecutionPolicy Bypass -File scripts\install.ps1
```
Installs uv + Ollama, pulls the local models, downloads whisper + the Piper voice, and
adds a Start-menu **Earshot** shortcut. Then launch **Earshot** (runs the daemon + caption bar).

## Pair your phone
Run `uv run earshot serve --demo` — a **QR** is printed in the terminal and shown on
`http://127.0.0.1:7777/live`. Scan it with your iPhone (Safari) and tap **Start**. No app,
no token to copy — the page fetches its own token. Add to Home Screen for full-screen captions.

## Offline proof (measured, live)
- The only HTTP client refuses any non-local host, so **bytes to the internet = 0 by construction**.
- `HF_HUB_OFFLINE=1` — models never phone home. The `/live` privacy panel shows live
  `bytes to internet`, `internet connections` (psutil), and RAM. `earshot net cut` (admin)
  blocks the laptop's internet via Windows Firewall while the phone keeps working over the LAN.

## Measured performance (this laptop, Intel Iris Xe, CPU int8 — see `docs/bench.txt`)
- English fast tier `tiny.en`, final `base.en` (chosen by WER + latency data).
- First words ~0.8 s, final line ~1.4 s, worst (15 s run-on) ~1.8 s on synthetic clips.
- RAM (Earshot + Ollama) ~1.85 GB. qwen2.5:1.5b only, 5-min keep-alive.
- Tagalog/Arabic accuracy: **needs a live check** (no ground-truth clips).

## Privacy
Raw audio lives only in a 30-second RAM ring buffer — **never written to disk**. Text is
stored locally and auto-expires. One tap mutes the mic. Use where recording is allowed;
ask first. Not legal advice.

## Stack
faster-whisper (CTranslate2, int8 CPU) · Silero VAD · Ollama qwen2.5:1.5b + nomic-embed-text ·
Piper TTS (SAPI fallback) · FastAPI · a plain-HTML phone PWA. No cloud APIs.

## License
MIT (code). Fonts OFL. Models under their own licenses.
