"""
tests/test_image_quality.py
===========================
9A Image Quality Preservation Regression Test

Tests that the processing pipeline:
1. Preserves original image dimensions
2. Preserves aspect ratio
3. Preserves format (JPEG->JPEG, PNG->PNG, WEBP->WEBP)
4. Does not degrade pixels OUTSIDE the inpaint mask (Zone B)
5. Reports PSNR and SSIM across three zones:
   - Zone A: entire image
   - Zone B: outside mask (CRITICAL preservation metric)
   - Zone C: inpainted region (expected to differ)

Acceptance Criteria (Zone B):
   - JPEG: PSNR >= 38dB, SSIM >= 0.97
   - PNG:  PSNR == inf (lossless), SSIM == 1.0
   - WEBP: PSNR >= 38dB, SSIM >= 0.97
"""

import sys
import time
import numpy as np
from pathlib import Path

root = Path(__file__).parent.parent
sys.path.insert(0, str(root))

from skimage.metrics import structural_similarity, peak_signal_noise_ratio
from PIL import Image
import cv2

from backend.core.detection import detect_watermark
from backend.core.inpainting import process_image_single, get_source_format, export_with_quality


# ─── Thresholds ───────────────────────────────────────────────────────────────
QUALITY_THRESHOLDS = {
    ".jpg":  {"psnr_min": 38.0, "ssim_min": 0.970},
    ".jpeg": {"psnr_min": 38.0, "ssim_min": 0.970},
    ".png":  {"psnr_min": 80.0, "ssim_min": 0.999},   # lossless — should be perfect
    ".webp": {"psnr_min": 38.0, "ssim_min": 0.970},
    ".bmp":  {"psnr_min": 80.0, "ssim_min": 0.999},
    ".tiff": {"psnr_min": 80.0, "ssim_min": 0.999},
}


def compute_quality(original: np.ndarray, result: np.ndarray, mask: np.ndarray):
    """
    Computes PSNR and SSIM for three zones.
    All arrays must be same shape HxWxC (uint8).

    Returns dict with zone_a, zone_b, zone_c metrics.
    """
    assert original.shape == result.shape, \
        f"DIMENSION MISMATCH: original={original.shape} vs result={result.shape}"

    def _metrics(orig_crop, res_crop, label):
        if orig_crop.size == 0:
            return {"label": label, "psnr": None, "ssim": None, "note": "empty region"}
        try:
            psnr = peak_signal_noise_ratio(orig_crop, res_crop, data_range=255)
        except Exception:
            psnr = float("inf")
        try:
            ssim = structural_similarity(
                orig_crop, res_crop,
                channel_axis=2 if orig_crop.ndim == 3 else None,
                data_range=255
            )
        except Exception:
            ssim = 1.0
        return {"label": label, "psnr": round(psnr, 2), "ssim": round(ssim, 4)}

    # Zone A: Entire image
    zone_a = _metrics(original, result, "Zone A (entire image)")

    # Binary mask (dilated) — 255 = inpainted region
    binary_mask = (mask > 128).astype(bool)

    # Zone B: Outside mask (the preservation-critical zone)
    outside = ~binary_mask
    if outside.any():
        orig_b = original.copy()
        res_b  = result.copy()
        orig_b[binary_mask] = 0
        res_b[binary_mask]  = 0
        zone_b = _metrics(orig_b, res_b, "Zone B (outside mask — CRITICAL)")
    else:
        zone_b = {"label": "Zone B (outside mask)", "psnr": None, "ssim": None, "note": "mask covers full image"}

    # Zone C: Inpainted region (expected to differ)
    if binary_mask.any():
        orig_c = original[binary_mask].reshape(-1, original.shape[2]) if original.ndim == 3 else original[binary_mask]
        res_c  = result[binary_mask].reshape(-1, result.shape[2]) if result.ndim == 3 else result[binary_mask]
        try:
            psnr_c = peak_signal_noise_ratio(orig_c, res_c, data_range=255)
        except Exception:
            psnr_c = 0.0
        zone_c = {"label": "Zone C (inpainted region)", "psnr": round(psnr_c, 2), "ssim": None, "note": "expected to differ"}
    else:
        zone_c = {"label": "Zone C (inpainted region)", "psnr": None, "ssim": None, "note": "no watermark detected"}

    return {"zone_a": zone_a, "zone_b": zone_b, "zone_c": zone_c}


def run_quality_test(test_name: str, image_path: Path) -> dict:
    """Run quality test on a single image and return structured result."""
    print(f"\n--- [{test_name}] {image_path.name} ---")

    if not image_path.exists():
        print(f"  SKIP: file not found")
        return {"name": test_name, "status": "SKIP"}

    # --- Record original properties ---
    orig_pil = Image.open(str(image_path))
    orig_w, orig_h = orig_pil.size
    orig_mode   = orig_pil.mode
    orig_format = orig_pil.format or "UNKNOWN"
    orig_size_kb = image_path.stat().st_size / 1024
    orig_ext = get_source_format(image_path)

    orig_arr = np.array(orig_pil.convert("RGB"))
    print(f"  Input:  {orig_w}×{orig_h}  mode={orig_mode}  format={orig_format}  {orig_size_kb:.1f} KB  ext={orig_ext}")

    # --- Detect watermark (on original resolution) ---
    t0 = time.time()
    det = detect_watermark(image_path)
    detect_ms = (time.time() - t0) * 1000
    mask = det["mask"]
    print(f"  Detect: {det['confidence_level']} conf={det['confidence']:.3f} ({detect_ms:.1f}ms)")

    # --- Process (inpaint on original resolution) ---
    stage_in  = root / "stage_input"
    stage_out = root / "stage_output"
    stage_mask = root / "stage_mask"
    for d in [stage_in, stage_out, stage_mask]:
        d.mkdir(exist_ok=True)

    import shutil, uuid
    job_id = uuid.uuid4().hex[:8]
    tmp_in   = stage_in   / f"qt_{job_id}{orig_ext}"
    tmp_mask = stage_mask / f"qt_{job_id}_mask.png"
    tmp_out  = stage_out  / f"qt_{job_id}{orig_ext}"

    shutil.copy2(image_path, tmp_in)
    cv2.imwrite(str(tmp_mask), mask)

    t1 = time.time()
    success, actual_out = process_image_single(tmp_in, tmp_mask, tmp_out)
    process_ms = (time.time() - t1) * 1000

    tmp_in.unlink(missing_ok=True)
    tmp_mask.unlink(missing_ok=True)

    if not success or not actual_out.exists():
        print(f"  FAIL: processing returned no output")
        return {"name": test_name, "status": "FAIL", "error": "No output produced"}

    # --- Verify output properties ---
    out_pil = Image.open(str(actual_out))
    out_w, out_h = out_pil.size
    out_format   = out_pil.format or "UNKNOWN"
    out_ext      = get_source_format(actual_out)
    out_size_kb  = actual_out.stat().st_size / 1024
    out_arr = np.array(out_pil.convert("RGB"))

    print(f"  Output: {out_w}×{out_h}  format={out_format}  {out_size_kb:.1f} KB  ext={out_ext}  ({process_ms:.0f}ms)")

    # ── Dimension check ──────────────────────────────────────────────────────
    dim_ok = (orig_w == out_w and orig_h == out_h)
    ratio_ok = abs((orig_w / orig_h) - (out_w / out_h)) < 0.001
    fmt_ok = (orig_ext == out_ext)

    print(f"  Dimensions preserved: {'✓' if dim_ok else '✗ FAIL'} ({orig_w}×{orig_h} → {out_w}×{out_h})")
    print(f"  Aspect ratio preserved: {'✓' if ratio_ok else '✗ FAIL'}")
    print(f"  Format preserved: {'✓' if fmt_ok else f'✗ FAIL ({orig_ext} → {out_ext})'}")

    # ── Quality metrics (3 zones) ─────────────────────────────────────────────
    quality = compute_quality(orig_arr, out_arr, mask)
    thresholds = QUALITY_THRESHOLDS.get(orig_ext, QUALITY_THRESHOLDS[".jpg"])

    for zone in ["zone_a", "zone_b", "zone_c"]:
        z = quality[zone]
        psnr_str = f"{z['psnr']:.2f} dB" if z["psnr"] is not None else "N/A"
        ssim_str = f"{z['ssim']:.4f}" if z["ssim"] is not None else "N/A"
        print(f"  {z['label']}: PSNR={psnr_str}  SSIM={ssim_str}")

    # ── Zone B acceptance ─────────────────────────────────────────────────────
    zone_b = quality["zone_b"]
    zone_b_pass = True
    if zone_b["psnr"] is not None:
        if zone_b["psnr"] < thresholds["psnr_min"]:
            print(f"  ✗ Zone B PSNR FAIL: {zone_b['psnr']:.2f} < {thresholds['psnr_min']}")
            zone_b_pass = False
        if zone_b["ssim"] is not None and zone_b["ssim"] < thresholds["ssim_min"]:
            print(f"  ✗ Zone B SSIM FAIL: {zone_b['ssim']:.4f} < {thresholds['ssim_min']}")
            zone_b_pass = False
    if zone_b_pass:
        print(f"  ✓ Zone B quality: PASS")

    actual_out.unlink(missing_ok=True)

    passed = dim_ok and ratio_ok and fmt_ok and zone_b_pass
    print(f"  RESULT: {'PASS' if passed else 'FAIL'}")

    return {
        "name":         test_name,
        "status":       "PASS" if passed else "FAIL",
        "input_dims":   f"{orig_w}×{orig_h}",
        "output_dims":  f"{out_w}×{out_h}",
        "dim_ok":       dim_ok,
        "ratio_ok":     ratio_ok,
        "fmt_ok":       fmt_ok,
        "zone_b_pass":  zone_b_pass,
        "quality":      quality,
        "orig_ext":     orig_ext,
        "out_ext":      out_ext,
    }


def generate_test_image(path: Path, w: int, h: int, fmt: str, quality: int = 95):
    """Generate a synthetic test image for the given format."""
    path.parent.mkdir(parents=True, exist_ok=True)
    img = np.random.randint(40, 200, (h, w, 3), dtype=np.uint8)
    # Add some texture
    for i in range(0, w, 40):
        cv2.line(img, (i, 0), (i, h), (150, 120, 90), 1)
    for j in range(0, h, 40):
        cv2.line(img, (0, j), (w, j), (90, 120, 150), 1)
    pil = Image.fromarray(img)
    save_kwargs = {}
    if fmt == "JPEG":
        save_kwargs = {"quality": quality, "subsampling": 0}
    elif fmt == "WEBP":
        save_kwargs = {"quality": quality}
    pil.save(str(path), format=fmt, **save_kwargs)


def main():
    print("=" * 60)
    print("  9A — IMAGE QUALITY PRESERVATION REGRESSION TEST")
    print("=" * 60)

    test_dir = root / "tests" / "quality_test_images"
    test_dir.mkdir(parents=True, exist_ok=True)

    # Generate synthetic test images if not present
    tests = [
        ("JPEG_800x600",   test_dir / "test_800x600.jpg",  800, 600, "JPEG", 95),
        ("JPEG_1920x1080", test_dir / "test_1920x1080.jpg", 1920, 1080, "JPEG", 90),
        ("PNG_800x600",    test_dir / "test_800x600.png",  800, 600, "PNG",  None),
        ("WEBP_800x600",   test_dir / "test_800x600.webp", 800, 600, "WEBP", 90),
    ]

    for name, path, w, h, fmt, q in tests:
        if not path.exists():
            kw = {"quality": q} if q else {}
            generate_test_image(path, w, h, fmt, **kw)
            print(f"  Generated: {path.name}")

    # Run quality tests
    results = []
    for name, path, *_ in tests:
        r = run_quality_test(name, path)
        results.append(r)

    # Summary
    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    passed = sum(1 for r in results if r.get("status") == "PASS")
    failed = sum(1 for r in results if r.get("status") == "FAIL")
    print(f"  PASS: {passed}/{len(results)}   FAIL: {failed}/{len(results)}")
    for r in results:
        icon = "✓" if r.get("status") == "PASS" else "✗"
        print(f"  {icon} {r['name']}: {r.get('status', 'SKIP')}")
        if r.get("status") == "FAIL":
            if not r.get("dim_ok"):   print(f"      → Dimension mismatch: {r.get('input_dims')} → {r.get('output_dims')}")
            if not r.get("fmt_ok"):   print(f"      → Format mismatch: {r.get('orig_ext')} → {r.get('out_ext')}")
            if not r.get("zone_b_pass"): print(f"      → Zone B quality degradation detected")
    print("=" * 60)

    if failed > 0:
        print("\n  ⚠ QUALITY FAILURES DETECTED. DO NOT PROCEED TO PRODUCTION.")
        sys.exit(1)
    else:
        print("\n  ✓ All quality tests passed.")


if __name__ == "__main__":
    main()
