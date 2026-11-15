Set-Location (Split-Path -Parent $PSScriptRoot)
.\.venv\Scripts\Activate.ps1
if (-not $env:WHISPER_MODEL) { $env:WHISPER_MODEL = "base" }
Write-Host "Open http://127.0.0.1:8000 in your browser"
python server.py
