"""
AI Watermark Remover — Backend FastAPI Application Entry Point
Exposes REST API endpoints for single/batch processing, system diagnostics, and job management.
"""

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pathlib import Path
import shutil
import uuid
import time
import os
import cv2
from pydantic import BaseModel
from typing import List
from backend.core.cv_utils import safe_imread, safe_imwrite

from backend.core.file_validation import validate_image_file
from backend.core.detection import detect_watermark
from backend.core.inpainting import process_image_single, ensure_model_loaded, clear_gpu_cache, get_source_format
from backend.core.paths import STAGE_INPUT, STAGE_OUTPUT, STAGE_MASK, init_staging_dirs

# Initialize directory structures on application startup
init_staging_dirs()

# MIME type map for format-correct responses
FORMAT_MIME = {
    ".jpg":  "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png":  "image/png",
    ".webp": "image/webp",
    ".bmp":  "image/bmp",
    ".tiff": "image/tiff",
    ".tif":  "image/tiff",
}

app = FastAPI(
    title="AI Watermark Remover API",
    version="1.0.0",
    description="Local-first Neural Inpainting & Top-Hat Watermark Detection Engine"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory Job Tracking
JOBS = {}

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "AI Watermark Remover API", "version": "1.0.0"}

@app.get("/system")
def system_diagnostics():
    import psutil, platform
    from backend.core.device_manager import get_device_info
    
    dev_info = get_device_info()
    
    # Query model active loaded status authoritatively from manifest
    from backend.core.model_manager import get_models_manifest
    manifest = get_models_manifest()
    is_lama_ready = any(m["id"] == "lama" and m["status"] == "READY" for m in manifest)

    return {
        "platform": f"{platform.system()} {platform.release()} ({platform.machine()})",
        "cpu_count": psutil.cpu_count(),
        "ram_total_gb": round(psutil.virtual_memory().total / (1024**3), 1),
        "ram_available_gb": round(psutil.virtual_memory().available / (1024**3), 1),
        "vram_total_gb": dev_info["vram_total_gb"],
        "gpu_name": dev_info["gpu_name"],
        "gpu_label": dev_info["gpu_label"],
        "cuda_available": dev_info["cuda_available"],
        "pytorch_version": dev_info["pytorch_version"],
        "model_loaded": is_lama_ready,
    }

@app.get("/models")
def get_models():
    from backend.core.model_manager import get_models_manifest
    return {"models": get_models_manifest()}

@app.post("/models/{model_id}/download")
def download_model_weights(model_id: str):
    from backend.core.model_manager import start_model_download, SUPPORTED_MODELS
    if model_id not in SUPPORTED_MODELS:
        raise HTTPException(status_code=404, detail=f"Model {model_id} not supported.")
    try:
        start_model_download(model_id)
        return {"success": True, "message": f"Download initiated for {model_id}."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/detect")
async def detect_only(
    file: UploadFile = File(...),
    sensitivity: int = Form(160),
    padding: int = Form(12),
):
    """
    Non-destructive detect-only endpoint.
    Returns watermark detection result WITH mask as base64 PNG.
    Does NOT run inpainting.
    """
    import base64
    job_id = str(uuid.uuid4())
    original_ext = Path(file.filename).suffix.lower() or ".jpg"
    temp_path = STAGE_INPUT / f"{job_id}{original_ext}"

    with open(temp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    is_valid, err_msg = validate_image_file(temp_path)
    if not is_valid:
        temp_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail={"code": "UNSUPPORTED_FILE", "message": err_msg})

    result = detect_watermark(temp_path, sensitivity=sensitivity, padding=padding)
    temp_path.unlink(missing_ok=True)

    mask_b64 = None
    if result["mask"] is not None:
        ok, buf = cv2.imencode(".png", result["mask"])
        if ok:
            mask_b64 = base64.b64encode(buf.tobytes()).decode("utf-8")

    return {
        "detected": result["detected"],
        "confidence": result["confidence"],
        "confidence_level": result["confidence_level"],
        "detections": result["detections"],
        "message": result["message"],
        "mask_png_b64": mask_b64,
    }


@app.post("/process")
async def process_single_image(
    file: UploadFile = File(...),
    mask_file: UploadFile = File(None),
    sensitivity: int = Form(160),
    padding: int = Form(12),
    device: str = Form("cuda")
):
    """
    9A Quality Contract:
    - Input saved with original extension (format preserved)
    - Mask always saved as PNG (binary mask — format-agnostic)
    - Output exported in source format at maximum quality (JPEG q=95, PNG lossless)
    - Job output served with correct MIME type
    """
    try:
        job_id = str(uuid.uuid4())

        # Preserve original extension for format detection
        original_ext = Path(file.filename).suffix.lower() or ".jpg"
        temp_input_path = STAGE_INPUT / f"{job_id}{original_ext}"

        with open(temp_input_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # Detect true format from file header (not trusting extension alone)
        true_ext = get_source_format(temp_input_path)
        if true_ext != original_ext:
            corrected = temp_input_path.with_suffix(true_ext)
            temp_input_path.rename(corrected)
            temp_input_path = corrected

        # Layer 3 Security & File Validation
        is_valid, err_msg = validate_image_file(temp_input_path)
        if not is_valid:
            temp_input_path.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail={"code": "UNSUPPORTED_FILE", "message": err_msg})

        mask_path = STAGE_MASK / f"{temp_input_path.stem}.png"
        
        # If user provided a custom mask, use it directly. Otherwise auto-detect.
        if mask_file is not None:
            with open(mask_path, "wb") as f:
                shutil.copyfileobj(mask_file.file, f)
            detect_res = {
                "detections": [],
                "confidence_level": "HIGH",
                "message": "Processed with manual mask adjustment"
            }
        else:
            # Watermark Detection (runs on original-resolution image)
            detect_res = detect_watermark(temp_input_path, sensitivity=sensitivity, padding=padding)
            mask = detect_res["mask"]
            # Save mask as PNG using input stem (IOPaint matches by stem.png)
            safe_imwrite(str(mask_path), mask)

        # Output path uses correct source extension
        output_path = STAGE_OUTPUT / f"{job_id}{true_ext}"

        # Process via LaMa Engine (format-preserving)
        success, actual_output = process_image_single(temp_input_path, mask_path, output_path, device=device)

        JOBS[job_id] = {
            "id": job_id,
            "filename": file.filename,
            "true_format": true_ext,
            "status": "COMPLETED" if success else "FAILED",
            "created_at": time.time(),
            "output_path": str(actual_output) if success else None,
            "detections": detect_res["detections"],
            "confidence_level": detect_res["confidence_level"],
        }

        # Cleanup temp input (output stays for /job/{id} retrieval)
        temp_input_path.unlink(missing_ok=True)
        mask_path.unlink(missing_ok=True)

        if success:
            return {
                "success": True,
                "job_id": job_id,
                "source_format": true_ext,
                "message": detect_res["message"],
                "detections": detect_res["detections"],
                "confidence_level": detect_res["confidence_level"],
                "output_url": f"/job/{job_id}"
            }
        else:
            raise HTTPException(status_code=500, detail={"code": "PROCESSING_FAILED", "message": "Inpainting execution failed."})
    except HTTPException:
        raise
    except Exception as e:
        print(f"[{time.time()}] Unexpected backend error: {str(e)}")
        raise HTTPException(status_code=500, detail={"code": "INTERNAL_ERROR", "message": "An unexpected server error occurred during processing."})

@app.post("/batch")
@app.post("/process_batch")
async def process_batch_images(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    output_dir: str = Form("./processed_images"),
    sensitivity: int = Form(160),
    padding: int = Form(12),
    skip_low_confidence: bool = Form(True),
    device: str = Form(None),
    clear_cache: bool = Form(True),
    output_format: str = Form("source"),
    reference_image: UploadFile = File(None),
    reference_mask: UploadFile = File(None)
):
    from backend.core.batch_engine import run_batch_processing
    batch_id = str(uuid.uuid4())
    
    # Handle reference mode inputs
    ref_image_path = None
    ref_mask_path = None
    if reference_image and reference_mask:
        ref_image_path = STAGE_INPUT / f"ref_{batch_id}_{reference_image.filename}"
        with open(ref_image_path, "wb") as f:
            shutil.copyfileobj(reference_image.file, f)
            
        ref_mask_path = STAGE_MASK / f"ref_{batch_id}_{reference_mask.filename}"
        with open(ref_mask_path, "wb") as f:
            shutil.copyfileobj(reference_mask.file, f)

    target_dir = Path(output_dir) / batch_id
    target_dir.mkdir(parents=True, exist_ok=True)

    # Pre-save files synchronously to prevent closed temp file issues in background thread
    saved_inputs = []
    for file in files:
        temp_path = STAGE_INPUT / f"{batch_id}_{file.filename}"
        with open(temp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        saved_inputs.append((file.filename, temp_path))

    # Trigger background async task using our batch engine
    background_tasks.add_task(
        run_batch_processing,
        batch_id=batch_id,
        saved_inputs=saved_inputs,
        stage_mask_dir=STAGE_MASK,
        output_dir=target_dir,
        sensitivity=sensitivity,
        padding=padding,
        skip_low_confidence=skip_low_confidence,
        device=device,
        output_format=output_format,
        reference_image_path=ref_image_path,
        reference_mask_path=ref_mask_path
    )

    if clear_cache:
        clear_gpu_cache()

    return {
        "success": True,
        "batch_id": batch_id,
        "status": "PROCESSING",
        "message": "Batch processing queue initiated."
    }

@app.get("/batch/{batch_id}")
def get_batch_progress(batch_id: str):
    from backend.core.batch_engine import get_batch_status
    status = get_batch_status(batch_id)
    if not status:
        raise HTTPException(status_code=404, detail="Batch job not found.")
    return status

@app.get("/batch/{batch_id}/download")
def download_batch_results(batch_id: str, output_dir: str = "./processed_images"):
    from fastapi.responses import FileResponse
    target_dir = Path(output_dir) / batch_id
    if not target_dir.exists() or not any(target_dir.iterdir()):
        raise HTTPException(status_code=404, detail="No output found for this batch.")
    
    zip_path = Path(output_dir) / f"batch_{batch_id}.zip"
    shutil.make_archive(str(zip_path.with_suffix('')), 'zip', target_dir)
    
    return FileResponse(
        zip_path, 
        media_type="application/zip", 
        filename=f"watermark_batch_{batch_id}.zip"
    )

class DownloadBatchRequest(BaseModel):
    filenames: List[str]

@app.post("/batch/{batch_id}/download")
def download_batch_selected_results(batch_id: str, payload: DownloadBatchRequest, output_dir: str = "./processed_images"):
    from fastapi.responses import FileResponse
    target_dir = Path(output_dir) / batch_id
    if not target_dir.exists():
        raise HTTPException(status_code=404, detail="No output found for this batch.")
    
    # Create a temporary directory to zip only the selected files
    import tempfile
    temp_zip_dir = Path(tempfile.mkdtemp(prefix=f"zip_{batch_id}_"))
    
    import re
    def normalize_filename(name: str):
        return re.sub(r'[^a-zA-Z0-9]', '', name).lower()
        
    added_count = 0
    for filename in payload.filenames:
        stem = Path(filename).stem
        norm_stem = normalize_filename(stem)
        for file in target_dir.iterdir():
            if file.stem == stem or normalize_filename(file.stem) == norm_stem:
                shutil.copy(file, temp_zip_dir / file.name)
                added_count += 1
                break
                
    if added_count == 0:
        shutil.rmtree(temp_zip_dir, ignore_errors=True)
        raise HTTPException(status_code=404, detail="No matching output files found for the selected items.")
        
    zip_path = Path(output_dir) / f"batch_{batch_id}_selected.zip"
    shutil.make_archive(str(zip_path.with_suffix('')), 'zip', temp_zip_dir)
    shutil.rmtree(temp_zip_dir, ignore_errors=True)
    
    return FileResponse(
        zip_path, 
        media_type="application/zip", 
        filename=f"watermark_batch_{batch_id}_selected.zip"
    )

@app.get("/batch/{batch_id}/download/{filename}")
def download_single_batch_item(batch_id: str, filename: str, output_dir: str = "./processed_images"):
    from fastapi.responses import FileResponse
    target_dir = Path(output_dir) / batch_id
    if not target_dir.exists():
        raise HTTPException(status_code=404, detail="Batch output directory not found.")
    
    # The saved file might have a different extension due to output_format conversion
    stem = Path(filename).stem
    import re
    norm_stem = re.sub(r'[^a-zA-Z0-9]', '', stem).lower()
    
    for file in target_dir.iterdir():
        if file.stem == stem or re.sub(r'[^a-zA-Z0-9]', '', file.stem).lower() == norm_stem:
            return FileResponse(file, filename=file.name)
            
    raise HTTPException(status_code=404, detail="Image not found in batch output.")

@app.post("/system/device")
def set_system_device(device: str = Form(...)):
    from backend.core.device_manager import force_cpu_mode
    if device == "cpu":
        force_cpu_mode(True)
    else:
        force_cpu_mode(False)
    return {"success": True, "device": device}

@app.get("/settings/omniroute")
def get_omniroute_settings():
    from backend.core.omniroute_config import get_masked_settings
    return get_masked_settings()

class OmniRouteSettingsUpdate(BaseModel):
    OMNIROUTE_ENABLED: bool = None
    OMNIROUTE_BASE_URL: str = None
    OMNIROUTE_API_KEY: str = None
    OMNIROUTE_VISION_MODEL: str = None

@app.post("/settings/omniroute")
def update_omniroute_settings(payload: OmniRouteSettingsUpdate):
    from backend.core.omniroute_config import save_settings, get_masked_settings
    update_data = {k: v for k, v in payload.dict().items() if v is not None}
    # If the user sends all asterisks, it means they didn't change the masked password, so ignore it
    if update_data.get("OMNIROUTE_API_KEY") and set(update_data["OMNIROUTE_API_KEY"]) == {"*"}:
        del update_data["OMNIROUTE_API_KEY"]
    # If the user sends a partially masked key, they didn't change it, so ignore it
    elif update_data.get("OMNIROUTE_API_KEY") and "*" in update_data["OMNIROUTE_API_KEY"]:
        del update_data["OMNIROUTE_API_KEY"]

    if update_data:
        save_settings(update_data)
    return get_masked_settings()

@app.get("/omniroute/health")
def check_omniroute_health():
    import httpx
    from backend.core.omniroute_config import load_settings
    settings = load_settings()
    
    if not settings.get("OMNIROUTE_ENABLED"):
        return {"status": "disabled", "message": "OmniRoute AI fallback is disabled."}
        
    base_url = settings.get("OMNIROUTE_BASE_URL")
    api_key = settings.get("OMNIROUTE_API_KEY")
    model = settings.get("OMNIROUTE_VISION_MODEL")
    
    if not base_url or not api_key:
        return {"status": "error", "message": "Missing API Key or Base URL."}
        
    try:
        # Simple models endpoint check
        models_url = f"{base_url.rstrip('/')}/models"
        headers = {"Authorization": f"Bearer {api_key}"}
        # In a real app, we would verify vision capability here by looking at model list
        with httpx.Client(timeout=5.0) as client:
            res = client.get(models_url, headers=headers)
            if res.status_code == 200:
                data = res.json()
                models = [m["id"] for m in data.get("data", [])]
                if model in models:
                    return {"status": "ok", "message": f"Connected to {model}"}
                else:
                    return {"status": "warning", "message": f"Connected, but model '{model}' not found in available models."}
            else:
                return {"status": "error", "message": f"API Error: {res.status_code}"}
    except Exception as e:
        return {"status": "error", "message": f"Connection failed: {str(e)}"}


@app.post("/batch/{batch_id}/cancel")
def cancel_batch_job(batch_id: str):
    from backend.core.batch_engine import cancel_batch
    cancel_batch(batch_id)
    return {"success": True, "batch_id": batch_id}

@app.get("/job/{job_id}")
def get_job_output(job_id: str):
    """
    Returns processed image with correct Content-Type matching source format.
    9A: Never returns image/png for a JPEG source.
    """
    job = JOBS.get(job_id)
    if job and job.get("output_path"):
        output_file = Path(job["output_path"])
        if output_file.exists():
            true_ext = job.get("true_format", output_file.suffix.lower())
            mime = FORMAT_MIME.get(true_ext, "application/octet-stream")
            return FileResponse(
                str(output_file),
                media_type=mime,
                filename=f"cleaned_{Path(job['filename']).stem}{true_ext}"
            )
    # Fallback: scan stage_output for any file starting with job_id
    for f in STAGE_OUTPUT.iterdir():
        if f.name.startswith(job_id):
            ext = f.suffix.lower()
            return FileResponse(str(f), media_type=FORMAT_MIME.get(ext, "application/octet-stream"))
    raise HTTPException(status_code=404, detail="Job output file not found.")

@app.delete("/job/{job_id}")
def delete_job(job_id: str):
    if job_id in JOBS:
        del JOBS[job_id]
        return {"success": True, "message": f"Job {job_id} deleted."}
    raise HTTPException(status_code=404, detail="Job not found.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=7860)
