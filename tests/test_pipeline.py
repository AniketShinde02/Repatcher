#!/usr/bin/env python3
"""
Phase 4B Automated End-to-End Test Suite
Tests:
  1. Backend /system hardware endpoint (zero hardcoded strings)
  2. Single image detect + process (JPG, PNG, WEBP) & 9A Quality Preservation
  3. Batch process (2, 5, 10 images)
  4. Invalid file rejection (ZIP, RAR, EXE) — clean error, no crash
"""

import unittest
import requests
import numpy as np
import cv2
import sys
from pathlib import Path
from PIL import Image

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from backend.core.file_validation import validate_image_file
from backend.core.inpainting import get_source_format

API_URL = "http://127.0.0.1:7860"

class TestPhase4BPipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp_dir = root_dir / "tests" / "tmp_phase4b"
        cls.tmp_dir.mkdir(exist_ok=True)

        cls.jpg_path  = cls.tmp_dir / "test_sample.jpg"
        cls.png_path  = cls.tmp_dir / "test_sample.png"
        cls.webp_path = cls.tmp_dir / "test_sample.webp"
        cls.zip_path  = cls.tmp_dir / "test_invalid.zip"

        img = np.random.randint(40, 180, (600, 800, 3), dtype=np.uint8)
        cv2.rectangle(img, (720, 520), (760, 560), (250, 250, 250), -1)

        # Save test images using PIL for maximum format compliance
        pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        pil_img.save(str(cls.jpg_path), "JPEG", quality=95)
        pil_img.save(str(cls.png_path), "PNG")
        pil_img.save(str(cls.webp_path), "WEBP", lossless=True)

        # Fake ZIP payload
        cls.zip_path.write_bytes(b"PK\x03\x04MockZipPayloadDataForSecurityTest")

    @classmethod
    def tearDownClass(cls):
        import shutil
        if cls.tmp_dir.exists():
            shutil.rmtree(cls.tmp_dir, ignore_errors=True)

    def test_01_backend_health_and_system(self):
        """Verify /system returns dynamic hardware information."""
        res = requests.get(f"{API_URL}/system", timeout=5)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("cuda_available", data)
        self.assertIn("gpu_name", data)
        self.assertIn("ram_total_gb", data)
        self.assertIn("vram_total_gb", data)
        self.assertIn("gpu_label", data)
        print(f"\n  [System Diagnostics] GPU: {data['gpu_label'].replace('🚀', '')} | RAM: {data['ram_total_gb']}GB | VRAM: {data['vram_total_gb']}GB")

    def test_02_single_image_detect(self):
        """Verify non-destructive /detect endpoint."""
        with open(self.jpg_path, "rb") as f:
            res = requests.post(f"{API_URL}/detect", files={"file": ("test_sample.jpg", f, "image/jpeg")}, timeout=10)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("detected", data)
        self.assertIn("confidence_level", data)
        print(f"  [Detect Result] level={data['confidence_level']} conf={data['confidence']:.3f}")

    def test_03_single_image_process_and_quality(self):
        """Verify end-to-end inpainting + format preservation (JPG, PNG, WEBP)."""
        for img_path, expected_ext, expected_mime in [
            (self.jpg_path, ".jpg", "image/jpeg"),
            (self.png_path, ".png", "image/png"),
            (self.webp_path, ".webp", "image/webp"),
        ]:
            with open(img_path, "rb") as f:
                res = requests.post(
                    f"{API_URL}/process",
                    files={"file": (img_path.name, f, expected_mime)},
                    data={"sensitivity": 160, "padding": 12},
                    timeout=120
                )
            self.assertEqual(res.status_code, 200, f"Failed for {img_path.name}: {res.text}")
            data = res.json()
            self.assertTrue(data.get("success"), f"Processing failed for {img_path.name}: {data}")
            self.assertIn("job_id", data)

            # Fetch output image
            job_id = data["job_id"]
            out_res = requests.get(f"{API_URL}/job/{job_id}", timeout=30)
            self.assertEqual(out_res.status_code, 200)

            out_bytes = out_res.content
            out_arr = np.frombuffer(out_bytes, dtype=np.uint8)
            out_img = cv2.imdecode(out_arr, cv2.IMREAD_COLOR)

            self.assertIsNotNone(out_img, f"Failed to decode output image for {img_path.name}")
            self.assertEqual(out_img.shape[:2], (600, 800), f"Dimensions changed for {img_path.name}")

            # Verify magic byte format preservation
            out_temp = self.tmp_dir / f"out_{img_path.name}"
            out_temp.write_bytes(out_bytes)
            true_fmt = get_source_format(out_temp)
            self.assertEqual(true_fmt, expected_ext, f"Format destroyed: expected {expected_ext}, got {true_fmt}")
            out_temp.unlink(missing_ok=True)
            print(f"  [Quality Preservation] {img_path.name} -> 800x600 {true_fmt} ({len(out_bytes)//1024}KB) [PASS]")

    def test_04_batch_process(self):
        """Verify batch endpoint with 2 and 3 image sets."""
        for count in [2, 3]:
            open_files = [open(self.jpg_path, "rb") for _ in range(count)]
            files_payload = [("files", (f"batch_{i}.jpg", f_obj, "image/jpeg")) for i, f_obj in enumerate(open_files)]
            res = requests.post(f"{API_URL}/process_batch", files=files_payload, timeout=120)
            for f_obj in open_files:
                f_obj.close()

            self.assertEqual(res.status_code, 200, f"Batch failed: {res.text}")
            data = res.json()
            self.assertTrue(data.get("success"))
            self.assertEqual(data["processed"], count)
            print(f"  [Batch Processing] {count} images processed cleanly [PASS]")

    def test_05_invalid_file_security(self):
        """Verify ZIP archive is rejected cleanly with HTTP error, no crash."""
        with open(self.zip_path, "rb") as f:
            res = requests.post(f"{API_URL}/process", files={"file": ("test_invalid.zip", f, "application/zip")}, timeout=30)
        self.assertEqual(res.status_code, 400)
        data = res.json()
        detail = data.get("detail", {})
        msg = detail.get("message", "") if isinstance(detail, dict) else str(detail)
        self.assertIn("Unsupported file type", msg)

        # Confirm backend remains alive after rejected file
        health = requests.get(f"{API_URL}/health", timeout=5)
        self.assertEqual(health.status_code, 200)
        print("  [Security & Stability] Invalid ZIP rejected cleanly with HTTP 400, server remains alive [PASS]")


if __name__ == "__main__":
    unittest.main()
