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
DEFAULT_ASR_MODELS = ["tiny.en", "base.en", "base"]
DEFAULT_LLM_MODELS = ["qwen2.5:3b", "qwen2.5:1.5b"]


# ---------------------------------------------------------------- ASR ----------


@dataclass
class AsrRow:
    model: str
    wav: str
    audio_s: float
    proc_s: float
    rtf: float
    wer: float | None
    text: str


def _load_model(name: str):
    from faster_whisper import WhisperModel

    return WhisperModel(
        name,
        device="cpu",
        compute_type="int8",
        cpu_threads=4,
        download_root=str(WHISPER_ROOT),
    )


def _decode(path: Path):
    """Decode a WAV into a 16 kHz mono float32 numpy array, in RAM only."""
    from faster_whisper.audio import decode_audio

    return decode_audio(str(path), sampling_rate=16000)


def _transcribe(model, samples) -> str:
    segments, _info = model.transcribe(
        samples,
        beam_size=1,
        vad_filter=True,
        condition_on_previous_text=False,
        no_speech_threshold=0.6,
    )
    return " ".join(s.text.strip() for s in segments).strip()


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
            f"No WAVs in {AUDIO_DIR}. Record a few short clips there first "
            f"(16 kHz mono preferred; a matching <name>.txt enables WER)."
        )
    rows: list[AsrRow] = []
    # Pre-decode once; reuse across models.
    decoded = {w: _decode(w) for w in wavs}
    for name in models:
        model = _load_model(name)
        # Warm the model (not timed).
        _transcribe(model, decoded[wavs[0]])
        for w in wavs:
            samples = decoded[w]
            audio_s = len(samples) / 16000.0
            t0 = time.perf_counter()
            text = _transcribe(model, samples)
            proc_s = time.perf_counter() - t0
            ref_file = w.with_suffix(".txt")
            wer = _wer(ref_file.read_text(encoding="utf-8").strip(), text) if ref_file.exists() else None
            rows.append(
                AsrRow(
                    model=name,
                    wav=w.name,
                    audio_s=round(audio_s, 2),
                    proc_s=round(proc_s, 2),
                    rtf=round(proc_s / audio_s, 3) if audio_s else float("nan"),
                    wer=round(wer, 3) if wer is not None else None,
                    text=text,
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
    lines.append("## ASR (faster-whisper int8, cpu_threads=4, VAD on, warm; RTF = proc/audio)")
    lines.append(f"{'model':<9} {'wav':<20} {'audio_s':>8} {'proc_s':>8} {'rtf':>7} {'wer':>7}")
    for r in asr_rows:
        wer = f"{r.wer:.3f}" if r.wer is not None else "—"
        lines.append(f"{r.model:<9} {r.wav:<20} {r.audio_s:>8.2f} {r.proc_s:>8.2f} {r.rtf:>7.3f} {wer:>7}")
    if asr_rows:
        by_model: dict[str, list[float]] = {}
        for r in asr_rows:
            by_model.setdefault(r.model, []).append(r.rtf)
        lines.append("")
        lines.append("mean RTF by model (pass <= 0.5):")
        for m, rtfs in by_model.items():
            mean = sum(rtfs) / len(rtfs)
            verdict = "PASS" if mean <= 0.5 else "FAIL"
            lines.append(f"  {m:<9} {mean:.3f}  {verdict}")
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
