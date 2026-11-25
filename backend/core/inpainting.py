"""
Inpainting Neural Engine & Model Lifecycle Manager
Reuses in-memory loaded weights for IOPaint LaMa model across single and batch requests.
Ensures zero-reload session-based execution and bit-exact quality preservation.
"""

import os
import time
import shutil
import psutil
from pathlib import Path
import cv2
from backend.core.cv_utils import safe_imread, safe_imwrite
import numpy as np
from PIL import Image

from backend.core.paths import discover_model_file
from backend.core.device_manager import get_target_device, force_cpu_mode
import backend.core.model_manager as mm

# Session caching variables
_MODEL_LOADED = False
_MODEL_MANAGER = None

# Format quality params
FORMAT_PARAMS = {
    ".jpg":  {"format": "JPEG",    "quality": 95, "subsampling": 0},
    ".jpeg": {"format": "JPEG",    "quality": 95, "subsampling": 0},
    ".png":  {"format": "PNG",     "compress_level": 0},
    ".webp": {"format": "WEBP",    "lossless": True, "quality": 100},
    ".bmp":  {"format": "BMP"},
    ".tiff": {"format": "TIFF"},
    ".tif":  {"format": "TIFF"},
}

def get_source_format(image_path: Path) -> str:
    SIGNATURES = {
        b"\xff\xd8\xff":    ".jpg",
        b"\x89PNG\r\n":     ".png",
        b"RIFF":            ".webp_candidate",
        b"BM":              ".bmp",
        b"II*\x00":         ".tiff",
        b"MM\x00*":         ".tiff",
    }
    try:
        header = image_path.read_bytes()[:12]
        for sig, ext in SIGNATURES.items():
            if header.startswith(sig):
                if ext == ".webp_candidate":
                    return ".webp" if b"WEBP" in header else ".bmp"
                return ext
    except Exception:
        pass
    return image_path.suffix.lower()

def export_with_quality(img_array: np.ndarray, output_path: Path, source_ext: str) -> Path:
    source_ext = source_ext.lower()
    params = FORMAT_PARAMS.get(source_ext, FORMAT_PARAMS[".png"])
    correct_path = output_path.with_suffix(source_ext)

    if img_array.ndim == 3 and img_array.shape[2] in (3, 4):
        if img_array.shape[2] == 4:
            img_rgb = cv2.cvtColor(img_array, cv2.COLOR_BGRA2RGBA)
        else:
            img_rgb = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)
    else:
        img_rgb = img_array

    pil_img = Image.fromarray(img_rgb)
    fmt = params["format"]
    save_kwargs = {k: v for k, v in params.items() if k != "format"}
    pil_img.save(str(correct_path), format=fmt, **save_kwargs)
    return correct_path

export_with_format_preservation = export_with_quality

def ensure_model_loaded(target_device: str | None = None) -> bool:
    """Loads the model weights exactly once into the session."""
    global _MODEL_LOADED, _MODEL_MANAGER
    if _MODEL_LOADED and _MODEL_MANAGER is not None:
        return True

    # 1. Resolve Target Device target dynamically
    target_device = target_device or get_target_device()

    # 2. Check model availability
    if not mm.is_model_downloaded("lama"):
        err = "LaMa model weights are not downloaded yet."
        mm.set_model_error("lama", err)
        raise RuntimeError(err)

    mm.set_model_loading("lama")

    try:
        import torch
        from iopaint.model_manager import ModelManager
        
        # Measure RAM/VRAM before load
        process = psutil.Process(os.getpid())
        ram_before = process.memory_info().rss / (1024 ** 2)
        vram_before = 0.0
        if torch.cuda.is_available() and target_device == "cuda":
            vram_before = torch.cuda.memory_allocated() / (1024 ** 2)

        dev_target = torch.device(target_device if torch.cuda.is_available() and target_device == "cuda" else "cpu")
        print(f"[Model Session] Loading LaMa weights on {dev_target}...")
        
        start_time = time.time()
        _MODEL_MANAGER = ModelManager("lama", device=dev_target)
        load_time = time.time() - start_time

        # Measure RAM/VRAM after load
        ram_after = process.memory_info().rss / (1024 ** 2)
        vram_after = 0.0
        if torch.cuda.is_available() and target_device == "cuda":
            vram_after = torch.cuda.memory_allocated() / (1024 ** 2)

        ram_diff = max(0.0, ram_after - ram_before)
        vram_diff = max(0.0, vram_after - vram_before) if torch.cuda.is_available() and target_device == "cuda" else 0.0

        mm.set_model_ready("lama", load_time, ram_diff, vram_diff)
        _MODEL_LOADED = True
        print(f"[Model Session] Load successful in {load_time:.3f}s (RAM +{ram_diff:.1f}MB, VRAM +{vram_diff:.1f}MB).")
        return True
    except Exception as e:
        err_msg = f"Failed to load weights: {str(e)}"
        print(f"[Model Session] Error: {err_msg}")
        mm.set_model_error("lama", err_msg)
        
        # Try CPU fallback if CUDA failed
        if target_device == "cuda":
            print("[Model Session] Attempting CPU fallback loading...")
            force_cpu_mode(True)
            return ensure_model_loaded("cpu")
            
        _MODEL_LOADED = False
        raise RuntimeError(err_msg)

def process_image_in_memory(
    image_bgr: np.ndarray,
    mask_gray: np.ndarray,
    device: str | None = None
) -> np.ndarray:
    """Runs LaMa inpainting in-memory utilizing the cached model session."""
    global _MODEL_MANAGER
    ensure_model_loaded(device)

    from iopaint.schema import InpaintRequest
    config = InpaintRequest()
    
    # Ensure image_bgr is at least 3-channel
    if image_bgr.ndim == 2:
        image_bgr = cv2.cvtColor(image_bgr, cv2.COLOR_GRAY2BGR)
        
    # Convert BGR (cv2) to RGB (expected by iopaint)
    if image_bgr.ndim == 3 and image_bgr.shape[2] == 4:
        image_rgb = cv2.cvtColor(image_bgr[:, :, :3], cv2.COLOR_BGR2RGB)
    else:
        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

    # Execute model session run
    start_time = time.time()
    res_bgr = _MODEL_MANAGER(image_rgb, mask_gray, config)
    inf_time = time.time() - start_time
    mm.record_inference_time("lama", inf_time)

    # --- Silent failure detection ---
    # iopaint's ModelManager silently catches CUDA OOM and returns the original image unchanged.
    # Detect this: if the output is pixel-identical to the input in the masked region, inference
    # did nothing. We raise explicitly so the caller can trigger a CPU fallback.
    if np.any(mask_gray > 0):
        mask_bool = mask_gray > 0
        # Compare RGB input vs RGB output in the masked area
        input_rgb_masked = image_rgb[mask_bool]
        output_rgb_masked = res_bgr[mask_bool]
        if np.array_equal(input_rgb_masked, output_rgb_masked):
            raise RuntimeError(
                "Inference produced no change in the masked region (likely silent CUDA OutOfMemory). "
                "Will retry on CPU."
            )

    # 100% untouched pixels preservation:
    # paste inpainted region only onto the original image where mask > 0
    mask_3d = np.expand_dims(mask_gray, axis=2)
    
    # Handle alpha channel preservation if source has 4 channels
    if image_bgr.ndim == 3 and image_bgr.shape[2] == 4:
        inpainted_rgb = res_bgr
        alpha = image_bgr[:, :, 3:]
        inpainted_rgba = np.dstack([inpainted_rgb, alpha])
        blended = np.where(mask_3d > 0, inpainted_rgba, image_bgr)
    else:
        blended = np.where(mask_3d > 0, res_bgr, image_bgr)

    return blended

def process_image_single(
    image_path: Path,
    mask_path: Path,
    output_path: Path,
    device: str | None = None,
) -> tuple[bool, Path]:
    """Processes a single image file cleanly using in-memory session pipelines."""
    source_ext = get_source_format(image_path)
    
    try:
        # Load image & mask grayscale
        img = safe_imread(str(image_path), cv2.IMREAD_UNCHANGED)
        mask = safe_imread(str(mask_path), cv2.IMREAD_GRAYSCALE)

        if img is None or mask is None:
            raise ValueError("Failed to read image or mask files.")

        # Match mask size if there's any slight scaling delta
        if img.shape[:2] != mask.shape[:2]:
            mask = cv2.resize(mask, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_NEAREST)

        # Run in-memory pipeline
        res = process_image_in_memory(img, mask, device)
        correct_path = export_with_quality(res, output_path, source_ext)
        return True, correct_path
    except Exception as e:
        print(f"[Inpaint Error] {str(e)}. Falling back to OpenCV Telea...")
        return _fallback_inpaint(image_path, mask_path, output_path, source_ext)

def _fallback_inpaint(
    image_path: Path,
    mask_path: Path,
    output_path: Path,
    source_ext: str,
) -> tuple[bool, Path]:
    try:
        img = safe_imread(str(image_path), cv2.IMREAD_UNCHANGED)
        mask = safe_imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
        if img is None or mask is None:
            return False, output_path

        if img.shape[:2] != mask.shape[:2]:
            mask = cv2.resize(mask, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_NEAREST)

        # OpenCV Telea
        if img.ndim == 3 and img.shape[2] == 4:
            alpha = img[:, :, 3]
            bgr = img[:, :, :3]
            result_bgr = cv2.inpaint(bgr, mask, inpaintRadius=5, flags=cv2.INPAINT_TELEA)
            result = np.dstack([result_bgr, alpha])
        else:
            result = cv2.inpaint(img, mask, inpaintRadius=5, flags=cv2.INPAINT_TELEA)

        # Paste back unmasked pixels to guarantee quality
        mask_3d = np.expand_dims(mask, axis=2)
        blended = np.where(mask_3d > 0, result, img)

        correct_path = export_with_quality(blended, output_path, source_ext)
        return True, correct_path
    except Exception as e:
        print(f"[Fallback Error] OpenCV Inpainting failed: {e}")
        return False, output_path

def clear_gpu_cache():
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            print("[Memory] PyTorch GPU VRAM cache flushed.")
    except Exception as e:
        print(f"[Warning] Cache flush error: {e}")
