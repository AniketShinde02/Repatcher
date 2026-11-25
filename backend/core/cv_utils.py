import cv2
import numpy as np
from pathlib import Path

def safe_imread(path: Path | str, flags=cv2.IMREAD_COLOR) -> np.ndarray | None:
    """Safely reads an image using numpy to avoid OpenCV Windows Unicode path issues."""
    try:
        path_str = str(path)
        with open(path_str, "rb") as f:
            chunk = f.read()
        img_array = np.frombuffer(chunk, dtype=np.uint8)
        img = cv2.imdecode(img_array, flags)
        return img
    except Exception as e:
        print(f"[cv_utils] Error reading {path}: {e}")
        return None

def safe_imwrite(path: Path | str, img: np.ndarray) -> bool:
    """Safely writes an image using numpy to avoid OpenCV Windows Unicode path issues."""
    try:
        path_str = str(path)
        ext = Path(path_str).suffix
        if not ext:
            ext = ".png"
        is_success, im_buf_arr = cv2.imencode(ext, img)
        if is_success:
            im_buf_arr.tofile(path_str)
            return True
        return False
    except Exception as e:
        print(f"[cv_utils] Error writing {path}: {e}")
        return False
