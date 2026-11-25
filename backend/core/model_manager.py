"""
Local Model Manager & Registry Abstraction
Responsible for model metadata, dynamic scanning, checksum verification, download tracking,
and active memory state diagnostics.
"""

import os
import time
import hashlib
import threading
from pathlib import Path
import requests

from backend.core.paths import discover_model_file, get_checkpoints_dir

SUPPORTED_MODELS = {
    "lama": {
        "id": "lama",
        "name": "IOPaint LaMa Neural Inpainting",
        "version": "1.0.0",
        "filename": "big-lama.pt",
        "expected_size_mb": 196,
        "checksum": "e3aa4aaa15225a33ec84f9f4bc47e500",
        "download_url": "https://github.com/Sanster/models/releases/download/add_big_lama/big-lama.pt",
        "description": "Fast Fourier Convolution model for seamless background texture reconstruction."
    }
}

# Global Status Trackers
DOWNLOAD_TASKS = {}
LOAD_DIAGNOSTICS = {}
_ACTIVE_LOADED_MODELS = {} # model_id -> loaded status
_MODEL_ERRORS = {}        # model_id -> error string

def is_model_downloaded(model_id: str) -> bool:
    """Verifies if the model exists and size is compatible."""
    model_cfg = SUPPORTED_MODELS.get(model_id)
    if not model_cfg:
        return False
    path = discover_model_file(model_cfg["filename"])
    if not path:
        return False
    try:
        # Allow +/- 10% discrepancy
        expected_bytes = model_cfg["expected_size_mb"] * 1024 * 1024
        actual_bytes = path.stat().st_size
        if abs(actual_bytes - expected_bytes) / expected_bytes > 0.1:
            return False
        return True
    except Exception:
        return False

def verify_checksum(model_id: str) -> bool:
    """Verifies MD5 checksum of the model file if downloaded."""
    model_cfg = SUPPORTED_MODELS.get(model_id)
    if not model_cfg:
        return False
    path = discover_model_file(model_cfg["filename"])
    if not path:
        return False
        
    md5 = hashlib.md5()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                md5.update(chunk)
        return md5.hexdigest() == model_cfg["checksum"]
    except Exception:
        return False

def get_model_file_path(model_id: str) -> Path:
    """Returns the path to the model file (whether it exists or not)."""
    model_cfg = SUPPORTED_MODELS.get(model_id)
    if not model_cfg:
        raise ValueError(f"Unknown model: {model_id}")
    
    # Try discovering first
    discovered = discover_model_file(model_cfg["filename"])
    if discovered:
        return discovered
        
    # If not discovered, default to active checkpoints dir
    return get_checkpoints_dir() / model_cfg["filename"]

def _download_worker(model_id: str, url: str, dest_path: Path):
    try:
        DOWNLOAD_TASKS[model_id] = {"status": "downloading", "progress": 0.0, "error": None}
        response = requests.get(url, stream=True, timeout=30)
        total_length = response.headers.get('content-length')
        
        temp_dest = dest_path.with_suffix(".tmp")
        with open(temp_dest, "wb") as f:
            if total_length is None:
                f.write(response.content)
            else:
                dl = 0
                total_length = int(total_length)
                for data in response.iter_content(chunk_size=8192):
                    dl += len(data)
                    f.write(data)
                    progress = round((dl / total_length) * 100, 1)
                    DOWNLOAD_TASKS[model_id] = {"status": "downloading", "progress": progress, "error": None}
        
        # Verify integrity
        expected_md5 = SUPPORTED_MODELS[model_id]["checksum"]
        temp_md5 = hashlib.md5()
        with open(temp_dest, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                temp_md5.update(chunk)
                
        if expected_md5 and temp_md5.hexdigest() != expected_md5:
            temp_dest.unlink(missing_ok=True)
            DOWNLOAD_TASKS[model_id] = {
                "status": "failed",
                "progress": 0.0,
                "error": "Checksum verification failed. Weights file is corrupted."
            }
            return
            
        if dest_path.exists():
            dest_path.unlink()
        temp_dest.rename(dest_path)
        DOWNLOAD_TASKS[model_id] = {"status": "completed", "progress": 100.0, "error": None}
    except Exception as e:
        dest_path.with_suffix(".tmp").unlink(missing_ok=True)
        DOWNLOAD_TASKS[model_id] = {"status": "failed", "progress": 0.0, "error": str(e)}

def start_model_download(model_id: str):
    if model_id not in SUPPORTED_MODELS:
        raise ValueError(f"Unknown model: {model_id}")
    if is_model_downloaded(model_id):
        return
        
    task = DOWNLOAD_TASKS.get(model_id)
    if task and task["status"] == "downloading":
        return
        
    url = SUPPORTED_MODELS[model_id]["download_url"]
    dest_path = get_model_file_path(model_id)
    
    t = threading.Thread(target=_download_worker, args=(model_id, url, dest_path), daemon=True)
    t.start()

# --- Memory Load States ---

def set_model_loading(model_id: str):
    _ACTIVE_LOADED_MODELS[model_id] = "LOADING"
    _MODEL_ERRORS.pop(model_id, None)

def set_model_ready(model_id: str, load_time: float, ram_mb: float, vram_mb: float):
    _ACTIVE_LOADED_MODELS[model_id] = "READY"
    LOAD_DIAGNOSTICS[model_id] = {
        "load_time_sec": round(load_time, 3),
        "inference_time_sec": None,
        "ram_usage_mb": round(ram_mb, 1),
        "vram_usage_mb": round(vram_mb, 1) if vram_mb else None
    }

def set_model_error(model_id: str, error_msg: str):
    _ACTIVE_LOADED_MODELS[model_id] = "ERROR"
    _MODEL_ERRORS[model_id] = error_msg

def record_inference_time(model_id: str, inference_time: float):
    if model_id in LOAD_DIAGNOSTICS:
        LOAD_DIAGNOSTICS[model_id]["inference_time_sec"] = round(inference_time, 3)

def get_models_manifest() -> list:
    manifest = []
    for model_id, cfg in SUPPORTED_MODELS.items():
        is_dl = is_model_downloaded(model_id)
        task = DOWNLOAD_TASKS.get(model_id)
        
        # Determine Status State Authoritatively
        active_state = _ACTIVE_LOADED_MODELS.get(model_id)
        
        if active_state == "READY":
            status = "READY"
        elif active_state == "LOADING":
            status = "LOADING"
        elif active_state == "ERROR":
            status = f"ERROR: {_MODEL_ERRORS.get(model_id, 'Unknown Error')}"
        elif task and task["status"] == "downloading":
            status = "DOWNLOADING"
        elif is_dl:
            status = "AVAILABLE"
        else:
            status = "NOT_INSTALLED"

        progress = 0.0
        if task:
            progress = task["progress"]
        elif is_dl:
            progress = 100.0

        manifest.append({
            "id": cfg["id"],
            "name": cfg["name"],
            "version": cfg["version"],
            "local_path": str(get_model_file_path(model_id)),
            "expected_size_mb": cfg["expected_size_mb"],
            "is_downloaded": is_dl,
            "is_loaded": active_state == "READY",
            "status": status,
            "download_progress": progress,
            "error": task["error"] if task else None,
            "description": cfg["description"],
            "diagnostics": LOAD_DIAGNOSTICS.get(model_id, {
                "load_time_sec": None,
                "inference_time_sec": None,
                "ram_usage_mb": None,
                "vram_usage_mb": None
            })
        })
    return manifest
