import cv2
import numpy as np
from typing import Dict, Any, Tuple
from backend.core.sparkle_detector import GeminiSparkleDetector
from backend.core.inpainting import process_image_in_memory

ENABLE_VISION_FALLBACK = False

class GeminiWatermarkEngine:
    def __init__(self):
        self.detector = GeminiSparkleDetector()

    def detect(self, image_bgr: np.ndarray) -> Dict[str, Any]:
        """
        Unified robust multi-scale template matching via GeminiSparkleDetector.
        """
        res = self.detector.detect(image_bgr)
        
        score = res.get("score", 0.0)
        bbox = res.get("bbox")
        
        if score < 0.70 or bbox is None:
            return {"detected": False, "reason": "LOW_CONFIDENCE", "confidence": float(score)}
            
        x, y, w, h = bbox
        
        return {
            "detected": True,
            "confidence": float(score),
            "x": int(x),
            "y": int(y),
            "width": int(w),
            "height": int(h),
            "profile_id": "unified_alpha"
        }

    def _local_lama_crop_inpaint(self, image_bgr: np.ndarray, bbox: Tuple[int, int, int, int]) -> Dict[str, Any]:
        """Runs LaMa inference on a local crop and composites it back."""
        try:
            x, y, w, h = bbox
            img_h, img_w = image_bgr.shape[:2]
            
            # Add padding
            px, py = 32, 32
            x1, y1 = max(0, x - px), max(0, y - py)
            x2, y2 = min(img_w, x + w + px), min(img_h, y + h + py)
            
            crop_bgr = image_bgr[y1:y2, x1:x2]
            
            # Generate mask for the crop
            mask_alpha = self.detector.get_alpha_for_bbox((x, y, w, h))
            crop_mask = np.zeros_like(crop_bgr[:,:,0])
            dy, dx = y - y1, x - x1
            crop_mask[dy:dy+h, dx:dx+w] = (mask_alpha > 0.1).astype(np.uint8) * 255
            
            # Dilate mask for LaMa
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            crop_mask = cv2.dilate(crop_mask, kernel)
            
            result_crop = process_image_in_memory(crop_bgr, crop_mask)
            
            final_bgr = image_bgr.copy()
            final_bgr[y1:y2, x1:x2] = result_crop
            
            return {
                "status": "REMOVED",
                "image": final_bgr,
                "metrics": {"method": "LaMa_Crop", "bbox": bbox}
            }
        except Exception as e:
            return {
                "status": "REMOVAL_FAILED",
                "reason": f"LaMa crop inpainting failed: {e}",
                "image": image_bgr,
                "metrics": {"method": "LaMa_Crop_Failed"}
            }

    def process(self, image_bgr: np.ndarray) -> Dict[str, Any]:
        """
        Smart Routing Engine:
        Tier 1: Confidence > 0.90 -> deterministic removal
        Tier 2: Confidence 0.70 - 0.90 -> local LaMa crop
        Tier 3: Uncertain -> optional OmniRouter -> local LaMa crop
        Tier 4: Review
        """
        det = self.detect(image_bgr)
        confidence = det.get("confidence", 0.0)
        
        # --- Tier 1 & Tier 2: Local Detector Found Something ---
        if det.get("detected", False) and confidence >= 0.70:
            bbox = (det["x"], det["y"], det["width"], det["height"])
            
            # Tier 1: Very High Confidence -> Try Deterministic Reverse Blend
            if confidence >= 0.90:
                result = self._try_deterministic_removal(image_bgr, det)
                if result["status"] == "REMOVED":
                    return result
                
                # If deterministic failed (err_ratio high), fall through to Tier 2 LaMa!
                print(f"[Router] Deterministic failed ({result.get('reason')}). Falling back to LaMa Crop.")
            
            # Tier 2: Medium Confidence or Deterministic Failed -> LaMa Crop
            return self._local_lama_crop_inpaint(image_bgr, bbox)
            
        # --- Tier 3: Low Confidence / Uncertain -> Vision Fallback ---
        if ENABLE_VISION_FALLBACK:
            # TODO: Call OmniRouter client to get bbox
            pass
            
        # --- Tier 4: Review ---
        return {
            "status": "REVIEW_REQUIRED" if confidence > 0.40 else "NO_WATERMARK",
            "reason": "Detection confidence too low and vision fallback disabled.",
            "image": image_bgr,
            "metrics": det
        }

    def _try_deterministic_removal(self, image_bgr: np.ndarray, det: Dict[str, Any]) -> Dict[str, Any]:
        """Attempts the fast deterministic reverse-blend. Returns dict with status."""
        x, y, w, h = det["x"], det["y"], det["width"], det["height"]
        alpha = self.detector.get_alpha_for_bbox((x, y, w, h))
        
        img_h, img_w = image_bgr.shape[:2]
        x1, y1 = max(0, x), max(0, y)
        x2, y2 = min(img_w, x + w), min(img_h, y + h)
        w_real, h_real = x2 - x1, y2 - y1
        
        if w_real != w or h_real != h:
            alpha = alpha[:h_real, :w_real]
            
        alpha_3d = np.stack([alpha]*3, axis=-1)
        roi = image_bgr[y1:y2, x1:x2].astype(np.float32)
        logo_pixels = 255.0
        
        safe_alpha = np.clip(alpha_3d, 0, 0.95)
        recovered_raw = (roi - safe_alpha * logo_pixels) / (1.0 - safe_alpha)
        
        neg_count = np.count_nonzero(recovered_raw < -10)
        over_count = np.count_nonzero(recovered_raw > 265)
        total_pixels = w_real * h_real * 3
        err_ratio = (neg_count + over_count) / total_pixels
        
        if err_ratio > 0.05:
            return {"status": "REMOVAL_FAILED", "reason": f"Bad blend math. err_ratio={err_ratio:.3f}"}
            
        recovered = np.clip(recovered_raw, 0, 255).astype(np.uint8)
        
        diff = cv2.absdiff(roi.astype(np.uint8), recovered)
        changed_pixels = np.count_nonzero(diff > 0)
        
        if changed_pixels == 0:
            return {"status": "REMOVAL_FAILED", "reason": "No pixels changed in ROI."}
            
        core_mask = (alpha > 0.85).astype(np.uint8) * 255
        if np.any(core_mask > 0):
            kernel = np.ones((3,3), np.uint8)
            edge_mask = cv2.dilate(core_mask, kernel, iterations=1) - core_mask
            if np.any(edge_mask > 0):
                recovered = cv2.inpaint(recovered, edge_mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)

        result = image_bgr.copy()
        result[y1:y2, x1:x2] = recovered
        
        det["method"] = "Deterministic_Reverse_Blend"
        det["err_ratio"] = float(err_ratio)
        
        if err_ratio > 0.01:
            return {"status": "REMOVAL_FAILED", "reason": f"Borderline err_ratio={err_ratio:.3f}"}
            
        return {
            "status": "REMOVED",
            "image": result,
            "metrics": det
        }
