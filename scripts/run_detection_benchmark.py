"""
scripts/run_detection_benchmark.py
====================================
Phase 4 — Full Per-Category Detection Benchmark

Evaluates the detector against all available dataset categories.
Reports per-category and overall metrics.

Categories:
  synthetic_positive    — Phase 2/3 synthetic positives (5 images)
  synthetic_negative    — Phase 2/3 synthetic negatives (5 images)
  adversarial           — Phase 3/4 adversarial images (100 images)
  realistic_positive    — Phase 4 realistic composited positives (200 images)
  real_positive         — Real Gemini-watermarked images (user-provided)
  real_negative         — Real images without watermarks (user-provided)
"""

import time
import sys
from pathlib import Path

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from backend.core.detection import detect_watermark, CONFIDENCE_HIGH, CONFIDENCE_MEDIUM

CATEGORIES = {
    "synthetic_positive":  {"path": root_dir / "tests/dataset/positive",           "expect": True},
    "synthetic_negative":  {"path": root_dir / "tests/dataset/negative",           "expect": False},
    "adversarial":         {"path": root_dir / "tests/dataset/adversarial",        "expect": False},
    "realistic_positive":  {"path": root_dir / "tests/dataset/realistic_positive", "expect": True},
    "real_positive":       {"path": root_dir / "tests/dataset/real_positive",      "expect": True},
    "real_negative":       {"path": root_dir / "tests/dataset/real_negative",      "expect": False},
}

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def run_category(name: str, path: Path, expect: bool) -> dict | None:
    images = [f for f in path.glob("*") if f.suffix.lower() in IMAGE_EXTS]
    if not images:
        print(f"\n  [{name}] DATASET INCOMPLETE -- no images found.")
        return None

    # Limit output lines for large datasets (show summary, not every image)
    verbose = len(images) <= 30
    tp = tn = fp = fn = 0
    total_time = 0.0
    fp_cases = []

    print(f"\n--- [{name}] ({len(images)} images) ---")

    for img_path in sorted(images):
        t0 = time.time()
        res = detect_watermark(img_path)
        dt = time.time() - t0
        total_time += dt

        # "Detected" = confidence_level is HIGH or MEDIUM
        detected = res["detected"] and res["confidence_level"] in ("HIGH", "MEDIUM")

        if expect:
            if detected:
                tp += 1
                status = "TP"
            else:
                fn += 1
                status = f"FN (score={res['confidence']:.3f})"
        else:
            if not detected:
                tn += 1
                status = "TN"
            else:
                fp += 1
                fp_cases.append((img_path.name, res["confidence_level"], res["confidence"]))
                status = f"FP [{res['confidence_level']} score={res['confidence']:.3f}]"

        if verbose:
            print(f"  [{status}] {img_path.name} -- {dt*1000:.1f}ms")

    total = tp + tn + fp + fn
    precision = tp / (tp + fp) if (tp + fp) > 0 else (1.0 if fp == 0 else 0.0)
    recall    = tp / (tp + fn) if (tp + fn) > 0 else (1.0 if fn == 0 else 0.0)
    f1        = 2*precision*recall / (precision+recall) if (precision+recall) > 0 else 0.0
    fp_rate   = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fn_rate   = fn / (fn + tp) if (fn + tp) > 0 else 0.0
    avg_ms    = total_time / total * 1000 if total > 0 else 0.0

    print(f"  Precision={precision:.4f}  Recall={recall:.4f}  F1={f1:.4f}  "
          f"FP_rate={fp_rate:.4f}  FN_rate={fn_rate:.4f}  Avg={avg_ms:.1f}ms")

    if not verbose and fp_cases:
        print(f"  FP cases ({len(fp_cases)}):")
        for fname, level, score in fp_cases[:10]:
            print(f"    {fname}: {level} score={score:.3f}")
        if len(fp_cases) > 10:
            print(f"    ... and {len(fp_cases)-10} more")

    return {
        "name": name, "total": total,
        "tp": tp, "tn": tn, "fp": fp, "fn": fn,
        "precision": precision, "recall": recall, "f1": f1,
        "fp_rate": fp_rate, "fn_rate": fn_rate, "avg_ms": avg_ms,
    }


def classify_detector(results: list) -> str:
    """GREEN / YELLOW / RED classification based on key category results."""
    adv = next((r for r in results if r["name"] == "adversarial"), None)
    real_pos = next((r for r in results if r["name"] == "realistic_positive"), None)

    if not adv and not real_pos:
        return "UNKNOWN (insufficient data)"

    fp_rate = adv["fp_rate"] if adv else 1.0
    recall  = real_pos["recall"] if real_pos else 0.0

    if fp_rate <= 0.05 and recall >= 0.80:
        return "GREEN -- lightweight detector is sufficiently reliable"
    elif fp_rate <= 0.20 and recall >= 0.60:
        return "YELLOW -- acceptable with confidence-gated UI review"
    else:
        return "RED -- classical CV cannot reliably distinguish target; ML investigation required"


def run_all():
    print("=" * 70)
    print("  PHASE 4 -- FULL DETECTION BENCHMARK (Per-Category)")
    print("=" * 70)
    print(f"  Confidence thresholds: HIGH>={CONFIDENCE_HIGH}  MEDIUM>={CONFIDENCE_MEDIUM}")

    results = []
    for name, cfg in CATEGORIES.items():
        r = run_category(name, cfg["path"], cfg["expect"])
        if r:
            results.append(r)

    print("\n" + "=" * 70)
    print("  SUMMARY TABLE")
    print("=" * 70)
    hdr = f"{'Category':<22} {'N':>5} {'TP':>4} {'TN':>4} {'FP':>4} {'FN':>4} {'Prec':>7} {'Rec':>7} {'F1':>7} {'FP%':>6}"
    print(hdr)
    print("-" * 75)
    for r in results:
        print(f"{r['name']:<22} {r['total']:>5} {r['tp']:>4} {r['tn']:>4} {r['fp']:>4} {r['fn']:>4} "
              f"{r['precision']:>7.4f} {r['recall']:>7.4f} {r['f1']:>7.4f} {r['fp_rate']*100:>5.1f}%")

    classification = classify_detector(results)
    print(f"\n  DETECTOR CLASSIFICATION: {classification}")
    print("=" * 70)

    return results, classification


if __name__ == "__main__":
    run_all()
