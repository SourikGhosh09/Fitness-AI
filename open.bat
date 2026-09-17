@echo off
setlocal enabledelayedexpansion
title Fitness AI - One-Click Launcher
color 0B

set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

cls
echo ===============================================================================
echo                FITNESS AI - ONE-CLICK SYSTEM LAUNCHER
echo ===============================================================================
echo.
echo   [1/3] Launching Backend API Server (FastAPI on Port 8000)...
start "Fitness AI - Backend Server [Port 8000]" "%SCRIPT_DIR%\start_backend.bat"

echo   [2/3] Launching Mobile App (Expo Metro Bundler on Port 8081)...
start "Fitness AI - Mobile App [Expo Metro]" "%SCRIPT_DIR%\start_mobile.bat"

echo   [3/3] Opening Interactive API Documentation in Web Browser...
timeout /t 2 /nobreak >nul
start "" "http://localhost:8000/docs"

echo.
echo ===============================================================================
echo   SUCCESS: Fitness AI is now up and running!
echo.
echo   - Backend Server:   http://localhost:8000
echo   - Swagger Docs:     http://localhost:8000/docs (opened in your browser)
echo   - Mobile App Metro: Port 8081 (scan QR code in Mobile window with Expo Go)
echo.
echo   (Both services are running in their own console windows.)
echo   (To stop a service, simply close its console window.)
echo ===============================================================================
echo.
echo You may close this launcher window at any time. Press any key to exit.
pause >nul
exit /b 0
