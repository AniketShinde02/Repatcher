#!/usr/bin/env python3
"""
Environment & Hardware Diagnostic Tool for AI Watermark Remover
Detects OS, Python version, CPU, RAM, GPU (CUDA), Storage, and Dependencies.
"""

import sys
import os
import platform
import shutil
from pathlib import Path

# Ensure UTF-8 output encoding for Windows terminals
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def run_diagnostic():
    print("=" * 60)
    print(" AI Watermark Remover Environment & Hardware Diagnostic")
    print("=" * 60)

    issues = []
    warnings = []

    # 1. Operating System
    os_name = platform.system()
    os_release = platform.release()
    arch = platform.machine()
    print(f"[OS] Platform: {os_name} {os_release} ({arch})")

    # 2. Python Version Check
    py_ver = sys.version.split()[0]
    py_major, py_minor = sys.version_info[:2]
    print(f"[Python] Version: {py_ver}")
    if py_major < 3 or (py_major == 3 and py_minor < 10):
        issues.append(f"Python version {py_ver} is unsupported. Python 3.10+ is required.")
    else:
        print("  [OK] Python version supported.")

    # 3. System RAM Check
    try:
        import psutil
        total_ram_gb = round(psutil.virtual_memory().total / (1024 ** 3), 2)
        avail_ram_gb = round(psutil.virtual_memory().available / (1024 ** 3), 2)
        print(f"[RAM] Total: {total_ram_gb} GB | Available: {avail_ram_gb} GB")
        if total_ram_gb < 4.0:
            warnings.append("System RAM is under 4GB. Processing large batch images may be slow.")
        else:
            print("  [OK] System RAM sufficient.")
    except ImportError:
        print("[RAM] psutil not installed — skipping detailed memory check.")

    # 4. Storage Space Check
    cwd = Path.cwd()
    total_disk, used_disk, free_disk = shutil.disk_usage(cwd)
    free_disk_gb = round(free_disk / (1024 ** 3), 2)
    print(f"[Storage] Free Space on {cwd.drive if hasattr(cwd, 'drive') else cwd}: {free_disk_gb} GB")
    if free_disk_gb < 2.0:
        warnings.append("Less than 2GB free storage available. Model downloads or outputs may fail.")
    else:
        print("  [OK] Storage space sufficient.")

    # 5. Directory Write Permissions Check
    try:
        test_file = cwd / ".write_test.tmp"
        test_file.write_text("test")
        test_file.unlink()
        print("  [OK] Workspace write permissions verified.")
    except Exception as e:
        issues.append(f"Workspace directory is not writable: {e}")

    # 6. Dependency Checks
    print("\n[Dependencies]")
    required_pkgs = {
        "iopaint": "IOPaint (Neural Inpainting Backend)",
        "torch": "PyTorch (Deep Learning Framework)",
        "cv2": "OpenCV (Computer Vision)",
        "gradio": "Gradio (Web GUI Framework)",
        "PIL": "Pillow (Image Processing)",
        "numpy": "NumPy (Array Operations)",
    }

    for pkg_import, pkg_desc in required_pkgs.items():
        try:
            mod = __import__(pkg_import)
            ver = getattr(mod, "__version__", "Installed")
            print(f"  [OK] {pkg_desc}: {ver}")
        except ImportError:
            issues.append(f"Missing required dependency: {pkg_import} ({pkg_desc})")
            print(f"  [FAIL] {pkg_desc}: NOT INSTALLED")

    # 7. GPU Acceleration Check (PyTorch CUDA)
    print("\n[Hardware Acceleration]")
    try:
        import torch
        if torch.cuda.is_available():
            device_name = torch.cuda.get_device_name(0)
            vram_gb = round(torch.cuda.get_device_properties(0).total_memory / (1024 ** 3), 2)
            print(f"  [GPU] Device: {device_name}")
            print(f"  [GPU] VRAM: {vram_gb} GB | CUDA Version: {torch.version.cuda}")
            print("  [OK] Hardware acceleration ready (1-2s per image).")
        else:
            warnings.append("CUDA GPU unavailable. Application will run in CPU fallback mode (10-20s per image).")
            print("  [WARN] CUDA GPU unavailable — CPU fallback mode active.")
    except Exception as e:
        warnings.append(f"Error checking CUDA status: {e}")

    # Summary Output
    print("\n" + "=" * 60)
    if issues:
        print(" [STATUS] CRITICAL ISSUES DETECTED")
        for issue in issues:
            print(f"   • {issue}")
        print("\nPlease fix the above issues before running the application.")
        return 2
    elif warnings:
        print(" [STATUS] PASSED WITH WARNINGS")
        for warning in warnings:
            print(f"   • {warning}")
        print("\nThe application can run, but performance may be impacted.")
        return 1
    else:
        print(" [STATUS] ALL CHECKS PASSED PERFECTLY!")
        print(" System is 100% ready for AI Watermark Removal.")
        return 0

if __name__ == "__main__":
    sys.exit(run_diagnostic())
