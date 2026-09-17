@echo off
setlocal enabledelayedexpansion
title Fitness AI - Control Center
color 0B

set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

:MENU
cls
echo ===============================================================================
echo                 FITNESS AI - CONTROL CENTER & LAUNCHER
echo ===============================================================================
echo.
echo   Please select an action:
echo.
echo   [1] ?? One-Click Launch (Backend Server + Mobile App + Open Docs in Browser)
echo   [2] ?? Launch Backend API Server Only (Port 8000 + Docs)
echo   [3] ?? Launch Mobile App Only (Expo Metro Bundler on Port 8081)
echo   [4] ?? Launch Notion Sync Worker (Background Worker, 300s interval)
echo   [5] ? Launch Everything (Backend + Mobile + Notion Worker + Docs)
echo   [6] ???  Create Desktop Shortcut (Put 1-Click icon on Windows Desktop)
echo   [7] ?? Open Project in VS Code
echo   [0] ? Exit
echo.
echo ===============================================================================
set /p "CHOICE=Enter your choice [1-7, 0]: "

if "%CHOICE%"=="1" (
    call "%SCRIPT_DIR%\open.bat"
    goto MENU
)
if "%CHOICE%"=="2" (
    start "Fitness AI - Backend Server [Port 8000]" "%SCRIPT_DIR%\start_backend.bat"
    timeout /t 2 /nobreak >nul
    start "" "http://localhost:8000/docs"
    goto MENU
)
if "%CHOICE%"=="3" (
    start "Fitness AI - Mobile App [Expo Metro]" "%SCRIPT_DIR%\start_mobile.bat"
    goto MENU
)
if "%CHOICE%"=="4" (
    start "Fitness AI - Notion Sync Worker" "%SCRIPT_DIR%\start_notion_sync.bat"
    goto MENU
)
if "%CHOICE%"=="5" (
    start "Fitness AI - Backend Server [Port 8000]" "%SCRIPT_DIR%\start_backend.bat"
    start "Fitness AI - Mobile App [Expo Metro]" "%SCRIPT_DIR%\start_mobile.bat"
    start "Fitness AI - Notion Sync Worker" "%SCRIPT_DIR%\start_notion_sync.bat"
    timeout /t 2 /nobreak >nul
    start "" "http://localhost:8000/docs"
    goto MENU
)
if "%CHOICE%"=="6" (
    call "%SCRIPT_DIR%\create_desktop_shortcut.bat"
    goto MENU
)
if "%CHOICE%"=="7" (
    code "%SCRIPT_DIR%"
    goto MENU
)
if "%CHOICE%"=="0" exit /b 0

echo Invalid choice. Please try again.
timeout /t 2 /nobreak >nul
goto MENU
