"""
Device Manager Abstraction
Handles dynamic hardware detection, CUDA capability checks, and PyTorch versioning.
Allows inpainting engines to target CUDA or CPU transparently.
"""

import sys

# Cache device configuration to avoid repeating PyTorch lookups
_DETECTED_DEVICE = None
_FORCE_CPU = False

def force_cpu_mode(force: bool = True):
    global _FORCE_CPU, _DETECTED_DEVICE
    _FORCE_CPU = force
    _DETECTED_DEVICE = None # Reset cached device lookup

def get_pytorch_version() -> str:
    try:
        import torch
        return torch.__version__
    except ImportError:
        return "Not Installed"

def get_device_info() -> dict:
    """Returns dynamic hardware accelerator metadata."""
    try:
        import torch
        cuda_avail = torch.cuda.is_available() and not _FORCE_CPU
        if cuda_avail:
            try:
                gpu_name = torch.cuda.get_device_name(0)
                vram_bytes = torch.cuda.get_device_properties(0).total_memory
                vram_total_gb = round(vram_bytes / (1024**3), 1)
                device_target = "cuda"
                status_label = f"{gpu_name} · CUDA 🚀"
            except Exception as e:
                # Handle edge cases where CUDA is reported but driver instantiation fails
                gpu_name = f"CUDA Init Failed ({str(e)})"
                vram_total_gb = 0.0
                device_target = "cpu"
                status_label = "CPU Mode (CUDA Fallback)"
        else:
            gpu_name = "None (CPU Mode)"
            vram_total_gb = 0.0
            device_target = "cpu"
            status_label = "CPU Mode"
    except ImportError:
        gpu_name = "None (PyTorch Unavailable)"
        vram_total_gb = 0.0
        device_target = "cpu"
        status_label = "CPU Mode"

    return {
        "gpu_name": gpu_name,
        "gpu_label": status_label,
        "vram_total_gb": vram_total_gb,
        "device": device_target,
        "cuda_available": cuda_avail if 'cuda_avail' in locals() else False,
        "pytorch_version": get_pytorch_version()
    }

def get_target_device() -> str:
    """Returns the string device name to be passed to PyTorch ('cuda' or 'cpu')."""
    global _DETECTED_DEVICE
    if _DETECTED_DEVICE is not None:
        return _DETECTED_DEVICE
        
    info = get_device_info()
    _DETECTED_DEVICE = info["device"]
    return _DETECTED_DEVICE
