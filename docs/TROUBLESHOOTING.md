# Troubleshooting Guide

Common issues and resolution steps for AI Watermark Remover.

---

## 🔍 Diagnostic First Step

Before debugging manually, run the environment diagnostic tool:

```bash
# Windows
.\venv\Scripts\python.exe scripts\env_check.py

# Linux/macOS
./venv/bin/python scripts/env_check.py
```

---

## ❌ Common Errors & Solutions

### 1. `CUDA out of memory` / GPU Memory Errors
- **Cause**: Batch size or input image resolution is very large.
- **Solution**: Ensure **Clear GPU/RAM Cache** is checked in **⚙️ Advanced Options**. Alternatively, switch **Hardware Acceleration** to `cpu`.

### 2. `NameError` or Gradio UI Component Failures
- **Cause**: Corrupted dependencies or stale pycache.
- **Solution**: Run `python scripts/clean_temp.py` and restart via `Start_AI_Remover.bat`.

### 3. Port `7860` Already in Use
- **Cause**: Another Gradio or web application is running on port 7860.
- **Solution**: Set `SERVER_PORT=7861` in `.env` or close the process listening on port 7860 using task manager.

### 4. Smart Auto-Detect Misses Watermark
- **Cause**: Logo is located outside the bottom-right 300x300 search box or isn't a bright translucent star.
- **Solution**: Lower the **Star Luminance Sensitivity Threshold** slider in the UI, or switch to the **🖌️ Precision Brush Tool**.
