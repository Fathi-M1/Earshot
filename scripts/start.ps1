# Launch Earshot: caption bar (separate window) + daemon (this window, shows the QR).
$ErrorActionPreference = "SilentlyContinue"
Set-Location $PSScriptRoot\..

# Caption bar in its own window.
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; uv run earshot bar"

# Daemon in this window (prints the phone QR to scan).
uv run earshot serve
