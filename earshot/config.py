"""Central runtime config — the model/language/pipeline decisions Fathi made.

Demo languages: English, Tagalog, Arabic, Spanish. MULTILINGUAL whisper, but
language detection is restricted to these 4 (pick the highest-prob among them).
The laptop bar + phone full-screen show the ORIGINAL; the watch / lock screen
(Now Playing) show the ENGLISH translation (whisper task=translate).

Accuracy over speed: whisper small int8 (fallback base), beam_size 5 on commit,
VAD endpointing, commit on speaker pause.

LLM default qwen2.5:1.5b (measured 9.1 tok/s); 3b only if fast enough under load.
"""

from __future__ import annotations

# --- Languages (detect among these only) ---
ASR_LANGS = ["en", "tl", "ar", "es"]
LANG_NAMES = {"en": "English", "tl": "Tagalog", "ar": "Arabic", "es": "Spanish"}
RTL_LANGS = {"ar", "he", "fa", "ur"}  # render right-to-left

# --- Conversation mode (explicit languages, turn-based; no auto-guessing) ---
# their = the other person's language; mine = the user's language; turn = who speaks.
CONV_DEFAULT = {"their": "ar", "mine": "en", "turn": "them"}

# --- ASR models (multilingual; NOT the .en models) ---
ASR_MODEL = "small"          # accuracy pick; use base if small RTF > 0.5 under load
ASR_MODEL_FALLBACK = "base"
ASR_BEAM_COMMIT = 5          # accurate pass on commit
ASR_BEAM_PARTIAL = 1         # fast pass for live partials

# Now Playing (watch / lock screen) shows the English translation.
TRANSLATE_FOR_NOWPLAYING = True

# --- live pipeline / VAD endpointing ---
SAMPLE_RATE = 16000
RING_SECONDS = 30            # RAM ring buffer length (privacy: last 30 s only)
LOOP_TICK_S = 0.4            # how often the worker checks VAD state
PARTIAL_INTERVAL_S = 1.5     # re-transcribe active utterance for a partial
MAX_UTTERANCE_S = 12.0       # force a commit if speech runs this long
PAUSE_SILENCE_MS = 600       # commit the utterance after this much trailing silence
VAD_THRESHOLD = 0.5
VAD_MIN_SPEECH_MS = 250
VAD_MIN_SILENCE_MS = 300

# --- watch rolling chunks (lock screen / Garmin) ---
WATCH_CHUNK_INTERVAL_S = 1.5
WATCH_CHUNK_MAXCHARS = 28
WATCH_CHUNK_WORDS = 6
ALERT_HOLD_S = 8.0           # an alert overrides the watch title for this long

# --- initial prompts (bias spelling) ---
EN_PROMPT = "Class announcement. Names: Fathi. Terms: quiz, exam, midterm, deadline, due, submit, assignment, Monday."
TAGLISH_PROMPT = (
    "Anunsyo sa klase. Taglish: Fathi, quiz, exam, deadline, due, submit, assignment, "
    "professor, ma'am, sir, Lunes, Martes, bukas, ngayon, tayo, kailangan, grabe, pasok."
)
INITIAL_PROMPTS = {"en": EN_PROMPT, "tl": TAGLISH_PROMPT}

# --- LLM (Ollama) ---
LLM_DEFAULT = "qwen2.5:1.5b"
LLM_HEAVY = "qwen2.5:3b"

# --- Alerts (heard-your-name / announcements) ---
ALERT_KEYWORDS = [
    "Fathi", "quiz", "exam", "deadline", "Monday", "assignment",
    # Tagalog
    "pagsusulit", "deadline", "bukas",
]
ALERT_FUZZY_THRESHOLD = 88     # rapidfuzz partial_ratio
ALERT_COOLDOWN_S = 20          # per-keyword cooldown
ALERT_LLM_MODEL = LLM_DEFAULT  # qwen2.5:1.5b intent check
ALERT_LLM_TIMEOUT = 4.0        # on timeout, the keyword hit stands
ALERT_USE_LLM = True           # fuzzy pre-filter, then LLM intent confirm

# --- Catch me up ---
CATCHUP_MINUTES = 5
CATCHUP_MODEL = LLM_DEFAULT    # qwen2.5:1.5b
CATCHUP_TIMEOUT = 12.0         # extractive fallback beyond this
CATCHUP_MAX_WORDS = 900

# --- hallucination filter ---
# Whole-segment strings whisper emits in silence/noise.
HALLUCINATIONS = {
    "thank you.", "thank you", "thanks for watching!", "thanks for watching.",
    "thank you for watching.", "thank you for watching!", "see you in the next video.",
    "see you next time.", "please subscribe.", "like and subscribe.", "[blank_audio]",
    "you", ".", "", "bye.", "bye bye.", "okay.", "ok.",
}
# Drop committed lines with fewer than this many words AND low confidence.
MIN_WORDS_LOWCONF = 2
LOWCONF_LOGPROB = -1.0       # avg_logprob below this is "low confidence"
