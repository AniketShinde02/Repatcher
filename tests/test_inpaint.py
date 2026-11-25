import cv2
import numpy as np
import os

input_path = r"input_images\Indo_Western_garment_synthesis_202607312246_2.jpeg"
output_path = r"test_inpainted.jpeg"
mask_path = r"test_mask.jpeg"

img = cv2.imread(input_path)
if img is None:
    print(f"Could not read {input_path}")
    exit(1)

h, w = img.shape[:2]

# We will try a fixed rectangular mask over where the watermark usually is.
# Typical Midjourney/AI watermarks are around 40-80 pixels wide, near the bottom right.
# Let's mask a 120x120 area in the bottom right corner (offset by a few pixels)
mask = np.zeros((h, w), dtype=np.uint8)

# Coordinates for the mask (we can adjust these after checking the output)
# Let's guess the star is between x = w-130 to w-30, and y = h-130 to h-30
x1, x2 = w - 140, w - 20
y1, y2 = h - 140, h - 20

# Create a solid white box on the mask for the region
mask[y1:y2, x1:x2] = 255

# Apply Telea inpainting algorithm
# inpaintRadius=5 controls the radius of a circular neighborhood of each point inpainted
inpainted = cv2.inpaint(img, mask, 5, cv2.INPAINT_TELEA)

cv2.imwrite(output_path, inpainted)
cv2.imwrite(mask_path, mask)

print(f"Original shape: {w}x{h}")
print("Saved test_inpainted.jpeg and test_mask.jpeg")
