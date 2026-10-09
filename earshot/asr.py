"""faster-whisper ASR wrapper (multilingual; detection restricted to the demo
languages en/tl/ar/es).

One pass transcribes in the original language (laptop bar + phone full-screen)
and a second pass with task="translate" gives the English for the watch / lock
screen. int8 CPU, cpu_threads=4, VAD on, condition_on_previous_text=False,
anti-repetition params, per-language initial prompts (Taglish for tl).

Hallucination filter: whole-segment blacklist, collapse repeats, drop very short
low-confidence lines.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from . import config

REPO_ROOT = Path(__file__).resolve().parent.parent
WHISPER_ROOT = REPO_ROOT / "models" / "whisper"


@dataclass
class Caption:
    original: str
    english: str
    language: str
    confidence: float   # avg logprob (higher is better; ~0 best, negative worse)
    rtf: float


def _is_hallucination(text: str) -> bool:
    return text.strip().lower() in config.HALLUCINATIONS


def _collapse_repeats(text: str) -> str:
    """Collapse immediate duplicated words/phrases whisper loops on."""
    # repeated single words: "the the the" -> "the"
    text = re.sub(r"\b(\w+)(\s+\1\b)+", r"\1", text, flags=re.IGNORECASE)
    # repeated short phrases: "see you see you see you" -> "see you"
    text = re.sub(r"\b(\w+\s+\w+)( \1\b)+", r"\1", text, flags=re.IGNORECASE)
    return text.strip()


def _clean(text: str, avg_logprob: float) -> str:
    t = _collapse_repeats(text.strip())
    if _is_hallucination(t):
        return ""
    words = t.split()
    # Drop very short, low-confidence lines (noise blips).
    if len(words) < config.MIN_WORDS_LOWCONF and avg_logprob < config.LOWCONF_LOGPROB:
        return ""
    return t


class Transcriber:
    def __init__(self, model_name: str = config.ASR_MODEL):
        self.model_name = model_name
        self._model = None

    def load(self):
        from faster_whisper import WhisperModel

        if self._model is None:
            self._model = WhisperModel(
                self.model_name,
                device="cpu",
                compute_type="int8",
                cpu_threads=4,
                download_root=str(WHISPER_ROOT),
            )
        return self._model

    def detect(self, samples: np.ndarray) -> tuple[str, float]:
        """Detect language, restricted to config.ASR_LANGS (highest prob among them)."""
        model = self.load()
        try:
            _lang, _prob, all_probs = model.detect_language(samples)
        except Exception:
            return "en", 0.0
        allowed = {lang: p for lang, p in all_probs if lang in config.ASR_LANGS}
        if not allowed:
            return "en", 0.0
        best = max(allowed.items(), key=lambda kv: kv[1])
        return best[0], float(best[1])

    def _run(self, samples, task: str, language: str | None, beam_size: int):
        model = self.load()
        segments, info = model.transcribe(
            samples,
            task=task,
            language=language,
            beam_size=beam_size,
            vad_filter=True,
            condition_on_previous_text=False,
            no_speech_threshold=0.6,
            compression_ratio_threshold=2.4,   # drop gibberish/repeated loops
            no_repeat_ngram_size=3,
            repetition_penalty=1.15,
            log_prob_threshold=-1.0,
            initial_prompt=config.INITIAL_PROMPTS.get(language),
            hotwords=(config.HOTWORDS if (task == "transcribe" and language == "en") else None),
        )
        segs = list(segments)
        text = " ".join(s.text.strip() for s in segs).strip()
        if segs:
            avg_logprob = sum(s.avg_logprob for s in segs) / len(segs)
        else:
            avg_logprob = -2.0
        return text, avg_logprob

    def caption(
        self,
        samples: np.ndarray,
        *,
        beam_size: int = config.ASR_BEAM_COMMIT,
        language: str | None = None,
    ) -> Caption:
        """Transcribe original (restricted language) + English translation."""
        import time

        dur = len(samples) / config.SAMPLE_RATE if len(samples) else 0.0
        if language is None:
            language, _ = self.detect(samples)
        t0 = time.perf_counter()
        raw, conf = self._run(samples, task="transcribe", language=language, beam_size=beam_size)
        original = _clean(raw, conf)
        if not original:
            rtf = (time.perf_counter() - t0) / dur if dur else 0.0
            return Caption("", "", language, conf, round(rtf, 3))
        if language == "en" or not config.TRANSLATE_FOR_NOWPLAYING:
            english = original
        else:
            raw_en, conf_en = self._run(samples, task="translate", language=language, beam_size=beam_size)
            english = _clean(raw_en, conf_en) or original
        rtf = (time.perf_counter() - t0) / dur if dur else 0.0
        return Caption(original, english, language, round(conf, 2), round(rtf, 3))
