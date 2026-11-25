#!/usr/bin/env python3
"""
Temporary Staging & Cache Cleanup Tool
Safely resets local staging directories without removing user output images.
"""

import sys
import os
import shutil
from pathlib import Path

# Ensure UTF-8 output encoding for Windows terminals
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def clean_staging():
    root = Path(__file__).parent.parent
    temp_dirs = [
        root / "stage_input",
        root / "stage_output",
        root / "stage_mask",
    ]
    
    temp_files = [
        root / "mask.png",
        root / "test_mask.jpeg",
        root / "test_inpainted.jpeg",
    ]
    
    print("[Clean] Resetting temporary staging files...")
    
    for tdir in temp_dirs:
        if tdir.exists():
            shutil.rmtree(tdir, ignore_errors=True)
            tdir.mkdir(exist_ok=True)
            print(f"  [OK] Cleared: {tdir.name}/")
            
    for tfile in temp_files:
        if tfile.exists():
            try:
                tfile.unlink()
                print(f"  [OK] Removed: {tfile.name}")
            except Exception as e:
                print(f"  [WARN] Could not remove {tfile.name}: {e}")
                
    # Clean debug masks
    for debug_img in root.glob("debug_mask_*.png"):
        try:
            debug_img.unlink()
            print(f"  [OK] Removed: {debug_img.name}")
        except Exception:
            pass
            
    print(" [OK] Cleanup complete!")

if __name__ == "__main__":
    clean_staging()
