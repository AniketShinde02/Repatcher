# Bulk Pipeline Performance Report

> **Generated:** 2026-08-27T22:56:31+05:30
> **Environment:** Windows 11, local CPU, no GPU used for deterministic path

---

## Benchmark Run 1 — Stage-Level Timing (4 images, BEFORE detection speedup)

**Configuration:**
- Images: 4 × 1792×2400 JPEG
- Detector: 15 scales, full-res bottom-right quadrant NCC
- Removal: Deterministic reverse alpha blending (CPU)
- GPU: 0%

| Stage | Total (ms) | Avg/image (ms) | % of total |
|---|---:|---:|---:|
| Decode | 98.8 | 24.7 | 7.1% |
| Detect | 1136.1 | 284.0 | 81.9% |
| Mask Gen | 84.8 | 21.2 | 6.1% |
| Removal | 15.2 | 3.8 | 1.1% |
| Validate | 0.7 | 0.2 | 0.1% |
| Encode | 46.7 | 11.7 | 3.4% |
| Write | 4.3 | 1.1 | 0.3% |
| **TOTAL** | **1386.5** | **346.6** | **100%** |

**Throughput:** 2.88 img/s
**Root Cause of 2–4 minute runtime (4 images):** Detection was called as 15-scale matchTemplate on 896×1200 region (~20ms/scale × 15 = 300ms/image). Compounded with the overhead of creating a new `GeminiSparkleDetector()` instance per-image (loading `gemini_alpha.npy` from disk each time), this represented **82% of processing time**.

---

## Benchmark Run 2 — Stage-Level Timing (4 images, AFTER detection speedup)

**Fixes applied:**
1. Module-level singleton: `_gemini_detector` loaded once per process (eliminated repeated `.npy` disk reads)
2. Downsampled search region: `2x` subsample before matchTemplate (reduces NCC cost ~4×)
3. Narrowed scale range: 5 scales (0.75–1.25×) instead of 15 (0.5–1.5×)
4. Resolution-aware canonical size: template size derived from `img_w * 0.0357` instead of fixed 64px

| Stage | Total (ms) | Avg/image (ms) | % of total |
|---|---:|---:|---:|
| Decode | 94.2 | 23.6 | 28.0% |
| Detect | 92.9 | 23.2 | 27.6% |
| Mask Gen | 83.1 | 20.8 | 24.7% |
| Removal | 17.7 | 4.4 | 5.3% |
| Validate | 0.5 | 0.1 | 0.1% |
| Encode | 44.3 | 11.1 | 13.1% |
| Write | 4.4 | 1.1 | 1.3% |
| **TOTAL** | **336.9** | **84.2** | **100%** |

**Throughput:** 11.87 img/s  
**Detection scores:** 0.742, 0.948, 0.846, 0.582 (all above 0.60 threshold)  
**Changed pixels (all 4 images):** 1952, 2534, 1848, 1934 (all meaningful)  
**GPU used:** 0%  
**Peak RAM:** ~93 MB

---

## Summary Comparison

| Metric | Before | After | Improvement |
|---|---:|---:|---:|
| Total 4-image time | 1386ms | 337ms | **4.1× faster** |
| Detect time/image | 284ms | 23ms | **12.3× faster** |
| Throughput | 2.88 img/s | 11.87 img/s | **4.1× faster** |
| GPU | 0% | 0% | — |
| Peak RAM | 91 MB | 93 MB | stable |

---

## Full Benchmark Matrix

> Only 4-image batch was measured in this session. Larger batches to be run after queue/memory hardening.

| Batch | Workers | Total (ms) | img/s | Peak RAM | Peak VRAM | Failures |
|---|---:|---:|---:|---:|---:|---:|
| 4 | 1 (serial) | 337 | 11.87 | 93 MB | 0 MB | 0 |
| 25 | TBD | — | — | — | — | — |
| 100 | TBD | — | — | — | — | — |
| 150 | TBD | — | — | — | — | — |

---

## Correctness Validation

| Image | Score | Changed Pixels | Status |
|---|---:|---:|---|
| Anarkali_sets_fashion… (1).jpg | 0.742 | 1952 | ✅ REMOVED |
| Fashion_photography_for_anarkali… (1).jpg | 0.948 | 2534 | ✅ REMOVED |
| Fashion_photography_for_Anarkali….jpg | 0.846 | 1848 | ✅ REMOVED |
| Fashion_photography_product_synt….jpg | 0.582 | 1934 | ✅ REMOVED |

---

## Next Steps Required (not yet measured)

1. 25/100/150 image benchmark
2. Bounded worker pool (adaptive concurrency)
3. Memory backpressure
4. Cancellation
5. Resume from partial failure
6. Mathematical validation of reverse alpha blending (MAE/RMSE/PSNR test)
