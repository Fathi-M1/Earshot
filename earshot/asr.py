"""faster-whisper ASR wrapper (multilingual, auto-detect language).

One pass transcribes in the original language (for the laptop caption bar) and
reports the detected language; when the language isn't English a second pass
with task="translate" produces the English text for the watch / lock screen.

int8 CPU, beam_size=1, cpu_threads=4, VAD on, condition_on_previous_text=False
(stops hallucination loops). Known whisper hallucination strings are dropped.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from . import config

REPO_ROOT = Path(__file__).resolve().parent.parent
WHISPER_ROOT = REPO_ROOT / "models" / "whisper"

# Whole-segment hallucinations whisper emits in silence/noise (01 §3.3).
HALLUCINATIONS = {
    "thank you.",
    "thanks for watching!",
    "thank you for watching.",
    "[blank_audio]",
    "you",
    ".",
    "",
}


@dataclass
class Caption:
    original: str
    english: str
    language: str
    rtf: float


def _clean(text: str) -> str:
    t = text.strip()
    return "" if t.lower() in HALLUCINATIONS else t


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

    def _run(self, samples: np.ndarray, task: str, language: str | None = None):
        model = self.load()
        segments, info = model.transcribe(
            samples,
            task=task,
            language=language,
            beam_size=1,
            vad_filter=True,
            condition_on_previous_text=False,
            no_speech_threshold=0.6,
        )
        text = " ".join(s.text.strip() for s in segments).strip()
        return text, info

    def caption(self, samples: np.ndarray) -> Caption:
        """Transcribe original + detect language (+ English translation)."""
        import time

        dur = len(samples) / config.SAMPLE_RATE if len(samples) else 0.0
        t0 = time.perf_counter()
        original, info = self._run(samples, task="transcribe")
        lang = getattr(info, "language", "") or ""
        original = _clean(original)
        if not original:
            rtf = (time.perf_counter() - t0) / dur if dur else 0.0
            return Caption(original="", english="", language=lang, rtf=round(rtf, 3))
        if lang == "en" or not config.TRANSLATE_FOR_NOWPLAYING:
            english = original
        else:
            english, _ = self._run(samples, task="translate", language=lang)
            english = _clean(english) or original
        rtf = (time.perf_counter() - t0) / dur if dur else 0.0
        return Caption(original=original, english=english, language=lang, rtf=round(rtf, 3))
