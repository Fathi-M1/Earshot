"""Phase 0 benchmarks (03 Phase 0, 07, 01 §9). Real numbers only.

- ASR: real-time factor (RTF) and optional WER for tiny.en / base.en / base over
  the WAVs *you* record into ``tests/audio/``. Audio is decoded into a RAM numpy
  array (faster_whisper.decode_audio); the bench never writes audio to disk.
  Models are warmed before timing; VAD on; cpu_threads=4 (per Fathi's note).
- Ollama: tokens/s for qwen2.5:3b / 1.5b from Ollama's own eval metrics, plus one
  end-to-end catch-up-style call timing. All HTTP goes through localclient
  (loopback only, byte-counted).

Results print as a table and append to ``docs/bench.txt`` with a timestamp.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from . import localclient

REPO_ROOT = Path(__file__).resolve().parent.parent
AUDIO_DIR = REPO_ROOT / "tests" / "audio"
WHISPER_ROOT = REPO_ROOT / "models" / "whisper"
BENCH_TXT = REPO_ROOT / "docs" / "bench.txt"

OLLAMA = "http://127.0.0.1:11434"
# Demo languages: English, Tagalog, Arabic.
DEFAULT_ASR_MODELS = ["tiny", "base", "small"]
DEFAULT_LLM_MODELS = ["qwen2.5:1.5b"]
KNOWN_LANGS = {"en", "tl", "ar"}


# ---------------------------------------------------------------- ASR ----------


@dataclass
class AsrRow:
    model: str
    wav: str
    lang_file: str       # language tag parsed from the filename prefix (en-/tl-/ar-)
    lang_detected: str   # language whisper auto-detected
    audio_s: float
    proc_s: float        # transcribe time
    rtf: float           # transcribe RTF (vs the <= 0.5 budget)
    translate_rtf: float | None
    wer: float | None
    original: str
    english: str


def _decode(path: Path):
    """Decode a WAV into a 16 kHz mono float32 numpy array, in RAM only."""
    from faster_whisper.audio import decode_audio

    return decode_audio(str(path), sampling_rate=16000)


def _lang_from_name(name: str) -> str:
    stem = name.lower()
    for sep in ("-", "_", "."):
        if sep in stem:
            head = stem.split(sep, 1)[0]
            if head in KNOWN_LANGS:
                return head
    return stem[:2] if stem[:2] in KNOWN_LANGS else "?"


def _wer(ref: str, hyp: str) -> float | None:
    try:
        from jiwer import wer as _jiwer

        return float(_jiwer(ref, hyp))
    except Exception:
        return None


def bench_asr(models: list[str] | None = None) -> list[AsrRow]:
    models = models or DEFAULT_ASR_MODELS
    wavs = sorted(AUDIO_DIR.glob("*.wav"))
    if not wavs:
        raise FileNotFoundError(
            f"No WAVs in {AUDIO_DIR}. Record short clips there named by language, "
            f"e.g. en-1.wav, tl-1.wav, ar-1.wav (16 kHz mono; a matching <name>.txt enables WER)."
        )
    from . import asr, config
    from .asr import _clean

    rows: list[AsrRow] = []
    decoded = {w: _decode(w) for w in wavs}
    beam = config.ASR_BEAM_COMMIT  # bench mirrors the live commit pass (accurate)
    for name in models:
        t = asr.Transcriber(name)
        t.load()
        t.caption(decoded[wavs[0]], beam_size=beam)  # warm (not timed)
        for w in wavs:
            samples = decoded[w]
            audio_s = len(samples) / 16000.0
            lang_detected, _p = t.detect(samples)  # restricted to en/tl/ar/es
            t0 = time.perf_counter()
            raw, conf = t._run(samples, "transcribe", lang_detected, beam)
            proc_s = time.perf_counter() - t0
            original = _clean(raw, conf)
            translate_rtf = None
            english = original
            if lang_detected != "en" and original:
                t1 = time.perf_counter()
                raw_en, conf_en = t._run(samples, "translate", lang_detected, beam)
                translate_rtf = round((time.perf_counter() - t1) / audio_s, 3) if audio_s else None
                english = _clean(raw_en, conf_en) or original
            ref_file = w.with_suffix(".txt")
            wer = _wer(ref_file.read_text(encoding="utf-8").strip(), original) if ref_file.exists() else None
            rows.append(
                AsrRow(
                    model=name,
                    wav=w.name,
                    lang_file=_lang_from_name(w.name),
                    lang_detected=lang_detected,
                    audio_s=round(audio_s, 2),
                    proc_s=round(proc_s, 2),
                    rtf=round(proc_s / audio_s, 3) if audio_s else float("nan"),
                    translate_rtf=translate_rtf,
                    wer=round(wer, 3) if wer is not None else None,
                    original=original,
                    english=english,
                )
            )
    return rows


# --------------------------------------------------------------- Ollama --------


@dataclass
class LlmRow:
    model: str
    tokens: int
    eval_s: float
    tok_per_s: float
    wall_s: float


def bench_ollama(models: list[str] | None = None) -> list[LlmRow]:
    models = models or DEFAULT_LLM_MODELS
    prompt = (
        "Summarize in two short lines what a student missed: "
        "'The quiz is next Friday. Submit chapter 3 by Monday.'"
    )
    rows: list[LlmRow] = []
    for m in models:
        body = {
            "model": m,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0, "seed": 7, "num_thread": 2},
        }
        t0 = time.perf_counter()
        resp = localclient.post_json(f"{OLLAMA}/api/generate", body, timeout=60.0)
        wall = time.perf_counter() - t0
        data = resp.json()
        eval_count = int(data.get("eval_count", 0))
        eval_ns = int(data.get("eval_duration", 0))
        eval_s = eval_ns / 1e9 if eval_ns else 0.0
        tps = (eval_count / eval_s) if eval_s else 0.0
        rows.append(
            LlmRow(
                model=m,
                tokens=eval_count,
                eval_s=round(eval_s, 2),
                tok_per_s=round(tps, 1),
                wall_s=round(wall, 2),
            )
        )
    return rows


# --------------------------------------------------------------- output --------


def _format(asr_rows: list[AsrRow], llm_rows: list[LlmRow]) -> str:
    lines: list[str] = []
    lines.append("## ASR (multilingual faster-whisper int8, cpu_threads=4, VAD on, warm; RTF=proc/audio)")
    lines.append(
        f"{'model':<7} {'wav':<16} {'file':>4} {'det':>4} {'audio':>6} {'rtf':>6} {'tr_rtf':>7} {'wer':>6}  text"
    )
    for r in asr_rows:
        wer = f"{r.wer:.2f}" if r.wer is not None else "—"
        trr = f"{r.translate_rtf:.3f}" if r.translate_rtf is not None else "—"
        snippet = (r.original[:40] + ("…" if len(r.original) > 40 else "")) if r.original else "(no speech)"
        lines.append(
            f"{r.model:<7} {r.wav:<16} {r.lang_file:>4} {r.lang_detected:>4} "
            f"{r.audio_s:>6.2f} {r.rtf:>6.3f} {trr:>7} {wer:>6}  {snippet}"
        )
    if asr_rows:
        lines.append("")
        lines.append("mean transcribe RTF by model x detected-language (pass <= 0.5):")
        agg: dict[tuple[str, str], list[float]] = {}
        for r in asr_rows:
            agg.setdefault((r.model, r.lang_detected or "?"), []).append(r.rtf)
        for (m, lang), rtfs in sorted(agg.items()):
            mean = sum(rtfs) / len(rtfs)
            verdict = "PASS" if mean <= 0.5 else "FAIL"
            lines.append(f"  {m:<7} {lang:>4}  {mean:.3f}  {verdict}  (n={len(rtfs)})")
        lines.append("")
        by_model: dict[str, list[float]] = {}
        for r in asr_rows:
            by_model.setdefault(r.model, []).append(r.rtf)
        lines.append("mean transcribe RTF by model (all languages):")
        for m, rtfs in sorted(by_model.items()):
            mean = sum(rtfs) / len(rtfs)
            verdict = "PASS" if mean <= 0.5 else "FAIL"
            lines.append(f"  {m:<7} {mean:.3f}  {verdict}  -> pick biggest PASS")
    lines.append("")
    lines.append("## Ollama (tokens/s from eval metrics; options num_thread=2)")
    lines.append(f"{'model':<16} {'tokens':>7} {'eval_s':>8} {'tok/s':>8} {'wall_s':>8}")
    for r in llm_rows:
        lines.append(f"{r.model:<16} {r.tokens:>7} {r.eval_s:>8.2f} {r.tok_per_s:>8.1f} {r.wall_s:>8.2f}")
    c = localclient.counters()
    lines.append("")
    lines.append(f"localclient bytes sent/recv: {c.bytes_sent} / {c.bytes_recv} (requests {c.requests})")
    return "\n".join(lines)


def run(
    *,
    asr: bool = True,
    ollama: bool = True,
    asr_models: list[str] | None = None,
    llm_models: list[str] | None = None,
) -> str:
    asr_rows = bench_asr(asr_models) if asr else []
    llm_rows = bench_ollama(llm_models) if ollama else []
    report = _format(asr_rows, llm_rows)
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    BENCH_TXT.parent.mkdir(parents=True, exist_ok=True)
    with BENCH_TXT.open("a", encoding="utf-8") as f:
        f.write(f"\n# bench {stamp}\n{report}\n")
    print(report)
    print(f"\n(appended to {BENCH_TXT})")
    return report
