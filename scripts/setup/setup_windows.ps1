# SwarmForge development environment check/setup (Windows 11, PowerShell).
# Usage:  .\scripts\setup\setup_windows.ps1
$ErrorActionPreference = "Stop"
Write-Host "== Tool check =="
py -0p
py -3.12 --version
git --version
cmake --version
if (Get-Command cl -ErrorAction SilentlyContinue) { cl } else { Write-Warning "cl not found: run from a Developer PowerShell for VS (MSVC) or use g++/clang++." }
wsl --status

Write-Host "== Virtual environment =="
if (-not (Test-Path .venv)) { py -3.12 -m venv .venv }
. .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev,api]"
swarmforge info
Write-Host "Done. Run 'pytest' to verify."
