# 07 · Test checklist (tick in order; record real numbers in docs/bench.txt)

## Phase 0 · go/no-go (by 8:00 PM)
- [ ] Garmin refresh: title changes every 2 s; film the watch + laptop clock at 60 fps; 20 samples → p50/p90 delay: ____ / ____ s. Decision: ≤3 s live captions on watch · 3–8 s alerts/catch-up only · >8 s buttons + alerts only (captions on bar/iPhone).
- [ ] Same for iPhone lock screen: ____ / ____ s; Windows lock screen (SMTC): ____ s.
- [ ] Buttons from Garmin: which actions arrive (play/pause/toggle/next/previous)? Duplicates? ____ → pick button map (01 §5).
- [ ] ASR RTF on 5 own WAVs: tiny.en ____ base.en ____ base ____ (pass ≤ 0.5). WER base.en ____.
- [ ] Ollama tok/s qwen2.5:3b ____ 1.5b ____; catch-up prompt end-to-end ____ s (pass ≤ 12 s).
- [ ] Hotspot: laptop + iPhone; phone page loads at `172.20.10.x:7778`.
- [ ] `cut-internet.ps1` (admin): `Test-NetConnection 1.1.1.1 -Port 443` = False; browser to example.com fails; phone page still works; `restore-internet.ps1` brings internet back. Profiles enabled (`Get-NetFirewallProfile`).

## P1 captions
- [ ] Speak 60 s: bar shows partials ≤ 2 s behind; committed lines 30–40 chars; watch ≤ 1 update / 1.5 s.
- [ ] Silence 60 s: no hallucinated lines ("Thank you." etc. filtered).
- [ ] No `.wav`/audio files created anywhere (`Get-ChildItem -Recurse -Include *.wav,*.pcm,*.mp3 $env:LOCALAPPDATA\Earshot, .`).
- [ ] CPU stays < ~80 % sustained during captions (Task Manager), note value.

## P2 alerts ★ offline pass
- [ ] Name said 10 times by 2 voices: hits ____/10; false alerts in 10 min of other talk: ____.
- [ ] Misspelled/accented variants (Fati, Fatty?) behaviour noted.
- [ ] Alert shows on bar + iPhone + watch title + chime; cooldown 20 s works.
- [ ] **Wi-Fi off entirely** (airplane mode): captions + alerts still work on the bar + Windows lock screen.

## P3 buttons + privacy + net toggle
- [ ] Each Garmin button → correct action once (press 10×, count): ____.
- [ ] Double events ≤ 500 ms ignored; reconnect after locking phone 2 min: no burst of old actions.
- [ ] Mute: mic released (Windows mic indicator off), MUTED on all surfaces, nothing transcribed.
- [ ] Privacy panel: bytes sent to internet 0 during 10 min; connections list shows only loopback/LAN.
- [ ] Dashboard Cut internet toggle = same result as the script; restore on Ctrl+C/exit verified.

## P4 catch-up
- [ ] Previous → spoken 2 lines in EarPods ≤ 12 s warm; lines reflect the last 5 min (check against transcript); extractive fallback when Ollama stopped.

## P5–P9 (only if reached)
- [ ] Dashboard: live transcript, alerts, bookmarks, privacy, wipe works (`earshot wipe` → DB empty).
- [ ] Translate: 5 Tagalog sentences → English; note quality honestly.
- [ ] Recall: 5 questions → exact quote + timestamp; a question with no answer → "Not found".
- [ ] Notes: .ics opens in Windows Calendar with right date.
- [ ] Safe Word: code phrase → "Saved. Alert ready", evidence file with SHA-256; offline → nothing sent; online → Next required; 10 min normal talk → no false trigger.
- [ ] Auto-expire: set 1 min → old text deleted.

## Rehearsal (Sat 6:45 AM)
- [ ] 3 timed full runs of 04_DEMO_SCRIPT from fresh start; backup video recorded.

## Submission (by 9:15 AM, deadline 10:00 AM)
- [ ] Repo public, README complete (disclosures, local vs internet, hardware, setup, bench), LICENSE, no secrets/tokens/models/DB committed (`git ls-files`).
- [ ] Fresh clone + setup instructions read through once.
- [ ] Video ~1 min, uploaded, link works logged-out.
- [ ] X/LinkedIn post with @DevinAI @cognition #AppBuildersPH; link copied.
- [ ] Why-local answer pasted; one submission only; screenshot of confirmation.

## Venue bag (if finalist; reg 12 PM, Cyberzone SM Makati)
Laptop + charger · iPhone + cable · Garmin charged · EarPods · USB mic/extension if available · HDMI/USB-C adapter · power bank · backup video offline on laptop + phone · printed QR. Sound check the mic in the room. Leave by the time needed for the 5 PM midterm.
