"""
tests/test_position_invariance.py
==================================
Phase 4 §11: Center-Crop Position Invariance Test

Generates one clean base image and composites a realistic Gemini-style watermark
at 6 distinct positions. The v4 detector must find it at ALL 6 positions.

Tests:
  1. Bottom-right (canonical)
  2. Bottom-left
  3. Top-right
  4. Top-left
  5. Center
  6. Near top edge (center-horizontal)

A detector that fails on any position other than bottom-right has a hard location bias.
The v4 detector should pass all 6 (no hard location gate).
"""

import sys
import math
import numpy as np
import cv2
from pathlib import Path

root = Path(__file__).parent.parent
sys.path.insert(0, str(root))

from backend.core.detection import detect_watermark


def build_star(outer_r: int) -> np.ndarray:
    """4-pointed star, semi-transparent BGRA."""
    size = outer_r * 4
    cx = cy = size // 2
    inner_r = outer_r / 2.5
    pts = []
    for i in range(8):
        angle = math.pi * i / 4 - math.pi / 4
        r = outer_r if i % 2 == 0 else inner_r
        pts.append([int(cx + r * math.cos(angle)), int(cy + r * math.sin(angle))])
    canvas = np.zeros((size, size, 4), dtype=np.uint8)
    poly = np.array(pts, np.int32)
    bgr = np.ascontiguousarray(canvas[:, :, :3])
    alpha = np.ascontiguousarray(canvas[:, :, 3])
    cv2.fillPoly(bgr, [poly], (255, 255, 255))
    cv2.fillPoly(alpha, [poly], 255)
    canvas[:, :, :3] = bgr
    canvas[:, :, 3] = alpha
    return canvas


def composite(base: np.ndarray, star: np.ndarray, cx: int, cy: int, opacity: float = 0.35) -> np.ndarray:
    result = base.copy()
    h, w = result.shape[:2]
    sh, sw = star.shape[:2]
    x0, y0 = cx - sw // 2, cy - sh // 2
    x1, y1 = x0 + sw, y0 + sh
    sx0 = max(0, -x0); sx1 = sw - max(0, x1 - w)
    sy0 = max(0, -y0); sy1 = sh - max(0, y1 - h)
    dx0, dy0 = max(0, x0), max(0, y0)
    dx1, dy1 = min(w, x1), min(h, y1)
    if dx1 <= dx0 or dy1 <= dy0:
        return result
    sc = star[sy0:sy1, sx0:sx1]
    alpha = (sc[:, :, 3] / 255.0 * opacity).astype(np.float32)
    roi = result[dy0:dy1, dx0:dx1]
    for c in range(3):
        roi[:, :, c] = (roi[:, :, c] * (1 - alpha) + sc[:, :, c] * alpha).clip(0, 255).astype(np.uint8)
    result[dy0:dy1, dx0:dx1] = roi
    return result


def run():
    print("=" * 60)
    print("  POSITION INVARIANCE TEST — v4 Detector")
    print("=" * 60)

    W, H = 800, 600
    OUTER_R = 22  # ~5.5% of 400px width — within target range

    # Base image: fabric-like texture
    rng = np.random.RandomState(42)
    base = rng.randint(40, 120, (H, W, 3), dtype=np.uint8)
    for i in range(0, W, 40):
        cv2.line(base, (i, 0), (i, H), (80, 60, 50), 1)
    for j in range(0, H, 40):
        cv2.line(base, (0, j), (W, j), (50, 60, 80), 1)

    star = build_star(OUTER_R)

    positions = [
        ("bottom_right", W - 60,  H - 50),
        ("bottom_left",  60,       H - 50),
        ("top_right",    W - 60,  50),
        ("top_left",     60,      50),
        ("center",       W // 2,  H // 2),
        ("top_edge_center", W // 2, 40),
    ]

    tmp_dir = root / "stage_input"
    tmp_dir.mkdir(exist_ok=True)

    results = []
    for name, cx, cy in positions:
        composited = composite(base, star, cx, cy, opacity=0.35)
        tmp_path = tmp_dir / f"pos_test_{name}.jpg"
        cv2.imwrite(str(tmp_path), composited,
                    [cv2.IMWRITE_JPEG_QUALITY, 90])

        det = detect_watermark(tmp_path)
        detected = det["detected"] and det["confidence_level"] in ("HIGH", "MEDIUM")
        conf = det["confidence"]
        level = det["confidence_level"]

        status = "PASS" if detected else "FAIL"
        icon = "✓" if detected else "✗"
        print(f"  {icon} [{name:<22}] cx={cx:>4} cy={cy:>4} | {level:<6} score={conf:.3f} | {status}")

        results.append({
            "position": name,
            "cx": cx, "cy": cy,
            "detected": detected,
            "confidence_level": level,
            "confidence": conf,
            "status": status,
        })

        tmp_path.unlink(missing_ok=True)

    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = len(results) - passed

    print("\n" + "=" * 60)
    print(f"  RESULT: {passed}/{len(results)} positions detected")
    if failed > 0:
        print(f"  ✗ {failed} position(s) MISSED — location bias may be present")
        failed_positions = [r["position"] for r in results if r["status"] == "FAIL"]
        print(f"    Missed: {failed_positions}")
    else:
        print("  ✓ All positions detected — no hard location bias")

    if passed >= 5:
        print("  Classification: ACCEPTABLE (≥5/6 positions)")
    elif passed >= 4:
        print("  Classification: MARGINAL (4/6 — soft location bias present)")
    else:
        print("  Classification: LOCATION BIASED — detector has significant position dependency")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    ok = run()
    sys.exit(0 if ok else 1)
