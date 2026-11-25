# Privacy Policy — AI Watermark Remover

## 🛡️ Privacy-by-Design Commitment

AI Watermark Remover & Background Preserver is built on a strict **Privacy-First Architecture**. We believe your data, intellectual property, and media assets belong solely to you.

---

## 🚫 What We DO NOT Collect

1. **No Image Uploads**: Your media files are processed locally on your hardware. Images are never uploaded to any remote server or third-party cloud.
2. **No Image Data / Content Ingestion**: We do not store, copy, analyze, or train models on your images.
3. **No Metadata Harvest**: We do not read, transmit, or extract EXIF metadata, GPS locations, camera info, or filenames outside your local workspace.
4. **No Telemetry / No Tracking**: There are no stealth analytics, hidden trackers, user profiling, or crash report beacons in this application.
5. **No Personal Identification**: No user accounts, email addresses, or personal credentials are required or stored.

---

## 🌐 Network Activity & Internet Usage

The application requires internet access **ONLY ONCE** during initial setup to download the official LaMa neural model weights (~350MB) from official Hugging Face / PyTorch repositories over encrypted HTTPS. 

Once downloaded, the application operates **100% OFFLINE**. You can safely disconnect your machine from the internet or run in an air-gapped environment.

---

## 📁 Local Data Storage

All temporary processing artifacts (`stage_input/`, `stage_output/`, `stage_mask/`, `mask.png`) reside exclusively inside your local project workspace directory. You can clear them at any time by running `python scripts/clean_temp.py`.
