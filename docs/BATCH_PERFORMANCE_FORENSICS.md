# Phase 8A: Batch Performance Forensics

## 1. Objective
Compare the backend execution efficiency of the current asynchronous Next.js FastAPI batch pipeline against the previous synchronous Gradio prototype. The primary goal is to ensure the batch pipeline amortizes model load time and offers significant performance gains over independent single-image processing.

## 2. Methodology
The `backend/core/batch_engine.py` has been instrumented with precise `time.perf_counter()` metrics, collecting the following breakdown for every processed image:
*   `validation_ms`: Time spent verifying file signatures (T1)
*   `decode_ms`: Time spent decoding bytes to OpenCV numpy array (T2)
*   `detection_ms`: Time spent detecting watermark (T3)
*   `ai_verify_ms`: Time spent in OmniRoute AI fallback (T4, optional)
*   `mask_ms`: Time spent rendering mask (T5)
*   `model_load_ms`: One-time cost of caching model into VRAM (T6)
*   `inference_ms`: Time spent running the LaMa neural network (T7)
*   `disk_write_ms`: Time spent encoding and writing to disk (T10)

These metrics are dynamically served via the `/batch/{batch_id}` endpoint and summarized in the frontend.

## 3. Implementation Details
*   **Model Reuse**: `ensure_model_loaded()` is invoked once per batch request. If the global `_MODEL_LOADED` flag is true, subsequent image tasks reuse the weights in VRAM. This is tracked via `model_reuse_count`.
*   **System Resource Tracking**: RAM and VRAM utilization are extracted dynamically via `psutil` and `torch.cuda` memory statistics respectively.
*   **Reference Mode Routing**: `ReferenceEngine` (OpenCV Template Matching) acts as a high-speed bypass to automatic detection if reference inputs are supplied.
*   **AI Validation Gateway**: `OmniRoute` fallback kicks in dynamically only for `MEDIUM`, `LOW`, or `NONE` confidence items.

## 4. Expected Findings
By amortizing the `model_load_ms` cost (which can be up to 1-3 seconds) across hundreds of images, the new architecture significantly outperforms naive single-file iterations. 

---
_Note: To run a full synthetic benchmark and populate raw numeric results, run the `benchmark_batch.py` script included in the codebase._
