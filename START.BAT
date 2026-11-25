@echo off
title AI Watermark Remover — Genesis Glassmorphism Engine
echo ===================================================
echo   Starting AI Watermark Remover Engine ^& Web UI...
echo ===================================================

cd /d "%~dp0"
set PYTHONUTF8=1

if not exist "venv\Scripts\python.exe" (
    echo [WARNING] Virtual environment not found. Running setup.bat first...
    call setup.bat
)

echo [0/3] Running Launcher Bootstrap Validator...
.\venv\Scripts\python.exe scripts\bootstrap.py
if %errorlevel% neq 0 (
    echo [ERROR] Bootstrap failed. Please inspect logs.
    pause
    exit /b 1
)

echo [1/3] Booting FastAPI Neural Inpainting Backend on http://127.0.0.1:7860...
start "FastAPI Inpainting Backend" /min .\venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 7860

echo [2/3] Launching Genesis Next.js Glassmorphism Frontend (Software UI) on http://localhost:3000...
start "Next.js Software UI" /min cmd /c "cd web_ui && pnpm run dev"

echo [3/3] Launching Marketing Site on http://localhost:3003...
start "Next.js Marketing Site" /min cmd /c "cd marketing-site && pnpm run dev"

pause
