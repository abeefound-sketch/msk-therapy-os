@echo off
title MSK-Therapy-OS - 3D MSK Studio Launcher
cd /d "%~dp0"

echo ========================================================================
echo               MSK-THERAPY-OS: 3D EDUCATION STUDIO
echo ========================================================================
echo [1/2] Dang kiem tra moi truong Python...

where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo.
    echo [LOI] Khong tim thay Python tren he thong!
    echo Vui long cai dat Python 3.10 tro len va tick chon "Add Python to PATH".
    echo.
    pause
    exit /b 1
)

echo [2/2] Dang khoi dong may chu noi bo va mo trinh duyet 3D...
echo.
python start_app.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo [!] Ung dung da dung lai.
    pause
)
