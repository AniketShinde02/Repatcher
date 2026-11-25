"""
Batch Inpainting Engine
Handles controlled sequential/concurrent processing of multiple images utilizing a single loaded model session.
Supports cancellation, failure isolation, and dynamic device query updates.
"""

import time
import psutil
import os
import csv
from pathlib import Path
import cv2
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Thread lock for safe concurrent operations
BATCH_LOCK = threading.Lock()
CSV_LOCK = threading.Lock()

from backend.core.cv_utils import safe_imread, safe_imwrite
from backend.core.file_validation import validate_image_file
from backend.core.watermark_engine import GeminiWatermarkEngine
from backend.core.inpainting import get_source_format
from backend.core.device_manager import get_target_device

# In-memory batch progress tracking
BATCHES = {}
CANCELLED_BATCHES = set()

class BatchManager:
    @staticmethod
    def initialize_batch(batch_id: str, total_files: int):
        BATCHES[batch_id] = {
            "batch_id": batch_id,
            "status": "PROCESSING",
            "total": total_files,
            "processed": 0,
            "completed": 0,
            "failed": 0,
            "skipped": 0,
            "items": [],
            "start_time": time.time(),
            "device": get_target_device(),
            "avg_time_per_image": 0.0,
            "total_time_sec": 0.0, 
            "metrics": {"model_load_count": 0, "model_reuse_count": 0, "ram_usage_mb": 0.0, "vram_usage_mb": 0.0}
        }

    @staticmethod
    def update_item(batch_id: str, filename: str, **kwargs):
        with BATCH_LOCK:
            if batch_id not in BATCHES:
                return
            batch = BATCHES[batch_id]
            item = next((i for i in batch["items"] if i["filename"] == filename), None)
            if not item:
                item = {"filename": filename, "status": "PENDING", "duration_sec": 0.0, "debug": {}}
                batch["items"].append(item)
            
            for k, v in kwargs.items():
                if k == 'debug':
                    item['debug'].update(v)
                else:
                    item[k] = v
                    
            # Recalculate stats dynamically for frontend polling
            comp = len([i for i in batch["items"] if i["status"] in ("REMOVED", "NO_WATERMARK")])
            failed = len([i for i in batch["items"] if i["status"] in ("FAILED", "REMOVAL_FAILED", "ERROR")])
            skipped = len([i for i in batch["items"] if i["status"] in ("SKIPPED", "REVIEW_REQUIRED")])
            
            batch["processed"] = len(batch["items"])
            batch["completed"] = comp
            batch["failed"] = failed
            batch["skipped"] = skipped

    @staticmethod
    def finalize_batch(batch_id: str):
        if batch_id not in BATCHES:
            return
        batch = BATCHES[batch_id]
        
        if batch_id in CANCELLED_BATCHES:
            batch["status"] = "CANCELLED"
        else:
            batch["status"] = "COMPLETED"
            
        batch["total_time_sec"] = round(time.time() - batch["start_time"], 2)
        
        comp = len([i for i in batch["items"] if i["status"] in ("REMOVED", "NO_WATERMARK")])
        failed = len([i for i in batch["items"] if i["status"] in ("FAILED", "REMOVAL_FAILED", "ERROR")])
        skipped = len([i for i in batch["items"] if i["status"] in ("SKIPPED", "REVIEW_REQUIRED")])
        
        batch["processed"] = len(batch["items"])
        batch["completed"] = comp
        batch["failed"] = failed
        batch["skipped"] = skipped
        
        if comp > 0:
            total_inf_time = sum([i["duration_sec"] for i in batch["items"] if i["status"] in ("REMOVED", "NO_WATERMARK")])
            batch["avg_time_per_image"] = round(total_inf_time / comp, 3)

def get_batch_status(batch_id: str) -> dict | None:
    return BATCHES.get(batch_id)

def cancel_batch(batch_id: str):
    with BATCH_LOCK:
        CANCELLED_BATCHES.add(batch_id)
        if batch_id in BATCHES:
            BATCHES[batch_id]["status"] = "CANCELLED"

def process_single_image(
    batch_id: str, 
    filename: str, 
    temp_in: Path, 
    output_dir: Path, 
    debug_dir: Path, 
    output_format: str, 
    skip_low_confidence: bool,
    engine: GeminiWatermarkEngine,
    csv_writer,
    csv_file
):
    start_time = time.time()
    row_data = {
        "filename": filename,
        "width": 0, "height": 0,
        "profile_id": "NONE", "detected": False, 
        "confidence": 0.0, "x": 0, "y": 0, 
        "watermark_width": 0, "watermark_height": 0, 
        "reverse_blend_valid": False, "changed_pixels": 0, 
        "residual_score": 0.0, "status": "ERROR", 
        "processing_ms": 0.0
    }

    try:
        if batch_id in CANCELLED_BATCHES:
            BatchManager.update_item(batch_id, filename, status="SKIPPED", error="Cancelled")
            temp_in.unlink(missing_ok=True)
            return

        BatchManager.update_item(batch_id, filename, status="VALIDATING")
        is_valid, err_msg = validate_image_file(temp_in)
        if not is_valid:
            BatchManager.update_item(batch_id, filename, status="FAILED", error=err_msg)
            return

        img_bgr = safe_imread(str(temp_in), cv2.IMREAD_UNCHANGED)
        if img_bgr is None:
            BatchManager.update_item(batch_id, filename, status="FAILED", error="Failed to read image")
            return
            
        row_data["width"], row_data["height"] = img_bgr.shape[1], img_bgr.shape[0]

        BatchManager.update_item(batch_id, filename, status="PROCESSING")
        
        # Unified Engine Call
        res = engine.process(img_bgr)
        status = res["status"]
        metrics = res["metrics"]
        
        row_data["detected"] = metrics.get("detected", False)
        row_data["status"] = status
        
        if row_data["detected"]:
            row_data["profile_id"] = metrics.get("profile_id", "NONE")
            row_data["x"] = metrics.get("x", 0)
            row_data["y"] = metrics.get("y", 0)
            row_data["watermark_width"] = metrics.get("width", 0)
            row_data["watermark_height"] = metrics.get("height", 0)
            row_data["confidence"] = metrics.get("confidence", 0.0)
            row_data["changed_pixels"] = metrics.get("changed_pixels", 0)
            row_data["residual_score"] = metrics.get("err_ratio", 0.0)
            row_data["reverse_blend_valid"] = (status != "REMOVAL_FAILED")
            
        if status in ("REMOVED", "NO_WATERMARK", "REVIEW_REQUIRED"):
            source_ext = get_source_format(temp_in)
            final_ext = source_ext if output_format == "source" else f".{output_format}"
            out_filename = Path(filename).with_suffix(final_ext).name
            final_out_path = output_dir / out_filename
            safe_imwrite(str(final_out_path), res["image"])
        else:
            # If failed, save debug overlay
            overlay = img_bgr.copy()
            if row_data["detected"]:
                x, y, w, h = row_data["x"], row_data["y"], row_data["watermark_width"], row_data["watermark_height"]
                cv2.rectangle(overlay, (x, y), (x+w, y+h), (0, 0, 255), 2)
            safe_imwrite(str(debug_dir / f"failures_{filename}_overlay.jpg"), overlay)
            
        duration = time.time() - start_time
        row_data["processing_ms"] = duration * 1000
        
        BatchManager.update_item(batch_id, filename, status=status, duration_sec=duration, error=metrics.get("reason", ""))
        
    except Exception as e:
        row_data["status"] = "ERROR"
        BatchManager.update_item(batch_id, filename, status="ERROR", error=str(e))
    finally:
        temp_in.unlink(missing_ok=True)
        with CSV_LOCK:
            try:
                csv_writer.writerow(row_data)
                csv_file.flush()
            except:
                pass

def run_batch_processing(
    batch_id: str,
    saved_inputs: list[tuple[str, Path]],
    stage_mask_dir: Path,
    output_dir: Path,
    sensitivity: int = 160,
    padding: int = 12,
    skip_low_confidence: bool = True,
    device: str = None,
    output_format: str = "source",
    reference_image_path: Path = None,
    reference_mask_path: Path = None
):
    BatchManager.initialize_batch(batch_id, len(saved_inputs))
    
    debug_dir = output_dir / "debug"
    debug_dir.mkdir(parents=True, exist_ok=True)
    
    csv_path = debug_dir / "results.csv"
    
    fieldnames = [
        "filename", "width", "height", "profile_id", "detected", 
        "confidence", "x", "y", "watermark_width", "watermark_height", 
        "reverse_blend_valid", "changed_pixels", "residual_score", "status", "processing_ms"
    ]
    
    engine = GeminiWatermarkEngine()
    
    with open(csv_path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        max_workers = 2 
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for filename, temp_in in saved_inputs:
                futures.append(
                    executor.submit(
                        process_single_image,
                        batch_id, filename, temp_in, output_dir, debug_dir, 
                        output_format, skip_low_confidence, engine, writer, f
                    )
                )
            
            for future in as_completed(futures):
                pass 

    BatchManager.finalize_batch(batch_id)
    return BATCHES[batch_id]
