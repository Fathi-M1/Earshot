"""Raw audio never touches disk (CLAUDE.md non-negotiable). The only audio files
allowed in the tree are the explicit bench WAVs under tests/audio/. The silent
Media-Session WAV is generated in RAM and must not be a file on disk."""

from pathlib import Path

from earshot import daemon

REPO_ROOT = Path(__file__).resolve().parent.parent
AUDIO_EXTS = {".wav", ".pcm", ".mp3", ".flac", ".m4a"}
ALLOWED_DIR = REPO_ROOT / "tests" / "audio"
SKIP_DIRS = {".venv", ".git", "models", "node_modules", "__pycache__"}


def _iter_audio_files():
    for p in REPO_ROOT.rglob("*"):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.suffix.lower() in AUDIO_EXTS and p.is_file():
            yield p


def test_no_audio_files_outside_bench_dir():
    offenders = [str(p) for p in _iter_audio_files() if ALLOWED_DIR not in p.parents]
    assert not offenders, f"unexpected audio files on disk: {offenders}"


def test_silent_wav_is_in_memory_only():
    data = daemon._silent_wav()
    assert data[:4] == b"RIFF" and data[8:12] == b"WAVE"
    # Generating it must not create any file on disk.
    offenders = [str(p) for p in _iter_audio_files() if ALLOWED_DIR not in p.parents]
    assert not offenders
