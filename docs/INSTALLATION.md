# Installation & Setup Guide

This guide covers setup instructions for Windows, Linux, macOS, and cloud environments.

---

## 💻 System Requirements

- **Operating System**: Windows 10/11, Ubuntu 20.04+, macOS 12+
- **Python**: 3.10, 3.11, or 3.12
- **System Memory**: Minimum 4GB RAM
- **GPU (Recommended)**: NVIDIA GPU with CUDA 11.8 or 12.1+ (2GB+ VRAM)
- **Disk Space**: ~1.5 GB free storage (includes PyTorch runtime and LaMa model weights)

---

## 🪟 Windows Setup

1. **One-Click Automated Setup**:
   Double-click `setup.bat`. This script will:
   - Create a local Python virtual environment (`venv`)
   - Install pinned dependencies from `requirements.txt`
   - Run system hardware diagnostics

2. **Launch Application**:
   Double-click `Start_AI_Remover.bat`. Your browser will automatically open `http://127.0.0.1:7860`.

---

## 🐧 Linux / 🍎 macOS Setup

1. **Run Setup Script**:
   ```bash
   chmod +x setup.sh start.sh
   ./setup.sh
   ```

2. **Launch Application**:
   ```bash
   ./start.sh
   ```

---

## ☁️ Google Colab Setup

1. Open [Google Colab](https://colab.research.google.com/).
2. Upload `AI_Watermark_Remover_Colab.ipynb`.
3. Ensure runtime type is set to **T4 GPU** (`Runtime > Change runtime type > T4 GPU`).
4. Execute cells in order to run in cloud GPU environment.
