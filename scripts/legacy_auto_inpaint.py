import cv2
import numpy as np
import os
import glob

input_dir = "input_images"
output_dir = "cleaned_images"

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

def remove_watermark(image_path, out_path):
    img = cv2.imread(image_path)
    if img is None:
        return
        
    h, w = img.shape[:2]
    
    # We will look for the bright star watermark in the bottom-right area.
    # Let's search the bottom right 300x300 pixels.
    search_size = 400
    x_start = max(0, w - search_size)
    y_start = max(0, h - search_size)
    
    roi = img[y_start:h, x_start:w]
    gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    
    # The star is typically a bright white translucent shape. 
    # We use a threshold to isolate bright spots.
    # To handle varying brightness, we can use an adaptive threshold or a high fixed one.
    _, thresh = cv2.threshold(gray_roi, 210, 255, cv2.THRESH_BINARY)
    
    # Find contours (shapes) in the thresholded image
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    roi_mask = np.zeros(roi.shape[:2], dtype=np.uint8)
    
    # Filter shapes that are likely to be the watermark star
    for cnt in contours:
        area = cv2.contourArea(cnt)
        # The star is usually between 50 and 5000 pixels in area
        if 20 < area < 4000:
            cv2.drawContours(roi_mask, [cnt], -1, 255, thickness=cv2.FILLED)
            
    # Dilate the mask aggressively to cover the translucent fading edges of the star
    kernel = np.ones((7,7), np.uint8)
    roi_mask = cv2.dilate(roi_mask, kernel, iterations=3)
    
    # Place it back in the full-size mask
    full_mask = np.zeros((h, w), dtype=np.uint8)
    full_mask[y_start:h, x_start:w] = roi_mask
    
    # Inpaint the original image using the mask
    # cv2.INPAINT_TELEA is excellent for smooth backgrounds like marble floors
    inpainted = cv2.inpaint(img, full_mask, 7, cv2.INPAINT_TELEA)
    
    cv2.imwrite(out_path, inpainted)

# Test it on a single image first
test_img = r"input_images\Indo_Western_garment_synthesis_202607312246_2.jpeg"
test_out = r"cleaned_images\test_smart_inpaint.jpeg"
remove_watermark(test_img, test_out)
print(f"Tested smart inpaint on {test_img}. Saved to {test_out}")
