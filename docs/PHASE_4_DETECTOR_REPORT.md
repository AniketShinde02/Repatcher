# Phase 4 — Detector Evaluation & Architecture Report

**Date**: 2026-08-12
**Author**: Antigravity AI
**Machine**: JinWoo-PC

---

## 1. Executive Summary & Status Classification

Phase 4 evaluated whether a lightweight classical Computer Vision (CV) detector can achieve production-grade reliability across arbitrary image resolutions, watermark positions, opacities, and background textures.

### Classification: **RED**
> **RED — Classical CV cannot reliably distinguish the target watermark.**
>
> While Detector v4 achieved **96.5% recall** across 200 realistic synthetic positives placed in arbitrary positions (bottom-right, bottom-left, center, top-right), removing the hard bottom-right location constraint exposed an unavoidable physical limitation: classical geometric heuristics (aspect ratio, solidity, extent, isoperimetric quotient Q, intensity) produce an **81.5% false-positive rate** on adversarial negative shapes (jewelry stars, cross logos, embroidery, glints).

---

## 2. Dataset Composition

| Dataset Category | Source | Images | Description | Expectation |
|---|---|---|---|---|
| **Synthetic Positive** | Phase 2 baseline | 5 | Machine-generated 4-point star polygons | Positive (True) |
| **Synthetic Negative** | Phase 2 baseline | 5 | Machine-generated shapes (circles, tags, text) | Negative (False) |
| **Adversarial** | Phase 4 generator | 130 | Rotated stars, glints, jewelry, embroidery, crosses | Negative (False) |
| **Realistic Positive** | Phase 4 generator | 200 | Composited watermarks (picsum.photos, opacity 15-55%, 4 positions) | Positive (True) |
| **Real Positive** | `tests/dataset/real_positive/` | 0 | Real Gemini-watermarked product photos | **DATASET INCOMPLETE** |
| **Real Negative** | `tests/dataset/real_negative/` | 0 | Real product photos without watermarks | **DATASET INCOMPLETE** |

---

## 3. Benchmark Results

### Detailed Metrics Table

| Category | Total (N) | TP | TN | FP | FN | Precision | Recall | F1 Score | FP Rate | Latency (avg) |
|---|---|---|---|---|---|---|---|---|---|---|
| **Synthetic Positive** | 5 | 5 | 0 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | 0.00% | 34.2 ms |
| **Synthetic Negative** | 5 | 0 | 4 | 1 | 0 | 0.0000 | 1.0000 | 0.0000 | 20.00% | 32.1 ms |
| **Adversarial** | 130 | 0 | 24 | 106 | 0 | 0.0000 | — | 0.0000 | **81.54%** | 63.0 ms |
| **Realistic Positive** | 200 | 193 | 0 | 0 | 7 | 1.0000 | **0.9650** | **0.9822** | 0.00% | 221.7 ms |
| **Position Invariance** | 6 | 6 | 0 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | 0.00% | — |

---

## 4. Root Cause Analysis: Why Classical CV Fails (v3 vs v4)

### The Detector v3 Dilemma (Phase 3)
In Phase 3, Detector v3 enforced a **hard bottom-right quadrant constraint** (`≥55% W+H`).
- **Result**: False positives dropped on non-corner shapes, but **recall on synthetic positives dropped to 0%** when watermarks were non-corner.
- **Flaw**: Hard-coding position violates real-world user workflows (cropped, centered, or re-aligned images).

### The Detector v4 Dilemma (Phase 4)
Detector v4 converted location into a **5% soft bonus signal (`S8`)**, evaluating candidates on 8 independent geometric/intensity signals:
1. `S1` Aspect Ratio (symmetric 1.0)
2. `S2` Solidity (concave 0.52)
3. `S3` Extent (0.28-0.68)
4. `S4` Isoperimetric Quotient Q (0.30-0.55)
5. `S5` Intensity Profile (translucent Top-Hat 15-80)
6. `S6` Relative Size (1.0-4.0% diagonal)
7. `S7` Edge Regularity (gradient variance)
8. `S8` Soft Location Bonus (corner preference)

- **Positive Result**: **96.5% recall (193/200)** on realistic positives across 4 position quadrants. 100% detection on 6-position invariance tests.
- **Negative Result**: **81.5% false positives (106/130)** on adversarial images.

### Fundamental Technical Barrier
Without a position lock, **any 4-pointed diamond star contour in an image** (jewelry reflections, embroidered fabric, cross motifs, star logos, sparkle filters) shares identical aspect ratio, solidity, extent, and isoperimetric quotient Q with the Gemini watermark. **Pure geometry cannot distinguish an anti-aliased 4-point star on a dress from a Gemini watermark.**

---

## 5. Image Quality Preservation (9A Mandate Verification)

As required by Phase 4 §9A, image quality preservation was tested across JPEG, PNG, and WEBP formats using objective PSNR and SSIM metrics evaluated across three distinct zones:
- **Zone A**: Entire Image
- **Zone B**: Outside-Mask Region (**CRITICAL Preservation Metric**)
- **Zone C**: Inpainted Region

### Quality Test Results (`tests/test_image_quality.py`)

| Image Format | Input Resolution | Output Resolution | Aspect Ratio Preserved | Format Preserved | Zone B PSNR | Zone B SSIM | Status |
|---|---|---|---|---|---|---|---|
| **JPEG** | 800×600 | 800×600 | Identical (1.333) | `.jpg` | **62.28 dB** | **1.0000** | PASS |
| **JPEG High-Res** | 1920×1080 | 1920×1080 | Identical (1.778) | `.jpg` | **45.62 dB** | **0.9996** | PASS |
| **PNG** | 800×600 | 800×600 | Identical (1.333) | `.png` | **inf dB** (Lossless) | **1.0000** | PASS |
| **WEBP** | 800×600 | 800×600 | Identical (1.333) | `.webp` | **inf dB** (Lossless) | **1.0000** | PASS |

### Quality Pipeline Safeguards Implemented
1. **Zero Silent Format Conversion**:
   - `web_ui/app/api/inpaint/single/route.js` fixed: removed hardcoded `.png` extension and MIME type.
   - `backend/app/main.py` `/process` endpoint fixed: detects true format via magic bytes (`get_source_format()`) and preserves original extension.
   - Response MIME types explicitly map to source format (`image/jpeg`, `image/png`, `image/webp`).
2. **Quality Settings**:
   - JPEG saved at `quality=95` with `subsampling=0`.
   - PNG saved with `compress_level=0` (lossless uncompressed).
   - WEBP saved with `lossless=True, quality=100`.
3. **No Quality-Destroying Preprocessing**:
   - Detection runs on full-resolution image arrays or temporary downsampled detection copies; inpainting and masking operate **strictly on full-resolution source pixels**.

---

## 6. Lightweight Machine Learning (ML) Tradeoff Analysis

Because classical CV is classified as **RED**, we evaluated lightweight ML options to replace or augment the geometric detector before introducing any heavy neural model.

### Options Comparison Table

| Approach | Model / Tech | Model Size | Process RAM | CPU Latency | GPU Latency | Precision (Est.) | Recall (Est.) | License | Integration Effort |
|---|---|---|---|---|---|---|---|---|---|
| **Option A: Signal Classifier** | **XGBoost / LightGBM** | **< 1 MB** | **< 5 MB** | **< 2 ms** | N/A | **92%** | **95%** | MIT / BSD | **Minimal (1 day)** |
| **Option B: Ultralytics YOLO Nano** | **YOLOv8n / YOLOv11n** | **~6 MB** | **~150 MB** | **15–30 ms** | **4–8 ms** | **98%** | **97%** | AGPL / Commercial | Low (2 days) |
| **Option C: MobileNet-SSD v3** | **MobileNetV3-Small SSD** | **~10 MB** | **~120 MB** | **20–30 ms** | **5–10 ms** | **94%** | **94%** | Apache 2.0 | Low (2 days) |
| **Option D: Open-Vocabulary / Zero-Shot** | **Grounding DINO / MobileSAM** | **~350 MB+** | **~2.5 GB+** | **800–2500 ms** | **150–400 ms** | **95%** | **90%** | Apache 2.0 | High (3–5 days) |

### Detailed Evaluation of Options

1. **Option A — XGBoost / LightGBM Signal Classifier (RECOMMENDED HYBRID)**:
   - **Mechanism**: Use classical CV (Top-Hat + contour extraction) to propose candidate bounding boxes, but extract a 16-element feature vector per candidate (intensity histogram, local patch HOG/LBP texture, gradient variance, spatial location, Q factor). Pass feature vector to a 200 KB trained XGBoost binary decision tree.
   - **Pros**: Zero heavy dependencies, <1MB disk footprint, <2ms latency, near-zero RAM overhead. Solves the 81.5% FP issue by learning texture/edge patterns of true Gemini stars vs. jewelry/embroidered stars.
   - **Cons**: Requires 100–200 annotated real product images for training.

2. **Option B — YOLOv8n / YOLOv11n Object Detector (BEST PURE ML)**:
   - **Mechanism**: Train a single-class (`gemini_watermark`) YOLO nano model directly on 640x640 images.
   - **Pros**: State-of-the-art precision/recall (98%+), robust against extreme backgrounds, highly optimized ONNX/OpenVINO runtime available.
   - **Cons**: ~6MB model weight, requires `ultralytics` or `onnxruntime` dependency.

3. **Option D — Heavy Vision Models (REJECTED)**:
   - Grounding DINO or Segment Anything (SAM) add 350MB+ weights, 2GB+ VRAM, and >1 second latency per image. They violate our core system constraint of remaining lightweight and local-first.

---

## 7. Recommended Next Steps & Roadmap

1. **Maintain Current Confidence-Gated UI Gating**:
   - Until ML classifier is trained, the current UI handles uncertainty gracefully:
     - `HIGH` confidence → automatic processing.
     - `MEDIUM` confidence → interactive mask preview modal requiring explicit user confirmation.
     - `LOW/NONE` → no action taken, original image preserved.

2. **Phase 5 Data Collection**:
   - Collect 50-100 real Gemini-watermarked product images in `tests/dataset/real_positive/` and 50 clean images in `tests/dataset/real_negative/`.

3. **Implement Hybrid OpenCV + XGBoost Candidate Classifier**:
   - Train an XGBoost model on patch HOG features extracted from contour candidates.
   - Keep total binary footprint under 1 MB.
