# Fetch local models into .\models (whisper + Piper voice). Run while online.
# Ollama models are pulled separately: ollama pull qwen2.5:3b qwen2.5:1.5b nomic-embed-text
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

New-Item -ItemType Directory -Force -Path .\models\whisper, .\models\piper | Out-Null

Write-Host "Downloading faster-whisper models (tiny.en, base.en, base)..."
uv run python -c "from faster_whisper import WhisperModel as W; [W(m, device='cpu', compute_type='int8', download_root='models/whisper') for m in ['tiny.en','base.en','base']]; print('whisper OK')"

Write-Host "Downloading Piper voice (en_US-lessac-medium)..."
# Piper is added in Phase 4; this is a no-op until piper-tts is a dependency.
try {
    uv run python -m piper.download_voices en_US-lessac-medium --data-dir models\piper
    Write-Host "piper OK"
} catch {
    Write-Host "piper-tts not installed yet (added in P4) — skipping voice download."
}

Write-Host "Done. Models in .\models (git-ignored)."
