# build.ps1 - Windows single-file build script
# Usage: .\build.ps1

$ErrorActionPreference = "Stop"

Write-Host "=" * 50
Write-Host "Alipay Notify - Windows Build"
Write-Host "=" * 50

# Check if virtual environment exists
if (-not (Test-Path ".venv")) {
    Write-Host "[*] Creating virtual environment..."
    python -m venv .venv
}

# Activate virtual environment
Write-Host "[*] Activating virtual environment..."
. .\.venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "[*] Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

# Clean previous builds
Write-Host "[*] Cleaning previous builds..."
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }

# Build
Write-Host "[*] Building single-file exe..."
pyinstaller alipay_notify.spec --clean --noconfirm

Write-Host ""
Write-Host "=" * 50
Write-Host "Build complete!"
Write-Host "Output: dist\alipay_notify.exe"
Write-Host "=" * 50
