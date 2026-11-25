import cv2
import numpy as np
from pathlib import Path
import math
from typing import Tuple, Dict, Any, Optional


class GeminiSparkleDetector:
    def __init__(self, template_path: Optional[str] = None):
        """
        Initializes the detector with a real calibrated alpha map of the Gemini Sparkle.
        Loaded ONCE per process via the module-level singleton in detection.py.
        """
        default_alpha_path = Path(__file__).parent / 'gemini_alpha.npy'
        if template_path and Path(template_path).exists():
            self.alpha = np.load(template_path)
        elif default_alpha_path.exists():
            self.alpha = np.load(default_alpha_path)
        else:
            raise FileNotFoundError(f"Empirical alpha map not found at {default_alpha_path}")

        # Template for NCC matching (alpha * 255)
        self.template = (self.alpha * 255).astype(np.uint8)

    def detect(self, image_bgr: np.ndarray, scales: list = None) -> Dict[str, Any]:
        """
        Detects the Gemini sparkle using multi-scale template matching.

        Performance: The search region is downsampled by 2x first (0.5 subsample factor).
        We search the FULL image (to support any watermark placement) and test a robust
        range of absolute template sizes (to support cropped images where relative
        sizing would fail).
        """
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        img_h, img_w = gray.shape

        # Search the entire image (no position hardcoding)
        region_full = gray
        offset_y, offset_x = 0, 0

        # Downsample search region by factor DOWNSAMPLE for speed
        DOWNSAMPLE = 2
        region = cv2.resize(
            region_full,
            (region_full.shape[1] // DOWNSAMPLE, region_full.shape[0] // DOWNSAMPLE),
            interpolation=cv2.INTER_AREA
        )

        # Absolute template pixel sizes in full-res (handling various generation sizes & crops)
        # Gemini renders are typically 512, 1024, 1536, 2048, placing the logo between ~18px and ~100px.
        target_sizes = [24, 32, 48, 64, 80, 96, 112, 128]

        best_score = -1.0
        best_bbox = None
        best_scale = 1.0

        for size in target_sizes:
            tw_full = size
            th_full = size
            tw = max(8, tw_full // DOWNSAMPLE)
            th = max(8, th_full // DOWNSAMPLE)

            if tw >= region.shape[1] or th >= region.shape[0]:
                continue

            resized_template = cv2.resize(
                self.template, (tw, th), interpolation=cv2.INTER_AREA
            )

            res = cv2.matchTemplate(region, resized_template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(res)

            if max_val > best_score:
                best_score = max_val
                # Convert back to full-resolution coordinates
                fx = max_loc[0] * DOWNSAMPLE + offset_x
                fy = max_loc[1] * DOWNSAMPLE + offset_y
                best_bbox = (fx, fy, tw_full, th_full)
                # Scale relative to the 64x64 base template for reporting
                best_scale = size / 64.0

        return {
            "score": best_score,
            "bbox": best_bbox,
            "scale": best_scale,
        }

    def get_alpha_for_bbox(self, bbox: Tuple[int, int, int, int]) -> np.ndarray:
        """Returns alpha map resized to the detected bounding box."""
        _, _, w, h = bbox
        return cv2.resize(self.alpha, (w, h), interpolation=cv2.INTER_AREA)

    def generate_mask(
        self,
        image_shape: Tuple[int, int],
        bbox: Tuple[int, int, int, int],
        padding: int = 12,
    ) -> np.ndarray:
        """
        Generates a precise mask from the alpha map rather than an ellipse.
        Applies a configurable dilation for padding.
        """
        mask = np.zeros(image_shape, dtype=np.uint8)
        if bbox:
            x, y, w, h = bbox
            img_h, img_w = image_shape

            # Clamp to image bounds
            x1 = max(0, x)
            y1 = max(0, y)
            x2 = min(img_w, x + w)
            y2 = min(img_h, y + h)
            w_real = x2 - x1
            h_real = y2 - y1
            if w_real <= 0 or h_real <= 0:
                return mask

            resized_alpha = cv2.resize(self.alpha, (w_real, h_real), interpolation=cv2.INTER_AREA)
            core_mask = (resized_alpha > 0.1).astype(np.uint8) * 255
            mask[y1:y2, x1:x2] = core_mask

            if padding > 0:
                kernel = cv2.getStructuringElement(
                    cv2.MORPH_ELLIPSE, (padding * 2 + 1, padding * 2 + 1)
                )
                mask = cv2.dilate(mask, kernel)

        return mask
