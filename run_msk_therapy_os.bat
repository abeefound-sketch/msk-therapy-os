@echo off
setlocal
title MSK-Therapy-OS V1.0 Desktop Runtime Launcher
echo ===============================================================================
echo            MSK-Therapy-OS V1.0 - Desktop 1-Click Runtime Launcher
echo                Scope: ENGINEERING_RESEARCH_ONLY
echo ===============================================================================
echo.

cd /d "%~dp0"
set "PYTHONPATH=%~dp0"

echo [1/3] Kiem tra moi truong Python...
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Khong tim thay Python trong PATH. Vui long cai dat Python 3.10 tro len.
    pause
    exit /b 1
)

echo [2/3] Khoi dong MSK-Therapy-OS Local Server tai cong 8000...
start "" http://127.0.0.1:8000/sandbox/p21/index.html

echo [3/3] Dang chay may chu. Nhap Ctrl+C de dung may chu.
python -m msk_therapy_os.server --port 8000
pause
