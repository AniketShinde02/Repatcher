# Phase 4 + 9A Task List

## Block A — Quality Pipeline Fix (9A)
- [x] A1: Fix backend/core/inpainting.py — format-preserving export
- [x] A2: Fix backend/app/main.py — format-aware /process endpoint
- [x] A3: Fix web_ui/app/api/inpaint/single/route.js — remove PNG hardcode
- [x] A4: Create tests/test_image_quality.py — PSNR/SSIM regression (4/4 passed)

## Block B — Detector v4 Redesign
- [x] B1: Copy detection.py → detection_v3_baseline.py
- [x] B2: Rewrite detection.py — 8-signal candidate scoring, soft location
- [x] B3: Multi-candidate NMS
- [x] B4: Precise contour-based mask generation

## Block C — Dataset Generation
- [x] C1: Create scripts/generate_realistic_dataset.py (200 positives)
- [x] C2: Create scripts/generate_adversarial_dataset.py (130 images)
- [x] C3: Run both generators (200 realistic, 130 adversarial generated)

## Block D — Tests + Regression Suite
- [x] D1: Extend scripts/run_detection_benchmark.py (realistic_positive category)
- [x] D2: Create tests/test_position_invariance.py (6-position test — 6/6 passed)
- [x] D3: Run full regression benchmark (200 realistic: 96.5% recall; adversarial: 81.5% FP rate)
- [x] D4: Run quality tests (4/4 passed)

## Block E — UI Update
- [x] E1: Update watermark-editor.jsx — remove raw scores, human messages, collapsed diagnostics

## Block F — Report
- [x] F1: Create docs/DETECTOR_REGRESSION.md
- [x] F2: GREEN/YELLOW/RED classification (RED — classical CV limit reached)
- [x] F3: Create docs/PHASE_4_DETECTOR_REPORT.md
- [x] F4: npm run build verification (✓ Compiled successfully in 2.4s)
- [x] F5: Update CHANGELOG.md
