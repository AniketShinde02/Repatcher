import cv2
import numpy as np
from pathlib import Path

def main():
    corpus_dir = Path("tests/input_images")
    valid_exts = {".png", ".jpg", ".jpeg", ".webp"}
    images = [p for p in corpus_dir.iterdir() if p.suffix.lower() in valid_exts]
    
    print(f"Aligning and averaging {len(images)} images to extract watermark...")
    
    # Load the preview PNG which we saved as legacy_48.npy to use as a crude template
    crude_template = np.load("backend/models/gemini/profiles/legacy_48.npy")
    crude_template_bgr = (crude_template * 255).astype(np.uint8)
    if len(crude_template_bgr.shape) == 2:
        crude_template_bgr = cv2.cvtColor(crude_template_bgr, cv2.COLOR_GRAY2BGR)
    
    th, tw = crude_template_bgr.shape[:2]
    
    # We will use Sobel gradients for matching since it's more robust to background color
    sobelx = cv2.Sobel(crude_template_bgr, cv2.CV_32F, 1, 0, ksize=3)
    sobely = cv2.Sobel(crude_template_bgr, cv2.CV_32F, 0, 1, ksize=3)
    template_grad = cv2.magnitude(sobelx, sobely)
    
    aligned_crops = []
    
    for img_path in images:
        try:
            file_bytes = np.fromfile(str(img_path), dtype=np.uint8)
            img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            if img is None:
                continue
                
            h, w = img.shape[:2]
            # Search only in the bottom right quadrant
            search_roi = img[h//2:h, w//2:w]
            
            sobelx_roi = cv2.Sobel(search_roi, cv2.CV_32F, 1, 0, ksize=3)
            sobely_roi = cv2.Sobel(search_roi, cv2.CV_32F, 0, 1, ksize=3)
            roi_grad = cv2.magnitude(sobelx_roi, sobely_roi)
            
            res = cv2.matchTemplate(roi_grad, template_grad, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
            
            # max_loc is (x, y) in the search_roi
            # translate to full image coords
            best_x = max_loc[0] + w//2
            best_y = max_loc[1] + h//2
            
            # Crop a 128x128 window centered around the template's center
            center_x = best_x + tw // 2
            center_y = best_y + th // 2
            
            crop_x1 = center_x - 64
            crop_y1 = center_y - 64
            crop_x2 = center_x + 64
            crop_y2 = center_y + 64
            
            if crop_x1 >= 0 and crop_y1 >= 0 and crop_x2 <= w and crop_y2 <= h:
                crop = img[crop_y1:crop_y2, crop_x1:crop_x2].astype(np.float32)
                aligned_crops.append(crop)
                
        except Exception as e:
            print(f"Error processing {img_path}: {e}")
            
    if not aligned_crops:
        print("No crops extracted.")
        return
        
    print(f"Successfully aligned {len(aligned_crops)} crops.")
    aligned_crops = np.array(aligned_crops)
    
    median_crop = np.median(aligned_crops, axis=0).astype(np.uint8)
    
    out_dir = Path("debug")
    out_dir.mkdir(exist_ok=True)
    cv2.imwrite(str(out_dir / "aligned_corpus_median.jpg"), median_crop)
    
    print("Saved aligned corpus median to debug/aligned_corpus_median.jpg")

if __name__ == "__main__":
    main()
