# Process Tree & Lock Audit Specification

This document details the single-process tree architecture and clean shutdown mechanics designed to prevent process locks, orphan processes, or duplicate server instances.

---

## 🌳 Controlled Single-Process Tree Architecture

```
Launcher (Start_AI_Remover.bat / start.sh)
 ├── Backend Process (Python FastAPI / app.py) — Port 7860
 └── Frontend Process (Next.js Node Dev/Prod) — Port 3000
```

---

## 🛡️ Lock & Orphan Process Controls

1. **Dev Lock Auto-Cleanup**:
   The launcher scripts automatically detect and purge stale `.next/dev/lock` files prior to starting the frontend dev server.

2. **Clean Port Binding**:
   - Backend binds strictly to `127.0.0.1:7860`.
   - Frontend binds to `http://localhost:3000`.

3. **Graceful Signal Shutdown**:
   Closing the launcher window or issuing `CTRL+C` terminates both the child Node process and python process cleanly without leaving zombie instances in Task Manager.
