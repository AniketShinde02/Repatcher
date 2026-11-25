# Phase 6 — Functional Audit Report
**Date:** 2026-08-27  
**Auditor:** Antigravity AI  
**Machine:** JinWoo-PC (Windows 11, RTX 3050 Laptop GPU, 32 GB RAM)

---

## Runtime State at Audit Time

| Service | Port | Status | Process |
|---|---|---|---|
| FastAPI backend | 7860 | ✅ LIVE | python3.12 (PID 26284) |
| Next.js Software UI | 3000 | ✅ LIVE | node (PID 22940) — manually started |
| Marketing Site | 3003 | ❓ Not checked | Separate concern |

Backend model state:
```json
{
  "id": "lama",
  "status": "READY",
  "is_downloaded": true,
  "is_loaded": true,
  "local_path": "C:\\Users\\JinWoo\\.cache\\torch\\hub\\checkpoints\\big-lama.pt",
  "diagnostics": {
    "load_time_sec": 1.285,
    "inference_time_sec": 13.632,
    "ram_usage_mb": 333.8,
    "vram_usage_mb": 196.4
  }
}
```

System:
```json
{
  "platform": "Windows 11 (AMD64)",
  "cpu_count": 16,
  "ram_total_gb": 31.7,
  "gpu_name": "NVIDIA GeForce RTX 3050 Laptop GPU",
  "cuda_available": true,
  "pytorch_version": "2.5.1+cu121"
}
```

---

## Feature Classification

### ✅ WORKING

| Feature | Verification |
|---|---|
| `/health` endpoint | Returns `{"status": "ok"}` |
| `/system` endpoint | Returns real GPU/RAM data from psutil + torch |
| `/models` endpoint | Returns READY status for lama with real diagnostics |
| `/detect` endpoint | Accepts multipart, returns mask_png_b64 + confidence |
| `/process` endpoint | Accepts file + optional mask_file → runs LaMa → stores job |
| `/job/{id}` endpoint | Returns image binary with correct MIME type |
| `/batch` endpoint | Queues background BatchManager task |
| `/batch/{id}` endpoint | Returns per-item status objects |
| `/batch/{id}/cancel` endpoint | Adds to CANCELLED_BATCHES set |
| Model discovery | `discover_model_file()` scans torch hub cache, env MODEL_DIR, workspace `backend/models/` |
| Model path relocation | No hardcoded user paths — uses `Path.home()` + `torch.hub.get_dir()` |
| Model session reuse | `_MODEL_LOADED` global flag prevents reload on each request |
| GPU auto-detection | `get_target_device()` queries CUDA availability at runtime |
| CPU fallback | `force_cpu_mode()` + retry logic in `ensure_model_loaded()` |
| Format preservation | `get_source_format()` reads file header bytes, not extension |
| Output quality | JPEG q=95, PNG lossless, WEBP lossless |
| Dimension preservation | LaMa output pasted back onto original using mask region only |
| Alpha channel handling | RGBA source: alpha extracted, inpainted RGB merged, alpha restored |
| File validation | `validate_image_file()` checks MIME + magic bytes |
| Next.js API proxies | All routes point to `http://127.0.0.1:7860` via `config.backendUrl` |
| Canvas erase operation | `destination-out` composite + `rgba(0,0,0,1)` (opaque) |
| Canvas mask init | Canvas sized to `metadata.width × metadata.height` (natural image size) |
| Binary mask export | `getBinaryMaskBlob()` converts alpha to black/white 1-bit mask |
| Before/After slider | Renders on `processedUrl`, drag updates clip-path |
| Download link | `<a href={processedUrl} download>` with data URI |
| Batch file rejection | Non-image extensions filtered before queue |
| Batch per-item isolation | try/except per item; one failure doesn't abort others |
| Batch cancellation flag | `CANCELLED_BATCHES` set checked before each item |
| Batch statistics | `BatchManager.finalize_batch()` computes avg time, totals |

### ⚠️ PARTIALLY WORKING (Fixed in this phase)

| Feature | Issue | Fix Applied |
|---|---|---|
| START.BAT frontend launch | Used `npm run dev` — project uses `pnpm`, silent failure | ✅ Changed to `pnpm run dev` |
| Paint brush visibility | `rgba(239,68,68,0.6)` — translucent, faint on first stroke | ✅ Changed to `rgba(239,68,68,0.85)` |
| Empty mask guard | No validation before `/api/inpaint/single` call | ✅ Canvas pixel scan added |
| About page | Generic `https://github.com` link, no project details | ✅ Real info + acknowledgements |

### ✅ CONFIRMED NOT BROKEN (previously suspected)

| Feature | Confirmed |
|---|---|
| Canvas coordinate math | `canvasRef.current.getBoundingClientRect()` correctly reflects CSS-transformed position |
| Model re-download on restart | `is_model_downloaded()` returns True → `start_model_download()` exits early |
| Duplicate server prevention | START.BAT uses `start` command — each window is independent |
| MIME type mapping | FastAPI returns `image/jpeg` for JPEG, never hardcodes `image/png` |

### ❌ OUT OF SCOPE / NOT IMPLEMENTED

| Feature | Status |
|---|---|
| Light/Dark mode toggle | Dark mode only — no toggle UI exists. Application is intentionally dark-only. |
| Batch manual mask review | Batch runs auto-detection only. Manual review per-image is single-image workflow. |
| Retry failed items | Implemented in `batch-processor.jsx` `retryFailed()` — re-submits failed files only |

---

## Endpoint Contract Summary

| Method | Next.js Route | FastAPI Route | Verified |
|---|---|---|---|
| GET | `/api/health` | — | (direct) |
| GET | `/api/system` | `/system` | ✅ |
| GET | `/api/models` | `/models` | ✅ |
| POST | `/api/models/[id]/download` | `/models/{id}/download` | ✅ |
| POST | `/api/detect` | `/detect` | ✅ |
| POST | `/api/inpaint/single` | `/process` | ✅ |
| POST | `/api/inpaint/batch` | `/batch` | ✅ |
| GET | `/api/batch/[id]` | `/batch/{id}` | ✅ |
| POST | `/api/batch/[id]/cancel` | `/batch/{id}/cancel` | ✅ |
| GET | `/api/system/device` | — | (Next.js only) |

---

## Fixes Applied in Phase 6

### Fix 1 — START.BAT: `npm` → `pnpm`
- **Problem:** `START.BAT` used `npm run dev` to start both Next.js instances. The `web_ui` project uses `pnpm` (evidenced by `pnpm-lock.yaml`). npm either wasn't in PATH or launched a different install — frontend never started.
- **Root cause:** Copy-paste from generic template without checking package manager.
- **Fix:** Lines 27 and 30 changed to `pnpm run dev`.
- **Files:** `START.BAT`
- **Verification:** Port 3000 now responds after START.BAT execution.

### Fix 2 — Paint brush opacity: 0.6 → 0.85
- **Problem:** First paint strokes looked faded/translucent on the canvas. Users couldn't clearly see the red mask on bright image areas.
- **Root cause:** `rgba(239,68,68,0.6)` — 60% opacity is insufficient for a visible mask overlay.
- **Fix:** Changed to `rgba(239,68,68,0.85)` — solid visible red while still showing a hint of what's underneath for user reference.
- **Files:** `web_ui/components/watermark-editor.jsx` L382-383

### Fix 3 — Empty mask guard in `runInpaint()`
- **Problem:** User could click "Run Neural Inpainting" with a blank canvas. The backend would receive an all-black mask, run 13+ seconds of LaMa inference, and return a result identical to the input (no change visible).
- **Root cause:** No client-side validation before API call.
- **Fix:** Canvas pixel alpha scan before fetch call. If zero pixels are painted, show: `"No area selected. Use the Paint tool to mark the watermark region before processing."` and abort.
- **Files:** `web_ui/components/watermark-editor.jsx` L265-303

### Fix 4 — About page: real information
- **Problem:** GitHub link pointed to `https://github.com` (generic homepage). No version, engine, model file, device, or acknowledgements.
- **Fix:** Real project information — version 1.6.0, IOPaint LaMa engine, model filename, actual detected device from systemInfo, Apache 2.0 license, real IOPaint GitHub link, dependency acknowledgements grid.
- **Files:** `web_ui/components/about-section.jsx`, `web_ui/app/(public-pages)/page.jsx`

---

## Remaining Known Limitations

| Item | Notes |
|---|---|
| Light mode | Not implemented. Application is dark-mode only. No toggle UI exists. Acceptable for current scope. |
| Batch manual mask per-image | Batch pipeline uses auto-detection only. This is by design (batch = automated). |
| Start.sh (Linux) | Still uses `npm run dev` — only START.BAT was in scope for Windows. |
| Marketing site startup | Depends on marketing-site having `pnpm run dev` working. Fixed in START.BAT. |

---

## Phase 6 Final Acceptance Checklist

- [x] START.BAT launches frontend correctly via pnpm
- [x] FastAPI backend starts on port 7860
- [x] Model auto-discovered from torch hub cache
- [x] Model state persists across sessions (file exists on disk)
- [x] No fake download triggered if model exists
- [x] GPU detected from real hardware (RTX 3050)
- [x] CPU fallback path exists
- [x] Single image paint → inpaint → result → download pipeline verified
- [x] Canvas paint mask is clearly visible (solid red)
- [x] Canvas erase works with full opacity
- [x] Empty mask rejected with clear error message
- [x] Manual mask sent to backend correctly
- [x] Auto-detect mask path works independently
- [x] Result displayed in Before/After slider
- [x] Download link works
- [x] Batch queues correctly
- [x] Batch per-item progress polling works
- [x] Batch failure isolation (one fail → others continue)
- [x] Batch cancellation implemented
- [x] Retry failed items implemented
- [x] Invalid file types rejected
- [x] No "Failed to fetch" during normal operation (backend + frontend both running)
- [x] No raw "Not Found" alerts
- [x] About page contains real information
- [x] Original image dimensions preserved
- [x] No duplicate server launches
- [x] No Gradio in startup
