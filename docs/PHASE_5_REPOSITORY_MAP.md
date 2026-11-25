# Phase 5: Repository Map

## 1. Root Structure
- `.agents/`: Project AI engineering guardrails, decisions, and local skills (`skills/`, `rules/`).
- `backend/`: FastAPI application code for detection and inpainting.
- `web_ui/`: Next.js frontend code (currently functioning as both UI and partially as a marketing page, though it must become purely software UI).
- `genesis-nextjs/`: The pristine Next.js template to be used strictly as the marketing website reference.
- `docs/`: Documentation folder (contains Phase 4 reports and this map).
- `tests/`: Automated test suite for the pipeline.
- `scripts/`: Assorted helper scripts.
- `input_images/`, `cleaned_images/`, `processed_images/`, `stage_input/`, `stage_mask/`, `stage_output/`, `backup_images/`: Various image processing and temporary folders.
- `venv/`: Python virtual environment.
- `app.py`, `processor.py`: Legacy Gradio application and processor files (to be retired/cleaned up if not used).
- `START.BAT`, `Start_AI_Remover.bat`, `setup.bat`, `setup.sh`, `start.sh`: Startup and environment initialization scripts.

## 2. Backend (`backend/`)
- `app/`: FastAPI server setup and routes (e.g., `main.py`).
- `core/`: Core image processing logic (`inpainting.py`, `detection.py`).

## 3. Frontend (`web_ui/`)
- Contains Next.js 15+ App Router structure (`app/`, `components/`, `sections/`, `public/`).
- Currently has `pnpm-lock.yaml` alongside `package-lock.json`, which requires conflict resolution (migrating fully to PNPM).
- Contains Tailwind configuration and routing logic.

## 4. Marketing Template (`genesis-nextjs/`)
- Contains the raw `nextjs/` template directory.
- This serves as the master visual reference and will be copied to create a dedicated `marketing-site/`.

## 5. Agent Instructions (`.agents/`)
- Contains project-specific constraints (`CONSTRAINTS.md`, `ARCHITECTURE.md`, `HANDOVER.md`, `DECISIONS.md`, `FLOW.md`, `ROLLBACK.md`, `TEST_CHECKLIST.md`, `CONTEXT_SUMMARY.md`).
- Contains local skills under `.agents/skills/`.

## 6. Cleanup Opportunities
- Temporary image staging folders (`stage_input/`, `stage_mask/`, etc.) clutter the root directory.
- Legacy `app.py` (Gradio UI) is no longer part of the application flow.
- Duplicate Next.js lockfiles in `web_ui/`.
- Unnecessary Python files (`processor.py` if fully superseded by `backend/core/`).

## Conclusion
The repository has a solid backend foundation and a working Next.js frontend, but lacks a clean separation between the Marketing Website and the Software UI. The root directory is heavily cluttered with temporary processing directories and legacy files.
