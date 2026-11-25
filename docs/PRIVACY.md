# Technical Privacy Specification

AI Watermark Remover & Background Preserver enforces a strict **Privacy-by-Design Architecture**.

---

## 🔒 Privacy Model Matrix

| Data Category | Transmitted Remotely? | Stored Locally? | Location / Notes |
| :--- | :--- | :--- | :--- |
| **Image Pixels / Media** | ❌ NO | Yes (Temp) | `stage_input/`, `stage_output/` |
| **Image EXIF / Metadata** | ❌ NO | ❌ NO | Excluded during inpainting |
| **Filenames** | ❌ NO | Yes (Temp) | Used locally during batch mapping |
| **IP Address / Analytics** | ❌ NO | ❌ NO | Zero telemetry collected |
| **User Identity** | ❌ NO | ❌ NO | No authentication required |
| **Model Weights** | ⚠️ HTTPS Download | Yes (Cache) | Downloaded once on first run |

---

## 🔌 Air-Gapped Operation

To run in a completely isolated air-gapped network:
1. Run setup once on an internet-connected machine so LaMa weights (~350MB) are cached.
2. Copy the cached PyTorch / IOPaint weights (`~/.cache/iopaint` or `torch/hub`) to your air-gapped machine.
3. Launch `Start_AI_Remover.bat` — application runs 100% offline.
