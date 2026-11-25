@echo off
title AI Watermark Remover - Setup
echo ===================================================
echo   AI Watermark Remover & Background Preserver Setup
echo ===================================================
echo.

cd /d "%~dp0"
set PYTHONUTF8=1

:: Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python was not found in PATH. Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

:: Create Virtual Environment if missing
if not exist "venv" (
    echo [1/3] Creating local virtual environment (venv)...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
) else (
    echo [1/3] Virtual environment already exists.
)

:: Upgrade pip and install dependencies
echo [2/3] Installing/upgrading dependencies from requirements.txt...
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\python.exe -m pip install -r requirements.txt

:: Run Environment & Hardware Diagnostic
echo.
echo [3/3] Running Environment Diagnostic...
.\venv\Scripts\python.exe scripts\env_check.py

echo.
echo ===================================================
echo   Setup completed successfully!
echo   Run Start_AI_Remover.bat to launch the application.
echo ===================================================
pause
