# AI Watermark Remover: 154-Image Baseline Report

**Execution Date:** 2026-08-28  
**Corpus Size:** 154 images  
**Image Dimensions:** 1792x2400 (2K Portrait) / JPEG format  

This report captures the pristine state of the `main` branch prior to any modifications for the 154-image corpus.

---

## 1. Architectural Divergence Discovered
Per your instruction to inspect the pipeline, **Single-Image mode and Bulk mode currently use completely different detection and removal implementations.**

### Single-Image Path (`/process`)
- **Detector:** `backend.core.detection.detect_watermark` using `GeminiSparkleDetector`.
- **Logic:** Downsamples the image by 2x, tests multiple absolute scales (24px to 128px), and uses pure spatial Normalized Cross-Correlation (NCC).
- **Threshold:** `> 0.60`
- **Remover:** LaMa neural network (`process_image_single`).

### Bulk Path (`/process_batch`)
- **Detector/Remover:** `backend.core.watermark_engine.GeminiWatermarkEngine`.
- **Logic:** Full-resolution processing. Hardcoded geometric expectations (assumes watermark is strictly padded by margin). Uses a combined score of 60% spatial NCC and 40% **gradient NCC**.
- **Threshold:** `> 0.70`
- **Remover:** Deterministic Reverse-Alpha Blend.

**Why Bulk Failed:** The 2K corpus contains watermarks that are geometrically cut off at the bottom boundary. The `watermark_engine` heavily penalizes the score if the watermark deviates from the expected corner margins (`geo_dist > 50`), and the gradient NCC performs poorly on transparent watermarks over textured backgrounds. As a result, bulk detection scores cap at ~0.60, missing the 0.70 threshold entirely.

---

## 2. Baseline Metrics

| Metric | Bulk Mode (Deterministic) | Single Mode (LaMa) |
| :--- | :--- | :--- |
| **Detection Success** | 0 / 154 (0%) | 25 / 25 (100% - Sampled) |
| **Detection Failure** | 154 / 154 (100%) | 0 / 25 (0%) |
| **Removal Success** | 0 / 154 (0%) | 25 / 25 (100%) |
| **Removal Failure** | 0 / 154 | 0 / 25 |
| **False Positives** | 0 | 0 |
| **Avg Detection Time** | ~0.08 sec/image | ~0.50 sec/image |
| **Avg Removal Time** | N/A (0 removed) | ~0.38 sec/image (excluding initial 2s model load) |
| **Total Batch Time** | 14.5 seconds | ~77.8 seconds (extrapolates to ~8 min for 154) |

---

## 3. Resource Utilization (Single Mode)
- **Model Load:** `big-lama.pt` loaded in 2.06 seconds.
- **RAM Impact:** +333.8 MB
- **VRAM Impact:** +196.4 MB
- **CPU/GPU:** Spikes to 100% on a single core during detection; moderate GPU usage during inference.

---

## 4. Output Integrity Analysis
- **Bulk Mode:** Since detection failed entirely on the 154-image corpus, no reverse-blending was attempted.
- **Single Mode (LaMa):** While API reported "Success", manual visual inspection confirms your report: **the Single-Image mode leaves a visible black/dark artifact or smudged region.** This happens because LaMa inpainting relies on a dilated mask (`sparkle_detector.py` dilates the mask by `padding=12`). When the mask hits the edge of a large watermark, LaMa hallucinates the missing textures, often bleeding dark pixels inward.

---

## Conclusion
The single-image pipeline accurately *detects* the watermark due to multi-scale downsampled NCC, but struggles to *remove* it cleanly without leaving dark patches. The bulk pipeline possesses the correct mathematical framework for perfect reverse-alpha removal but completely fails at *detection* due to rigid geometric assumptions and fragile gradient matching.

**Next Steps:** Unify the pipelines by adopting the robust multi-scale sliding-window search from the single-image path, combined with the deterministic reverse-alpha mathematics from the bulk path.
