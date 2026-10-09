"""Generate SYNTHETIC English test clips with Piper (normal 1.0 + fast 0.7 speech)
+ two 15 s run-ons, with ground-truth .txt, into tests/audio/.
tl/ar accuracy still needs a live human check (Piper has no tl/ar voice here)."""

import wave
from pathlib import Path

import numpy as np
from piper import PiperVoice
from piper.config import SynthesisConfig

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "tests" / "audio"
OUT.mkdir(parents=True, exist_ok=True)
VOICE = ROOT / "models" / "piper" / "en_US-lessac-medium.onnx"

SENTENCES = [
    "Fathi, the quiz is on Monday at nine.",
    "The deadline for the midterm is next Friday.",
    "Please submit assignment three before five p m.",
    "Fathi, don't forget the ACM meeting at FEU Tech.",
    "There are twelve questions and you have thirty minutes.",
    "The exam covers chapters four through eight.",
]
RUNONS = [
    "okay everyone listen the quiz on Monday has twenty questions and the deadline "
    "for the midterm project is next Friday at five so make sure Fathi and the whole "
    "team submit assignment three before then because the exam covers chapters four "
    "through eight and the ACM meeting at FEU Tech is right after",
    "so today we are going over the midterm review Fathi please remember there is a "
    "quiz on Monday a deadline on Friday and the final exam has fifty questions worth "
    "thirty percent of your grade and you only have one hour so manage your time and "
    "do not forget to submit assignment three",
]

v = PiperVoice.load(str(VOICE))


def save(name: str, text: str, length_scale: float) -> None:
    cfg = SynthesisConfig(length_scale=length_scale)
    chunks, rate = [], 22050
    for ch in v.synthesize(text, syn_config=cfg):
        chunks.append(ch.audio_int16_array)
        rate = ch.sample_rate
    pcm = np.concatenate(chunks).astype(np.int16)
    with wave.open(str(OUT / f"{name}.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
        w.writeframes(pcm.tobytes())
    (OUT / f"{name}.txt").write_text(text, encoding="utf-8")
    print(f"{name}.wav  {len(pcm)/rate:4.1f}s")


for i, s in enumerate(SENTENCES, 1):
    save(f"en-normal-{i}", s, 1.0)
    save(f"en-fast-{i}", s, 0.7)  # faster speech
for i, s in enumerate(RUNONS, 1):
    save(f"en-fast-runon-{i}", s, 0.9)
print("SYNTHETIC English only — tl/ar accuracy needs a live human check.")
