import cv2
import numpy as np
from pathlib import Path
from backend.core.watermark_engine import GeminiWatermarkEngine

def main():
    engine = GeminiWatermarkEngine()
    corpus_dir = Path("tests/input_images")
    output_dir = Path("debug/removal_test")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    images = [p for p in corpus_dir.iterdir() if p.suffix.lower() in {".jpg", ".jpeg"}]
    print(f"Testing removal on {len(images)} images...")
    
    stats = {"REMOVED": 0, "NO_WATERMARK": 0, "REMOVAL_FAILED": 0, "REVIEW_REQUIRED": 0}
    
    for idx, img_path in enumerate(images):
        file_bytes = np.fromfile(str(img_path), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        if img is None: continue
        
        result = engine.process(img)
        status = result["status"]
        stats[status] = stats.get(status, 0) + 1
        
        # Save a few examples of each status
        if stats[status] <= 5:
            out_name = f"{status}_{img_path.name}"
            # Extract just the bottom right quadrant for easy viewing
            h, w = img.shape[:2]
            quad = result["image"][h//2:, w//2:]
            
            is_success, im_buf = cv2.imencode('.jpg', quad)
            if is_success:
                im_buf.tofile(str(output_dir / out_name))
                
        if idx % 10 == 0:
            print(f"Processed {idx}/{len(images)}...")
            
    print("Final Stats:")
    for k, v in stats.items():
        print(f"  {k}: {v}")

if __name__ == "__main__":
    main()
