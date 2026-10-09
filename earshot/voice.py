"""Local text-to-speech + alert chime.

TTS prefers Piper (P4 hook) and falls back to Windows SAPI via pyttsx3 — both
fully local. The chime is a short two-tone sine played through the laptop
speakers/earbuds (generated in RAM, no file on disk).
"""

from __future__ import annotations

import threading
from pathlib import Path

import numpy as np

from . import config

_lock = threading.Lock()

REPO_ROOT = Path(__file__).resolve().parent.parent
PIPER_DIR = REPO_ROOT / "models" / "piper"
PIPER_VOICE = "en_US-lessac-medium"


def _find_piper_voice() -> Path | None:
    onnx = PIPER_DIR / f"{PIPER_VOICE}.onnx"
    return onnx if onnx.exists() else None


def _speak_piper(text: str) -> bool:
    """Piper TTS (preferred). Python wheel first, then a piper.exe binary."""
    voice = _find_piper_voice()
    if voice is None:
        return False
    # piper-tts Python wheel (1.3.0 API: synthesize() -> AudioChunk)
    try:
        import sounddevice as sd
        from piper import PiperVoice

        v = PiperVoice.load(str(voice))
        chunks = []
        rate = 22050
        for ch in v.synthesize(text):
            chunks.append(ch.audio_float_array)
            rate = ch.sample_rate
        if chunks:
            sd.play(np.concatenate(chunks), rate)
            sd.wait()
            return True
    except Exception:
        pass
    return False


def _speak_pyttsx3(text: str) -> bool:
    try:
        import pyttsx3

        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
        engine.stop()
        return True
    except Exception:
        return False


def speak(text: str) -> str:
    """Speak *text* locally (blocking). Returns the engine used, or 'none'."""
    if not text:
        return "none"
    with _lock:  # one utterance at a time
        if _speak_piper(text):
            return "piper"
        if _speak_pyttsx3(text):
            return "sapi"
    return "none"


def chime() -> None:
    """Play a short two-tone alert chime through the laptop output (RAM only)."""
    try:
        import sounddevice as sd

        sr = config.SAMPLE_RATE
        tone = []
        for freq, dur in ((880.0, 0.12), (1320.0, 0.16)):
            t = np.linspace(0, dur, int(sr * dur), endpoint=False)
            env = np.minimum(1.0, np.minimum(t * 40, (dur - t) * 40))  # soft attack/decay
            tone.append((0.25 * np.sin(2 * np.pi * freq * t) * env).astype(np.float32))
        sd.play(np.concatenate(tone), sr)
    except Exception:
        pass
