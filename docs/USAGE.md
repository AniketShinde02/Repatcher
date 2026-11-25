# User Guide & Operating Modes

AI Watermark Remover provides two primary operating modes in the web interface.

---

## ⚡ Mode 1: Smart Batch Processor

Designed for processing tens or hundreds of generated product images automatically.

### Workflow:
1. Navigate to the **⚡ Smart Batch Processor** tab.
2. Drag and drop product images (PNG, JPG, WEBP).
3. Select **Logo Masking Mode**:
   - **✨ Smart Auto-Detect Gemini Star**: Uses Morphological Top-Hat filtering to isolate transparent corner stars automatically.
   - **🎯 Custom Box with Offsets**: Allows setting fixed rectangular dimensions and X/Y offset sliders.
4. Click **🚀 Run Precision Batch Process**.
5. Cleaned images are displayed in the comparison gallery and automatically saved to `processed_images/`.

---

## 🖌️ Mode 2: Interactive Precision Brush Editor

Designed for custom logos, arbitrary positions, or challenging backgrounds.

### Workflow:
1. Navigate to the **🖌️ Precision Pixel / Brush Tool** tab.
2. Upload an image to the Canvas Editor.
3. Select the brush tool and paint *exactly* over the logo or watermark.
4. Click **🚀 Remove Logo from Brushed Region**.
5. View the inpainted output side-by-side with full background preservation.

---

## ⚙️ Advanced Options

- **Output Directory Path**: Custom absolute path where output images are written.
- **Hardware Acceleration**: Switch between `cuda` (GPU) and `cpu` (Fallback).
- **Clear GPU/RAM Cache**: Flushes PyTorch VRAM cache after each run to keep memory usage low.
