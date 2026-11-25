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

echo [0/2] Running Launcher Bootstrap Validator...
.\venv\Scripts\python.exe scripts\bootstrap.py
if %errorlevel% neq 0 (
    echo [ERROR] Bootstrap failed. Please inspect logs.
    pause
    exit /b 1
)

echo [1/2] Booting FastAPI Neural Inpainting Backend on http://127.0.0.1:7860...
start "FastAPI Inpainting Backend" /min .\venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 7860

echo [2/2] Launching Genesis Next.js Glassmorphism Frontend on http://localhost:3000...
cd web_ui
npm run dev

pause
