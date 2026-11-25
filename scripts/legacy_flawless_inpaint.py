import cv2
import numpy as np
import os
from concurrent.futures import ThreadPoolExecutor

input_dir = "input_images"
output_dir = "cleaned_images"

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

files = [f for f in os.listdir(input_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]

def process_file(filename):
    img_path = os.path.join(input_dir, filename)
    out_path = os.path.join(output_dir, filename)
    
    img = cv2.imread(img_path)
    if img is None:
        return
        
    h, w = img.shape[:2]
    
    # Create an empty mask for the full image
    mask = np.zeros((h, w), dtype=np.uint8)
    
    # Narrow down the search area to the exact bottom-right corner (150x150 pixels)
    # where the watermark star is located.
    search_size = 150
    x_s = max(0, w - search_size)
    y_s = max(0, h - search_size)
    
    roi = img[y_s:h, x_s:w]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    
    # Threshold to find bright pixels (the star watermark)
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    roi_mask = np.zeros(roi.shape[:2], dtype=np.uint8)
    for cnt in contours:
        # Filter out tiny noise, keep shapes that could be the star
        if cv2.contourArea(cnt) > 10:
            cv2.drawContours(roi_mask, [cnt], -1, 255, thickness=cv2.FILLED)
            
    # Dilate heavily so it completely covers the translucent fading edges of the star
    kernel = np.ones((7,7), np.uint8)
    roi_mask = cv2.dilate(roi_mask, kernel, iterations=3)
    
    # If the threshold didn't catch anything, we'll fall back to masking a small 80x80 box
    # right where the star usually is, just to be safe.
    if np.sum(roi_mask) == 0:
        fallback_w, fallback_h = 80, 80
        fx = max(0, roi_mask.shape[1] - fallback_w - 20)
        fy = max(0, roi_mask.shape[0] - fallback_h - 20)
        roi_mask[fy:fy+fallback_h, fx:fx+fallback_w] = 255
    
    mask[y_s:h, x_s:w] = roi_mask
    
    # Apply OpenCV Telea Inpainting algorithm to reconstruct the background flawlessly
    inpainted = cv2.inpaint(img, mask, inpaintRadius=7, flags=cv2.INPAINT_TELEA)
    
    cv2.imwrite(out_path, inpainted)
    print(f"Processed: {filename}")

print(f"Starting proper inpainting for {len(files)} images...")
with ThreadPoolExecutor(max_workers=8) as executor:
    executor.map(process_file, files)
print("Finished inpainting all images!")
