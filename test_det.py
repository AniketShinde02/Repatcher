import cv2
import os
from pathlib import Path
import numpy as np

os.makedirs('debug', exist_ok=True)
img_path = Path('d:/Starter Kit/image_processor_sandbox/tests/phase8_data/standard_batch_1.jpg')

from backend.core.detection import detect_watermark

res = detect_watermark(img_path)
print(f"Detected: {res['detected']}, Score: {res['confidence']:.3f}, Level: {res['confidence_level']}")

mask = res['mask']
img = cv2.imread(str(img_path))
cv2.imwrite('debug/test_original.jpg', img)

if mask is not None and np.any(mask > 0):
    cv2.imwrite('debug/test_mask.png', mask)
    img_overlay = img.copy()
    img_overlay[mask > 0] = [0, 0, 255]
    cv2.imwrite('debug/test_overlay.jpg', img_overlay)
    print('Saved debug files.')
else:
    print('No valid mask returned.')
