"""Far-field bench: take the clean en-normal clips, attenuate to ~-18 dB and mix
crowd+hum noise at 10 dB and 5 dB SNR, then measure WER + commit latency with AGC
OFF vs AGC ON (tiny.en -> base.en). Target: far WER within 0.05 of near.
Appends to docs/bench.txt. Synthetic audio.
"""

import re
import sys
import time
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from earshot import config  # noqa: E402
from earshot.asr import Transcriber, _clean  # noqa: E402
from earshot.audio import apply_agc_static  # noqa: E402
from earshot.bench import _decode  # noqa: E402

AUDIO = ROOT / "tests" / "audio"
SR = 16000
rng = np.random.default_rng(7)


def norm(s):
    return " ".join(re.sub(r"[^a-z0-9 ]", "", s.lower()).split())


def wer(ref, hyp):
    from jiwer import wer as _w
    return round(float(_w(norm(ref), norm(hyp))), 3)


def make_noise(n):
    white = rng.standard_normal(n).astype(np.float32)
    t = np.arange(n) / SR
    hum = 0.5 * np.sin(2 * np.pi * 120 * t).astype(np.float32)   # mains hum
    crowd = np.convolve(rng.standard_normal(n), np.ones(80) / 80, mode="same").astype(np.float32)  # murmur
    mix = white * 0.3 + hum + crowd
    return mix / (np.sqrt(np.mean(mix ** 2)) + 1e-9)


def gen_farfield():
    made = []
    for src in sorted(AUDIO.glob("en-normal-*.wav")):
        speech = _decode(src) * (10 ** (-18 / 20))  # attenuate to ~-18 dB (far)
        rms_s = np.sqrt(np.mean(speech ** 2)) + 1e-9
        for snr in (10, 5):
            noise = make_noise(len(speech))
            noise *= rms_s / (10 ** (snr / 20))     # scale noise to target SNR
            mix = np.clip(speech + noise, -1, 1).astype(np.float32)
            name = f"ff-{snr}db-{src.stem.split('-')[-1]}"
            with wave.open(str(AUDIO / f"{name}.wav"), "wb") as w:
                w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
                w.writeframes((mix * 32767).astype(np.int16).tobytes())
            (AUDIO / f"{name}.txt").write_text(src.with_suffix(".txt").read_text(encoding="utf-8"), encoding="utf-8")
            made.append(name)
    return made


_m = {}
def model(n):
    if n not in _m:
        _m[n] = Transcriber(n); _m[n].load()
    return _m[n]


def bench(agc: bool):
    fast, final = model("tiny.en"), model("base.en")
    cats = {}
    for wav in sorted(AUDIO.glob("ff-*.wav")) + sorted(AUDIO.glob("en-normal-*.wav")):
        audio = _decode(wav)
        if agc:
            audio = apply_agc_static(audio)
        ref = wav.with_suffix(".txt").read_text(encoding="utf-8").strip()
        t = time.perf_counter()
        hyp = _clean(*final._run(audio[: int(config.PARTIAL_WINDOW_S * SR)] if len(audio) > config.PARTIAL_WINDOW_S * SR else audio, "transcribe", "en", config.ASR_BEAM_FINAL))
        commit_ms = int((time.perf_counter() - t) * 1000)
        full = _clean(*final._run(audio, "transcribe", "en", config.ASR_BEAM_FINAL))
        cat = "near" if wav.stem.startswith("en-normal") else ("ff-10db" if "-10db-" in wav.stem else "ff-5db")
        cats.setdefault(cat, []).append((wer(ref, full), commit_ms))
    return cats


def report(tag, cats):
    out = [f"\n## far-field bench [{tag}] (tiny.en->base.en, synthetic, {time.strftime('%H:%M:%S')})"]
    for cat in ("near", "ff-10db", "ff-5db"):
        rs = cats.get(cat, [])
        if not rs:
            continue
        mw = sum(w for w, _ in rs) / len(rs)
        mc = sum(c for _, c in rs) // len(rs)
        out.append(f"  {cat:<9} WER={mw:.3f}  commit={mc}ms  n={len(rs)}")
    txt = "\n".join(out)
    print(txt)
    with (ROOT / "docs" / "bench.txt").open("a", encoding="utf-8") as f:
        f.write(txt + "\n")
    return cats


if __name__ == "__main__":
    print("generating far-field clips…", gen_farfield())
    off = report("AGC OFF", bench(agc=False))
    on = report("AGC ON", bench(agc=True))
    near = sum(w for w, _ in on.get("near", [(0, 0)])) / max(1, len(on.get("near", [1])))
    for cat in ("ff-10db", "ff-5db"):
        rs = on.get(cat, [])
        if rs:
            fw = sum(w for w, _ in rs) / len(rs)
            print(f"AGC ON: {cat} WER {fw:.3f} vs near {near:.3f}  (within 0.05: {abs(fw-near) <= 0.05})")
