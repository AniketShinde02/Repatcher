# Bulk Pipeline Rollback Checkpoint

## Created: 2026-08-27T22:48:29+05:30

This document records the exact state of the repository at the time the deterministic
Gemini watermark removal pipeline was confirmed working.

## Git Details

| Field       | Value                                          |
|-------------|------------------------------------------------|
| Branch      | `main`                                         |
| Commit SHA  | `219ecad`                                      |
| Tag         | `checkpoint-bulk-deterministic-2026-08-27`     |
| Rollback branch | `checkpoint/bulk-deterministic-working`    |
| Working tree | **Clean** (all changes committed)             |

## Rollback Instructions

To return to the exact pre-optimization state:

```bash
git checkout checkpoint/bulk-deterministic-working
```

Or using the tag:

```bash
git checkout checkpoint-bulk-deterministic-2026-08-27
```

## What This Checkpoint Contains

- `backend/core/sparkle_detector.py` — GeminiSparkleDetector using real empirical alpha map
- `backend/core/gemini_alpha.npy` — Calibrated alpha map extracted from real failing images
- `backend/core/deterministic_removal.py` — Reverse alpha blending `original = (watermarked - alpha * logo) / (1 - alpha)`
- `backend/core/detection.py` — v4 detector with template matching integration
- `backend/core/batch_engine.py` — Bulk engine with deterministic routing (LaMa bypassed for Gemini)
- `CHANGELOG.md` — Full project history up to this point
- `BULK_ROOT_CAUSE.md` — Root cause analysis

## State at Checkpoint

- 4/4 test images process correctly
- Watermark detection: 290ms/image (template matching over 15 scales on full-res region)
- Deterministic removal: ~4ms/image
- Total: ~350ms/image end-to-end
- GPU: 0% for deterministic Gemini path
- LaMa: bypassed for confirmed Gemini sparkle detections

## Known Bottleneck (Being Fixed Post-Checkpoint)

Detection accounts for 82% of per-image time (290ms/350ms).
This is being addressed by:
1. Module-level singleton caching of the detector
2. Downsampled search region (2x subsample)
3. Narrowed scale range (5 scales instead of 15)
