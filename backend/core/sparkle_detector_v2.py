import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple

class GeminiSparkleDetectorV2:
    def __init__(self):
        """
        Initializes the V2 Detector using calibrated mathematical profiles.
        Loads 48px and 96px profiles into memory once.
        """
        core_dir = Path(__file__).parent
        self.profile_48_alpha = np.load(core_dir / 'gemini_48.npy')
        self.profile_96_alpha = np.load(core_dir / 'gemini_96.npy')
        
        self.profile_48 = (self.profile_48_alpha * 255).astype(np.uint8)
        self.profile_96 = (self.profile_96_alpha * 255).astype(np.uint8)
        
        # Precompute Sobel gradients for templates
        self.grad_48 = self._compute_gradient_magnitude(self.profile_48)
        self.grad_96 = self._compute_gradient_magnitude(self.profile_96)
        
    def _compute_gradient_magnitude(self, img: np.ndarray) -> np.ndarray:
        gx = cv2.Sobel(img, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(img, cv2.CV_32F, 0, 1, ksize=3)
        mag = cv2.magnitude(gx, gy)
        return cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        
    def detect(self, image_bgr: np.ndarray) -> Dict[str, Any]:
        """
        Detects Gemini sparkle using a multi-profile, multi-scale strategy with 
        spatial NCC, gradient NCC, and variance scoring.
        Returns full geometry and multiple candidates.
        """
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        img_h, img_w = gray.shape
        
        DOWNSAMPLE = 2
        region = cv2.resize(gray, (img_w // DOWNSAMPLE, img_h // DOWNSAMPLE), interpolation=cv2.INTER_AREA)
        region_grad = self._compute_gradient_magnitude(region)
        
        candidates = []
        
        # Test scales for both profiles to cover effective sizes from ~20px to ~128px
        # 48px profile scales: 0.5 to 1.5 -> 24px to 72px
        # 96px profile scales: 0.8 to 1.4 -> 76px to 134px
        
        profiles_to_test = [
            ("48", self.profile_48, self.grad_48, [0.5, 0.75, 1.0, 1.25, 1.5]),
            ("96", self.profile_96, self.grad_96, [0.8, 1.0, 1.2, 1.4])
        ]
        
        for profile_name, template, template_grad, scales in profiles_to_test:
            for scale in scales:
                tw_full = int(template.shape[1] * scale)
                th_full = int(template.shape[0] * scale)
                tw = max(8, tw_full // DOWNSAMPLE)
                th = max(8, th_full // DOWNSAMPLE)
                
                if tw >= region.shape[1] or th >= region.shape[0]:
                    continue
                    
                resized_temp = cv2.resize(template, (tw, th), interpolation=cv2.INTER_AREA)
                resized_grad = cv2.resize(template_grad, (tw, th), interpolation=cv2.INTER_AREA)
                
                # Spatial NCC
                res_spatial = cv2.matchTemplate(region, resized_temp, cv2.TM_CCOEFF_NORMED)
                # Gradient NCC
                res_grad = cv2.matchTemplate(region_grad, resized_grad, cv2.TM_CCOEFF_NORMED)
                
                # Combined score (weighted)
                combined_res = (res_spatial * 0.6) + (res_grad * 0.4)
                
                # Find best in this scale
                _, max_val, _, max_loc = cv2.minMaxLoc(combined_res)
                
                if max_val > 0.4: # Only consider reasonable candidates
                    fx = max_loc[0] * DOWNSAMPLE
                    fy = max_loc[1] * DOWNSAMPLE
                    
                    # Local variance score at full res
                    patch = gray[fy:fy+th_full, fx:fx+tw_full]
                    variance_score = 0.0
                    if patch.shape == (th_full, tw_full):
                        variance = np.var(patch)
                        # Watermarks typically sit on fairly uniform/low-variance backgrounds
                        # A very high variance means highly textured background which might yield false positives
                        variance_score = max(0.0, 1.0 - (variance / 5000.0))
                    
                    candidates.append({
                        "profile": profile_name,
                        "x": fx,
                        "y": fy,
                        "width": tw_full,
                        "height": th_full,
                        "scale": scale,
                        "confidence": float(max_val),
                        "spatial_ncc": float(res_spatial[max_loc[1], max_loc[0]]),
                        "gradient_ncc": float(res_grad[max_loc[1], max_loc[0]]),
                        "variance_score": float(variance_score)
                    })
                    
        # Sort candidates by combined confidence
        # Prioritize corners: if candidate is in the bottom right 25% of the image, boost score slightly
        for c in candidates:
            in_bottom_right = (c["x"] > img_w * 0.75) and (c["y"] > img_h * 0.75)
            if in_bottom_right:
                c["confidence"] *= 1.15
            
        candidates.sort(key=lambda x: x["confidence"], reverse=True)
        
        # Filter overlapping candidates
        filtered = []
        for c in candidates:
            overlap = False
            for f in filtered:
                # Simple IoU/overlap check
                if abs(c["x"] - f["x"]) < c["width"] and abs(c["y"] - f["y"]) < c["height"]:
                    overlap = True
                    break
            if not overlap:
                filtered.append(c)
                
        # Return standardized geometry
        if not filtered or filtered[0]["confidence"] < 0.6:
            return {
                "detected": False,
                "profile": "NONE",
                "x": 0, "y": 0, "width": 0, "height": 0, "scale": 1.0,
                "confidence": 0.0,
                "spatial_ncc": 0.0,
                "gradient_ncc": 0.0,
                "variance_score": 0.0,
                "candidates": filtered[:2]
            }
            
        best = filtered[0]
        return {
            "detected": True,
            "profile": best["profile"],
            "x": best["x"],
            "y": best["y"],
            "width": best["width"],
            "height": best["height"],
            "scale": best["scale"],
            "confidence": best["confidence"],
            "spatial_ncc": best["spatial_ncc"],
            "gradient_ncc": best["gradient_ncc"],
            "variance_score": best["variance_score"],
            "candidates": filtered[:2]  # Top 2
        }

# Singleton instance
_detector = None

def detect_watermark_v2(image_bgr: np.ndarray) -> Dict[str, Any]:
    global _detector
    if _detector is None:
        _detector = GeminiSparkleDetectorV2()
    return _detector.detect(image_bgr)
