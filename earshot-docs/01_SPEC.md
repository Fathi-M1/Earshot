# 01 · EARSHOT spec (v1, Fri Oct 9 6:30 PM)

> **Name is a variable.** Working name "Earshot", may become "Kinig". Code reads `BRAND = tokens.json → brand.name` (Python: `earshot/brand.py`, web: `design/tokens.json`). Never hard-code the name in UI strings, titles, tiles or the CLI help. Package/CLI name `earshot` is fine for now (rename = one search/replace + `pyproject.toml`).

**One sentence:** Earshot is a private, fully offline companion that listens to your day on your laptop and puts what matters on the screens you already own (Garmin watch, iPhone lock screen, Windows lock screen, a caption bar, earbuds) through the OS Now Playing media session, with zero new apps.
**Theme fit:** "genuinely useful when the cloud disappears." Every feature is AI (speech recognition, intent detection, summarization, translation, retrieval) and all of it runs on the laptop. Without local AI, Earshot does nothing at all, and it works with the internet cut.
**Machine:** Windows 11, Intel Iris Xe (no NVIDIA), 16 GB RAM · iPhone (Safari Media Session page served by the laptop) · Garmin Forerunner 165 (Control Phone shows iPhone Now Playing title/artist; buttons arrive as `nexttrack`/`previoustrack`/`play`/`pause`) · borrowed wired EarPods. Every latency here is a **budget to measure**, never a claim.

## 1. Users and problem (honest)
- **Students in class** (primary demo): you zone out, your name gets called, a deadline gets announced, and you missed it. Earshot captions the room on your wrist, buzzes the laptop when it hears your name or "quiz/due/deadline", and gives you a 2-line catch-up on demand.
- **Hard-of-hearing / noisy rooms:** live captions at a glance without holding a phone up.
- **Travel / commuters:** gate and station announcements while you're in earbuds.
- **Why offline matters:** classrooms and terminals with bad Wi-Fi, brownouts, no data; and the audio is other people's voices, which shouldn't be streamed to a cloud.
Claims we can make only after measuring: caption delay, word accuracy on our own test recordings, alert hit rate.

## 2. Architecture
```
 mic (WASAPI, 16 kHz mono) ─► ring buffer (RAM only, 30 s, overwritten) ─► VAD (Silero VAD onnx / energy fallback)
        │ privacy mute closes the stream instantly
        ▼
 ASR engine  (faster-whisper int8 CPU: base.en default · tiny.en fast · base multilingual for Tagalog/translate
              · optional: Moonshine (English fast path) · optional: Filipino fine-tune if Phase 0 bench allows)
        ▼ partial + committed segments
 segmenter (30–40 char caption lines, commit rules)  ──► transcript store (SQLite, text only, auto-expire)
        ├─► alerts.py   keyword + fuzzy (instant)  ─► optional LLM intent check (qwen2.5:3b / 1.5b via Ollama)
        ├─► catchup.py  last 5 min ─► LLM 2-line summary ─► Piper TTS ─► earbuds (laptop audio)
        ├─► recall.py   chunks ─► nomic-embed-text ─► SQLite vectors ─► LLM answer with exact quote
        ├─► notes.py    session end ─► notes, to-dos, deadlines ─► .ics
        └─► safeword.py (stretch, first to cut)
 surfaces:  smtc.py (Windows lock screen + media keys) · caption bar (Tk topmost overlay, PRIMARY)
            · phone page web/index.html over LAN ─► iPhone lock screen ─► Garmin · dashboard (web, 127.0.0.1)
 privacy.py: network proof (bytes to internet, internet connections, probe) · cut-internet toggle (firewall)
```
Daemon: FastAPI `127.0.0.1:7777` (dashboard, API), phone server `0.0.0.0:7778` (LAN only, token). Ollama `127.0.0.1:11434`.

## 3. Components

### 3.1 Audio + VAD (`audio.py`)
`sounddevice.InputStream(samplerate=16000, channels=1, dtype="float32", blocksize=480)` (30 ms). Ring buffer 30 s in RAM (numpy), overwritten; **raw audio is never written to disk** (no WAV files, no temp files; tests assert no audio files appear). VAD: Silero VAD (onnx, via `faster-whisper`'s bundled VAD or `silero-vad` package) with 300 ms min speech / 500 ms min silence; fallback RMS energy gate. Device selection in settings (laptop mic default; a USB mic is better in a classroom; note which one you tested).

### 3.2 ASR (`asr.py`)
- **Default:** `faster-whisper` `WhisperModel("base.en", device="cpu", compute_type="int8", cpu_threads=4)`; `beam_size=1`, `vad_filter=False` (we VAD ourselves), `condition_on_previous_text=False` (stops hallucination loops), `no_speech_threshold=0.6`, `initial_prompt` = names + course terms from settings (biases spelling of "Fathi", "midterm", subject names).
- **Streaming strategy:** while speech is active, re-transcribe the current utterance window (≤ 12 s) every **1.5 s** → *partial* (laptop bar only). On VAD end-of-speech (or 12 s cap) → *commit* the final text for that utterance. Simple, robust, CPU-bounded.
- **Fast path:** `tiny.en` if Phase 0 shows base.en can't keep up (real-time factor > 0.5 on this CPU). Moonshine (English, onnx) = optional A/B in Phase 0 only (15-min cap).
- **Tagalog / Taglish + Translate (P5):** multilingual `base` (or `small` if the bench allows) with `language="tl"` for transcription or `task="translate"` for English captions. Honest: whisper base/small Tagalog accuracy is limited; we'll show measured examples. Optional Filipino fine-tune (e.g. a whisper-small fine-tune on Hugging Face such as the `sapinsapin/whisper-small-fsc` the team found ⚠️ verify it exists, its license and whether it converts with `ct2-transformers-converter`; download while online in Phase 0; skip if it takes > 20 min).
- **Alternative engine (fallback if faster-whisper misbehaves on Windows):** whisper.cpp release binaries (`whisper-server.exe` HTTP, or `whisper-stream.exe` with SDL2) + `ggml-base.en.bin`; `asr.py` keeps one interface `transcribe(window) -> Segment[]`.
- CPU contention: ASR has priority. Ollama calls run with `num_thread: 2`, max 1 in flight, and are skipped (fallback used) if ASR lag > 3 s.

### 3.3 Segmenter → caption lines (`captions.py`)
- Lines are **30–40 characters**, split at word boundaries, punctuation-aware; long words never cut.
- **Watch/lock screen** get only **committed** text, max **one metadata update per 1.5 s** (configurable 1–2 s; Phase 0 Garmin result may raise it), coalescing: newest line wins. `title` = current line, `artist` = previous line, `album` = `"{BRAND} · {room/mode}"`, artwork = state tile.
- **Laptop caption bar** gets partials + committed (2 lines, previous line muted).
- Profanity/odd hallucinations: drop known whisper hallucination strings ("Thank you.", "Thanks for watching!", "[BLANK_AUDIO]", "you") when they're the whole segment.

### 3.4 Alerts (`alerts.py`) — "heard your name"
1. **Deterministic, instant:** keyword list from settings (your name + nicknames + "Mr./Ms. <surname>", "quiz", "exam", "due", "deadline", "submit", "assignment", "attendance", "gate", "boarding", "final call", station names), normalized (lowercase, strip punctuation, Tagalog particles), matched with `rapidfuzz.fuzz.partial_ratio ≥ 88` on token windows + a phonetic key (Double Metaphone via `jellyfish`) for names ASR misspells ("Fati", "Fatty" → Fathi; tune and test, beware false hits).
2. **LLM intent (optional upgrade, P2b):** only when a committed sentence contains a cue word (pre-filter) and at most 1 call / 8 s: Ollama `qwen2.5:1.5b` (or 3b if bench allows), schema `alert_intent` (§4.1), timeout **4 s**; on timeout the keyword result stands.
3. **Output:** state ALERT, track title = the matching line (≤ 40 chars, the keyword kept in view), artist = alert type ("Your name", "Deadline", "Quiz", "Boarding"), laptop chime (local WAV), caption bar flashes once (no animation loops). Cooldown 20 s per keyword. Alerts logged with timestamp.
- The Garmin does **not** vibrate on a title change; the alert reaches you via the watch screen if you look, the laptop chime, and Piper in the earbuds (if worn). Never claim the watch buzzes.

### 3.5 Catch me up (`catchup.py`)
Trigger (see §5). Input: committed transcript of the last **5 min** (cap ~900 words, newest kept). Ollama `qwen2.5:3b`, schema `catchup` (§4.2), `temperature 0`, `num_predict 120`, timeout **12 s** (target p50 ≤ 8 s, measure). Output spoken by Piper ("In the last five minutes: …") into the earbuds, track title = line 1, artist = line 2, state CATCH_UP. **Fallback** (timeout/Ollama down): extractive: the last 2 alert/keyword lines + the last committed line, labeled "quick recap (no summary)". Never invent: the prompt forbids facts not in the transcript; the dashboard shows the source lines under the summary.

### 3.6 Translate (`asr.py` mode, P5)
Mode switch (dashboard/settings): `en` (base.en) · `tl→en` (multilingual model, `task="translate"`) · `tl` (transcribe Tagalog). Caption bar shows a small `TL→EN` badge. Honest about quality; demo only with a sentence we tested.

### 3.7 Recall (`recall.py`, P6)
Committed text grouped into ~60 s chunks with start/end timestamps → `POST /api/embed {"model":"nomic-embed-text","input":"search_document: …"}` → SQLite `chunks(id, session, t0, t1, text, emb BLOB)`. Query (typed in the dashboard, or push-to-talk on the laptop: hold `F9`/dashboard mic, transcribed by the same ASR) → `search_query:` embedding → cosine top 5 (+ keyword boost) → Ollama `qwen2.5:3b` schema `recall` (§4.3). **The quote must be an exact substring of a retrieved chunk** (validated); otherwise show "not found" + the top chunk. Answer shows timestamp + "jump to transcript".

### 3.8 Class notes + .ics (`notes.py`, P7)
On "End session": map (per ~1 200-token chunk → bullets) then reduce (schema `notes`, §4.4). Dates: the model returns the phrase ("next Friday", "Oct 17"); **dates are resolved deterministically** with `dateparser` (offline, `RELATIVE_BASE` = session date, `PREFER_DATES_FROM="future"`); unresolved → listed as "date unclear", not in the .ics. `.ics` written by hand (RFC 5545, `VEVENT` per deadline, all-day, `DESCRIPTION` = quote + timestamp). Saved to `%USERPROFILE%\Documents\{BRAND}\notes\<date>-<session>.md|.ics`.

### 3.9 Buttons + debounce (`buttons.py`)
See §5. Debounce/reconnect rules carried over from the earlier (verified Oct 8) spec:
- Ignore a repeat of the **same action within 500 ms** (all sources; duplicates observed ~0.2 s apart).
- After any action, ignore that same action for **1.5 s** (so a double fire can't bookmark twice / trigger two catch-ups).
- Drop any button event older than **3 s** (never replay queued actions).
- Phone page client: **one reconnect in flight**, exponential backoff (0.5 → 8 s), **never queue log events**; on reconnect send one state-resync request only. Server drops duplicate log lines. After a server restart the phone may flush a backlog of `sse/ws-reconnect` logs; ignore them.

### 3.10 Privacy (`privacy.py`)
- **Audio:** RAM ring buffer only, discarded; never written to disk. **Text:** SQLite in `%LOCALAPPDATA%\{BRAND}\`, auto-expire setting (default **24 h**; options 1 h / 24 h / 7 days / keep), "Delete everything" button.
- **Privacy mute:** closes the mic stream within 100 ms (measured), state MUTED on every surface, caption bar shows "Muted · not listening", the phone page and the dashboard both show it. Mic indicator: Windows shows its own mic-in-use icon; we rely on that plus our state.
- **Network proof (real, measured):** (a) `Bytes {BRAND} sent to the internet` = counter in `localclient.py`, the only HTTP client in the app, which refuses non-loopback/non-private hosts (true 0 by construction, unit-tested); (b) `Internet connections open by {BRAND} + Ollama` = sampled every 2 s from `psutil.net_connections()` filtered by our PIDs and the Ollama PID(s), counting remote addresses that are not private/loopback (should be 0); (c) `Internet reachable` = TCP probe to `1.1.1.1:443` and `8.8.8.8:53` (400 ms timeout) every 5 s. Shown on the dashboard privacy panel. No other number is shown.
- Set `OLLAMA_NO_CLOUD=1` ⚠️ verify the variable name in the installed Ollama version (`ollama serve` logs list env vars); never use Ollama cloud models.
- Consent: first-run screen + README "Use it where recording is allowed. Ask the speaker (e.g. your teacher) first. Mute is one press." (see 08 risk on the Philippine Anti-Wiretapping Act). Not legal advice.

### 3.11 Offline network + cut-internet toggle (`netcut.py`)
**Demo topology:** iPhone Personal Hotspot ON; laptop joins it (subnet `172.20.10.0/28`, gateway `172.20.10.1`). The iPhone is the remote; the **laptop** gets no internet via Windows Firewall block rules that leave the hotspot LAN working. (Honest framing: "the laptop is offline; the phone is only a remote screen".)
Admin PowerShell (also `scripts\cut-internet.ps1` / `scripts\restore-internet.ps1`):
```powershell
# CUT: block every non-private IPv4 destination, all global IPv6, and DNS via the hotspot
$v4 = "1.0.0.0-9.255.255.255","11.0.0.0-126.255.255.255","128.0.0.0-169.253.255.255","169.255.0.0-172.15.255.255","172.32.0.0-192.167.255.255","192.169.0.0-223.255.255.255"
New-NetFirewallRule -Group "EarshotOffline" -DisplayName "Earshot offline: block internet IPv4" -Direction Outbound -Action Block -RemoteAddress $v4 -Profile Any
New-NetFirewallRule -Group "EarshotOffline" -DisplayName "Earshot offline: block internet IPv6" -Direction Outbound -Action Block -RemoteAddress "2000::-3fff:ffff:ffff:ffff:ffff:ffff:ffff:ffff" -Profile Any
New-NetFirewallRule -Group "EarshotOffline" -DisplayName "Earshot offline: block DNS via hotspot UDP" -Direction Outbound -Action Block -Protocol UDP -RemotePort 53 -RemoteAddress "172.20.10.1" -Profile Any
New-NetFirewallRule -Group "EarshotOffline" -DisplayName "Earshot offline: block DNS via hotspot TCP" -Direction Outbound -Action Block -Protocol TCP -RemotePort 53 -RemoteAddress "172.20.10.1" -Profile Any
Get-NetFirewallProfile | Select Name, Enabled          # all must be True, or rules do nothing
Test-NetConnection 1.1.1.1 -Port 443                    # expect TcpTestSucceeded : False
# RESTORE
Remove-NetFirewallRule -Group "EarshotOffline"
```
Block rules beat allow rules in Windows Firewall, and private ranges (incl. `172.16.0.0/12` → hotspot) stay reachable, so the iPhone still loads `http://172.20.10.x:7778`.
- **Toggle:** `earshot net cut|restore|status` and a dashboard switch "Cut internet". It needs an **elevated** daemon (start `earshot serve` from an admin PowerShell for the demo); if not elevated, the switch is disabled with "Run as admin, or run scripts\cut-internet.ps1". `restore` also runs on `earshot serve` exit (so you never leave the laptop cut off), and `earshot net status` lists the rules.
- **Live proof on stage:** dashboard "Internet reachable: no", counters at 0, plus a browser tab failing to load `https://example.com` (real failure).
- **Fallback A:** laptop airplane mode (Wi-Fi off): caption bar + Windows lock screen (SMTC) + EarPods on the laptop. iPhone/Garmin unavailable; say so.
- **Fallback B:** backup recording of the full demo.
- Alternative LAN (if Phase 0 shows the iPhone hotspot is flaky): Android phone hotspot with mobile data off, or a pocket router with no WAN.

### 3.12 Surfaces
- **SMTC** (`smtc.py`, Python winrt 3.2.1, MediaPlayer + looping silent WAV, `command_manager.is_enabled=False`): title/artist/album/thumbnail; ButtonPressed → `buttons.py` (source `smtc`). Media keys and EarPods inline remote (when plugged into the laptop) arrive here; verify which EarPods presses Windows maps (single = play/pause; double/triple may not map on Windows: test).
- **Phone page** `web/index.html` (plain HTML, normal Safari tab, not Home Screen; WebKit 295518): START tap → `new Audio()` silent finite file `loop=true`, never change `src`; handlers only `play`, `pause`, `nexttrack`, `previoustrack` (**no seek handlers**: they replace next/prev); `navigator.mediaSession.metadata` updated from WS; `playbackState` mirrors LISTENING (`playing`) / MUTED (`paused`); 512 px artwork per state; WS `/ws/phone?t=<token>` with backoff + resync on `visibilitychange`; "Tap to resume" screen if audio stopped. `audioSession.type='playback'` if present.
- **Garmin FR165:** zero code; Control Phone mirrors iPhone Now Playing.
- **Caption bar** (`bar.py`): Tkinter borderless topmost window, bottom-center, 2 lines, Host Grotesk registered at runtime (`AddFontResourceExW`), colors from tokens, draggable, click-through off; shows state + `0 bytes sent`. Primary surface (always works, even in airplane mode).
- **Dashboard** (`web/dashboard`, served on 127.0.0.1): live transcript, alerts, bookmarks, recall search, notes, privacy panel. See 02_DESIGN.

### 3.13 Safe Word (`safeword.py`, LAST stretch, FIRST to cut)
- Settings: a personal **code phrase** (recommended: an unusual phrase, e.g. two unrelated words) + optional threat words ("hold-up", "akin na"). ⚠️ "akin na" is everyday Tagalog ("give it to me") and "hold up" is common English: they'll false-trigger; off by default, code phrase on.
- On match: save the **last 2 min of transcript text** (committed lines with timestamps, from the in-memory buffer) to `%LOCALAPPDATA%\{BRAND}\evidence\<iso-time>.txt` + a SHA-256 of the file in `evidence.log` (tamper-evidence, not legal proof). Watch/lock screen title: `Saved. Alert ready`, artist: time. Nothing is sent while offline.
- When the internet is back (probe), a track appears: `Send alert to <contact>?`. **Only Next confirms** (dashboard button also works); Previous dismisses. Then one pre-written message goes to **one** trusted contact via a secondary cloud channel (Telegram Bot API with a token stored locally, or SMTP), text: "<name> triggered their safe word at <time>. Last known place: <user-entered note>." No location tracking, no emergency services, no auto-send.
- Honest limit (README + pitch if shown): it's laptop-based, not a phone safety app; if the laptop is taken or closed, nothing happens.

## 4. Prompts + JSON schemas (Ollama `/api/chat`, `stream:false`, `format:<schema>`, `keep_alive:-1`, `options:{temperature:0, seed:7, num_thread:2}`)
All prompts in `earshot/prompts/*.md`; validated with pydantic; one retry only if budget remains; else fallback.

### 4.1 `alert_intent` (qwen2.5:1.5b, 4 s)
System: "You check one transcribed sentence from a class or public announcement for something the listener must act on. Reply JSON only. alert=true only for: the listener's name being called ({names}), a quiz/exam/test, a deadline or due date, a submission, attendance, a boarding/gate/platform announcement. title: the key words, max 40 characters, copied from the sentence. Never invent."
```json
{"type":"object","properties":{"alert":{"type":"boolean"},"type":{"type":"string","enum":["name","quiz","deadline","submission","attendance","travel","none"]},"title":{"type":"string","maxLength":40}},"required":["alert","type","title"]}
```
### 4.2 `catchup` (qwen2.5:3b, 12 s)
System: "Summarize what the listener missed in exactly two short lines, max 60 characters each, plain words, using only facts in the transcript. Mention deadlines, names and numbers exactly as said. If nothing important was said, say so."
```json
{"type":"object","properties":{"line1":{"type":"string","maxLength":60},"line2":{"type":"string","maxLength":60},"important":{"type":"boolean"}},"required":["line1","line2","important"]}
```
### 4.3 `recall` (qwen2.5:3b, 12 s)
System: "Answer the question using only the transcript excerpts. Copy the supporting quote exactly from one excerpt and give its excerpt id. If the answer isn't there, found=false."
```json
{"type":"object","properties":{"found":{"type":"boolean"},"answer":{"type":"string","maxLength":160},"quote":{"type":"string","maxLength":240},"excerpt_id":{"type":"integer"}},"required":["found","answer","quote","excerpt_id"]}
```
Validation: `quote in chunks[excerpt_id].text` (after whitespace normalization) else treat as not found.
### 4.4 `notes` (qwen2.5:3b, 30 s per call)
```json
{"type":"object","properties":{"summary":{"type":"array","items":{"type":"string","maxLength":120},"maxItems":6},
"todos":{"type":"array","items":{"type":"string","maxLength":100},"maxItems":8},
"deadlines":{"type":"array","items":{"type":"object","properties":{"what":{"type":"string"},"when_text":{"type":"string"},"quote":{"type":"string"}},"required":["what","when_text","quote"]},"maxItems":6}},
"required":["summary","todos","deadlines"]}
```

## 5. Button map (recommended; see 08 R-B7 for why it differs from the first draft)
The watch/phone have **one** play/pause toggle: iOS sends `pause` while playing and `play` while paused, so "Play" and "Pause" can't be two separate features. Recommended map:
| Button | While LISTENING | While MUTED |
|---|---|---|
| **Play/Pause** (one toggle) | `pause` → **Privacy mute** (mic closed instantly) | `play` → resume listening |
| **Next** | **Bookmark** this moment (last 30 s saved, title `Bookmarked 09:41`) | — |
| **Previous** | **Catch me up** (2-line summary spoken); a 2nd Previous within 10 s = **replay the last line** aloud | — |
| Laptop / dashboard | buttons for all of the above + Recall + End session | |
*Alternative if Fathi prefers the first draft (Play = catch me up):* keep `playbackState` always `playing` so the toggle always sends `pause` = catch me up; then mute lives only on the caption bar, dashboard, phone page and the media-key `Stop`/hotkey. Decide in Phase 0 after trying both on the Garmin.

## 6. States (02_DESIGN tiles)
`LISTENING ◉` · `ALERT ◆` · `CATCH_UP ▶` · `MUTED ‖` · `OFFLINE □` (shown as the tile when the internet is cut and listening continues: "Offline · all local") · plus non-tile UI states: `STARTING` (models loading), `MIC_ERROR` (clay band, caption bar only).

## 7. APIs
| Method | Path | Purpose |
|---|---|---|
| WS | `/ws` (dashboard) · `:7778/ws/phone?t=` | push `caption`, `state`, `alert`, `track`, `proof`; client sends `button` |
| POST | `/button` | `{action:"next|previous|play|pause", source:"smtc|iphone|dashboard|bar|cli", ts}` |
| POST | `/mute` · `/unmute` · `/catchup` · `/bookmark` · `/replay` | same paths as buttons |
| POST | `/recall` `{q}` · `/session/end` · `/net/cut` · `/net/restore` | features |
| GET | `/state` · `/transcript?since=` · `/alerts` · `/bookmarks` · `/notes/<id>` · `/proof` · `/health` | snapshots |
Phone server exposes only the page, artwork, phone WS.

## 8. Install (Windows PowerShell; do all downloads while online, then verify offline)
```powershell
winget install --id Ollama.Ollama -e
ollama pull qwen2.5:3b ; ollama pull qwen2.5:1.5b ; ollama pull nomic-embed-text
[Environment]::SetEnvironmentVariable("OLLAMA_KEEP_ALIVE","-1","User")
[Environment]::SetEnvironmentVariable("OLLAMA_NUM_PARALLEL","1","User")
uv init earshot ; cd earshot
uv add fastapi uvicorn httpx pydantic numpy sounddevice faster-whisper rapidfuzz jellyfish dateparser psutil pillow "winrt-runtime==3.2.1" "winrt-Windows.Media==3.2.1" "winrt-Windows.Media.Playback==3.2.1" "winrt-Windows.Media.Core==3.2.1" "winrt-Windows.Storage==3.2.1" "winrt-Windows.Storage.Streams==3.2.1" "winrt-Windows.Foundation==3.2.1" "winrt-Windows.Foundation.Collections==3.2.1"
# Pre-download ASR models into .\models (offline later)
uv run python -c "from faster_whisper import WhisperModel as W; [W(m, device='cpu', compute_type='int8', download_root='models/whisper') for m in ['tiny.en','base.en','base']]"
# Piper TTS: wheel first, then binary, then SAPI
uv add "piper-tts==1.3.0" ; uv run python -m piper.download_voices en_US-lessac-medium --data-dir models\piper
#   fallback: piper_windows_amd64.zip from github.com/rhasspy/piper/releases → models\piper\piper.exe (subprocess)
#   last resort: uv add pyttsx3  (Windows SAPI, still local)
# whisper.cpp fallback engine: download the Windows x64 release zip from github.com/ggml-org/whisper.cpp/releases
#   + models: ggml-base.en.bin (huggingface.co/ggerganov/whisper.cpp) into models\whispercpp
# Optional: Moonshine (uv add useful-moonshine-onnx ⚠️ verify package name) · Filipino fine-tune (verify on HF, convert with ct2-transformers-converter)
```

## 9. Performance budget (Iris Xe / 16 GB; verify in Phase 0, log in docs/bench.txt)
| Item | Budget | If missed |
|---|---|---|
| ASR real-time factor (base.en int8, 4 threads) | ≤ 0.5 | tiny.en |
| End of speech → caption on laptop bar | ≤ 1.5 s | shorter window, tiny.en |
| End of speech → title on iPhone lock screen | ≤ 2.5 s | — |
| → title on Garmin | **measure in Phase 0** (go/no-go) | see 03 Phase 0 decision |
| Keyword alert → chime | ≤ 300 ms after commit | — |
| LLM alert intent | ≤ 4 s or skipped | keywords only |
| Catch-up (summary + first word of speech) | ≤ 12 s, target 8 s | extractive recap |
| Recall answer | ≤ 12 s | top chunk only |
| Mute → mic closed | ≤ 100 ms | bug |
| RAM: base.en (~0.3 GB) + qwen2.5:3b (~2.5 GB) + 1.5b (~1.2 GB) + nomic (~0.3 GB) | < 6 GB | unload 1.5b, use 3b for both |
Plugged in, "Best performance" power mode, close browsers. Measure CPU % during captions + catch-up (contention).

## 10. Tests
pytest (no devices/models): segmenter (line lengths, word boundaries, 1.5 s throttle, title/artist roll), hallucination filter, keyword + fuzzy + phonetic matcher (table incl. misspellings + false-positive guards), debounce (500 ms dupes, 1.5 s lockout, 3 s stale), button map per state, recall quote validation, dateparser resolution table, .ics validity (parse back with `icalendar` in tests only), privacy: no audio files written (temp dir scan), `localclient` refuses public hosts and counts 0, net-cut rule builder produces the exact commands, auto-expire deletes, Ollama fake (`respx`) slow/invalid/down → fallbacks. Real-model tests `-m models`. **Accuracy check (P2+):** 5 short recordings Fathi makes on build day (reading a known script) → WER computed with `jiwer` → `docs/bench.txt`. Only measured numbers.

## 11. Safety + honesty (non-negotiable)
No raw audio on disk. No network calls from the core. Mute always works and always shows. Never claim the watch vibrates. Never show unmeasured numbers. Never script or pre-record model output for the live demo. Safe Word never sends anything without an explicit Next while online.
