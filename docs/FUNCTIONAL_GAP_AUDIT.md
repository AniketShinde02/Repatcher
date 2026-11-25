# Functional Gap Audit — Phase 5B

This audit categorizes every functional aspect of the AI Watermark Remover software based on the actual codebase implementation.

---

## Discovered Status Category Manifest

### 1. MODEL LIFECYCLE & DISCOVERY
- **Model Discovery**: `WORKING` — Resolves paths across `MODEL_DIR`, torch checkpoints cache, home directory, and local fallback paths.
- **Model Installation**: `PARTIALLY WORKING` — Standard downloader runs in a background thread, but does not prevent concurrent download triggers of the same model and lacks checksum-driven restart validation.
- **Model Loading**: `WORKING` — Model loads into global cached session once.
- **Model Caching**: `WORKING` — Correctly configures and reads from `TORCH_HOME`.
- **Model Already-Installed Behaviour**: `WORKING` — Skips downloading if the local file exists with correct size/checksum.
- **Model Missing Behaviour**: `WORKING` — Gracefully falls back to OpenCV Telea algorithm in backend, showing warning installer banners in the frontend.

### 2. IMAGE CANVAS & BRUSH WORKFLOW
- **Single-Image Processing**: `WORKING` — Seamless automatic detection, manual drawing overlay, and inpainting.
- **Automatic Detection**: `WORKING` — Run v4 Candidate Scoring logic.
- **Manual Brush Painting & Erasing**: `WORKING` — Precise smooth round line strokes drawing (`ctx.lineTo`) and erasing context.
- **Panning & Zooming**: `WORKING` — Zoom (0.25x to 8x) and drag-panning operations.
- **Mask Coordinates Mapping**: `WORKING` — Bounding rect scaling aspect ratios mapped to natural image dimensions.
- **Mask Preview**: `WORKING` — Screen-space visual pointer overlay matches drawing diameter.
- **Untouched Region Preservation**: `WORKING` — Blends inpainted mask region back onto original source image to guarantee 100% bit-exact pixels outside the mask.
- **JPEG/PNG/WEBP Format & Resolution**: `WORKING` — Resolution preserved exactly, format matching byte signatures preserved, lossless PNG max diff = 0, JPEG compression delta <= 2.
- **Large Image & Unicode Filename Handling**: `WORKING` — Safe loading of large inputs; string unicode characters handled correctly by OS.

### 3. BATCH PROCESSING ENGINE
- **Batch Queue & Queue Architecture**: `WORKING` — Asynchronous sequential FIFO background thread queue.
- **Batch Progress & Polling**: `WORKING` — Client-side 1-second interval polling from `GET /api/batch/[batch_id]`.
- **Failure Isolation**: `WORKING` — Wrapped individual item loops in try-catch so one bad file does not crash the batch.
- **Batch Statistics**: `WORKING` — Returns total, completed, skipped, failed, average time per image, device, and duration.
- **Batch Cancellation**: `NOT IMPLEMENTED` — No cancel endpoint exposed in backend and no Cancel button in UI.
- **Batch Retry**: `NOT IMPLEMENTED` — No option to retry failed queue items only.
- **Mixed-Format Batch Handling**: `WORKING` — Correctly validates and processes mixed lists of JPG, PNG, and WEBP.

### 4. HARDWARE MANAGEMENT
- **GPU Detection & CPU Fallback**: `WORKING` — PyTorch CUDA availability checked dynamically. Falls back to CPU if CUDA fails to initialize.
- **GPU/CPU Switching**: `PARTIALLY WORKING` — Frontend settings toggle device state in UI, but the backend `/process` endpoint does not dynamically override the active session device target on command.
- **Runtime Diagnostics**: `WORKING` — Dynamic RAM, VRAM, and device name returned via `/system`.

### 5. SYSTEM ARCHITECTURE
- **Startup Launcher**: `WORKING` — Launch script `START.BAT` starts FastAPI on `7860` and Next.js on `3000` with Gradio isolated.
- **Connectivity & Port Management**: `WORKING` — Proxy routes mapped cleanly with centralized config.
- **Staging Directory & Temp-File Cleanup**: `WORKING` — Temp files are unlinked after single and batch processing.
- **Settings Persistence**: `PARTIALLY WORKING` — Component states persistent during session, but not saved in LocalStorage.
- **Light/Dark Mode**: `WORKING` — Application is locked to a zinc dark theme; no broken light toggle is exposed.
- **Error Handling**: `WORKING` — Python tracebacks hidden; returns structured JSON.
- **Tauri Packaging Compatibility**: `IMPLEMENTED BUT UNVERIFIED` — Relocatable paths and variables prepared, but not compiled into an installer.
