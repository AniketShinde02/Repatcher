import time
import psutil
import os
import cv2
import numpy as np
from pathlib import Path
from backend.core.sparkle_detector import GeminiSparkleDetector
from backend.core.inpainting import process_image_in_memory
from backend.core.cv_utils import safe_imread, safe_imwrite
import torch

def get_memory():
    process = psutil.Process(os.getpid())
    ram = process.memory_info().rss / (1024 ** 2)
    vram = torch.cuda.memory_allocated() / (1024 ** 2) if torch.cuda.is_available() else 0.0
    return ram, vram

def main():
    detector = GeminiSparkleDetector()
    input_dir = Path("tests/input_images")
    output_dir = Path("debug/benchmark_inpaint")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    images = list(input_dir.glob("*.jp*g"))[:10]
    
    print("--- INPAINTING BENCHMARK ---")
    results = []
    
    ram_start, vram_start = get_memory()
    
    for img_path in images:
        img_bgr = safe_imread(str(img_path))
        if img_bgr is None: continue
        
        img_h, img_w = img_bgr.shape[:2]
        
        t0 = time.time()
        det = detector.detect(img_bgr)
        t_det = time.time() - t0
        
        if det["score"] < 0.70 or not det["bbox"]:
            print(f"[{img_path.name}] Detection failed.")
            continue
            
        x, y, w, h = map(int, det["bbox"])
        
        # padding
        px, py = 32, 32
        x1, y1 = max(0, x - px), max(0, y - py)
        x2, y2 = min(img_w, x + w + px), min(img_h, y + h + py)
        
        crop_bgr = img_bgr[y1:y2, x1:x2]
        
        mask_alpha = detector.get_alpha_for_bbox((x, y, w, h))
        crop_mask = np.zeros_like(crop_bgr[:,:,0])
        
        dy, dx = y - y1, x - x1
        crop_mask[dy:dy+h, dx:dx+w] = (mask_alpha > 0.1).astype(np.uint8) * 255
        
        # Dilate mask slightly for LaMa
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        crop_mask = cv2.dilate(crop_mask, kernel)
        
        # Inpaint
        ram_before, vram_before = get_memory()
        t1 = time.time()
        result_crop = process_image_in_memory(crop_bgr, crop_mask)
        t_inpaint = time.time() - t1
        ram_after, vram_after = get_memory()
        
        final_bgr = img_bgr.copy()
        final_bgr[y1:y2, x1:x2] = result_crop
        
        safe_imwrite(str(output_dir / f"clean_{img_path.name}"), final_bgr)
        
        print(f"[{img_path.name}] Crop: {crop_bgr.shape[1]}x{crop_bgr.shape[0]} | Det: {t_det*1000:.1f}ms | Inpaint: {t_inpaint*1000:.1f}ms")
        
        results.append({
            "name": img_path.name,
            "crop_size": f"{crop_bgr.shape[1]}x{crop_bgr.shape[0]}",
            "det_time_ms": t_det * 1000,
            "inpaint_time_ms": t_inpaint * 1000,
            "ram_delta": ram_after - ram_before,
            "vram_delta": vram_after - vram_before,
        })
        
    print("\n--- SUMMARY ---")
    avg_det = sum(r["det_time_ms"] for r in results) / len(results)
    avg_inpaint = sum(r["inpaint_time_ms"] for r in results) / len(results)
    
    print(f"Avg Detection Time: {avg_det:.1f}ms")
    print(f"Avg Inpainting Time (Crop): {avg_inpaint:.1f}ms")
    
if __name__ == "__main__":
    main()
