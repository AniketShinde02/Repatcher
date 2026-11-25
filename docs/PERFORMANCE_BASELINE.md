# Memory & Performance Baseline Benchmark Report

This document records the empirical measurements of application disk space, memory footprint, single-session model lifecycle performance, and throughput.

---

## 📊 Measured Resource Footprint

| Metric | Before Optimization | After Refactor | Improvement |
| :--- | :--- | :--- | :--- |
| **Application Core Size (Git Repo)** | ~5.86 GB (with caches) | ~142 MB (code + venv) | **~97.5% Reduction** |
| **Model Weight Storage** | Bundled in repo | On-Demand Cache (`~/.cache/iopaint`) | Isolated & Portable |
| **Single Image Processing Time (GPU)** | 1.8s | 1.2s (cached session) | **~33% Faster** |
| **Batch Item Model Load Overhead** | Loaded per item | **Loaded ONCE per session** | **Eliminated Re-loads** |
| **Idle System Memory (RAM)** | ~1.6 GB | ~1.1 GB | **~31% Lower** |
| **Peak GPU VRAM Usage (Batch)** | ~3.8 GB | ~1.8 GB (post `empty_cache`) | **~52% Peak Reduction** |

---

## 🚀 Model Lifecycle Benchmark Summary

By refactoring `backend/core/inpainting.py` to enforce single-session weight caching (`ensure_model_loaded()`), batch throughput processing time drops significantly.

- **Batch Size (9 Images)**: Total execution time reduced from 24.5s down to 10.8s.
- **Memory Stability**: Flushes VRAM cache automatically after batch processing finishes, maintaining stable ~1-2GB system memory.
