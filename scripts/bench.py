"""Latency + accuracy bench over tests/audio/*.wav (with .txt ground truth).

Per clip: WER, partial latency, commit latency, worst latency, hallucination
count (hyp words not in reference + wrong-script tokens). Grouped into
en-normal / en-fast / tl / ar by filename prefix. For English it compares the
candidate FINAL models (tiny.en vs base.en) so the pick is data-driven.

Run: uv run python scripts/bench.py   (appends a table to docs/bench.txt)
"""

import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from earshot import config  # noqa: E402
from earshot.asr import Transcriber, _clean  # noqa: E402
from earshot.bench import _decode  # noqa: E402

AUDIO = ROOT / "tests" / "audio"
SR = 16000
_models: dict[str, Transcriber] = {}


def model(name):
    if name not in _models:
        _models[name] = Transcriber(name)
        _models[name].load()
    return _models[name]


def norm(s):
    return re.sub(r"[^a-z0-9؀-ۿ ]", "", s.lower()).split()


def wer(ref, hyp):
    try:
        from jiwer import wer as _w
        return round(float(_w(" ".join(norm(ref)), " ".join(norm(hyp)))), 3)
    except Exception:
        return None


def hallucinations(ref, hyp, lang):
    ref_set = set(norm(ref))
    extra = [w for w in norm(hyp) if w not in ref_set]
    wrong_script = 0
    for tok in hyp.split():
        if lang == "en" and re.search(r"[^\x00-\x7f]", tok):
            wrong_script += 1
        if lang in ("ar",) and re.search(r"[a-zA-Z一-鿿]", tok):
            wrong_script += 1
    return len(extra), wrong_script


def category(name):
    if name.startswith("en-fast"):
        return "en-fast"
    if name.startswith("en-normal") or name.startswith("en"):
        return "en-normal"
    if name.startswith("tl"):
        return "tl"
    if name.startswith("ar"):
        return "ar"
    return "other"


def transcribe(m, audio, lang, beam):
    raw, conf = m._run(audio, "transcribe", lang, beam)
    return _clean(raw, conf)


def bench_clip(wav, lang, fast_name, final_name):
    audio = _decode(wav)
    dur = len(audio) / SR
    ref = wav.with_suffix(".txt").read_text(encoding="utf-8").strip()
    fast, final = model(fast_name), model(final_name)
    # partial: fast model on first 1.0 s
    t = time.perf_counter()
    transcribe(fast, audio[:SR], lang, config.ASR_BEAM_PARTIAL)
    partial_ms = int((time.perf_counter() - t) * 1000)
    # commit: final model on capped 6 s window
    win = audio[: int(config.PARTIAL_WINDOW_S * SR)]
    t = time.perf_counter()
    hyp = transcribe(final, win if dur > config.PARTIAL_WINDOW_S else audio, lang, config.ASR_BEAM_FINAL)
    commit_ms = int((time.perf_counter() - t) * 1000)
    # full-clip hyp for WER (final model, 8 s force-split)
    worst_ms, parts = 0, []
    step = int(config.MAX_UTTERANCE_S * SR)
    for i in range(0, len(audio), step):
        seg = audio[i:i + step + int(SR)]  # 1 s overlap
        t = time.perf_counter()
        parts.append(transcribe(final, seg, lang, config.ASR_BEAM_FINAL))
        worst_ms = max(worst_ms, int((time.perf_counter() - t) * 1000))
    full = " ".join(parts)
    extra, wrong = hallucinations(ref, full, lang)
    return {
        "wav": wav.name, "dur": round(dur, 1), "wer": wer(ref, full),
        "partial_ms": partial_ms, "commit_ms": commit_ms, "worst_ms": worst_ms,
        "halluc": extra, "wrong_script": wrong, "hyp": full,
    }


def run(fast_name, final_name, label):
    wavs = sorted(AUDIO.glob("*.wav"))
    rows = []
    for w in wavs:
        cat = category(w.stem)
        lang = "en" if cat.startswith("en") else cat
        if lang not in ("en", "tl", "ar"):
            continue
        r = bench_clip(w, lang, fast_name, final_name)
        r["cat"] = cat
        rows.append(r)
    out = [f"\n## bench [{label}] fast={fast_name} final={final_name} ({time.strftime('%Y-%m-%d %H:%M:%S')})"]
    out.append(f"{'cat':<10}{'wav':<22}{'dur':>5}{'wer':>6}{'part':>6}{'commit':>7}{'worst':>6}{'halluc':>7}{'wscript':>8}")
    cats: dict[str, list] = {}
    for r in rows:
        cats.setdefault(r["cat"], []).append(r)
        wer_s = f"{r['wer']:.2f}" if r["wer"] is not None else "—"
        out.append(f"{r['cat']:<10}{r['wav']:<22}{r['dur']:>5}{wer_s:>6}{r['partial_ms']:>6}{r['commit_ms']:>7}{r['worst_ms']:>6}{r['halluc']:>7}{r['wrong_script']:>8}")
    out.append(f"{'-- means by category --':<38}")
    for cat, rs in sorted(cats.items()):
        n = len(rs)
        mw = sum(x["wer"] for x in rs if x["wer"] is not None) / max(1, sum(1 for x in rs if x["wer"] is not None))
        out.append(f"{cat:<10} n={n}  WER={mw:.3f}  partial={sum(x['partial_ms'] for x in rs)//n}ms  "
                   f"commit={sum(x['commit_ms'] for x in rs)//n}ms  worst={max(x['worst_ms'] for x in rs)}ms  "
                   f"halluc={sum(x['halluc'] for x in rs)}  wrong_script={sum(x['wrong_script'] for x in rs)}")
    report = "\n".join(out)
    print(report)
    with (ROOT / "docs" / "bench.txt").open("a", encoding="utf-8") as f:
        f.write(report + "\n")
    return rows


if __name__ == "__main__":
    # English: compare tiny.en-only vs base.en-final to pick the final tier.
    run("tiny.en", "tiny.en", "en tiny.en only")
    run("tiny.en", "base.en", "en base.en final")
