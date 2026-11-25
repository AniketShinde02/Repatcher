import numpy as np
import cv2
from pathlib import Path
from typing import Dict, Any, Optional

class GeminiProfileManager:
    """
    Manages loading and querying of native Gemini alpha profiles.
    Different Gemini generations and output sizes use distinct watermark profiles.
    We DO NOT resize them. We select the one that natively matches the image.
    """
    def __init__(self, profiles_dir: Optional[str] = None):
        if profiles_dir is None:
            self.profiles_dir = Path(__file__).parent.parent / "models" / "gemini" / "profiles"
        else:
            self.profiles_dir = Path(profiles_dir)
            
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        
        # Profile definitions
        self.profile_definitions = {
            "legacy_48": {"filename": "legacy_48.npy", "width": 48, "height": 48, "margin_bottom": 16, "margin_right": 16},
            "gemini35_36": {"filename": "gemini35_36.npy", "width": 36, "height": 36, "margin_bottom": 12, "margin_right": 12},
            "gemini36_48": {"filename": "gemini36_48.npy", "width": 48, "height": 48, "margin_bottom": 16, "margin_right": 16},
            "large_96": {"filename": "large_96.npy", "width": 96, "height": 96, "margin_bottom": 32, "margin_right": 32}
        }
        
        self.loaded_profiles = {}
        
        # Load all available native profiles
        for pid, pdef in self.profile_definitions.items():
            path = self.profiles_dir / pdef["filename"]
            if path.exists():
                alpha = np.load(path)
                # Verify dimensions
                if alpha.shape == (pdef["height"], pdef["width"]):
                    self.loaded_profiles[pid] = {
                        "alpha": alpha,
                        "template_bgr": (alpha * 255).astype(np.uint8),
                        "width": pdef["width"],
                        "height": pdef["height"],
                        "margin_bottom": pdef["margin_bottom"],
                        "margin_right": pdef["margin_right"]
                    }
                else:
                    print(f"Warning: {pid} at {path} has shape {alpha.shape}, expected {(pdef['height'], pdef['width'])}. Skipping.")
            else:
                # If we don't have the native profile yet, we just skip it.
                # The engine will fallback to whatever is loaded.
                pass
                
        # For development / bootstrapping if NO profiles are present, load the old empirical one as legacy
        if not self.loaded_profiles:
            fallback_path = Path(__file__).parent / "gemini_alpha.npy"
            if fallback_path.exists():
                # The old one is 64x64, which doesn't perfectly match standard sizes, 
                # but we'll map it temporarily so the system doesn't crash while we extract native ones.
                alpha = np.load(fallback_path)
                h, w = alpha.shape
                self.loaded_profiles["fallback_empirical"] = {
                    "alpha": alpha,
                    "template_bgr": (alpha * 255).astype(np.uint8),
                    "width": w,
                    "height": h,
                    "margin_bottom": int(h / 3),
                    "margin_right": int(w / 3)
                }

    def get_profile(self, profile_id: str) -> Optional[Dict[str, Any]]:
        return self.loaded_profiles.get(profile_id)
        
    def get_all_profiles(self) -> Dict[str, Dict[str, Any]]:
        return self.loaded_profiles
        
# Singleton
_manager = None
def get_profile_manager() -> GeminiProfileManager:
    global _manager
    if _manager is None:
        _manager = GeminiProfileManager()
    return _manager
