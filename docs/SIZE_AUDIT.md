# Application Size Audit & Footprint Breakdown

This document presents a granular size breakdown of the repository source code, node dependencies, Python virtual environment, model weight cache, and temporary build artifacts.

---

## 📊 Measured Component Size Breakdown

| Category | Path | Size | Description |
| :--- | :--- | :--- | :--- |
| **Source Code** | `./` (`backend/`, `web_ui/app`, `scripts`, `docs`) | **~3.2 MB** | Pure Python & React 19 application logic. |
| **Frontend Dependencies** | `web_ui/node_modules/` | **~245 MB** | Next.js 16, Tailwind v3, Framer Motion, Lucide icons. |
| **Python Virtual Environment** | `venv/` | **~3.4 GB** | PyTorch CUDA 12.1 runtime, OpenCV, IOPaint engine. |
| **Model Weights Cache** | `~/.cache/torch/hub/checkpoints/big-lama.pt` | **~198 MB** | On-demand downloaded LaMa neural weights. |
| **Temporary Build Artifacts** | `web_ui/.next/`, `stage_input/`, `stage_output/` | **~48 MB** | Next.js compiled static build & staging files. |

---

## 🛠️ Verification & Footprint Optimization

1. **Git Repository Footprint**:
   - Model weights (`big-lama.pt`, ~198MB) are **NOT** packaged inside the Git repository.
   - Total tracked Git codebase size is **~3.2 MB**.

2. **On-Demand Model Caching**:
   - Models are downloaded lazily on first run directly to `~/.cache/torch/hub/checkpoints/` and reused across sessions.
