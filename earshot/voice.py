"""Local text-to-speech + alert chime.

TTS prefers Piper (P4 hook) and falls back to Windows SAPI via pyttsx3 — both
fully local. The chime is a short two-tone sine played through the laptop
speakers/earbuds (generated in RAM, no file on disk).
"""

from __future__ import annotations

import threading

import numpy as np

from . import config

_lock = threading.Lock()


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
        # Piper hook would go here (preferred); SAPI fallback for now.
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
