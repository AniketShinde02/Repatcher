# Security Policy

## 🔒 Security Philosophy & Architecture

AI Watermark Remover is designed with a **privacy-by-default, local-first security architecture**. 
- **100% Offline Execution**: Processing takes place exclusively on your local workstation or private server instance.
- **Zero Ingestion / No Uploads**: No image data, thumbnails, metadata, or telemetry leave your machine.
- **Model Integrity**: Model weights are downloaded strictly from official IOPaint and Hugging Face repositories over HTTPS.

---

## 🐛 Reporting a Vulnerability

If you discover a security vulnerability within this repository, please report it responsibly:

1. **Do NOT open a public GitHub issue.**
2. Send a detailed report describing the vulnerability, affected files, and steps to reproduce directly to the repository maintainers.
3. You will receive an acknowledgment within 48 hours.

---

## 🛡️ Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

---

## ⚠️ Security Guidelines for Users

- **Keep Dependencies Updated**: Regularly run `python -m pip install -r requirements.txt --upgrade` to ensure PyTorch and OpenCV security patches are applied.
- **Host Binding**: By default, `app.py` binds strictly to `127.0.0.1`. Do not bind to `0.0.0.0` in untrusted public networks without configuring proper reverse proxy authentication (e.g., Nginx with Basic Auth / SSL).
