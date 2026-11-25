#!/usr/bin/env python3
"""
AI Watermark Remover Launcher & Bootstrap Validator
Performs hardware check, locates local models, runs checksum checks, and downloads missing models.
"""

import sys
import os
import hashlib
from pathlib import Path
import urllib.request

# Ensure UTF-8 output encoding for Windows terminals
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Put project root into python module search path
sys.path.append(str(Path(__file__).parent.parent))

from backend.core.paths import discover_model_file, get_checkpoints_dir
from backend.core.model_manager import SUPPORTED_MODELS, verify_checksum
from backend.core.device_manager import get_target_device

last_percent = -1

def print_progress_bar(count, block_size, total_size):
    global last_percent
    percent = int(count * block_size * 100 / total_size)
    percent = min(100, max(0, percent))
    if percent != last_percent:
        sys.stdout.write(f"\r  Downloading weights: [{percent}%] ({count * block_size // (1024*1024)}MB / {total_size // (1024*1024)}MB)")
        sys.stdout.flush()
        last_percent = percent

def bootstrap():
    print("=" * 60)
    print(" AI Watermark Remover Launcher & Bootstrap Validator")
    print("=" * 60)

    # 1. Detect Hardware
    device = get_target_device()
    print(f"[Device] Hardware target: {device.upper()}")

    # 2. Detect and Verify Models
    print("[Models] Verifying weights registry...")
    for model_id, cfg in SUPPORTED_MODELS.items():
        filename = cfg["filename"]
        path = discover_model_file(filename)
        
        if path:
            print(f"  [OK] Model '{model_id}' found at: {path}")
            print("  [Integrity] Calculating MD5 hash checksum...")
            if verify_checksum(model_id):
                print("  [OK] Checksum validation passed.")
            else:
                print("  [FAIL] Checksum mismatch! File is corrupt or incomplete.")
                print("  [Fix] Re-downloading correct model weights...")
                download_model(model_id, cfg)
        else:
            print(f"  [MISSING] Model '{model_id}' weights not found locally.")
            download_model(model_id, cfg)

    print("\n[Bootstrap] All dependencies and models validated.")
    print("===================================================\n")

def download_model(model_id, cfg):
    global last_percent
    dest_dir = get_checkpoints_dir()
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / cfg["filename"]
    
    print(f"  [Download] Source: {cfg['download_url']}")
    print(f"  [Download] Destination: {dest_path}")
    
    temp_path = dest_path.with_suffix(".tmp")
    last_percent = -1
    
    try:
        urllib.request.urlretrieve(cfg["download_url"], temp_path, reporthook=print_progress_bar)
        print("\n  [Download] Finished. Verifying file signature...")
        
        # Verify checksum of downloaded tmp file
        md5 = hashlib.md5()
        with open(temp_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                md5.update(chunk)
                
        if md5.hexdigest() == cfg["checksum"]:
            if dest_path.exists():
                dest_path.unlink()
            temp_path.rename(dest_path)
            print("  [OK] Model successfully installed and registered.")
        else:
            temp_path.unlink(missing_ok=True)
            print(f"  [ERROR] Checksum verification failed! Expected: {cfg['checksum']}, Got: {md5.hexdigest()}")
            sys.exit(1)
    except Exception as e:
        temp_path.unlink(missing_ok=True)
        print(f"\n  [ERROR] Download failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    bootstrap()
