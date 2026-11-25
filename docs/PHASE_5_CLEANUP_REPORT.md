# Phase 5: Product Separation & UI System — Cleanup Report

## Summary
The "Phase 5" objective was to conceptually and structurally separate the monolithic application into three distinct layers:
1. **Marketing Website (Port 3003)**: Landing page and conversion funnel.
2. **Software UI (Port 3000)**: The core product interface (Single Editor, Batch Queue, Settings).
3. **Processing Engine (Port 7860)**: FastAPI neural inpainting backend.

## Key Accomplishments

### 1. PNPM Migration & Software UI Refinement
- Successfully migrated `web_ui` from npm/yarn to PNPM (`pnpm-lock.yaml` generated).
- Removed the marketing `HeroSection` from the core app's landing view.
- Changed default routing to immediately display the **Watermark Editor**.
- Centralized software UI branding into `web_ui/config/branding.ts` to replace hardcoded strings and standardize the visual footprint.

### 2. Marketing Site Extraction
- Duplicated the existing Next.js frontend into `marketing-site/`.
- Repurposed this directory strictly for public-facing pages, running on port `3003`.
- Updated `START.BAT` to launch all three discrete layers simultaneously without conflict.

### 3. Path Serialization & Encoding Fixes (Backend)
- Addressed the fatal character encoding bug (`UnicodeEncodeError: 'charmap'`) during file processing.
- Stripped original filenames from physical disk paths and migrated staging folders to use purely **UUID**-based filenames (`stage_input/{job_id}{ext}`).
- This guarantees zero edge cases when dealing with spaces, ellipses, emojis, or foreign characters in user filenames.

### 4. Codebase Cleanup
- **Staging Directories**: Safely moved all root-level staging folders (`stage_input`, `stage_mask`, etc.) to the internal `backend/temp/` directory.
- **Legacy Components**: Safely archived the old Gradio UI (`app.py`, `processor.py`) into the `legacy/` directory to prevent architectural confusion.

## Verification
- End-to-end processing pipeline tests passed cleanly (`test_pipeline.py`), confirming that UUID internal paths, detection algorithms, and format preservation (`.jpg`, `.png`, `.webp`) remain intact and reliable.
