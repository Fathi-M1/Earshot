# 08 · Risk register (ruthless loophole audit)
Severity: **H** = can lose the demo or get disqualified · **M** = costs points · **L** = nice to fix.

| # | Risk / loophole | Sev | Fix | Phase | Status |
|---|---|---|---|---|---|
| 1 | Garmin updates Now Playing too slowly (or truncates title) → captions on the watch look broken | H | Measure first hour; decision table in 07; watch shows alerts/catch-up only if slow; the caption bar is the primary surface | P0 | open |
| 2 | iOS suspends the Safari page / media session dies on lock | H | silent loop audio, keep tab foreground before locking, WS resync on wake, re-tap Start in demo setup; fallback SMTC + bar | P0–P3 | open |
| 3 | CPU contention: Whisper + Qwen on Iris Xe/16 GB lags captions | H | ASR priority, LLM num_thread 2, one LLM call at a time, 1.5b for intent, prewarm, extractive fallback | P0/P4 | open |
| 4 | "Is the laptop really offline? The phone has internet." | H | Firewall cut (only LAN allowed, DNS to hotspot blocked), failed website load live, bytes-sent counter, airplane-mode fallback; say the phone is just a screen | P3 | open |
| 5 | Recording other people / consent (RA 4200; judges ask) | H | No audio on disk, text only, auto-expire, one-press mute, first-run consent notice, ask the teacher; say "not legal advice" | P3 | open |
| 6 | Whisper hallucinations in silence/noise ("Thank you for watching") | M | VAD gate, no_speech/logprob thresholds, blacklist, condition_on_previous_text False | P1 | open |
| 7 | Name alert misses / false alerts (accent, Taglish) | M | fuzzy + Double Metaphone, initial_prompt with names, cooldown, measured hit/false rate, honest numbers | P2 | open |
| 8 | Loud venue → bad captions on stage | H | close mic/USB mic, sound check, judge speaks into mic; recorded-input fallback announced as such | demo | open |
| 9 | Pre-existing work / external help DQ (docs + brand kit + logo made before build) | H | Disclose in README: docs/brand prepared before, code all written in window, BUILDLOG + commit timestamps, Oct 8 spikes not reused; confirm logo is Fathi's own | README | open |
| 10 | Fake/unmeasured numbers on slides or README | H | Only `bench.txt` numbers; blanks otherwise; mock image labelled illustrative and never used as a real screenshot | all | open |
| 11 | Firewall toggle needs admin; profile disabled; rule left on after demo | M | admin PowerShell, `doctor` checks profiles, restore in finally/atexit + restore script | P3 | open |
| 12 | "Apple/Windows Live Captions already do this" | M | Edge: any Now Playing surface without an app, name alerts, catch-up, recall, offline on a normal laptop; acknowledge competitors first | pitch | open |
| 13 | Claiming the watch vibrates on alert | M | Never claim; laptop chime + watch title change only | all | open |
| 14 | Play/Pause arrives as a single toggle (can't map 4 distinct buttons) | M | Use recommended map (01 §5); decide in P0 from real events | P0 | open |
| 15 | Model downloads slow / fail Friday night | M | start downloads at 7 PM; tiny.en + 1.5b fallbacks; keep installers on disk | P0 | open |
| 16 | Tagalog/Filipino model weak or the HF model unavailable/unlicensed | M | Treat Filipino as stretch; check model card/license before use; honest demo | P6 | open |
| 17 | Safe Word false triggers / implied safety device | M | code phrase only by default, threat words opt-in, nothing auto-sent, Next confirmation, "not an emergency service", laptop-based; first to cut | P9 | open |
| 18 | Piper on Windows install pain | L | piper-tts==1.3.0 → binary → pyttsx3 SAPI | P4 | open |
| 19 | EarPods inline buttons on Windows unreliable | L | Don't depend on them; Garmin/phone/keyboard controls | P3 | open |
| 20 | Phone page reachable by anyone on the LAN | L | random token in URL, bind phone server only to hotspot interface if easy | P1 | open |
| 21 | Ollama cloud features / telemetry accidentally used | M | only local model tags (no `-cloud`), `localclient` blocks non-local hosts, firewall cut proves it | P0 | open |
| 22 | Battery/thermal throttling during pitch | L | plug in, High performance plan, prewarm, close other apps | demo | open |
| 23 | Finalist pitching collides with 5 PM midterm | M | ask organisers for an early slot at registration; know the leave-by time | Sat | open |
| 24 | Secrets/tokens or the transcript DB committed to public repo | M | .gitignore models/, *.db, .env; `git ls-files` check before making public | submit | open |
| 25 | Name change Earshot→Kinig late breaks UI | L | name only in tokens.json/brand.py; rename script in design/_src/README | any | open |
