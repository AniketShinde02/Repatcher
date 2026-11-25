"""
scripts/generate_realistic_dataset.py
======================================
Generates 200 realistic synthetic Gemini watermark positive images.

Base images: downloaded from https://picsum.photos (freely licensed / Unsplash License).
Watermark: programmatic 4-pointed Gemini star approximation composited via alpha blending.

Randomization per image:
  - Resolution: 400×400 to 2000×1500
  - Watermark position: anywhere (not restricted to bottom-right)
  - Opacity: 0.15–0.55 (semi-transparent overlay)
  - Star size: 1.0%–4.0% of image diagonal
  - Optional Gaussian blur sigma: 0–1.5
  - JPEG compression quality: 60–95
  - Output format: 120 JPEG, 50 PNG, 30 WEBP

Position distribution (50 images each quadrant):
  - bottom-right
  - bottom-left
  - center
  - top-right / near edges (random)

If assets/watermark_template.png exists → use real asset.
Otherwise → construct geometric approximation.
"""

import cv2
import numpy as np
import math
import random
import sys
import urllib.request
import ssl
from pathlib import Path

root = Path(__file__).parent.parent
OUTPUT_DIR = root / "tests" / "dataset" / "realistic_positive"
ASSET_TEMPLATE = root / "assets" / "watermark_template.png"

random.seed(42)
np.random.seed(42)


# ─── Watermark Construction ────────────────────────────────────────────────────

def build_star_template(outer_r: int, color: tuple = (255, 255, 255)) -> np.ndarray:
    """
    Renders a 4-pointed Gemini-style star via fillPoly.
    Narrow-arm profile: inner_r = outer_r / 2.5.
    Returns BGRA image (with alpha channel) at 2× for anti-aliasing.
    """
    scale = 2  # supersampling scale
    size = int(outer_r * 2 * scale + 4)
    center = size // 2
    inner_r = outer_r / 2.5

    pts = []
    for i in range(8):
        angle = math.pi * i / 4 - math.pi / 4
        r = outer_r * scale if i % 2 == 0 else inner_r * scale
        pts.append([
            int(center + r * math.cos(angle)),
            int(center + r * math.sin(angle))
        ])

    canvas = np.zeros((size, size, 4), dtype=np.uint8)
    poly = np.array(pts, np.int32)
    bgr_canvas = np.ascontiguousarray(canvas[:, :, :3])
    alpha_canvas = np.ascontiguousarray(canvas[:, :, 3])
    cv2.fillPoly(bgr_canvas, [poly], color)
    cv2.fillPoly(alpha_canvas, [poly], 255)
    canvas[:, :, :3] = bgr_canvas
    canvas[:, :, 3]  = alpha_canvas


    # Downsample for anti-aliasing
    out_size = outer_r * 2 + 4
    result = cv2.resize(canvas, (out_size, out_size), interpolation=cv2.INTER_AREA)
    return result


def load_template_asset() -> np.ndarray | None:
    """Load real watermark asset if it exists."""
    if ASSET_TEMPLATE.exists():
        img = cv2.imread(str(ASSET_TEMPLATE), cv2.IMREAD_UNCHANGED)
        if img is not None:
            print(f"  Using real watermark template: {ASSET_TEMPLATE}")
            return img
    return None


def composite_watermark(
    base: np.ndarray,
    star_template: np.ndarray,
    cx: int, cy: int,
    opacity: float,
    blur_sigma: float = 0.0,
) -> np.ndarray:
    """
    Alpha-composites star_template onto base at center (cx, cy) with given opacity.
    base: BGR or BGRA numpy array.
    star_template: BGRA numpy array.
    """
    result = base.copy()
    h, w = result.shape[:2]
    sh, sw = star_template.shape[:2]

    x0 = cx - sw // 2
    y0 = cy - sh // 2
    x1 = x0 + sw
    y1 = y0 + sh

    # Clamp to image bounds
    sx0 = max(0, -x0);  sx1 = sw - max(0, x1 - w)
    sy0 = max(0, -y0);  sy1 = sh - max(0, y1 - h)
    dx0 = max(0, x0);   dx1 = min(w, x1)
    dy0 = max(0, y0);   dy1 = min(h, y1)

    if dx1 <= dx0 or dy1 <= dy0:
        return result

    star_crop = star_template[sy0:sy1, sx0:sx1]
    if star_crop.size == 0:
        return result

    if blur_sigma > 0.1:
        ksize = int(blur_sigma * 3) * 2 + 1
        star_crop = cv2.GaussianBlur(star_crop, (ksize, ksize), blur_sigma)

    alpha_mask = (star_crop[:, :, 3] / 255.0 * opacity).astype(np.float32)

    roi = result[dy0:dy1, dx0:dx1]
    if result.ndim == 3 and result.shape[2] == 3:
        for c in range(3):
            roi[:, :, c] = (
                roi[:, :, c].astype(np.float32) * (1 - alpha_mask) +
                star_crop[:, :, c].astype(np.float32) * alpha_mask
            ).clip(0, 255).astype(np.uint8)
    result[dy0:dy1, dx0:dx1] = roi
    return result


# ─── Image Downloading ─────────────────────────────────────────────────────────

def download_base_image(seed: int, w: int, h: int) -> np.ndarray | None:
    """Download a freely-licensed base image from picsum.photos."""
    url = f"https://picsum.photos/seed/{seed}/{w}/{h}"
    try:
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(url, timeout=10, context=ctx) as resp:
            data = resp.read()
        arr = np.frombuffer(data, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        return img
    except Exception as e:
        return None


def make_fallback_base(w: int, h: int, seed: int) -> np.ndarray:
    """Generate a synthetic textured background when download fails."""
    rng = np.random.RandomState(seed)
    img = rng.randint(30, 180, (h, w, 3), dtype=np.uint8)
    # Add fabric-like grid texture
    for i in range(0, w, rng.randint(20, 60)):
        cv2.line(img, (i, 0), (i, h), (int(img[0, i, 0] * 0.8),) * 3, 1)
    for j in range(0, h, rng.randint(20, 60)):
        cv2.line(img, (0, j), (w, j), (int(img[j, 0, 1] * 0.8),) * 3, 1)
    return img


# ─── Position Zones ────────────────────────────────────────────────────────────

def get_position(zone: str, w: int, h: int, margin: int) -> tuple[int, int]:
    """Returns (cx, cy) for a watermark placement zone."""
    if zone == "bottom_right":
        return (random.randint(int(w * 0.70), w - margin),
                random.randint(int(h * 0.70), h - margin))
    elif zone == "bottom_left":
        return (random.randint(margin, int(w * 0.30)),
                random.randint(int(h * 0.70), h - margin))
    elif zone == "center":
        return (random.randint(int(w * 0.35), int(w * 0.65)),
                random.randint(int(h * 0.35), int(h * 0.65)))
    else:  # top_right / random near edges
        return (random.randint(int(w * 0.60), w - margin),
                random.randint(margin, int(h * 0.35)))


# ─── Main Generation ───────────────────────────────────────────────────────────

def generate(n_total: int = 200):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Generating {n_total} realistic synthetic positive images → {OUTPUT_DIR}")

    real_template = load_template_asset()

    zones = (
        ["bottom_right"] * 50 +
        ["bottom_left"]  * 50 +
        ["center"]       * 50 +
        ["top_right"]    * 50
    )
    random.shuffle(zones)

    # Format distribution
    formats = ["jpeg"] * 120 + ["png"] * 50 + ["webp"] * 30
    random.shuffle(formats)

    generated = 0
    failed_downloads = 0

    for i in range(n_total):
        rng_seed = 1000 + i
        random.seed(rng_seed)

        # Resolution
        w = random.randint(400, 2000)
        h = random.randint(400, 1500)

        # Download or fallback
        base = download_base_image(rng_seed, w, h)
        if base is None:
            failed_downloads += 1
            base = make_fallback_base(w, h, rng_seed)
        base_h, base_w = base.shape[:2]

        # Star size: 1.0%–4.0% of diagonal
        diag = math.sqrt(base_w ** 2 + base_h ** 2)
        size_frac = random.uniform(0.010, 0.040)
        outer_r = max(8, int(diag * size_frac / 2))

        margin = outer_r + 5
        zone = zones[i % len(zones)]
        cx, cy = get_position(zone, base_w, base_h, margin)

        opacity = random.uniform(0.15, 0.55)
        blur_sigma = random.uniform(0.0, 1.5)

        # Build or use real watermark
        if real_template is not None:
            scale = outer_r * 2 / max(real_template.shape[:2])
            sw = max(10, int(real_template.shape[1] * scale))
            sh = max(10, int(real_template.shape[0] * scale))
            star = cv2.resize(real_template, (sw, sh), interpolation=cv2.INTER_AREA)
        else:
            star = build_star_template(outer_r)

        composited = composite_watermark(base, star, cx, cy, opacity, blur_sigma)

        # Save in target format
        fmt = formats[i % len(formats)]
        if fmt == "jpeg":
            q = random.randint(65, 95)
            fname = OUTPUT_DIR / f"realistic_pos_{i+1:04d}.jpg"
            ok, buf = cv2.imencode(".jpg", composited, [cv2.IMWRITE_JPEG_QUALITY, q])
            if ok:
                fname.write_bytes(buf.tobytes())
        elif fmt == "png":
            fname = OUTPUT_DIR / f"realistic_pos_{i+1:04d}.png"
            cv2.imwrite(str(fname), composited)
        elif fmt == "webp":
            q = random.randint(75, 95)
            fname = OUTPUT_DIR / f"realistic_pos_{i+1:04d}.webp"
            ok, buf = cv2.imencode(".webp", composited, [cv2.IMWRITE_WEBP_QUALITY, q])
            if ok:
                fname.write_bytes(buf.tobytes())

        generated += 1
        if (i + 1) % 25 == 0:
            print(f"  [{i+1}/{n_total}] generated ({failed_downloads} fallback bases)")

    print(f"\nDone. {generated}/{n_total} images generated.")
    print(f"  Network fallbacks used: {failed_downloads}/{n_total}")
    print(f"  Output: {OUTPUT_DIR}")
    if real_template is None:
        print("  Note: Used geometric star approximation (no assets/watermark_template.png found).")


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    generate(n)
