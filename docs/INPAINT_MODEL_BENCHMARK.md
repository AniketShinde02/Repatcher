# Pretrained Inpainting Benchmark

**Objective:** Evaluate pretrained neural network models (LaMa) specifically applied to local bounding-box crops instead of the entire 1792x2400 (or higher) full resolution image, ensuring GPU memory limits are not breached and runtime remains fast.

## Configuration
- **Model:** Big-LaMa
- **Engine:** `iopaint` 
- **Method:** Detect Gemini Sparkle → Extract bounding box + 32px padding → Run inference only on the crop → Composite back into original image.
- **Hardware Profile:** CUDA target (NVIDIA RTX 3050 Laptop GPU 4GB)

## Benchmark Results (10 Image Sample)

| Model | Average Crop Size | Detection Time | Inference Time (Avg) | VRAM Delta | Output Quality |
| --- | --- | --- | --- | --- | --- |
| LaMa (Crop) | ~96x96 px | 137.7 ms | 230 ms / image * | +196.4 MB | Excellent (No dark artifacts) |

*\* Note: The first inference took ~4500ms due to PyTorch JIT compilation (warm-up), but subsequent crop inferences stabilized around 215–240ms.*

### Observations

1. **Inference Time:** Processing an 88x88 crop through LaMa takes **~230ms**. If we ran the entire 2K image, it would take multiple seconds and likely OOM the RTX 3050.
2. **Memory (VRAM):** Initializing LaMa into memory consumed ~196MB of VRAM, and processing tiny crops causes almost zero VRAM spiking during execution.
3. **Artifacts (Dark Spots):** Running LaMa on a tightly padded crop instead of a loosely padded global mask eliminated the "dark diamond" blending artifact observed in previous iterations.

### Recommendation
**WINNER: LaMa (Crop Mode)**

The LaMa crop implementation completely satisfies the requirements:
- VRAM usage is safely bounded and fits easily in 4GB.
- 230ms is highly acceptable for difficult or uncertain watermark removals.
- We will lock this in as the **Uncertain/Unknown Case AI Inpainting Fallback**.

*PowerPaint was omitted from the live test due to the large weight download and heavy VRAM requirement for a 4GB card, but its structure would be identical if a model router requires it later.*
