# 03 · Build plan: Fri Oct 9 7:00 PM → Sat Oct 10 10:00 AM PHT (deadline, no extensions)

**North star (check at every cutoff):** internet cut → someone speaks → caption on the laptop bar, iPhone lock screen and Garmin → your name is said → ALERT + chime → Previous → 2-line catch-up in the EarPods → Play/Pause mutes instantly.
**Rules:** hard cutoffs; at a cutoff take the FALLBACK, commit (`pN: <what>`), BUILDLOG line, move on. Feature freeze **6:45 AM**. Video **8:00 AM**. Submit **9:15 AM**.

## Before 7:00 PM (now)
- [ ] Start downloads (01 §8): Ollama + `qwen2.5:3b`, `qwen2.5:1.5b`, `nomic-embed-text`; faster-whisper `tiny.en`, `base.en`, `base`; Piper voice. On PH internet this can take a while, so start now.
- [ ] `mkdir C:\dev\earshot; git init`, copy docs into `docs\`, CLAUDE.md to root, paste 00_KICKOFF_PROMPT into Claude Code.
- [ ] Charge Garmin + iPhone, find a phone stand/stopwatch app for the Garmin latency test.

## Timeline
| Phase | Window | Hard cutoff | Done = | Fallback / decision |
|---|---|---|---|---|
| **P0 Go/no-go** | 7:00–8:00 PM | **8:00 PM** | (a) **Garmin refresh test**: minimal daemon + phone page pushes a counter title every 2 s; film watch + laptop screen at 60 fps, 20 samples → p50/p95 delay; same for iPhone lock screen. (b) **ASR bench**: tiny.en / base.en / base on 3 recordings → RTF + rough WER. (c) Ollama 3b/1.5b tokens/s. (d) iPhone hotspot + firewall cut: phone page still loads, `Test-NetConnection 1.1.1.1 -Port 443` fails. (e) try both button maps on the Garmin | **Garmin p50 ≤ 3 s → live captions on watch.** 3–8 s → watch shows only alerts, catch-up and state (captions stay on laptop bar + iPhone). > 8 s or flaky → watch = buttons + alerts only. ASR: pick the biggest model with RTF ≤ 0.5. Write all numbers to `docs/bench.txt` |
| **P1 Captions core** | 8:00–10:00 PM | **10:15 PM** | mic → VAD → faster-whisper partial/commit → segmenter → caption bar (Tk) + SMTC + phone page/Garmin; hallucination filter; debounce + reconnect rules; mute closes the mic | tiny.en; bar + SMTC only |
| dinner (eat while P1 tests run) | ~9:00 PM | | | |
| **P2 Alerts** | 10:15–11:15 PM | **11:30 PM** ★ | keyword + fuzzy + phonetic alerts → ALERT track + chime + bar flash, cooldown; **offline pass**: everything above works with the internet cut, on the watch (or per P0 decision) | keywords only (no LLM) |
| **P3 Buttons + privacy + net toggle** | 11:30 PM–12:30 AM | **12:45 AM** | Next bookmark, Previous catch-up/replay, toggle mute; `earshot net cut/restore` + dashboard switch (elevated); privacy panel counters (bytes to internet, internet connections, reachability); auto-expire; consent first-run screen | CLI scripts instead of toggle |
| **P4 Catch-up + Piper** | 12:45–1:45 AM | **2:00 AM** | qwen2.5:3b 2-line summary ≤ 12 s, extractive fallback, Piper into EarPods (laptop), replay last line; LLM alert intent (pre-filtered) if CPU allows | SAPI voice; extractive only |
| **P5 Dashboard** | 2:00–2:45 AM | **3:00 AM** | live transcript, alerts, bookmarks, privacy panel per 02_DESIGN §11 (plain but on-brand) | phone-page CSS dashboard |
| **Sleep** | 3:00–5:45 AM | | alarm 5:45 | if P2 not passed: sleep 1.5 h max |
| **P6 Translate** | 5:45–6:15 AM | **6:15 AM** | `tl→en` mode with multilingual base; tested on 3 real sentences | cut, mention as next |
| **P7 Recall** | 6:15–6:45 AM | **6:45 AM** FEATURE FREEZE | embeddings + search + quote-validated answer | cut |
| (P8 Class notes + .ics, P9 Safe Word) | only if P6–P7 finished early | 6:45 AM | | cut (roadmap line) |
| Rehearse ×3 + backup recording | 6:45–7:30 AM | | 04_DEMO_SCRIPT 3× offline, timed; record the best run | |
| README + disclosures + screenshots + fresh clone | 7:30–8:00 AM | **8:00 AM code freeze (internal)** | 06 template, hardware tested, `pytest` green | |
| Video + post | 8:00–9:00 AM | 9:00 AM | ~1 min video, X/LinkedIn post (@DevinAI @cognition #AppBuildersPH) | screen-only video |
| Submit | 9:00–9:15 AM | **9:15 AM** (deadline 10:00) | repo public (check logged out), form once, screenshot | |
| Leave for Cyberzone | ~10:30 AM | on site 12:00 PM | 07 bag list | |
★ = after 11:30 PM there must always be a working offline demo of captions + alerts.

## Cut order (cut from the bottom of the reveal list first)
1. **Safe Word** (P9) → 2. Class notes + .ics (P8) → 3. Recall (P7) → 4. Translate (P6) → 5. LLM alert intent (keywords stay) → 6. dashboard polish (privacy panel stays) → 7. Moonshine / Filipino model experiments.
**Never cut:** live captions, name alerts, privacy mute, catch-up (extractive fallback is fine), the offline proof, disclosures, the 9:15 AM submission.
