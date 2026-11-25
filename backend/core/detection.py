"""
Gemini Watermark Detector — v4 Candidate Scoring Architecture
==============================================================

Phase 4 redesign. Replaces binary-gate logic with weighted candidate scoring.

Core philosophy shift:
  v3: "Does this shape pass all 7 geometric filters?"
  v4: "How similar is this candidate to the known target watermark appearance?"

Architecture:
  Full-image Top-Hat extraction (no hard location constraint)
  → Contour extraction → N candidates
  → Per-candidate 8-signal weighted score
  → Multi-candidate NMS (suppress overlapping lower-score duplicates)
  → Confidence tier classification: HIGH / MEDIUM / LOW / NONE
  → Precise contour-based mask (not bounding box)

Location Handling:
  v3: Hard bottom-right gate (≥55% W+H) — caused 0% recall on synthetic positives
  v4: Location = Signal 8 (5% weight, soft bonus) — no candidate rejected for position alone

8 Scoring Signals:
  S1 Aspect Ratio     (0.15): Symmetric bounding box, peaks at AR=1.0
  S2 Solidity         (0.15): Concave star profile, peaks at solidity=0.52
  S3 Extent           (0.10): Area / bounding-box area in valid range
  S4 Isoperimetric Q  (0.15): 4-pointed star Q ≈ 0.30–0.55; crosses Q<0.20; circles Q≈1.0
  S5 Intensity Profile(0.15): Translucent (not hard white) — Top-Hat mean 15–80 ideal
  S6 Relative Size    (0.15): 1.0%–4.0% of image diagonal = score 1.0; outside = penalty
  S7 Edge Regularity  (0.10): Smooth antialiased star vs. embroidery pixel noise
  S8 Location Bonus   (0.05): Soft +bonus if bottom-right quadrant; neutral elsewhere

Hard Pre-filters (pure noise/decoration rejection, no impact on score):
  Area < 80px²    → reject (pure noise)
  Area > 6000px²  → reject (large decoration)
  AR < 0.60       → reject (strongly elongated)
  AR > 1.67       → reject (strongly elongated)

Confidence Tiers:
  score ≥ 0.68  → HIGH   (auto process)
  score ≥ 0.45  → MEDIUM (require user review)
  score < 0.45  → LOW    (ignore, do not modify image)
"""

import cv2
from backend.core.cv_utils import safe_imread, safe_imwrite
import numpy as np
from pathlib import Path
import math

# ─── Configuration ─────────────────────────────────────────────────────────────
CONFIDENCE_HIGH   = 0.68
CONFIDENCE_MEDIUM = 0.45

# Module-level singleton: GeminiSparkleDetector is loaded once per process
# to avoid re-reading gemini_alpha.npy for every image (that was 290ms/image overhead)
_gemini_detector = None

# Signal weights — must sum to 1.0
SIGNAL_WEIGHTS = {
    "aspect_ratio":   0.15,
    "solidity":       0.15,
    "extent":         0.10,
    "iso_q":          0.15,
    "intensity":      0.15,
    "relative_size":  0.15,
    "edge_regularity":0.10,
    "location_bonus": 0.05,
}
assert abs(sum(SIGNAL_WEIGHTS.values()) - 1.0) < 1e-9, "Signal weights must sum to 1.0"

# Hard pre-filter bounds (reject before scoring — not tunable signals)
HARD_AREA_MIN = 80
HARD_AREA_MAX = 6000
HARD_AR_MIN   = 0.60
HARD_AR_MAX   = 1.67

# Non-Maximum Suppression overlap threshold
NMS_IOU_THRESHOLD = 0.30


# ─── Signal Scoring Functions ───────────────────────────────────────────────────

def _score_aspect_ratio(ar: float) -> float:
    """
    Gemini star has near-square bounding box (AR ≈ 1.0).
    Score peaks at AR=1.0, falls off symmetrically.
    Score = 0 at AR ≤ 0.60 or AR ≥ 1.67 (already filtered by hard gate).
    """
    return max(0.0, 1.0 - abs(1.0 - ar) * 2.0)


def _score_solidity(s: float) -> float:
    """
    Gemini 4-pointed star has concave indentations → solidity ≈ 0.45–0.60.
    Solid circles: s ≈ 0.95. Thin cross/plus: s ≈ 0.25.
    Gaussian-like peak centered at 0.52.
    """
    return max(0.0, 1.0 - ((s - 0.52) / 0.18) ** 2)


def _score_extent(e: float) -> float:
    """
    Valid Gemini star extent: 0.28–0.68.
    Peaks at center of valid range (0.48).
    """
    ideal = 0.48
    half_range = 0.20
    deviation = abs(e - ideal)
    return max(0.0, 1.0 - (deviation / half_range) ** 1.5) if deviation <= half_range else 0.0


def _score_iso_q(q: float) -> float:
    """
    Isoperimetric quotient Q = 4π·A / P².
    Circles: Q≈1.0  |  4-pointed stars: Q≈0.30–0.55  |  thin crosses: Q<0.20.
    Peak at Q=0.40 for a 4-pointed star.
    Cross rejection: if Q < 0.20 → score 0.0 (hard gate inside score function).
    """
    if q < 0.20:
        return 0.0  # Cross/plus shape — definitive rejection
    ideal = 0.40
    return max(0.0, 1.0 - abs(q - ideal) / 0.30)


def _score_intensity(mean_tophat: float) -> float:
    """
    Gemini watermark is semi-transparent → moderate Top-Hat response (15–80).
    Hard white solid objects: response > 120.
    Score peaks at response ≈ 40, falls for very dim or very bright.
    """
    if mean_tophat < 5:
        return 0.0  # Probably a noise artifact
    ideal = 40.0
    # Soft penalize bright; do not hard-reject (real watermarks vary with background)
    if mean_tophat <= ideal:
        return min(1.0, mean_tophat / ideal)
    else:
        return max(0.0, 1.0 - (mean_tophat - ideal) / 100.0)


def _score_relative_size(area_px: float, img_diagonal: float) -> float:
    """
    Gemini star occupies ≈ 1.0%–4.0% of image diagonal as a linear measurement.
    Convert area to equivalent radius: r ≈ sqrt(area / π).
    Star linear size ≈ 2r → compare to diagonal.
    Score 1.0 when size/diagonal ∈ [0.010, 0.040].
    """
    if img_diagonal <= 0:
        return 0.5
    r = math.sqrt(area_px / math.pi)
    size_ratio = (2 * r) / img_diagonal
    lo, hi = 0.010, 0.040
    if lo <= size_ratio <= hi:
        center = (lo + hi) / 2
        return max(0.0, 1.0 - abs(size_ratio - center) / (hi - lo))
    elif size_ratio < lo:
        return max(0.0, size_ratio / lo)
    else:  # too large
        return max(0.0, 1.0 - (size_ratio - hi) / hi)


def _score_edge_regularity(cnt, tophat_roi: np.ndarray, bx, by, bw, bh) -> float:
    """
    Smooth antialiased star edges have low gradient variance along the contour.
    Embroidery/fabric noise has high local gradient variance.
    Computes variance of Canny edge strength in bounding box as regularity proxy.
    """
    if tophat_roi.size == 0 or bw < 4 or bh < 4:
        return 0.5
    patch = tophat_roi[by:by+bh, bx:bx+bw]
    if patch.size == 0:
        return 0.5
    edges = cv2.Canny(patch, 30, 90)
    edge_pixels = edges[edges > 0]
    if len(edge_pixels) < 4:
        return 0.5
    # Low variance = regular smooth edges (good). High variance = noisy edges (bad).
    variance = float(np.var(edge_pixels.astype(np.float32)))
    # Normalize: variance < 200 = smooth (score 1.0), variance > 2000 = noisy (score 0.0)
    return max(0.0, 1.0 - variance / 2000.0)


def _score_location_bonus(cx_rel: float, cy_rel: float) -> float:
    """
    Soft location bonus. Returns 0.0–1.0.
    Peak at bottom-right corner (cx_rel=1.0, cy_rel=1.0).
    Center: 0.25. Top-left corner: 0.0.
    This is a 5% weight — it nudges probability, does not decide it.
    """
    return (cx_rel ** 1.5 + cy_rel ** 1.5) / 2.0


# ─── NMS ───────────────────────────────────────────────────────────────────────

def _iou(b1, b2) -> float:
    """Compute IoU of two bounding boxes (x, y, w, h)."""
    x1, y1, w1, h1 = b1
    x2, y2, w2, h2 = b2
    ix = max(0, min(x1 + w1, x2 + w2) - max(x1, x2))
    iy = max(0, min(y1 + h1, y2 + h2) - max(y1, y2))
    inter = ix * iy
    union = w1 * h1 + w2 * h2 - inter
    return inter / union if union > 0 else 0.0


def non_max_suppression(candidates: list, iou_threshold: float = NMS_IOU_THRESHOLD) -> list:
    """Suppress overlapping candidates, keeping highest-score survivors."""
    if not candidates:
        return []
    candidates = sorted(candidates, key=lambda c: c["score"], reverse=True)
    kept = []
    suppressed = set()
    for i, c in enumerate(candidates):
        if i in suppressed:
            continue
        kept.append(c)
        for j, other in enumerate(candidates[i+1:], start=i+1):
            if j not in suppressed:
                if _iou((c["x"], c["y"], c["w"], c["h"]),
                        (other["x"], other["y"], other["w"], other["h"])) > iou_threshold:
                    suppressed.add(j)
    return kept


# ─── Mask Generation ───────────────────────────────────────────────────────────

def _build_precise_mask(candidates: list, img_h: int, img_w: int, padding: int) -> np.ndarray:
    """
    Builds precise contour-based mask (not bounding box).
    Applies morphological dilation + Gaussian feathering.
    """
    mask = np.zeros((img_h, img_w), dtype=np.uint8)
    for c in candidates:
        if c.get("contour") is not None:
            cv2.drawContours(mask, [c["contour"]], -1, 255, thickness=cv2.FILLED)

    if np.any(mask > 0):
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (padding, padding))
        mask = cv2.dilate(mask, kernel, iterations=2)
        # Feather edges for smoother inpainting transition
        mask = cv2.GaussianBlur(mask, (padding | 1, padding | 1), 0)
        _, mask = cv2.threshold(mask, 30, 255, cv2.THRESH_BINARY)

    return mask


# ─── Main Detector ─────────────────────────────────────────────────────────────

def detect_watermark(
    image_path: Path,
    sensitivity: int = 160,
    padding: int = 12,
    search_size: int = None,   # None = full image search
    thresholds: dict = None,
) -> dict:
    """
    v4 Candidate Scoring Detector.

    Returns:
    {
        "detected": bool,
        "confidence": float,
        "confidence_level": "HIGH" | "MEDIUM" | "LOW" | "NONE",
        "detections": [{"x","y","w","h","score","confidence","signals"}, ...],
        "mask": np.ndarray (full image resolution),
        "message": str,
    }
    """
    from backend.core.sparkle_detector import GeminiSparkleDetector
    
    img = safe_imread(str(image_path))
    if img is None:
        return _empty(f"Could not read image: {image_path}")

    h, w = img.shape[:2]
    img_diagonal = math.sqrt(w**2 + h**2)

    conf_high   = (thresholds or {}).get("high",   CONFIDENCE_HIGH)
    conf_medium = (thresholds or {}).get("medium",  CONFIDENCE_MEDIUM)

    # ── Top-Hat on full image (no location hard-gate) ──────────────────────────
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    kernel_size = max(31, min(71, int(min(h, w) * 0.08) | 1))  # adaptive kernel
    tophat_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    tophat = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, tophat_kernel)

    thresh_val = max(12, sensitivity - 110)
    _, thresh = cv2.threshold(tophat, thresh_val, 255, cv2.THRESH_BINARY)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    candidates = []

    for cnt in contours:
        area = cv2.contourArea(cnt)

        # ── Hard pre-filters (pure noise/decoration rejection) ──────────────
        if not (HARD_AREA_MIN <= area <= HARD_AREA_MAX):
            continue

        bx, by, bw, bh = cv2.boundingRect(cnt)
        if bw == 0 or bh == 0:
            continue

        ar = float(bw) / bh
        if not (HARD_AR_MIN <= ar <= HARD_AR_MAX):
            continue

        # ── Signal computations ──────────────────────────────────────────────
        hull = cv2.convexHull(cnt)
        hull_area = cv2.contourArea(hull)
        solidity = float(area) / hull_area if hull_area > 0 else 0

        bbox_area = bw * bh
        extent = float(area) / bbox_area if bbox_area > 0 else 0

        perimeter = cv2.arcLength(cnt, True)
        iso_q = (4 * math.pi * area / (perimeter ** 2)) if perimeter > 0 else 0

        roi_patch = tophat[by:by+bh, bx:bx+bw]
        mean_intensity = float(np.mean(roi_patch)) if roi_patch.size > 0 else 0

        cx_rel = (bx + bw / 2) / w  # 0 = left, 1 = right
        cy_rel = (by + bh / 2) / h  # 0 = top,  1 = bottom

        # ── Score each signal ────────────────────────────────────────────────
        signals = {
            "aspect_ratio":    _score_aspect_ratio(ar),
            "solidity":        _score_solidity(solidity),
            "extent":          _score_extent(extent),
            "iso_q":           _score_iso_q(iso_q),
            "intensity":       _score_intensity(mean_intensity),
            "relative_size":   _score_relative_size(area, img_diagonal),
            "edge_regularity": _score_edge_regularity(cnt, tophat, bx, by, bw, bh),
            "location_bonus":  _score_location_bonus(cx_rel, cy_rel),
        }

        # Weighted score
        score = sum(SIGNAL_WEIGHTS[k] * v for k, v in signals.items())
        score = round(min(0.99, max(0.01, score)), 4)

        if score < 0.30:
            continue  # Not worth collecting — too low to ever reach MEDIUM

        # Map absolute contour coordinates (relative to full image)
        candidates.append({
            "x": int(bx), "y": int(by), "w": int(bw), "h": int(bh),
            "score": score,
            "contour": cnt,
            "raw_signals": {
                "ar": round(ar, 3),
                "solidity": round(solidity, 3),
                "extent": round(extent, 3),
                "iso_q": round(iso_q, 3),
                "mean_tophat": round(mean_intensity, 1),
                "area": int(area),
                "location": (round(cx_rel, 2), round(cy_rel, 2)),
            },
            "signal_scores": {k: round(v, 3) for k, v in signals.items()},
        })

    # NMS: suppress overlapping lower-score duplicates
    candidates = non_max_suppression(candidates)

    # Classify candidates by confidence tier
    high_med = [c for c in candidates if c["score"] >= conf_medium]

    # Template Matching Detector: singleton loaded once per process
    global _gemini_detector
    if _gemini_detector is None:
        from backend.core.sparkle_detector import GeminiSparkleDetector
        _gemini_detector = GeminiSparkleDetector()
    detector = _gemini_detector
    template_res = detector.detect(img)
    t_score = template_res["score"]
    t_bbox = template_res["bbox"]

    is_gemini = False

    if t_score > 0.60:
        is_gemini = True
        # Create a candidate for the pipeline based on the template match
        fallback_candidate = {
            "x": t_bbox[0], "y": t_bbox[1], "w": t_bbox[2], "h": t_bbox[3],
            "score": t_score,
            "contour": None,
            "signal_scores": {},
            "raw_signals": {}
        }
        fallback_candidate["score"] = conf_high if t_score >= 0.75 else conf_medium
        high_med = [fallback_candidate]
        mask = detector.generate_mask(img.shape[:2], t_bbox, padding)
        print(f"[Detection] Using Template Matcher (Score: {t_score:.3f})")
    elif high_med:
        # If template failed, but v4 found something, it's highly suspect (often a false positive like a dress)
        # Mark as REVIEW_REQUIRED (Medium/Low)
        for c in high_med:
            c["score"] = conf_medium # Force it to be MEDIUM to trigger review
        mask = _build_precise_mask(high_med, h, w, padding)
        print("[Detection] Template matcher failed. Forcing v4 detections to REVIEW.")
    else:
        return _empty("No Gemini watermark detected.")

    # ── Output Formatting ───────────────────────────────────────────────────────
    detections_out = []
    for c in high_med:
        score = c["score"]
        if score >= conf_high:
            level = "HIGH"
        elif score >= conf_medium:
            level = "MEDIUM"
        else:
            level = "LOW"
        detections_out.append({
            "x": c["x"], "y": c["y"], "w": c["w"], "h": c["h"],
            "score": score,
            "confidence_level": level,
            "signal_scores": c["signal_scores"],
            "raw_signals": c["raw_signals"],
        })

    max_score = max(c["score"] for c in high_med)
    if max_score >= conf_high:
        conf_level = "HIGH"
    elif max_score >= conf_medium:
        conf_level = "MEDIUM"
    else:
        conf_level = "LOW"

    n = len(detections_out)
    msg = f"Detected {n} candidate(s) [{conf_level} — score={max_score:.3f}]."

    return {
        "detected": True,
        "confidence": max_score,
        "confidence_level": conf_level,
        "is_deterministic_gemini": is_gemini,
        "detections": detections_out,
        "mask": mask,
        "message": msg,
    }


def _empty(msg: str) -> dict:
    return {
        "detected": False,
        "confidence": 0.0,
        "confidence_level": "NONE",
        "is_deterministic_gemini": False,
        "detections": [],
        "mask": None,
        "message": msg,
    }
