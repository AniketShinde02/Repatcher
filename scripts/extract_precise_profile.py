import cv2
import numpy as np
import pandas as pd
from pathlib import Path

def main():
    # Load the detection results to get exact coordinates of the 52 detected images
    df = pd.read_csv("debug/gemini_detection_results.csv")
    detected_df = df[df['detected'] == True]
    
    print(f"Aligning {len(detected_df)} detected images using CSV coordinates...")
    
    corpus_dir = Path("tests/input_images")
    
    aligned_crops = []
    
    for _, row in detected_df.iterrows():
        img_path = corpus_dir / row['filename']
        try:
            file_bytes = np.fromfile(str(img_path), dtype=np.uint8)
            img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            if img is None:
                continue
                
            x, y, w, h = int(row['x']), int(row['y']), int(row['w']), int(row['h'])
            
            # Extract a slightly larger window to see the margins (128x128 centered at watermark)
            center_x = x + w // 2
            center_y = y + h // 2
            
            crop_x1 = center_x - 64
            crop_y1 = center_y - 64
            crop_x2 = center_x + 64
            crop_y2 = center_y + 64
            
            if crop_x1 >= 0 and crop_y1 >= 0 and crop_x2 <= img.shape[1] and crop_y2 <= img.shape[0]:
                crop = img[crop_y1:crop_y2, crop_x1:crop_x2].astype(np.float32)
                aligned_crops.append(crop)
                
        except Exception as e:
            print(f"Error processing {img_path}: {e}")
            
    if not aligned_crops:
        print("No crops extracted.")
        return
        
    print(f"Successfully extracted {len(aligned_crops)} precise crops.")
    aligned_crops = np.array(aligned_crops)
    
    median_crop = np.median(aligned_crops, axis=0).astype(np.uint8)
    
    out_dir = Path("debug")
    cv2.imwrite(str(out_dir / "precise_aligned_median.jpg"), median_crop)
    print("Saved to debug/precise_aligned_median.jpg")

if __name__ == "__main__":
    main()
