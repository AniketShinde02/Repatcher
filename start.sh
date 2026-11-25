#!/usr/bin/env bash
# AI Watermark Remover & Background Preserver — Unix/macOS Launcher
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

export PYTHONUTF8=1

if [ ! -f "venv/bin/python" ]; then
    echo "⚠️ Virtual environment not found. Running ./setup.sh..."
    bash ./setup.sh
fi

echo "==================================================="
echo "  Starting AI Watermark Remover..."
echo "==================================================="
echo "Booting server & AI models..."

./venv/bin/python app.py
