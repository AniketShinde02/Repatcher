import os
import cv2
import json
import time
import numpy as np
import pandas as pd
from pathlib import Path
from backend.core.gemini_profiles import get_profile_manager

# Ensure paths
CORPUS_DIR = Path("tests/input_images")
DEBUG_DIR = Path("debug")
OVERLAY_DIR = DEBUG_DIR / "detection_overlays"
MANIFEST_PATH = Path("tests/fixtures/gemini_manifest.json")
CSV_OUTPUT = DEBUG_DIR / "gemini_detection_results.csv"
CONTACT_SHEET = DEBUG_DIR / "detection_contact_sheet.jpg"

DEBUG_DIR.mkdir(parents=True, exist_ok=True)
OVERLAY_DIR.mkdir(parents=True, exist_ok=True)
MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)

def compute_gradient_magnitude(img):
    sobelx = cv2.Sobel(img, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(img, cv2.CV_64F, 0, 1, ksize=3)
    mag = np.sqrt(sobelx**2 + sobely**2)
    return cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)

def compute_variance_score(roi):
    # A flat ROI implies no watermark
    var = np.var(roi)
    # Map variance to a 0-1 score (e.g. variance > 100 is good enough for structure)
    return min(1.0, var / 500.0)

def main():
    print(f"Scanning {CORPUS_DIR} for images...")
    
    valid_exts = {".png", ".jpg", ".jpeg", ".webp"}
    images = [p for p in CORPUS_DIR.iterdir() if p.suffix.lower() in valid_exts]
    
    if not images:
        print("No images found.")
        return
        
    print(f"Found {len(images)} images.")
    
    # 1. Create Manifest
    manifest = []
    for img_path in images:
        manifest.append({
            "filename": img_path.name,
            "file_size": img_path.stat().st_size
        })
    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=4)
        
    manager = get_profile_manager()
    profiles = manager.get_all_profiles()
    print(f"Loaded {len(profiles)} native profiles.")
    
    results = []
    detected_images = []
    
    for i, img_path in enumerate(images):
        start_t = time.time()
        # Use np.fromfile to handle unicode characters in paths on Windows
        try:
            file_bytes = np.fromfile(str(img_path), dtype=np.uint8)
            img_bgr = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        except Exception:
            img_bgr = None
            
        if img_bgr is None:
            print(f"Failed to read: {img_path}")
            continue
            
        img_h, img_w = img_bgr.shape[:2]
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        
        candidates = []
        
        for pid, pdef in profiles.items():
            pw, ph = pdef["width"], pdef["height"]
            if img_w <= pw or img_h <= ph:
                continue
                
            template = pdef["template_bgr"]
            template_grad = compute_gradient_magnitude(template)
            
            # Phase 5: Search local area around prediction
            pred_x = img_w - pw - pdef["margin_right"]
            pred_y = img_h - ph - pdef["margin_bottom"]
            pred_x = max(0, min(img_w - pw, pred_x))
            pred_y = max(0, min(img_h - ph, pred_y))
            
            search_x1 = img_w // 2
            search_y1 = img_h // 2
            search_x2 = img_w
            search_y2 = img_h
            
            roi = gray[search_y1:search_y2, search_x1:search_x2]
            if roi.shape[0] < ph or roi.shape[1] < pw:
                continue
                
            roi_grad = compute_gradient_magnitude(roi)
            
            res_spatial = cv2.matchTemplate(roi, template, cv2.TM_CCOEFF_NORMED)
            res_grad = cv2.matchTemplate(roi_grad, template_grad, cv2.TM_CCOEFF_NORMED)
            
            min_spatial, max_spatial, min_loc_spatial, max_loc_spatial = cv2.minMaxLoc(res_spatial)
            min_grad, max_grad, min_loc_grad, max_loc_grad = cv2.minMaxLoc(res_grad)
            
            if abs(min_spatial) > abs(max_spatial):
                max_spatial = abs(min_spatial)
                max_loc_spatial = min_loc_spatial
                
            if abs(min_grad) > abs(max_grad):
                max_grad = abs(min_grad)
                max_loc_grad = min_loc_grad
            
            best_x = search_x1 + max_loc_spatial[0]
            best_y = search_y1 + max_loc_spatial[1]
            
            exact_roi = gray[best_y:best_y+ph, best_x:best_x+pw]
            if exact_roi.shape == (ph, pw):
                variance_score = compute_variance_score(exact_roi)
            else:
                variance_score = 0.0
                
            combined = (max_spatial * 0.6) + (max_grad * 0.4)
            
            candidates.append({
                "profile": pid,
                "x": int(best_x),
                "y": int(best_y),
                "w": pw,
                "h": ph,
                "spatial_ncc": float(max_spatial),
                "gradient_ncc": float(max_grad),
                "variance_score": float(variance_score),
                "combined_score": float(combined)
            })
            
        if not candidates:
            continue
            
        candidates.sort(key=lambda x: x["combined_score"], reverse=True)
        best = candidates[0]
        detected = best["combined_score"] > 0.65
        
        proc_ms = (time.time() - start_t) * 1000
        
        res_row = {
            "filename": img_path.name,
            "width": img_w,
            "height": img_h,
            "detected": detected,
            "profile": best["profile"],
            "x": best["x"],
            "y": best["y"],
            "w": best["w"],
            "h": best["h"],
            "spatial_ncc": best["spatial_ncc"],
            "gradient_ncc": best["gradient_ncc"],
            "variance_score": best["variance_score"],
            "combined_score": best["combined_score"],
            "processing_ms": proc_ms
        }
        results.append(res_row)
        
        if detected:
            overlay = img_bgr.copy()
            cv2.rectangle(overlay, (best["x"], best["y"]), (best["x"]+best["w"], best["y"]+best["h"]), (0, 0, 255), 2)
            label = f"{best['profile']} | {best['combined_score']:.3f}"
            cv2.putText(overlay, label, (best["x"], best["y"] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            out_path = OVERLAY_DIR / img_path.name
            is_success, im_buf_arr = cv2.imencode(out_path.suffix, overlay)
            if is_success:
                im_buf_arr.tofile(str(out_path))
            detected_images.append(out_path)
            
        if i % 10 == 0:
            print(f"Processed {i}/{len(images)} images...")
            
    df = pd.DataFrame(results)
    df.to_csv(CSV_OUTPUT, index=False)
    print(f"Saved {CSV_OUTPUT}")
    
    # Phase 3: Create Contact Sheet
    if detected_images:
        print(f"Building contact sheet from {len(detected_images)} detected images...")
        thumbs = []
        thumb_size = 256
        for p in detected_images:
            try:
                file_bytes = np.fromfile(str(p), dtype=np.uint8)
                img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            except Exception:
                img = None
                
            if img is not None:
                img_resize = cv2.resize(img, (thumb_size, thumb_size))
                thumbs.append(img_resize)
                
        cols = 10
        rows = (len(thumbs) + cols - 1) // cols
        
        # Pad with black squares
        while len(thumbs) < cols * rows:
            thumbs.append(np.zeros((thumb_size, thumb_size, 3), dtype=np.uint8))
            
        row_imgs = []
        for r in range(rows):
            row = np.hstack(thumbs[r*cols:(r+1)*cols])
            row_imgs.append(row)
            
        sheet = np.vstack(row_imgs)
        is_success, im_buf_arr = cv2.imencode(CONTACT_SHEET.suffix, sheet)
        if is_success:
            im_buf_arr.tofile(str(CONTACT_SHEET))
        print(f"Saved {CONTACT_SHEET}")

if __name__ == "__main__":
    main()
