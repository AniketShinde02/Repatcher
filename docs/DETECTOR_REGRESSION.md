# Detector Regression Tracking

**Last Updated**: 2026-08-12
**Author**: Antigravity AI
**Machine**: JinWoo-PC

---

## Benchmark History & Comparison

| Detector Version | Category | N | TP | TN | FP | FN | Precision | Recall | F1 | FP Rate | Latency |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **v3 Baseline** (Phase 3) | Synthetic Positive | 5 | 0 | 0 | 0 | 5 | 1.000 | **0.0000** | 0.0000 | 0.0000 | 7.9ms |
| **v3 Baseline** (Phase 3) | Synthetic Negative | 5 | 0 | 5 | 0 | 0 | 1.000 | 1.0000 | 1.0000 | 0.0000 | 7.4ms |
| **v3 Baseline** (Phase 3) | Adversarial | 30 | 0 | 20 | 10 | 0 | 0.000 | — | 0.0000 | **0.3333** | 7.9ms |
| **v3 Baseline** (Phase 3) | Realistic Positive | — | — | — | — | — | — | — | — | — | — |
| | | | | | | | | | | | |
| **v4 Candidate Scoring** | Synthetic Positive | 5 | 5 | 0 | 0 | 0 | 1.0000 | **1.0000** | 1.0000 | 0.0000 | 34.2ms |
| **v4 Candidate Scoring** | Synthetic Negative | 5 | 0 | 4 | 1 | 0 | 0.0000 | 1.0000 | 0.0000 | 0.2000 | 32.1ms |
| **v4 Candidate Scoring** | Adversarial (Expanded) | 130 | 0 | 24 | 106 | 0 | 0.0000 | — | 0.0000 | **0.8154** | 63.0ms |
| **v4 Candidate Scoring** | Realistic Positive | 200 | 193 | 0 | 0 | 7 | 1.0000 | **0.9650** | **0.9822** | 0.0000 | 221.7ms |
| **v4 Candidate Scoring** | Position Invariance | 6 | 6 | 0 | 0 | 0 | 1.0000 | **1.0000** | 1.0000 | 0.0000 | — |

---

## Core Findings & Progression Analysis

1. **Synthetic Positive Recall Fixed**:
   - v3 had **0% recall** on synthetic positives due to the hard bottom-right constraint (`≥55% W+H`).
   - v4 restored **100% recall (5/5)** by demoting location to a 5% soft bonus signal (`S8`).

2. **Position Invariance Verified**:
   - Tested 6 positions (bottom-right, bottom-left, top-right, top-left, center, top-edge-center).
   - v4 detected the target watermark at **6/6 positions (100%)**, demonstrating zero location bias.

3. **High Recall on Realistic Positives**:
   - Benchmark of 200 realistic synthetic positives (various positions, opacities 15-55%, resolutions 400x400 to 2000x1500, formats JPEG/PNG/WEBP).
   - Achieved **96.5% Recall (193/200)** with **0% False Positive Rate** on positive background images.

4. **The Fundamental Limit of Classical CV**:
   - On the expanded 130-image adversarial dataset (rotated stars, jewelry glints, antialiased stars, center stars, crosses, embroidery), v4 produced **106 false positives (81.5% FP rate)**.
   - Without a location gate, classical shape heuristics (aspect ratio, solidity, extent, isoperimetric quotient Q, intensity) cannot reliably distinguish generic 4-pointed diamond geometries (jewelry, embroidery, logos) from the target Gemini watermark.

---

## Status & Classification

- **Classification**: **RED**
- **Decision**: Classical OpenCV geometric heuristics have reached their physical limit. A lightweight machine learning (ML) object detector or trained feature classifier is required for production-grade watermark discrimination without false positive destruction.
