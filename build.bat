@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo            CadenceSync Build Automation
echo ===================================================

:: 1. Verify Python installation
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python was not found on your system PATH.
    echo Please install Python 3.8 or higher, ensure it is added to PATH, and rerun this script.
    pause
    exit /b 1
)

echo [SUCCESS] Python environment detected.

:: 2. Setup/Validate Virtual Environment
if not exist .venv (
    echo [INFO] Creating Python virtual environment venv...
    python -m venv .venv
    if !ERRORLEVEL! neq 0 (
        echo [ERROR] Failed to create Python virtual environment.
        pause
        exit /b 1
    )
) else (
    echo [INFO] Virtual environment venv already exists.
)

:: 3. Activate venv and install dependencies
echo [INFO] Activating virtual environment...
call .venv\Scripts\activate.bat
if !ERRORLEVEL! neq 0 (
    echo [ERROR] Failed to activate virtual environment.
    pause
    exit /b 1
)

echo [INFO] Upgrading pip...
python -m pip install --upgrade pip

echo [INFO] Installing project dependencies from requirements.txt...
pip install -r requirements.txt
if !ERRORLEVEL! neq 0 (
    echo [ERROR] Failed to install project dependencies.
    pause
    exit /b 1
)

:: 4. Verify/Regenerate app icons
if not exist assets\icon.ico (
    echo [WARNING] assets\icon.ico not found! Regenerating icons...
    if not exist scripts\convert_icon.py (
        echo [ERROR] convert_icon.py helper script is missing from the scripts folder.
        pause
        exit /b 1
    )
    python scripts\convert_icon.py "C:\Users\acer\.gemini\antigravity\brain\14af601a-85ef-432d-a73e-bda11c7ad07d\cadence_sync_icon_1784044531224.jpg" "assets"
    if !ERRORLEVEL! neq 0 (
        echo [ERROR] Icon generation failed.
        pause
        exit /b 1
    )
)

:: 5. Compile executable using PyInstaller
echo [INFO] Compiling CadenceSync.exe with PyInstaller...
pyinstaller --noconsole --onefile --icon=assets/icon.ico --add-data "assets;assets" --name="CadenceSync" main.py
if !ERRORLEVEL! neq 0 (
    echo [ERROR] PyInstaller compilation failed.
    pause
    exit /b 1
)

echo ===================================================
echo [SUCCESS] CadenceSync compilation completed!
echo The standalone executable is located in:
echo   %~dp0dist\CadenceSync.exe
echo ===================================================
pause
