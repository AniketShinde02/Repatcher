# AI Watermark Remover & Background Preserver

A privacy-first, local-execution AI utility designed to batch-process generated product and marketing images—removing Gemini star watermarks with pinpoint precision while keeping 100% of your background, skin, and fabric textures intact.

---

## 🎯 Project Philosophy

Modern AI image generators frequently embed translucent corner watermarks. Traditional watermark removal tools often resort to destructive cropping, heavy blurring, or naive background removal that ruins surrounding product details.

**AI Watermark Remover** is built on a non-destructive philosophy:
- **Local-First Processing**: 100% of your image data remains on your workstation. No cloud uploads, no telemetry, no subscription APIs.
- **Top-Hat Morphological Precision**: Auto-detects translucent 4-pointed star shapes regardless of background luminance, generating a surgical mask that covers *only* the watermark.
- **Neural Reconstruction**: Utilizes the LaMa (Large Mask Inpainting) deep learning model to reconstruct the background seamlessly using PyTorch CUDA hardware acceleration.

---

## ✨ Key Features

- **✨ Smart Star Auto-Detection**: Isolate translucent Gemini watermarks in the bottom-right region using Morphological Top-Hat filtering.
- **🖌️ Interactive Brush & Zoom Precision Editor**: Upload individual images, zoom in, and manually paint over custom logos with a binarized brush layer.
- **🎯 Custom Box & Offset Controls**: Configure exact pixel dimensions and X/Y offset sliders for custom watermark positions.
- **⚡ Standalone Bulk Batch Processing**: Automatically queue tens or hundreds of images and save outputs directly to your local target folder.
- **⚙️ Memory Optimization**: Automated PyTorch GPU/RAM cache flushing (`torch.cuda.empty_cache()`) to keep memory footprint capped at ~1-2GB.
- **💻 Cross-Platform Launchers & Environment Diagnostics**: Includes one-click scripts (`setup.bat`, `setup.sh`) and CLI hardware diagnostics (`scripts/env_check.py`).

---

## 📥 Supported Inputs & Technical Limits

- **Supported Formats**: PNG, JPG, JPEG, WEBP
- **Supported Input Resolutions**: 512x512 up to 4K (2048x2048+)
- **Processing Time**: ~1–2 seconds per image (NVIDIA GPU with CUDA) | ~10–20 seconds per image (CPU fallback)

---

## 💻 System Requirements

- **Operating System**: Windows 10/11, Linux (Ubuntu 20.04+), macOS 12+
- **Python**: Version 3.10, 3.11, or 3.12
- **System Memory**: 4 GB RAM minimum
- **Graphics Card (Recommended)**: NVIDIA GPU with CUDA support (2 GB+ VRAM)
- **Free Disk Space**: ~1.5 GB (for Python virtual environment and LaMa weights)

---

## 🚀 Quick Start & Installation

### Windows (Automated)

1. Clone the repository:
   ```cmd
   git clone https://github.com/your-username/image_processor_sandbox.git
   cd image_processor_sandbox
   ```

2. Run the automated setup script:
   ```cmd
   setup.bat
   ```
   *This creates a local `venv`, installs pinned dependencies from `requirements.txt`, and runs hardware diagnostics.*

3. Launch the application:
   ```cmd
   Start_AI_Remover.bat
   ```
   *Your default web browser will automatically open `http://127.0.0.1:7860` as soon as the server port is listening.*

### Linux & macOS

1. Make scripts executable and run setup:
   ```bash
   chmod +x setup.sh start.sh
   ./setup.sh
   ```

2. Launch the application:
   ```bash
   ./start.sh
   ```

---

## 📖 Usage Modes

1. **Smart Batch Processor Tab**:
   - Upload multiple product images.
   - Select **✨ Smart Auto-Detect Gemini Star**.
   - Click **🚀 Run Precision Batch Process**.
   - Outputs are displayed in the comparison gallery and automatically saved to `processed_images/`.

2. **Precision Pixel / Brush Tool Tab**:
   - Upload a single image.
   - Use the brush tool to highlight any custom logo or watermark.
   - Click **🚀 Remove Logo from Brushed Region**.

For advanced configuration, expand the **⚙️ Hardware Acceleration & Output Settings** accordion.

---

## 📐 Architecture Overview

```
Source Images ──► Morphological Top-Hat Masking ──► LaMa Neural Inpainting ──► Auto-Save Output
                           │                               │
                (Isolates Star Shape)           (NVIDIA CUDA / PyTorch)
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for full technical data flow specifications.

---

## 🔒 Privacy Model & Security

- **100% Local Execution**: No images, thumbnails, EXIF metadata, or telemetry leave your computer.
- **Air-Gapped Operation**: Network access is only required once during initial boot to download the official LaMa model weights (~350MB). Once cached, the application works completely offline.
- **Security Audit**: Codebase audited for path traversal, shell injection, and secret leakage.

See [PRIVACY.md](PRIVACY.md), [SECURITY.md](SECURITY.md), and [docs/PRIVACY.md](docs/PRIVACY.md) for details.

---

## ⚠️ Limitations & Acceptable Use

- **Search Region**: Smart Auto-Detection searches within a 300x300px region in the bottom-right corner. Logos positioned elsewhere require the Interactive Brush Tool or Custom Box mode.
- **Acceptable Use Policy**: Users must possess appropriate rights or licenses for all processed media. This tool must not be used to unlawfully strip copyright notices or redistribute protected commercial content. See [TERMS_OF_USE.md](TERMS_OF_USE.md).

---

## 🔧 Troubleshooting

If you encounter issues, run the environment diagnostic tool:
```bash
python scripts/env_check.py
```
For common solutions (CUDA OOM, port conflicts), consult [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) and [docs/FAQ.md](docs/FAQ.md).

---

## 🗺️ Roadmap & Contributing

We welcome community contributions! Please review our [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

Check [ROADMAP.md](ROADMAP.md) for upcoming features (Multi-model SDXL inpainting, REST API, Docker support).

---

## 📄 License & Acknowledgements

- **License**: Released under the [Apache 2.0 License](LICENSE).
- **Core Neural Engine**: Powered by [IOPaint](https://github.com/Sanster/IOPaint) and the LaMa (Large Mask Inpainting) model by Samsung AI Lab.
- **UI Framework**: Powered by [Gradio](https://github.com/gradio-app/gradio).
