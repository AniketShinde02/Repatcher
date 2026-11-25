import cv2
import numpy as np
from pathlib import Path

def main():
    corpus_dir = Path("tests/input_images")
    valid_exts = {".png", ".jpg", ".jpeg", ".webp"}
    images = [p for p in corpus_dir.iterdir() if p.suffix.lower() in valid_exts]
    
    print(f"Averaging corners of {len(images)} images to extract watermark...")
    
    corners = []
    for img_path in images:
        try:
            file_bytes = np.fromfile(str(img_path), dtype=np.uint8)
            img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            if img is not None:
                h, w = img.shape[:2]
                corner = img[max(0, h-128):h, max(0, w-128):w].astype(np.float32)
                if corner.shape[:2] == (128, 128):
                    corners.append(corner)
        except Exception:
            pass
            
    if not corners:
        print("No corners extracted.")
        return
        
    corners = np.array(corners)
    
    # Using median is better than mean to eliminate strong background edges
    median_corner = np.median(corners, axis=0).astype(np.uint8)
    mean_corner = np.mean(corners, axis=0).astype(np.uint8)
    
    out_dir = Path("debug")
    cv2.imwrite(str(out_dir / "corpus_median_corner.jpg"), median_corner)
    cv2.imwrite(str(out_dir / "corpus_mean_corner.jpg"), mean_corner)
    
    # Try to enhance the alpha channel from the median
    # Convert to grayscale
    gray = cv2.cvtColor(median_corner, cv2.COLOR_BGR2GRAY)
    
    # Enhance contrast to see the watermark clearly
    # Assuming watermark makes pixels brighter
    blur = cv2.GaussianBlur(gray, (5,5), 0)
    
    cv2.imwrite(str(out_dir / "corpus_watermark_enhanced.jpg"), blur)
    print("Saved corpus extraction results in debug/")

if __name__ == "__main__":
    main()
