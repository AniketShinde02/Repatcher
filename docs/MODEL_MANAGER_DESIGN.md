# Model Manager Design Specification

This document details the architectural design for the on-demand Model Lifecycle Manager, handling detection, downloading, checksum verification, caching, and VRAM management.

---

## 🏛️ Model Manager Responsibilities

```
                      ┌─────────────────────────────────┐
                      │    Application Startup / API    │
                      └────────────────┬────────────────┘
                                       │
                                       ▼
                      ┌─────────────────────────────────┐
                      │  Check ~/.cache/torch/hub/...   │
                      └────────┬───────────────┬────────┘
                               │               │
                     (Exists & Valid)      (Missing)
                               │               │
                               ▼               ▼
                      ┌────────────────┐ ┌──────────────┐
                      │ Load Weights   │ │ Download via │
                      │ into VRAM      │ │ HTTPS Stream │
                      └────────────────┘ └──────┬───────┘
                                                │
                                                ▼
                                         ┌──────────────┐
                                         │ Verify MD5   │
                                         │ Checksum     │
                                         └──────────────┘
```

---

## 🔑 Key Features

1. **Model Detection & Diagnostics**:
   Exposes `/models` GET endpoint indicating cached models, file path, download size (~198MB), and status (`cached` vs `downloading`).

2. **On-Demand Progress Streaming**:
   When a required model is missing, the backend streams download progress (`0% -> 100%`) to the UI without blocking the main event loop.

3. **MD5 Checksum Integrity Verification**:
   Verifies downloaded `.pt` weight files against trusted hashes before loading into PyTorch memory.

4. **Zero-Bloat Git Repository**:
   Ensures model weights are never stored or committed to Git source control.
