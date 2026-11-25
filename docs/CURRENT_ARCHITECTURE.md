# Current System Architecture & Process Map

This document outlines the system architecture, component mapping, process tree, and data flow of the AI Watermark Remover & Background Preserver.

---

## 🗺️ System Data Flow Map

```
                  ┌────────────────────────────────────────┐
                  │                 User                   │
                  └───────────────────┬────────────────────┘
                                      │
                                      ▼
                  ┌────────────────────────────────────────┐
                  │       Frontend (Next.js 16 UI)         │
                  │   • Port: http://localhost:3000        │
                  │   • Drag & Drop File Picker            │
                  │   • Before/After Comparison Slider     │
                  └───────────────────┬────────────────────┘
                                      │  REST API (JSON / FormData)
                                      ▼
                  ┌────────────────────────────────────────┐
                  │       Backend (FastAPI Engine)         │
                  │   • Port: http://127.0.0.1:7860        │
                  │   • Strict File Security Validation    │
                  └───────────────────┬────────────────────┘
                                      │
                                      ▼
                  ┌────────────────────────────────────────┐
                  │     Detection & Mask Generation        │
                  │   • Morphological Top-Hat Filter       │
                  │   • Adaptive Contour Dilation          │
                  └───────────────────┬────────────────────┘
                                      │
                                      ▼
                  ┌────────────────────────────────────────┐
                  │      Inpainting Neural Engine          │
                  │   • IOPaint LaMa Model (NVIDIA CUDA)   │
                  │   • Single-Session Weight Caching      │
                  └───────────────────┬────────────────────┘
                                      │
                                      ▼
                  ┌────────────────────────────────────────┐
                  │          Output & Storage              │
                  │   • Target: ./processed_images         │
                  │   • Automatic Cache Cleanup            │
                  └────────────────────────────────────────┘
```

---

## ⚙️ Running Processes & Port Assignment

1. **Frontend Server**:
   - **Framework**: Next.js 16 (App Router) + React 19 + Turbopack
   - **Port**: `3000` (or `3001` fallback if 3000 occupied)
   - **Process Name**: `node.exe`

2. **Backend Engine**:
   - **Framework**: Python 3.12 + FastAPI / Gradio Backend Bridge
   - **Port**: `7860`
   - **Process Name**: `python.exe`

3. **Storage & Caching Directories**:
   - `stage_input/`: Local workspace temporary input staging
   - `stage_output/`: Local workspace temporary output staging
   - `stage_mask/`: Per-image dynamic binary mask staging
   - `processed_images/`: Final destination for processed media
   - `~/.cache/iopaint` / `torch/hub`: On-demand neural model cache
