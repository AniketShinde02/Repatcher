import cv2
import numpy as np
from pathlib import Path
from typing import Tuple

class DeterministicGeminiRemover:
    def __init__(self):
        core_dir = Path(__file__).parent
        self.profile_48 = np.load(core_dir / 'gemini_48.npy')
        self.profile_96 = np.load(core_dir / 'gemini_96.npy')

    def remove(self, image_bgr: np.ndarray, bbox: Tuple[int, int, int, int], profile: str = "96") -> np.ndarray:
        """
        Removes the Gemini sparkle from the specified bounding box using Reverse Alpha Blending.
        Equation: original = (watermarked - alpha * 255) / (1 - alpha)
        """
        x, y, w, h = bbox
        
        # Ensure bbox is within image bounds
        img_h, img_w = image_bgr.shape[:2]
        x1 = max(0, x)
        y1 = max(0, y)
        x2 = min(img_w, x + w)
        y2 = min(img_h, y + h)
        
        # Adjust w, h if we hit the boundary
        w_real = x2 - x1
        h_real = y2 - y1
        
        if w_real <= 0 or h_real <= 0:
            return image_bgr.copy()
            
        result = image_bgr.copy()
        
        base_alpha = self.profile_48 if profile == "48" else self.profile_96
        
        # Resize alpha to exactly match the detection bounding box
        alpha_patch = cv2.resize(base_alpha, (w_real, h_real), interpolation=cv2.INTER_AREA)
        
        # Convert to 3 channels to match BGR
        alpha_3d = np.stack([alpha_patch]*3, axis=-1)
        
        roi = result[y1:y2, x1:x2].astype(np.float32)
        
        # Prevent division by exactly zero. 
        # When alpha approaches 1, the original pixels are completely lost and cannot be recovered via blending.
        # We cap alpha at 0.95 for the mathematical inversion.
        safe_alpha = np.clip(alpha_3d, 0, 0.95)
        
        # Reverse Alpha Blending
        # watermark is white (255, 255, 255)
        logo_pixels = 255.0
        
        # original = (watermarked - alpha * logo) / (1 - alpha)
        recovered = (roi - safe_alpha * logo_pixels) / (1.0 - safe_alpha)
        
        # Clip to valid range and cast back to uint8
        recovered = np.clip(recovered, 0, 255).astype(np.uint8)
        
        # To handle the fully opaque core where alpha was > 0.95 (which we capped),
        # the reverse math leaves some noise/artifacts.
        # We can use a tiny CPU Telea inpainting just on the absolute core.
        core_mask = (alpha_patch > 0.95).astype(np.uint8) * 255
        if np.any(core_mask > 0):
            # Expand the core mask slightly to blend the edges of the recovered area
            kernel = np.ones((3,3), np.uint8)
            core_mask = cv2.dilate(core_mask, kernel, iterations=1)
            recovered = cv2.inpaint(recovered, core_mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)
            
        result[y1:y2, x1:x2] = recovered
        
        return result
