# Earshot one-line install (Windows PowerShell). Run from the repo root:
#   powershell -ExecutionPolicy Bypass -File scripts\install.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

function Have($name) { [bool](Get-Command $name -ErrorAction SilentlyContinue) }

Write-Host "== Earshot install =="

# 1. uv
if (-not (Have uv)) {
    Write-Host "Installing uv..."
    winget install -e --id astral-sh.uv --accept-source-agreements --accept-package-agreements
}

# 2. Ollama
$ollamaExe = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
if (-not (Have ollama) -and -not (Test-Path $ollamaExe)) {
    Write-Host "Installing Ollama..."
    winget install -e --id Ollama.Ollama --accept-source-agreements --accept-package-agreements
}
if (-not (Have ollama)) { $ollama = $ollamaExe } else { $ollama = (Get-Command ollama).Source }

# 3. Ollama env (keep models warm, single inference)
[Environment]::SetEnvironmentVariable("OLLAMA_KEEP_ALIVE", "-1", "User")
[Environment]::SetEnvironmentVariable("OLLAMA_NUM_PARALLEL", "1", "User")

# 4. Python deps
Write-Host "Syncing Python dependencies..."
uv sync --extra dev

# 5. Ollama models
Write-Host "Pulling local models (qwen2.5:3b, 1.5b, nomic-embed-text)..."
& $ollama pull qwen2.5:3b
& $ollama pull qwen2.5:1.5b
& $ollama pull nomic-embed-text

# 6. Whisper (small + base) and Piper voice
Write-Host "Downloading whisper + Piper..."
& "$PSScriptRoot\fetch-models.ps1"
uv run python -c "from faster_whisper import WhisperModel as W; W('small', device='cpu', compute_type='int8', download_root='models/whisper'); print('whisper small OK')"

# 7. Start-menu shortcut "Earshot" -> daemon + caption bar
$startDir = [Environment]::GetFolderPath('Programs')
$lnk = Join-Path $startDir 'Earshot.lnk'
$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut($lnk)
$sc.TargetPath = "powershell.exe"
$sc.Arguments = "-NoExit -ExecutionPolicy Bypass -File `"$PWD\scripts\start.ps1`""
$sc.WorkingDirectory = "$PWD"
$ico = "$PWD\design\favicon.ico"
if (Test-Path $ico) { $sc.IconLocation = $ico }
$sc.Save()

Write-Host ""
Write-Host "Done. Launch 'Earshot' from the Start menu (it starts the daemon + caption bar)."
Write-Host "Scan the QR shown in the terminal / on http://127.0.0.1:7777/live with your iPhone."
