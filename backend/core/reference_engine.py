import cv2
import numpy as np
from pathlib import Path
from backend.core.cv_utils import safe_imread

class ReferenceEngine:
    def __init__(self, ref_image_path: Path, ref_mask_path: Path):
        self.ref_image = safe_imread(ref_image_path, cv2.IMREAD_COLOR)
        self.ref_mask = safe_imread(ref_mask_path, cv2.IMREAD_GRAYSCALE)
        
        if self.ref_image is None or self.ref_mask is None:
            raise ValueError("Could not read reference image or mask.")
            
        # Extract features (bounding box of the mask)
        y_indices, x_indices = np.where(self.ref_mask > 0)
        if len(y_indices) == 0:
            raise ValueError("Reference mask is empty.")
            
        self.y_min, self.y_max = y_indices.min(), y_indices.max()
        self.x_min, self.x_max = x_indices.min(), x_indices.max()
        
        # Extract the template from the reference image corresponding to the mask
        self.template = self.ref_image[self.y_min:self.y_max, self.x_min:self.x_max]
        self.template_mask = self.ref_mask[self.y_min:self.y_max, self.x_min:self.x_max]
        
        # Calculate relative position and scale
        h, w = self.ref_image.shape[:2]
        self.rel_x = self.x_min / w
        self.rel_y = self.y_min / h
        self.rel_w = (self.x_max - self.x_min) / w
        self.rel_h = (self.y_max - self.y_min) / h
        
    def match_target(self, target_image_path: Path) -> dict:
        """
        Attempts to locate the reference watermark in the target image.
        Returns: {"found": bool, "confidence": float, "mask": np.ndarray, "confidence_level": str}
        """
        target_img = safe_imread(target_image_path, cv2.IMREAD_COLOR)
        if target_img is None:
            return {"found": False, "confidence": 0.0, "mask": None, "confidence_level": "NONE"}
            
        t_h, t_w = target_img.shape[:2]
        
        # LEVEL 1: Relative position/size matching (Estimate)
        est_w = int(self.rel_w * t_w)
        est_h = int(self.rel_h * t_h)
        est_x = int(self.rel_x * t_w)
        est_y = int(self.rel_y * t_h)
        
        # Resize template to match target scale estimation
        if est_w == 0 or est_h == 0:
            return {"found": False, "confidence": 0.0, "mask": None, "confidence_level": "NONE"}
            
        scaled_template = cv2.resize(self.template, (est_w, est_h))
        scaled_template_mask = cv2.resize(self.template_mask, (est_w, est_h), interpolation=cv2.INTER_NEAREST)
        scaled_template_mask = (scaled_template_mask > 0).astype(np.uint8) * 255
        
        # LEVEL 2: Template / feature matching
        # We search a region around the estimated position to handle slight shifts
        padding_x = int(est_w * 0.5)
        padding_y = int(est_h * 0.5)
        
        search_x_min = max(0, est_x - padding_x)
        search_y_min = max(0, est_y - padding_y)
        search_x_max = min(t_w, est_x + est_w + padding_x)
        search_y_max = min(t_h, est_y + est_h + padding_y)
        
        search_region = target_img[search_y_min:search_y_max, search_x_min:search_x_max]
        
        if search_region.shape[0] < est_h or search_region.shape[1] < est_w:
            return {"found": False, "confidence": 0.0, "mask": None, "confidence_level": "NONE"}
            
        # Perform Template Matching
        result = cv2.matchTemplate(search_region, scaled_template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        confidence = max_val
        
        # Map localized match back to global coordinates
        best_x = max_loc[0] + search_x_min
        best_y = max_loc[1] + search_y_min
        
        # LEVEL 3: Geometric Validation
        # Check if the matched position is reasonably close to the expected relative position
        dist_x = abs(best_x - est_x) / t_w
        dist_y = abs(best_y - est_y) / t_h
        
        if dist_x > 0.1 or dist_y > 0.1:
            confidence -= 0.3 # Penalize for geometric deviation
            
        confidence = max(0.0, min(1.0, confidence))
        
        level = "NONE"
        if confidence > 0.8:
            level = "HIGH"
        elif confidence > 0.5:
            level = "MEDIUM"
        else:
            level = "LOW"
            
        # Create output mask
        out_mask = np.zeros((t_h, t_w), dtype=np.uint8)
        if level in ["HIGH", "MEDIUM"]:
            # Place scaled mask at best location
            end_y = min(t_h, best_y + est_h)
            end_x = min(t_w, best_x + est_w)
            
            # Crop scaled mask if it goes out of bounds
            mask_h = end_y - best_y
            mask_w = end_x - best_x
            
            out_mask[best_y:end_y, best_x:end_x] = scaled_template_mask[:mask_h, :mask_w]
            
        return {
            "found": level in ["HIGH", "MEDIUM"],
            "confidence": confidence,
            "mask": out_mask,
            "confidence_level": level,
            "bbox": [best_x, best_y, est_w, est_h] if level in ["HIGH", "MEDIUM"] else None
        }
