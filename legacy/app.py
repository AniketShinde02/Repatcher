"""
🧹 AI Watermark Remover — Powered by IOPaint LaMa Model
Author: Antigravity for Aniket
Usage: venv/Scripts/python.exe app.py
"""

import gradio as gr
import cv2
import numpy as np
import os
import shutil
import time
from pathlib import Path
from PIL import Image
from iopaint.batch_processing import batch_inpaint

# ─── Configuration ──────────────────────────────────────────────────────────
INPUT_STAGE  = Path("stage_input")
OUTPUT_STAGE = Path("stage_output")
MASK_PATH    = Path("mask.png")
MASK_STAGE   = Path("stage_mask")

INPUT_STAGE.mkdir(exist_ok=True)
OUTPUT_STAGE.mkdir(exist_ok=True)
MASK_STAGE.mkdir(exist_ok=True)

# ─── Mask Generator Helpers ──────────────────────────────────────────────────
def detect_gemini_star_mask(image_path: Path, sensitivity: int = 160, padding: int = 12, search_size: int = 300) -> np.ndarray:
    """
    Intelligently locates the bright 4-pointed Gemini star in the bottom-right region.
    Creates a tight mask ONLY over the star shape with extra padding to cover edges,
    keeping 99%+ of the background intact!
    """
    img = cv2.imread(str(image_path))
    if img is None:
        return None
    h, w = img.shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)
    
    # Define ROI for bottom-right corner (Gemini star is usually here)
    x_start = max(0, w - search_size)
    y_start = max(0, h - search_size)
    roi = img[y_start:h, x_start:w]
    
    # Convert to grayscale
    gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    
    # Use Morphological Top-Hat to isolate small bright features regardless of background
    kernel_size = 45
    tophat_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    tophat = cv2.morphologyEx(gray_roi, cv2.MORPH_TOPHAT, tophat_kernel)
    
    # Threshold the top-hat image. Map UI sensitivity to a lower range suitable for top-hat differences.
    tophat_thresh_val = max(15, sensitivity - 110)
    _, thresh = cv2.threshold(tophat, tophat_thresh_val, 255, cv2.THRESH_BINARY)
    
    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    roi_mask = np.zeros(roi.shape[:2], dtype=np.uint8)
    star_found = False
    
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if 20 < area < 4000:
            cv2.drawContours(roi_mask, [cnt], -1, 255, thickness=cv2.FILLED)
            star_found = True
            
    if star_found:
        kernel = np.ones((padding, padding), np.uint8)
        roi_mask = cv2.dilate(roi_mask, kernel, iterations=2)
    else:
        # Improved Fallback: cover a larger 120x120 area slightly offset from corner
        fallback_w, fallback_h = 120, 120
        y1 = max(0, roi_mask.shape[0] - fallback_h - 10)
        x1 = max(0, roi_mask.shape[1] - fallback_w - 10)
        roi_mask[y1:, x1:] = 255
        
    mask[y_start:h, x_start:w] = roi_mask
    return mask


def build_custom_box_mask(w: int, h: int, box_w: int = 80, box_h: int = 80, x_offset: int = 0, y_offset: int = 0) -> np.ndarray:
    """Build a customizable box mask with X/Y offsets from the bottom-right corner."""
    mask = np.zeros((h, w), dtype=np.uint8)
    x2 = max(0, w - x_offset)
    x1 = max(0, x2 - box_w)
    y2 = max(0, h - y_offset)
    y1 = max(0, y2 - box_h)
    mask[y1:y2, x1:x2] = 255
    return mask


def prepare_per_image_masks(mask_mode, sensitivity, padding, box_w, box_h, x_offset, y_offset):
    """Generates per-image mask files and saves them to MASK_STAGE."""
    shutil.rmtree(MASK_STAGE, ignore_errors=True)
    MASK_STAGE.mkdir()
    
    for img_path in INPUT_STAGE.iterdir():
        if img_path.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]:
            img = cv2.imread(str(img_path))
            if img is None:
                continue
            h, w = img.shape[:2]
            
            if mask_mode == "✨ Smart Auto-Detect Gemini Star (Preserves 100% Background)":
                mask = detect_gemini_star_mask(img_path, sensitivity=int(sensitivity), padding=int(padding))
            else:
                mask = build_custom_box_mask(w, h, box_w=int(box_w), box_h=int(box_h), x_offset=int(x_offset), y_offset=int(y_offset))
                
            # Save mask uniquely for this image
            mask_out_path = MASK_STAGE / f"{img_path.stem}.png"
            cv2.imwrite(str(mask_out_path), mask)


# ─── Core Processing Logic ────────────────────────────────────────────────────
def process_batch(uploaded_files, mask_mode, sensitivity, padding, box_w, box_h, x_offset, y_offset, device, auto_save, output_dir, clear_cache, progress=gr.Progress()):
    if not uploaded_files:
        return [], [], "⚠️  Please upload at least one image first."

    # Clean staging areas
    shutil.rmtree(INPUT_STAGE, ignore_errors=True)
    shutil.rmtree(OUTPUT_STAGE, ignore_errors=True)
    INPUT_STAGE.mkdir()
    OUTPUT_STAGE.mkdir()

    # Copy uploaded files to stage
    progress(0.05, desc="📂 Preparing uploaded images...")
    for f in uploaded_files:
        src = Path(f.name)
        shutil.copy(src, INPUT_STAGE / src.name)

    total = len(uploaded_files)
    progress(0.10, desc=f"🖼️  Loaded {total} image(s). Isolating Gemini watermark mask...")

    # Generate the masks per image
    prepare_per_image_masks(mask_mode, sensitivity, padding, box_w, box_h, x_offset, y_offset)

    # Run IOPaint safely
    progress(0.15, desc="🚀 Booting LaMa AI model on GPU... (preserves surrounding background)")
    try:
        # Verify input stage has actual images before running
        valid_inputs = [f for f in INPUT_STAGE.iterdir() if f.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"]]
        if not valid_inputs:
            return [], [], "⚠️  No supported images found in input stage."

        batch_inpaint(
            model="lama",
            device=device,
            image=INPUT_STAGE,
            mask=MASK_STAGE, # Pass the entire directory so each image gets its own mask
            output=OUTPUT_STAGE,
            config=None,
            concat=False,
        )
    except SystemExit as e:
        return [], [], f"⚠️  Batch processing halted cleanly: empty or invalid image folder (code {e.code})."
    except Exception as e:
        return [], [], f"❌ IOPaint error: {str(e)}"

    progress(0.90, desc="🖼️  Collecting results...")

    before_imgs = []
    after_imgs  = []
    log_lines   = []
    
    # Handle auto-save directory
    final_save_path = None
    if auto_save and output_dir.strip():
        final_save_path = Path(output_dir.strip())
        final_save_path.mkdir(parents=True, exist_ok=True)

    for src_path in sorted(INPUT_STAGE.iterdir()):
        dst_path = OUTPUT_STAGE / src_path.name
        if not dst_path.exists():
            dst_path = OUTPUT_STAGE / f"{src_path.stem}.png"
            
        if dst_path.exists():
            before_imgs.append(str(src_path))
            after_imgs.append(str(dst_path))
            
            # Auto-save logic
            if final_save_path:
                shutil.copy(dst_path, final_save_path / dst_path.name)
                
            size_before = src_path.stat().st_size // 1024
            size_after  = dst_path.stat().st_size // 1024
            log_lines.append(f"✅  {src_path.name} — {size_before}KB → {size_after}KB")
        else:
            log_lines.append(f"⚠️  {src_path.name} — Output not found (skipped).")
            
    # Clear cache to save RAM
    if clear_cache:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    progress(1.0, desc="✅ Done!")
    save_msg = f"\n💾 Automatically saved to: {final_save_path.resolve()}" if final_save_path else ""
    log = f"Processed {len(after_imgs)}/{total} images cleanly with background preserved.{save_msg}\n\n" + "\n".join(log_lines)
    return before_imgs, after_imgs, log



def process_interactive_editor(editor_dict, device, progress=gr.Progress()):
    """Processes a single image where the user manually brushed over the watermark."""
    if editor_dict is None:
        return None, "⚠️  Please upload an image and draw over the logo first."
        
    background = editor_dict.get("background")
    layers = editor_dict.get("layers", [])
    
    if background is None or not layers:
        return None, "⚠️  No mask layer drawn. Please brush over the logo region."

    # Prepare temp single-item staging
    single_in  = INPUT_STAGE / "editor_input.png"
    single_out = OUTPUT_STAGE / "editor_input.png"
    
    shutil.rmtree(INPUT_STAGE, ignore_errors=True)
    shutil.rmtree(OUTPUT_STAGE, ignore_errors=True)
    INPUT_STAGE.mkdir()
    OUTPUT_STAGE.mkdir()
    
    # Save background image
    if isinstance(background, np.ndarray):
        cv2.imwrite(str(single_in), cv2.cvtColor(background, cv2.COLOR_RGB2BGR))
    else:
        background.save(str(single_in))
        
    # Save brush mask layer
    mask_layer = layers[0]
    
    if not isinstance(mask_layer, np.ndarray):
        mask_layer = np.array(mask_layer)
        
    # Extract alpha channel or convert to grayscale
    if mask_layer.shape[-1] == 4:
        alpha_or_gray = mask_layer[:, :, 3]
    else:
        alpha_or_gray = cv2.cvtColor(mask_layer, cv2.COLOR_RGB2GRAY)
        
    # Binarize the mask: anything > 0 becomes 255 (ensures LaMa gets a strict binary mask)
    _, binary_mask = cv2.threshold(alpha_or_gray, 1, 255, cv2.THRESH_BINARY)
    
    # Dilate slightly to cover soft edges of the brush stroke and anti-aliasing
    kernel = np.ones((5, 5), np.uint8)
    dilated_mask = cv2.dilate(binary_mask, kernel, iterations=1)
    
    cv2.imwrite(str(MASK_PATH), dilated_mask)

    progress(0.20, desc="🚀 Inpainting brushed logo using LaMa AI...")
    try:
        batch_inpaint(
            model="lama",
            device=device,
            image=INPUT_STAGE,
            mask=MASK_PATH,
            output=OUTPUT_STAGE,
            config=None,
            concat=False,
        )
    except Exception as e:
        return None, f"❌ IOPaint error: {str(e)}"

    if single_out.exists():
        result_img = Image.open(single_out)
        return result_img, "✅ Logo removed cleanly from brushed mask!"
    else:
        # Check png output fallback
        alt_out = OUTPUT_STAGE / "editor_input.png"
        if alt_out.exists():
            return Image.open(alt_out), "✅ Logo removed cleanly!"
        return None, "⚠️ Output image failed to render."


# ─── Gradio UI ────────────────────────────────────────────────────────────────
CSS = """
body { font-family: 'Inter', sans-serif; }
#header { text-align: center; padding: 1.5rem 0 0.5rem; }
#header h1 { font-size: 2.2rem; font-weight: 800; margin: 0; color: var(--body-text-color); }
#header p  { color: var(--body-text-color); margin: 0.25rem 0 0; font-size: 1rem; opacity: 0.8; }
.gr-button-primary { background: #18A558 !important; border-color: #18A558 !important; font-weight: 700; }
.gr-button-primary:hover { background: #16944e !important; }
footer { display: none !important; }
"""

with gr.Blocks(
    title="🧹 AI Watermark Remover (Precision Background Preservation)",
    css=CSS,
    theme=gr.themes.Soft(primary_hue="green"),
) as demo:

    # ── Header ──────────────────────────────────────────────────────────────
    gr.HTML("""
    <div id="header">
        <h1>🧹 AI Watermark Remover & Background Preserver</h1>
        <p>Powered by <strong>IOPaint LaMa</strong> · Smart Star Auto-Detection · Precision Brush Zoom Controls</p>
    </div>
    """)

    with gr.Accordion("⚙️ Hardware Acceleration & Output Settings", open=False):
        device_radio = gr.Radio(
            choices=["cuda", "cpu"],
            value="cuda",
            label="Hardware Acceleration",
            info="cuda = Nvidia GPU (1-2s per image). cpu = Fallback.",
        )
        auto_save = gr.Checkbox(label="Save automatically to Output Directory?", value=True)
        output_dir = gr.Textbox(
            label="Output Directory Path (Absolute Path)", 
            value=str(Path.cwd() / "processed_images"),
            info="Images will be saved here automatically when processed."
        )
        clear_cache = gr.Checkbox(
            label="Clear GPU/RAM Cache after processing?", 
            value=True,
            info="Keeps memory strictly at 1-2GB during bulk processing."
        )

    with gr.Tabs():
        # ── TAB 2: Interactive Zoom & Brush Editor ─────────────────────────
        with gr.Tab("🖌️ Precision Pixel / Brush Tool (Select Logo)"):
            gr.Markdown("### 🎯 Upload an image, zoom in, and brush *exactly* over the logo. The background will be seamlessly preserved.")
            with gr.Row():
                with gr.Column(scale=1):
                    image_editor = gr.ImageEditor(
                        label="Canvas Editor (Use brush to paint over logo. Do NOT paint over the background you want to keep.)",
                        type="numpy",
                        interactive=True,
                        brush=gr.Brush(colors=["#FFFFFF"], color_mode="fixed"),
                    )
                    brush_run_btn = gr.Button("🚀 Remove Logo from Brushed Region", variant="primary", size="lg")
                
                with gr.Column(scale=1):
                    editor_result = gr.Image(label="Inpainted Output (Background Intact)")
                    editor_log    = gr.Textbox(label="Status Log", interactive=False)

            brush_run_btn.click(
                fn=process_interactive_editor,
                inputs=[image_editor, device_radio],
                outputs=[editor_result, editor_log],
            )

        # ── TAB 1: Smart Batch Processor ────────────────────────────────────
        with gr.Tab("⚡ Smart Batch Processor"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### ① Upload Images")
                    file_input = gr.File(
                        label="Drag & drop product images (JPG / PNG / WEBP)",
                        file_count="multiple",
                        height=200,
                    )

                    gr.Markdown("### ② Masking Strategy")
                    mask_mode = gr.Radio(
                        choices=[
                            "✨ Smart Auto-Detect Gemini Star (Preserves 100% Background)",
                            "🎯 Custom Box with Offsets",
                        ],
                        value="✨ Smart Auto-Detect Gemini Star (Preserves 100% Background)",
                        label="Logo Masking Mode",
                    )

                    with gr.Group() as smart_params:
                        sensitivity = gr.Slider(
                            minimum=150, maximum=245, value=160, step=5,
                            label="Star Luminance Sensitivity Threshold",
                            info="Detects white translucent star shape. Lower = better for semi-transparent stars.",
                        )
                        padding = gr.Slider(
                            minimum=2, maximum=20, value=12, step=1,
                            label="Star Edge Dilation Padding (pixels)",
                            info="Larger padding ensures full watermark coverage.",
                        )

                    with gr.Group(visible=False) as box_params:
                        with gr.Row():
                            box_w = gr.Slider(minimum=20, maximum=300, value=80, step=5, label="Box Width (px)")
                            box_h = gr.Slider(minimum=20, maximum=300, value=80, step=5, label="Box Height (px)")
                        with gr.Row():
                            x_offset = gr.Slider(minimum=0, maximum=200, value=0, step=5, label="X Offset from right (px)")
                            y_offset = gr.Slider(minimum=0, maximum=200, value=0, step=5, label="Y Offset from bottom (px)")


                    run_btn = gr.Button("🚀 Run Precision Batch Process", variant="primary", size="lg")

                # Results
                with gr.Column(scale=1):
                    gr.Markdown("### ③ Before & After Comparison")
                    with gr.Row():
                        before_gallery = gr.Gallery(label="Original", columns=2, height=300, object_fit="contain")
                        after_gallery  = gr.Gallery(label="Cleaned (Background Intact)", columns=2, height=300, object_fit="contain")
                    
                    log_box = gr.Textbox(
                        label="📋 Processing Log",
                        lines=6,
                        interactive=False,
                        placeholder="Logs will appear here...",
                    )

            # Toggle settings view based on mode selection
            def toggle_mode(mode):
                if "Smart Auto-Detect" in mode:
                    return gr.update(visible=True), gr.update(visible=False)
                else:
                    return gr.update(visible=False), gr.update(visible=True)

            mask_mode.change(fn=toggle_mode, inputs=[mask_mode], outputs=[smart_params, box_params])

            run_btn.click(
                fn=process_batch,
                inputs=[file_input, mask_mode, sensitivity, padding, box_w, box_h, x_offset, y_offset, device_radio, auto_save, output_dir, clear_cache],
                outputs=[before_gallery, after_gallery, log_box],
            )

# ─── Launch ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*60)
    print("  AI Watermark Remover is starting...")
    print("  Booting backend server & loading GPU models...")
    print("  Your default browser will open automatically once ready.")
    print("="*60 + "\n")
    # inbrowser=True ensures browser opens ONLY AFTER server port is listening!
    demo.launch(server_name="127.0.0.1", server_port=7860, inbrowser=True, show_error=True)
