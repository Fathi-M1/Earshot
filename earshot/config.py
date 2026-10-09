"""Central runtime config — the model/language decisions Fathi made in P0.

Languages for the demo: English, Tagalog, Arabic. Use the MULTILINGUAL whisper
models (auto-detect), never the `.en` models. The laptop caption bar shows the
ORIGINAL language; the watch / lock screen (Now Playing) show the ENGLISH
translation (whisper task=translate).

LLM default is qwen2.5:1.5b (measured 9.1 tok/s); 3b only if it proves fast
enough under ASR load.
"""

from __future__ import annotations

# --- ASR (multilingual; auto-detect language) ---
ASR_MODEL = "base"          # multilingual base (NOT base.en)
ASR_MODEL_FALLBACK = "tiny"  # multilingual tiny if base RTF > 0.5 under load
ASR_MODEL_BETTER = "small"   # use only if the bench shows RTF <= 0.5

# Now Playing (watch / lock screen) shows the English translation; the laptop
# caption bar shows the original-language text.
TRANSLATE_FOR_NOWPLAYING = True

# How often the live loop re-transcribes the recent audio window.
LIVE_INTERVAL_S = 2.5
LIVE_WINDOW_S = 6.0          # transcribe the last N seconds each cycle
RING_SECONDS = 30           # RAM ring buffer length (privacy: last 30 s only)
SAMPLE_RATE = 16000

# --- LLM (Ollama) ---
LLM_DEFAULT = "qwen2.5:1.5b"   # alerts + catch-up default (9.1 tok/s measured)
LLM_HEAVY = "qwen2.5:3b"       # only if measured fast enough during ASR load

# Lightweight keyword highlight so the live log confirms detection (full alert
# logic is P2). Name + a couple of cue words.
DEMO_KEYWORDS = ["fathi", "quiz", "deadline", "exam", "monday"]
