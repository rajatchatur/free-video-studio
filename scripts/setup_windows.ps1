# Free Video Studio - setup for Windows 10/11 (run in PowerShell, not as admin is fine)
$ErrorActionPreference = "Stop"

# Free tools via winget (built into Windows 10/11)
winget install --id Gyan.FFmpeg -e --accept-package-agreements --accept-source-agreements
winget install --id OpenJS.NodeJS.LTS -e --accept-package-agreements --accept-source-agreements
winget install --id Python.Python.3.12 -e --accept-package-agreements --accept-source-agreements
winget install --id Git.Git -e --accept-package-agreements --accept-source-agreements

Write-Host "Close and reopen PowerShell so PATH updates, then run this script again."
if (-not (Get-Command node -ErrorAction SilentlyContinue)) { exit 0 }

Set-Location (Split-Path -Parent $PSScriptRoot)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

npx --yes hyperframes doctor
npx skills add heygen-com/hyperframes

Write-Host "Setup finished. Start the studio with:  .\scripts\run_windows.ps1"
