# Technical Architecture & Pipeline Specification

AI Watermark Remover & Background Preserver is structured as a privacy-first, local-execution desktop and web utility designed for high-precision watermark removal.

---

## 🏗️ High-Level System Architecture

```
                       ┌────────────────────────────────────────┐
                       │               User Interface           │
                       │   (Gradio Web App / Tkinter GUI)       │
                       └───────────────────┬────────────────────┘
                                           │
                                           ▼
                       ┌────────────────────────────────────────┐
                       │          Mask Generation Stage         │
                       │  • Morphological Top-Hat (Auto)        │
                       │  • Interactive Canvas (Brush)          │
                       │  • Offset Bounding Box (Custom)        │
                       └───────────────────┬────────────────────┘
                                           │
                                           ▼
                       ┌────────────────────────────────────────┐
                       │       Inpainting Neural Engine          │
                       │  • IOPaint LaMa (NVIDIA CUDA / CPU)    │
                       │  • Selective Edge Dilation Masking     │
                       └───────────────────┬────────────────────┘
                                           │
                                           ▼
                       ┌────────────────────────────────────────┐
                       │       Output Management & Cleanup      │
                       │  • Auto-save to Output Directory       │
                       │  • GPU Cache Clearing (empty_cache)    │
                       └────────────────────────────────────────┘
```

---

## 🔬 Core Components & Data Flow

### 1. Auto-Detection Pipeline (`detect_gemini_star_mask`)
- **ROI Extraction**: Crop bottom-right region (default 300x300px).
- **Top-Hat Filtering**: Apply `cv2.morphologyEx` using `cv2.MORPH_TOPHAT` with a 45px elliptical kernel to isolate bright local features independently of background luminance.
- **Binarization & Contour Filtering**: Apply thresholding (`tophat_thresh_val`), locate external contours, and filter by area size ($20 < \text{area} < 4000$).
- **Mask Dilation**: Apply binary dilation using an $N \times N$ kernel (default 12px padding) to cover translucent antialiased edges.

### 2. Neural Inpainting Engine (`iopaint.batch_processing`)
- **Model**: LaMa (Large Mask Inpainting) fast Fourier convolution architecture.
- **Execution Target**: PyTorch CUDA (NVIDIA GPU, ~1-2s per image) or CPU (~10-20s per image).
- **Batch Processing**: Per-image masks stored in `stage_mask/<name>.png` matched to `stage_input/<name>.png`.

### 3. Memory & Resource Control
- Memory footprint is capped at ~1.2 - 1.8 GB RAM / VRAM by flusing `torch.cuda.empty_cache()` after each batch execution.
