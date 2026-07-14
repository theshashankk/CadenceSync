@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo             CadenceSync Direct Run Script
echo ===================================================

:: 1. Verify Python installation
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python was not found on your system PATH.
    echo Please install Python 3.8 or higher, ensure it is added to PATH, and rerun this script.
    pause
    exit /b 1
)

:: 2. Setup/Validate Virtual Environment if missing
if not exist .venv (
    echo [WARNING] Virtual environment venv was not found!
    echo Running build.bat to set up environment first...
    call build.bat
    if !ERRORLEVEL! neq 0 (
        echo [ERROR] Failed to set up build environment.
        pause
        exit /b 1
    )
)

:: 3. Verify/Regenerate app icons if missing
if not exist assets\icon.png (
    echo [WARNING] assets\icon.png not found. Generating...
    python scripts\convert_icon.py "C:\Users\acer\.gemini\antigravity\brain\14af601a-85ef-432d-a73e-bda11c7ad07d\cadence_sync_icon_1784044531224.jpg" "assets"
)

:: 4. Activate venv and run main.py
echo [INFO] Activating virtual environment...
call .venv\Scripts\activate.bat
if !ERRORLEVEL! neq 0 (
    echo [ERROR] Failed to activate virtual environment.
    pause
    exit /b 1
)

echo [INFO] Launching CadenceSync directly from Python...
echo (Check the system tray icon to interact with the app. Logs are written to cadence_sync.log)
python main.py
if !ERRORLEVEL! neq 0 (
    echo [WARNING] Application terminated with exit code !ERRORLEVEL!.
    pause
)
