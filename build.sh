#!/bin/bash
# build.sh - Linux single-file build script
# Usage: ./build.sh

set -e

echo "=================================================="
echo "Alipay Notify - Linux Build"
echo "=================================================="

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "[*] Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "[*] Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "[*] Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

# Clean previous builds
echo "[*] Cleaning previous builds..."
rm -rf build dist

# Build
echo "[*] Building single-file executable..."
pyinstaller alipay_notify.spec --clean --noconfirm

echo ""
echo "=================================================="
echo "Build complete!"
echo "Output: dist/alipay_notify"
echo "=================================================="
