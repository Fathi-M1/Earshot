"""Generate clearly-marked SYNTHETIC English test clips with Piper + ground-truth
.txt, into tests/audio/. (tl/ar accuracy still needs a live human check.)"""

import wave
from pathlib import Path

import numpy as np
from piper import PiperVoice

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "tests" / "audio"
OUT.mkdir(parents=True, exist_ok=True)
VOICE = ROOT / "models" / "piper" / "en_US-lessac-medium.onnx"

CLIPS = {
    "en-syn-1": "Fathi, the quiz is on Monday at nine.",
    "en-syn-2": "The deadline for the assignment is next Friday.",
    "en-syn-3": "Attention passengers, the train is now boarding.",
}

v = PiperVoice.load(str(VOICE))
for name, text in CLIPS.items():
    chunks, rate = [], 22050
    for ch in v.synthesize(text):
        chunks.append(ch.audio_int16_array)
        rate = ch.sample_rate
    pcm = np.concatenate(chunks).astype(np.int16)
    wav_path = OUT / f"{name}.wav"
    with wave.open(str(wav_path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm.tobytes())
    (OUT / f"{name}.txt").write_text(text, encoding="utf-8")
    print(f"wrote {wav_path.name} ({len(pcm)/rate:.1f}s) + ground truth")
print("SYNTHETIC English clips only — tl/ar accuracy needs a live human check.")
