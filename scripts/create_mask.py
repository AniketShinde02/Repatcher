import cv2
import numpy as np

# Image dimensions based on your specific images
w, h = 896, 1200

# Create a fully black mask
mask = np.zeros((h, w), dtype=np.uint8)

# The watermark is in the bottom right corner.
# Based on our previous script, we mask a 150x150 region at the bottom right.
# You can adjust this box slightly if needed.
roi_size = 150
x_s = max(0, w - roi_size)
y_s = max(0, h - roi_size)

# Create a white box where the watermark is
mask[y_s:h, x_s:w] = 255

# Save the mask
cv2.imwrite("mask.png", mask)
print("Created mask.png successfully.")
