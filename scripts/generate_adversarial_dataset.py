"""
scripts/generate_adversarial_dataset.py
========================================
Generates 80+ adversarial synthetic images that should NOT trigger the detector.
Replaces the Phase 3 inline adversarial generator.

Categories (all must produce FALSE NEGATIVES — detector must NOT fire on these):
  - Small stars (8×8 to 14×14 px) — near-noise threshold
  - Medium star jewelry (15×15 to 40×40)
  - Large decorative stars (60+ px) — above area limit
  - Rotated 4-pointed stars (15°, 30°, 45°, 60°)
  - Partially occluded stars (25%–50% cropped at edge)
  - Anti-aliased solid stars (hard white, no transparency)
  - Stars on complex textures (tartan, floral, noise)
  - Stars near each of the 4 edges
  - Stars in center of image
  - Cross logos (+ shapes)
  - Four-point diamond logos
  - Sequin patterns (dense small round dots)
  - Jewelry highlights (bright circular glints)
  - Embroidery patterns
  - Text + star symbols
  - Brand mark patches

Note: Each adversarial image is designed to fool simple geometric detectors
while being genuinely NOT a Gemini watermark. They must be rejected.
"""

import cv2
import numpy as np
import math
import random
from pathlib import Path

root = Path(__file__).parent.parent
OUTPUT_DIR = root / "tests" / "dataset" / "adversarial"

random.seed(99)
np.random.seed(99)


def make_bg(h: int = 600, w: int = 600, color_range=(30, 90)) -> np.ndarray:
    rng = np.random.RandomState(random.randint(0, 9999))
    lo, hi = color_range
    base = rng.randint(lo, hi, (h, w, 3), dtype=np.uint8)
    # Subtle texture
    for i in range(0, w, rng.randint(30, 80)):
        c = rng.randint(lo - 10, hi + 10)
        cv2.line(base, (i, 0), (i, h), (int(c),) * 3, 1)
    return base


def draw_star_rotated(img, cx, cy, outer_r, inner_r, color, angle_deg=0):
    angle_rad = math.radians(angle_deg)
    pts = []
    for i in range(8):
        a = math.pi * i / 4 - math.pi / 4 + angle_rad
        r = outer_r if i % 2 == 0 else inner_r
        pts.append([int(cx + r * math.cos(a)), int(cy + r * math.sin(a))])
    cv2.fillPoly(img, [np.array(pts, np.int32)], color)


def draw_cross(img, cx, cy, arm_len, thickness, color):
    cv2.rectangle(img, (cx - arm_len, cy - thickness), (cx + arm_len, cy + thickness), color, -1)
    cv2.rectangle(img, (cx - thickness, cy - arm_len), (cx + thickness, cy + arm_len), color, -1)


idx = 1

def save(img, category):
    global idx
    path = OUTPUT_DIR / f"adv_{category}_{idx:04d}.jpg"
    cv2.imwrite(str(path), img)
    idx += 1


def generate():
    global idx
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Generating adversarial images → {OUTPUT_DIR}")
    idx = 1

    # ── 1. Small stars (8–14px) — below meaningful area threshold ─────────────
    for i in range(8):
        img = make_bg()
        r = random.randint(4, 7)
        draw_star_rotated(img, 520, 520, r, r // 2, (240, 240, 240))
        save(img, "small_star")

    # ── 2. Medium jewelry stars (solid white, hard-white tophat response) ──────
    for i in range(8):
        img = make_bg()
        r = random.randint(10, 20)
        draw_star_rotated(img, random.randint(400, 560), random.randint(400, 560),
                          r, r // 2, (255, 255, 255))
        save(img, "jewelry_star")

    # ── 3. Large decorative stars (>60px — above area limit) ──────────────────
    for i in range(6):
        img = make_bg()
        r = random.randint(60, 100)
        draw_star_rotated(img, 300, 300, r, r // 2, (220, 200, 180), angle_deg=random.randint(0, 45))
        save(img, "large_star")

    # ── 4. Rotated stars (15°, 30°, 45°, 60°) ─────────────────────────────────
    for angle in [15, 30, 45, 60]:
        for _ in range(3):
            img = make_bg()
            r = random.randint(18, 28)
            draw_star_rotated(img, 500, 500, r, r // 2, (230, 230, 230), angle_deg=angle)
            save(img, f"rotated_star_{angle}deg")

    # ── 5. Partially occluded (cropped near edge) ──────────────────────────────
    for i in range(6):
        img = make_bg()
        # Star partially outside image boundary
        cx = random.choice([0, 595, random.randint(10, 30)])
        cy = random.choice([0, 595, random.randint(10, 30)])
        draw_star_rotated(img, cx, cy, 20, 8, (220, 220, 220))
        save(img, "partial_star")

    # ── 6. Anti-aliased smooth solid stars (hard white, studio-lit appearance) ─
    for i in range(6):
        size = random.randint(40, 80)
        star_canvas = np.zeros((size*4, size*4, 3), dtype=np.uint8)
        draw_star_rotated(star_canvas, size*2, size*2, size*2-2, size//2, (255, 255, 255))
        star_small = cv2.resize(star_canvas, (size, size), interpolation=cv2.INTER_AREA)
        img = make_bg(color_range=(20, 60))
        x, y = random.randint(400, 550), random.randint(400, 550)
        try:
            img[y:y+size, x:x+size] = np.where(star_small > 30, star_small, img[y:y+size, x:x+size])
        except Exception:
            pass
        save(img, "antialiased_star")

    # ── 7. Stars on complex tartan textures ────────────────────────────────────
    for i in range(6):
        img = np.zeros((600, 600, 3), dtype=np.uint8)
        colors = [(200, 30, 30), (30, 30, 200), (200, 200, 30)]
        for j in range(0, 600, 20):
            cv2.line(img, (j, 0), (j, 600), random.choice(colors), random.randint(2, 8))
            cv2.line(img, (0, j), (600, j), random.choice(colors), random.randint(2, 8))
        r = random.randint(15, 25)
        draw_star_rotated(img, random.randint(400, 560), random.randint(400, 560),
                          r, r // 2, (240, 240, 100))
        save(img, "tartan_star")

    # ── 8. Stars near each of the 4 edges (center-column positions) ───────────
    positions = [(520, 300), (80, 300), (300, 520), (300, 80)]
    labels = ["edge_right", "edge_left", "edge_bottom", "edge_top"]
    for (cx, cy), label in zip(positions, labels):
        for _ in range(3):
            img = make_bg()
            r = random.randint(15, 25)
            draw_star_rotated(img, cx, cy, r, r // 2, (210, 210, 210))
            save(img, label)

    # ── 9. Stars in exact image center ────────────────────────────────────────
    for i in range(5):
        img = make_bg()
        r = random.randint(15, 25)
        draw_star_rotated(img, 300, 300, r, r // 2, (220, 220, 220))
        save(img, "center_star")

    # ── 10. Cross logos ───────────────────────────────────────────────────────
    for i in range(8):
        img = make_bg()
        arm = random.randint(15, 30)
        thick = random.randint(3, 8)
        draw_cross(img, random.randint(400, 550), random.randint(400, 550), arm, thick, (230, 230, 230))
        save(img, "cross_logo")

    # ── 11. Four-point diamond logos (aspect ratio elongated) ─────────────────
    for i in range(6):
        img = make_bg()
        cx, cy = random.randint(430, 560), random.randint(430, 560)
        pts = [(cx, cy-25), (cx+12, cy), (cx, cy+25), (cx-12, cy)]
        cv2.fillPoly(img, [np.array(pts, np.int32)], (220, 200, 180))
        save(img, "diamond_logo")

    # ── 12. Sequin patterns (dense small round dots) ──────────────────────────
    for i in range(5):
        img = make_bg(color_range=(50, 80))
        for _ in range(40):
            x, y = random.randint(350, 560), random.randint(350, 560)
            cv2.circle(img, (x, y), random.randint(3, 7), (220, 220, 220), -1)
        save(img, "sequins")

    # ── 13. Jewelry glint highlights (circular bright spots) ──────────────────
    for i in range(4):
        img = make_bg(color_range=(20, 50))
        for _ in range(5):
            x, y = random.randint(400, 560), random.randint(400, 560)
            r = random.randint(8, 18)
            cv2.circle(img, (x, y), r, (250, 250, 250), -1)
        save(img, "jewelry_glint")

    # ── 14. Embroidery pattern (many overlapping small stars) ─────────────────
    for i in range(4):
        img = make_bg(color_range=(40, 70))
        for dx, dy in [(490, 490), (505, 480), (495, 505), (478, 498)]:
            r = random.randint(6, 11)
            draw_star_rotated(img, dx, dy, r, r // 2, (200 - i*10,) * 3)
        save(img, "embroidery")

    # ── 15. Text + star symbols ────────────────────────────────────────────────
    for i in range(4):
        img = make_bg()
        cv2.putText(img, "SALE", (420, 500), cv2.FONT_HERSHEY_SIMPLEX,
                    1.0, (240, 240, 240), 2, cv2.LINE_AA)
        draw_star_rotated(img, 510, 520, 10, 4, (230, 230, 230))
        save(img, "text_star")

    total = idx - 1
    print(f"Generated {total} adversarial images.")
    print(f"  Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    generate()
