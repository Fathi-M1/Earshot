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

# --- Languages: ONLY English, Tagalog, Arabic. No auto-detect anywhere; the
# user-selected language is always passed as language=<code> to every transcribe. ---
ASR_LANGS = ["en", "tl", "ar"]
LANG_NAMES = {"en": "English", "tl": "Tagalog", "ar": "Arabic"}
RTL_LANGS = {"ar", "he", "fa", "ur"}  # render right-to-left

# --- Conversation mode (explicit languages, turn-based; no auto-guessing) ---
# their = the other person's language; mine = the user's language; turn = who speaks.
CONV_DEFAULT = {"their": "ar", "mine": "en", "turn": "them"}
# AMBIENT/CAPTIONS: the spoken language (user-picked, no auto-detect) + read language.
SRC_LANG_DEFAULT = "en"

# --- ASR models (multilingual; NOT the .en models) ---
# Two-tier, per language. English uses the faster+more-accurate .en models;
# tl/ar use multilingual. FAST = partials + instant commit; FINAL = background
# refine that replaces the line in place (skipped when FINAL == FAST).
ASR_FAST_EN = "tiny.en"
ASR_FINAL_EN = "base.en"
ASR_FAST_ML = "tiny"         # tl/ar partials
ASR_FINAL_ML = "small"       # tl/ar refine
# back-compat (bench/asr defaults)
ASR_FAST = "tiny"
ASR_ACCURATE = "small"


def fast_model(lang: str) -> str:
    return ASR_FAST_EN if lang == "en" else ASR_FAST_ML


def final_model(lang: str) -> str:
    return ASR_FINAL_EN if lang == "en" else ASR_FINAL_ML
ASR_MODEL = ASR_FAST         # back-compat for bench/asr default
ASR_MODEL_FALLBACK = "tiny"
ASR_BEAM_COMMIT = 1          # NEVER beam-search on the hot (instant-commit) path
ASR_BEAM_PARTIAL = 1
ASR_BEAM_FINAL = 5           # background refine can afford beam 5 (accuracy)

# Now Playing (watch / lock screen) shows the English translation.
TRANSLATE_FOR_NOWPLAYING = True

# --- live pipeline / VAD endpointing (tuned for latency) ---
SAMPLE_RATE = 16000
RING_SECONDS = 30            # RAM ring buffer length (privacy: last 30 s only)
LOOP_TICK_S = 0.25           # how often the worker checks VAD state
PARTIAL_INTERVAL_S = 0.7     # stream a partial this often while speaking
MAX_UTTERANCE_S = 8.0        # force-split run-on speech at 8 s (never one huge chunk)
SPLIT_OVERLAP_S = 1.0        # overlap kept after a forced split (dedupe in _commit)
PARTIAL_WINDOW_S = 6.0       # cap the sliding partial/commit window (speed)
PAUSE_SILENCE_MS = 450       # commit after this much trailing silence
MIN_SEGMENT_S = 0.6          # drop utterances shorter than this (noise blips)
VAD_THRESHOLD = 0.5
VAD_MIN_SPEECH_MS = 200
VAD_MIN_SILENCE_MS = 400
LANG_LOCK_S = 5.0            # AMBIENT: detect once per this much speech, then lock
LLM_TRANSLATE_MAX_TOKENS = 60  # English -> their language, kept short

# --- watch rolling chunks (lock screen / Garmin) ---
WATCH_CHUNK_INTERVAL_S = 1.5
WATCH_CHUNK_MAXCHARS = 28
WATCH_CHUNK_WORDS = 6
ALERT_HOLD_S = 8.0           # an alert overrides the watch title for this long

# --- initial prompts (bias spelling) ---
EN_PROMPT = "Class at FEU Tech. Names: Fathi. Terms: quiz, exam, midterm, deadline, due, submit, assignment, ACM, Monday."
# hotwords bias the decoder toward these exact tokens (faster-whisper `hotwords`).
HOTWORDS = "Fathi quiz deadline midterm exam assignment FEU Tech ACM Monday"
TAGLISH_PROMPT = (
    "Kumusta, ayos lang, salamat, opo, hindi, saan, ano. "
    "Fathi, quiz, exam, deadline, submit, assignment, Lunes, bukas, pagsusulit."
)
INITIAL_PROMPTS = {"en": EN_PROMPT, "tl": TAGLISH_PROMPT}
# Tagalog exact-word fixes for frequent whisper misspellings (from live log).
TL_FIXES = {"umaarga": "umaga", "ponsusta": "kumusta", "magandan": "magandang"}

# --- LLM (Ollama) --- qwen2.5:3b removed entirely (RAM). Only 1.5b, lazy, 5m idle.
LLM_DEFAULT = "qwen2.5:1.5b"
LLM_HEAVY = "qwen2.5:1.5b"   # kept as an alias; 3b is gone
LLM_KEEP_ALIVE = "5m"        # unload after 5 min idle (was -1 = never, a RAM hog)
IDLE_SECONDS = 10.0          # recall embeddings + insights only after this much silence

# --- Alerts (heard-your-name / announcements) ---
ALERT_KEYWORDS = [
    "Fathi", "quiz", "exam", "deadline", "Monday", "assignment",
    # Tagalog
    "pagsusulit", "deadline", "bukas",
]
# Public-announcement cues (AMBIENT mode watches for these too).
ANNOUNCEMENT_KEYWORDS = [
    "attention", "boarding", "next station", "last call", "final call",
    "gate", "platform", "now boarding", "all aboard",
]
ALERT_FUZZY_THRESHOLD = 88     # rapidfuzz partial_ratio
ALERT_COOLDOWN_S = 30          # per-reason debounce
ALERT_LLM_MODEL = LLM_DEFAULT  # qwen2.5:1.5b intent check
ALERT_LLM_TIMEOUT = 4.0        # on timeout, the keyword hit stands
ALERT_USE_LLM = True           # fuzzy pre-filter, then LLM intent confirm

# --- Catch me up ---
CATCHUP_MINUTES = 5
CATCHUP_MODEL = LLM_DEFAULT    # qwen2.5:1.5b
CATCHUP_TIMEOUT = 3.0          # extractive fallback if the model is slower than this
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
