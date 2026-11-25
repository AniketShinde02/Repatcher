"""
Quality Preservation & Regression Test Suite
Verifies that original image quality, aspect ratio, and dimensions are strictly preserved.
Ensures that unmasked areas remain 100% bit-exact identical to the source in lossless formats.
"""

import unittest
from pathlib import Path
import shutil
import cv2
import numpy as np
import os

from backend.core.inpainting import process_image_single, get_source_format

PROJECT_ROOT = Path("d:/Starter Kit/image_processor_sandbox")
TEST_IMAGE = PROJECT_ROOT / "tests" / "dataset" / "positive" / "positive_star_1.jpg"

class TestQualityPreservation(unittest.TestCase):
    def setUp(self):
        self.temp_dir = PROJECT_ROOT / "backend" / "temp" / "quality_regression_test"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.img_in_jpg = self.temp_dir / "input.jpg"
        self.img_in_png = self.temp_dir / "input.png"
        self.mask_in = self.temp_dir / "mask.png"
        self.img_out_jpg = self.temp_dir / "output.jpg"
        self.img_out_png = self.temp_dir / "output.png"
        
        # Load sample image
        self.img = cv2.imread(str(TEST_IMAGE), cv2.IMREAD_UNCHANGED)
        self.h, self.w = self.img.shape[:2]
        
        # Save both JPEG and PNG inputs
        cv2.imwrite(str(self.img_in_jpg), self.img, [cv2.IMWRITE_JPEG_QUALITY, 95])
        cv2.imwrite(str(self.img_in_png), self.img)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_dimensions_and_format_preserved(self):
        # Create a mock mask in the center
        mask = np.zeros((self.h, self.w), dtype=np.uint8)
        cv2.circle(mask, (self.w // 2, self.h // 2), 10, 255, -1)
        cv2.imwrite(str(self.mask_in), mask)
        
        # Run process on JPEG
        success, out_path = process_image_single(self.img_in_jpg, self.mask_in, self.img_out_jpg, device="cpu")
        self.assertTrue(success)
        self.assertEqual(out_path.suffix.lower(), ".jpg")
        
        out_img = cv2.imread(str(out_path), cv2.IMREAD_UNCHANGED)
        self.assertEqual(out_img.shape, self.img.shape)

    def test_lossless_png_untouched_pixels_preservation(self):
        # Create a mock mask covering bottom right corner
        mask = np.zeros((self.h, self.w), dtype=np.uint8)
        cv2.rectangle(mask, (self.w - 50, self.h - 50), (self.w, self.h), 255, -1)
        cv2.imwrite(str(self.mask_in), mask)
        
        # Run process on PNG (lossless)
        success, out_path = process_image_single(self.img_in_png, self.mask_in, self.img_out_png, device="cpu")
        self.assertTrue(success)
        
        # Load inputs and outputs
        src_png = cv2.imread(str(self.img_in_png), cv2.IMREAD_UNCHANGED)
        out_png = cv2.imread(str(out_path), cv2.IMREAD_UNCHANGED)
        
        unmasked_region = (mask == 0)
        diff = cv2.absdiff(src_png, out_png)
        diff_unmasked = diff[unmasked_region]
        
        # In PNG lossless format, unmasked pixels MUST be 100% identical
        self.assertEqual(np.max(diff_unmasked), 0)

    def test_jpeg_lossy_pixels_tolerance(self):
        mask = np.zeros((self.h, self.w), dtype=np.uint8)
        cv2.rectangle(mask, (self.w - 50, self.h - 50), (self.w, self.h), 255, -1)
        cv2.imwrite(str(self.mask_in), mask)
        
        # Run process on JPEG (lossy)
        success, out_path = process_image_single(self.img_in_jpg, self.mask_in, self.img_out_jpg, device="cpu")
        self.assertTrue(success)
        
        src_jpg = cv2.imread(str(self.img_in_jpg), cv2.IMREAD_UNCHANGED)
        out_jpg = cv2.imread(str(out_path), cv2.IMREAD_UNCHANGED)
        
        unmasked_region = (mask == 0)
        diff = cv2.absdiff(src_jpg, out_jpg)
        diff_unmasked = diff[unmasked_region]
        
        # For JPEG, allow a tiny encoder compression rounding tolerance of <= 2
        self.assertTrue(np.max(diff_unmasked) <= 2)

if __name__ == "__main__":
    unittest.main()
