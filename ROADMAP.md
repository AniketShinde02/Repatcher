# Product Roadmap — AI Watermark Remover

This roadmap outlines planned features, technical enhancements, and community milestones for AI Watermark Remover & Background Preserver.

---

## 🚀 v1.0.0 — Stable Open-Source Release (Current)
- [x] **Smart Gemini Star Detection**: Top-Hat morphology algorithm to isolate transparent 4-pointed stars on bright/dark backgrounds.
- [x] **Interactive Brush Tool**: Gradio canvas editor with zoom and binary stroke dilation.
- [x] **Standalone Bulk Processor**: Auto-saving to designated output directories with batch queue support.
- [x] **RAM Optimization**: Automated GPU/RAM cache flushing (`torch.cuda.empty_cache()`) keeping memory at ~1-2GB.
- [x] **Cross-Platform Support**: One-click setup scripts and launchers for Windows (`setup.bat`, `Start_AI_Remover.bat`) and Linux/macOS (`setup.sh`, `start.sh`).
- [x] **Environment Diagnostics**: CLI diagnostic suite (`scripts/env_check.py`) to verify hardware, CUDA, system RAM, storage, and dependencies.

---

## 🔮 v1.1.0 — Future Enhancements
- [ ] **Multi-Model Support**: Integration with SDXL Inpainting and Manga-Inpainting models for complex non-corner logos.
- [ ] **EXIF Preservation**: Option to preserve original EXIF metadata in cleaned output images.
- [ ] **Docker Container**: Official lightweight Docker image for server deployment.
- [ ] **FastAPI REST API**: Headless REST API mode for integration into e-commerce product asset pipelines.
