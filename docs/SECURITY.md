# Technical Security Architecture

Security controls and threat model for AI Watermark Remover.

---

## 🛡️ Security Controls

1. **Local Host Binding**:
   By default, `app.py` binds to `127.0.0.1:7860` (loopback interface), preventing unauthorized external network access.

2. **No Remote Code Execution (RCE)**:
   Input filenames are strictly sanitized before passing to filesystem calls using Python's `Path` objects.

3. **Subprocess Safety**:
   Inpainting operations use direct Python library calls (`iopaint.batch_processing.batch_inpaint`) rather than shell subprocess strings to eliminate shell injection vectors.

4. **Input Validation**:
   File uploads are validated by OpenCV (`cv2.imread`) and Pillow (`Image.open`). Non-image binary payloads are discarded.
