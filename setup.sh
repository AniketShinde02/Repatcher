#!/usr/bin/env bash
# AI Watermark Remover & Background Preserver — Setup Script for Linux/macOS
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

export PYTHONUTF8=1

echo "==================================================="
echo "  AI Watermark Remover & Background Preserver Setup"
echo "==================================================="
echo ""

# Find Python 3.10+
PYTHON_BIN=""
for cmd in python3.12 python3.11 python3.10 python3 python; do
    if command -v "$cmd" >/dev/null 2>&1; then
        PYTHON_BIN="$cmd"
        break
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo "❌ Error: Python 3.10+ was not found in PATH."
    exit 1
fi

echo "Using Python binary: $PYTHON_BIN"

# Create Virtual Environment if missing
if [ ! -d "venv" ]; then
    echo "[1/3] Creating virtual environment (venv)..."
    "$PYTHON_BIN" -m venv venv
else
    echo "[1/3] Virtual environment already exists."
fi

# Upgrade pip and install requirements
echo "[2/3] Installing dependencies..."
./venv/bin/python -m pip install --upgrade pip
./venv/bin/python -m pip install -r requirements.txt

# Run Environment Diagnostic
echo ""
echo "[3/3] Running Environment Diagnostic..."
./venv/bin/python scripts/env_check.py || true

echo ""
echo "==================================================="
echo "  Setup complete! Run ./start.sh to launch."
echo "==================================================="
