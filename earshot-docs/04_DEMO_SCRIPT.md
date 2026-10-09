# 04 · Live demo script (real, live, honest)

**Honesty rules:** every caption, alert and summary on stage is produced live from real speech in the room. No pre-recorded model output, no canned transcripts, no hidden text files. If we use a recorded audio clip as *input* (fallback only), we say "this is a recording of me reading, played through a speaker; the transcription is live." Numbers on screen come from the privacy panel / `docs/bench.txt` only.

## Setup (before going on, 5 min)
- iPhone Personal Hotspot ON; laptop on the hotspot; `earshot serve` running **from an admin PowerShell**; dashboard open (Live tab + Privacy card visible); caption bar visible bottom-center; OBS: Scene 1 = laptop screen + overhead camera on the Garmin + iPhone; Scene 2 = video; Scene 3 = backup recording.
- iPhone: Safari tab on `http://172.20.10.x:7778`, tapped **Start**, locked, brightness max, auto-lock 5 min. Garmin: Music → Control Phone, showing the caption.
- EarPods plugged into the **laptop** (Piper speaks there). Laptop audio also to the PA if the venue allows, so judges hear catch-up.
- Mic: closest decent mic (laptop mic pointed at the speaker, or a USB/lapel mic if we have one; note which on the slide). Do a 10 s sound check: say a sentence, check the caption.
- Settings: names = `Fathi`, `Mr. <surname>`; keywords = quiz, deadline, due, submit, exam. Mode EN. Auto-expire 1 h for stage (and say so).
- Warm-up: one catch-up call 2 min before (loads the model; not shown).

## Run (≈ 2:00 inside the 5-min pitch)
| # | Time | Action | What appears (live) | Line |
|---|---|---|---|---|
| 1 | 0:00 | Toggle **Cut internet** on the dashboard; open a browser tab to `https://example.com` → fails | Privacy: Internet reachable **no**, bytes sent 0, connections 0; offline tile on the watch | "The laptop is now cut off from the internet. The phone is only a screen for it." |
| 2 | 0:15 | Fathi keeps talking to the judges naturally | Captions on the bar, the iPhone lock screen and the Garmin (per Phase 0 decision) | "Everything I say is being transcribed on this laptop. Look at my wrist." (raise the watch to the overhead camera) |
| 3 | 0:40 | Ask a judge/host: "Could you say: *Fathi, the quiz is next Friday*?" | ALERT ◆ on bar + lock screen + watch title, laptop chime | "That's the moment you'd miss if you zoned out." |
| 4 | 1:00 | Press **Previous** on the Garmin | CATCH_UP ▶; Piper speaks a 2-line summary of the last minutes (to PA/EarPods); title/artist = the 2 lines | "Previous: catch me up." |
| 5 | 1:20 | Press **Next** | `Bookmarked 10:41` | "Next bookmarks the moment." |
| 6 | 1:30 | Press **Play/Pause** | MUTED ‖ everywhere; bar "Muted · not listening"; speak → nothing appears | "And one press stops the microphone. Audio is never saved; only text, and it expires." |
| 7 | 1:45 | Unmute; "and it also…" (only features that passed rehearsal): Recall query "what did they say about the quiz?" → exact quote + timestamp; or `TL→EN` sentence in Tagalog | live answer / translated caption | "And it also…" |
| 8 | end | Toggle **Restore internet** after the pitch | — | — |

## If something fails (say it, keep moving)
- Garmin slow/stuck: "The watch mirrors my phone; here's the phone." → iPhone; then caption bar.
- iPhone lost the page: caption bar + Windows lock screen (Win+L) via SMTC + EarPods; "fully offline mode: laptop only."
- Venue too loud: move the mic closer / speak into it; last resort: the recorded clip (announced as a recording).
- Catch-up slow: extractive recap appears (labeled); "the small model is still thinking; this is the fallback."
- Anything else: Scene 3 backup recording, labeled "this morning's run".

## Rehearsal checklist (Sat 6:45 AM, 3 runs, timed)
- [ ] Each run from a fresh `earshot serve`, internet cut, judge line read by a different voice if possible (family member, or Fathi with a changed voice for practice only; on stage it's a real judge).
- [ ] Note measured delays (watch, iPhone, bar) and the catch-up time; use those numbers if asked.
- [ ] Record the best run (Scene 3 backup).
