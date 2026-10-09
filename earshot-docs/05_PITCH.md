# 05 · Pitch: Earshot (Demo Day, Sat Oct 10)

**One sentence:** Earshot is a private companion that listens to your day on your laptop, fully offline, and puts what matters (live captions, your name, a quick catch-up) on the screens you already own: your watch, your lock screen, your earbuds. No new app.
**Line to repeat:** "Hear what matters. Even when the cloud doesn't."
**Honesty rules:** live = live; model output never scripted; every number from `docs/bench.txt` or the live privacy panel; the watch does not vibrate (don't say it does); captions aren't perfect, say so; we never claim it's an accessibility-certified or safety product.

## Judging fit
| Criterion | Weight | Evidence |
|---|---|---|
| Problem & usefulness | 25 % | Students miss the quiz date / their name / deadlines; hard-of-hearing captions at a glance; travel announcements. Shown with a real judge's sentence |
| Local AI | 25 % | Speech recognition, alert intent, summarization, translation, recall all on the laptop; without local AI there is no product. Internet visibly cut, privacy counters at 0 |
| Technical execution | 20 % | Live captions on three surfaces from a 16 GB laptop with integrated graphics; debounce, reconnect, fallbacks; tests in repo |
| Innovation | 15 % | Uses the OS Now Playing session as a caption/alert display on any watch or lock screen, no app; one-button catch-up |
| Product & demo | 15 % | Editorial Forest design, 1-min video, clean run, 3 slides |

## Format: 5:00 + 3:00 Q&A, max 3 slides
**Slides:** (1) Problem: a lecture photo-like frame with a speech bubble "Quiz next Friday" and a student looking away. "Said once. Missed forever." (2) How it works: `mic → speech recognition (Whisper, on laptop) → alerts + summaries (Qwen 3B, on laptop) → Now Playing → watch · lock screen · earbuds`, a laptop outline around all the AI, "internet: off". (3) Close: measured numbers (caption delay p50, model sizes, 0 bytes sent) + repo URL + People's Choice QR.

## 5-minute script
| Time | Screen | Spoken |
|---|---|---|
| 0:00–0:30 HOOK | Slide 1 | "Last week my teacher announced a quiz date once, out loud, while I was looking at my notes. I missed it. Everyone has a version of this: your name gets called, the deadline moves, the gate changes." (use a true story; adjust) |
| 0:30–1:00 PROBLEM | Slide 1 | "Captions exist, but they live in one app on one screen, often need the cloud, and streaming a whole classroom's voices to a server isn't something people agreed to. I wanted something private, offline, on the screens I already wear." |
| 1:00–2:00 VIDEO | Scene 2 (silent) | — |
| 2:00–3:45 LIVE DEMO | Scene 1 | 04_DEMO_SCRIPT steps 1–7 |
| 3:45–4:15 HOW I BUILT IT | Slide 2 | "The laptop runs Whisper for speech, a 3-billion-parameter Qwen model through Ollama for alerts and summaries, Piper for voice, all offline. Each caption line becomes the Now Playing track, so anything that shows music, a Garmin, an iPhone lock screen, Windows, shows it. Raw audio stays in memory for 30 seconds and is gone. Built in 24 hours; Claude Code wrote most of the code from my specs, all disclosed." |
| 4:15–4:35 CLOSE | Slide 3 | "Hear what matters, even when the cloud doesn't. That's Earshot. Scan to vote." |
| 4:35–5:00 BUFFER | — | one more "and it also" only if it passed rehearsal |
**"And it also…" reveals (only if they passed rehearsal, in this order):** Recall with exact quote + timestamp → Tagalog→English caption → class notes with a downloadable calendar file → (Safe Word: don't demo on stage; mention only if asked).
**Cut order if long:** reveals → HOW to one line → never cut CUT INTERNET, captions, name alert, catch-up, mute.

## Why does this product benefit from running AI locally? (~120 words)
> Earshot listens to real rooms: classrooms, offices, terminals, full of other people's voices who never agreed to be streamed to a server. Running speech recognition, alerts and summaries on the laptop means raw audio never leaves it: it lives in memory for 30 seconds and is discarded, and only text is kept, with auto-expiry. Local also means it works exactly where captions are needed and the internet isn't: classrooms with weak Wi-Fi, brownouts, commutes and flights. There's no per-minute transcription cost, so it can listen all day, and latency doesn't depend on a network. Without local AI Earshot has no function at all: captions, name alerts, catch-up, translation and recall are all on-device inference.

## Judge Q&A (≤ 20 s each)
1. **Is it legal / ethical to record people?** "Earshot doesn't keep recordings: audio stays in memory for 30 seconds and is gone; only text is stored, it expires, and mute is one press. Still, you should only use it where it's allowed and ask the speaker; I asked my teacher <only if true>. In the Philippines, recording private conversations without consent is restricted by law, so the app shows a consent notice on first run." (not legal advice)
2. **How accurate is a small model?** "On my own test recordings, base.en got <measured WER> (bench.txt). It's not perfect, so alerts use fuzzy matching on names, and every summary shows the source lines it came from."
3. **Apple Live Captions already exists.** "It's great on the iPhone screen. Earshot puts captions and alerts on any Now Playing surface (a Garmin, Windows lock screen, earbuds), adds name and deadline alerts, catch-up, recall, and runs from the laptop that's already in the room."
4. **Windows 11 has Live Captions.** "Yes, on the laptop screen only, and translation needs a Copilot+ PC with an NPU. This laptop has neither; Earshot runs on integrated graphics and reaches your wrist."
5. **Why not the cloud?** "Other people's voices, bad classroom Wi-Fi, brownouts, cost per minute. The cloud is the wrong place for an always-on microphone."
6. **Hearing Buddy / XRAI / Captify glasses?** "Hearing Buddy is a phone app; XRAI and Captify need special glasses. Earshot needs no new device or app: the watch and lock screen you already have."
7. **What if the watch is slow?** "We measured it: <p50> s on the Forerunner (bench.txt). Captions are fastest on the laptop bar; the watch is for glances and alerts."
8. **Does it work in Filipino?** "Taglish transcription and Tagalog→English translation use a multilingual Whisper model; it's weaker than English and I'll show you what it gets right and wrong." (only if P6 shipped)
9. **What happens to the data?** "Text only, in a local SQLite file, auto-deleted after the period you choose; 'Delete everything' wipes it. Bytes sent to the internet: zero, measured live on the dashboard."
10. **What did you build vs AI tools?** "Architecture, button map, privacy design, prompts, alert logic and design are mine; Claude Code wrote most code from my specs. BUILDLOG has timestamps; the logo was traced from my own mark (<provenance>)."
11. **Battery?** "It's CPU work; I'll only quote a number I measured." 12. **What if no media buttons?** "The caption bar and dashboard have every control; the watch is a bonus."

## Competitors (acknowledge first)
Hearing Buddy (hearingbuddyapp.com, phone captions app) · Apple Live Captions / Live Listen (iPhone/AirPods) · Windows 11 Live Captions (translation needs a Copilot+ NPU) · XRAI Glass / Captify (caption glasses). **Our edge:** any Now Playing surface with no app, fully offline on a normal laptop, name/deadline alerts + catch-up + recall, Taglish path.

## Video (~1 min, REAL footage, filmed Sat 8:00 AM)
| # | Time | Shot | Text |
|---|---|---|---|
| 1 | 0–6 s | Classroom-style shot (Fathi at a desk), someone speaking | "Said once. Out loud." |
| 2 | 6–14 s | Garmin close-up: captions changing | "Captions on your wrist." |
| 3 | 14–22 s | Name said → ALERT on watch + laptop | "It hears your name." |
| 4 | 22–32 s | Previous → catch-up spoken (subtitle) | "Catch me up." |
| 5 | 32–38 s | Mute → everything shows MUTED | "Mute is one press." |
| 6 | 38–48 s | Wi-Fi off / privacy panel 0 bytes | "Nothing leaves the laptop." |
| 7 | 48–60 s | Lockup on forest | "Hear what matters. Offline." + repo URL |

## Social post (required)
Handles **@DevinAI** and **@cognition** (tap-check). LinkedIn: "@Cognition" page.
**X:** "Built Earshot in 24h at #AppBuildersPH: live captions, 'heard your name' alerts and a 2-line catch-up on my Garmin and lock screen. All AI runs offline on a 16 GB laptop: Whisper + Qwen 3B. Audio never leaves it. @DevinAI @cognition <repo URL>"
**LinkedIn:** "For AppBuilders PH ('AI that stays useful when the cloud disappears') I built Earshot: a private companion that listens on my laptop and puts live captions, name/deadline alerts and a spoken catch-up on screens I already own, a Garmin, my iPhone lock screen, Windows, with no new app. Speech recognition, summaries and alerts all run offline; raw audio is never saved. Models, tools and AI dev tools are disclosed in the README. Thanks @Cognition and App Builders PH. #AppBuildersPH <repo URL>"
