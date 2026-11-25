import cv2
import numpy as np
from pathlib import Path
import time
import psutil
import json

from backend.core.watermark_engine import GeminiWatermarkEngine
from backend.core.detection import detect_watermark
from backend.core.inpainting import process_image_single

def get_peak_memory():
    return psutil.virtual_memory().used / (1024**3)

def run_baseline():
    corpus_dir = Path("tests/input_images")
    images = list(corpus_dir.glob("*.jpeg")) + list(corpus_dir.glob("*.jpg"))
    images = images[:154]
    
    print(f"Loaded {len(images)} images.")
    
    bulk_engine = GeminiWatermarkEngine()
    
    bulk_stats = {
        "detected": 0, "failed_detect": 0, "removed": 0, "failed_remove": 0,
        "det_times": [], "rem_times": []
    }
    
    single_stats = {
        "detected": 0, "failed_detect": 0, "removed": 0, "failed_remove": 0,
        "det_times": [], "rem_times": []
    }
    
    t0 = time.time()
    
    # Run Bulk (Deterministic)
    print("Running Bulk Baseline...")
    for idx, img_path in enumerate(images):
        img = cv2.imdecode(np.fromfile(str(img_path), dtype=np.uint8), cv2.IMREAD_COLOR)
        h, w = img.shape[:2]
        
        # We can just time the whole process since detect/process are unified in process()
        t1 = time.time()
        res = bulk_engine.process(img)
        dt = time.time() - t1
        
        status = res["status"]
        if status in ("REMOVED", "REVIEW_REQUIRED"):
            bulk_stats["detected"] += 1
            bulk_stats["removed"] += 1
            bulk_stats["rem_times"].append(dt)
        elif status == "NO_WATERMARK":
            bulk_stats["failed_detect"] += 1
        elif status == "REMOVAL_FAILED":
            bulk_stats["detected"] += 1
            bulk_stats["failed_remove"] += 1
            bulk_stats["rem_times"].append(dt)
            
        if idx % 20 == 0:
            print(f"  Bulk {idx}/{len(images)}")
            
    bulk_total = time.time() - t0
            
    # Run Single (v4 Detector + LaMa)
    # We will sample 25 images to avoid a 10 minute wait, or run all if fast
    sample_size = 25
    print(f"\nRunning Single Baseline (sampled {sample_size} images)...")
    
    import shutil
    import uuid
    from backend.core.paths import STAGE_INPUT, STAGE_OUTPUT, STAGE_MASK
    
    t0_s = time.time()
    for idx, img_path in enumerate(images[:sample_size]):
        # Setup temp paths
        job_id = str(uuid.uuid4())
        temp_input = STAGE_INPUT / f"{job_id}.jpeg"
        shutil.copy2(img_path, temp_input)
        mask_path = STAGE_MASK / f"{job_id}.png"
        out_path = STAGE_OUTPUT / f"{job_id}.jpeg"
        
        # Detection
        t_d = time.time()
        det = detect_watermark(temp_input)
        det_time = time.time() - t_d
        single_stats["det_times"].append(det_time)
        
        if det["detected"]:
            single_stats["detected"] += 1
            cv2.imwrite(str(mask_path), det["mask"])
            
            # Removal
            t_r = time.time()
            success, _ = process_image_single(temp_input, mask_path, out_path)
            rem_time = time.time() - t_r
            single_stats["rem_times"].append(rem_time)
            
            if success:
                single_stats["removed"] += 1
            else:
                single_stats["failed_remove"] += 1
        else:
            single_stats["failed_detect"] += 1
            
        temp_input.unlink(missing_ok=True)
        mask_path.unlink(missing_ok=True)
        out_path.unlink(missing_ok=True)
        
        if idx % 5 == 0:
            print(f"  Single {idx}/{sample_size}")
            
    single_total = time.time() - t0_s
    
    with open("debug/baseline_stats.json", "w") as f:
        json.dump({
            "bulk": bulk_stats,
            "single": single_stats,
            "bulk_total_time": bulk_total,
            "single_total_time": single_total,
            "single_sample_size": sample_size,
            "total_images": len(images)
        }, f, indent=2)
        
    print("Baseline stats generated.")

if __name__ == "__main__":
    run_baseline()
