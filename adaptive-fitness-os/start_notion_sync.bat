@echo off
setlocal enabledelayedexpansion
title Fitness AI - Notion Sync Worker
color 0D

echo ===============================================================================
echo                   FITNESS AI - NOTION SYNC WORKER
echo ===============================================================================
echo.

set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

if exist "%SCRIPT_DIR%\adaptive-fitness-os\backend" (
    set "PROJECT_ROOT=%SCRIPT_DIR%\adaptive-fitness-os"
) else if exist "%SCRIPT_DIR%\backend" (
    set "PROJECT_ROOT=%SCRIPT_DIR%"
) else (
    echo [ERROR] Backend directory not found!
    pause
    exit /b 1
)

set "BACKEND_DIR=%PROJECT_ROOT%\backend"

if exist "%PROJECT_ROOT%\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%PROJECT_ROOT%\.venv\Scripts\python.exe"
) else if exist "%SCRIPT_DIR%\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%SCRIPT_DIR%\.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

if exist "%PROJECT_ROOT%\fitness.db" (
    set "DB_FILE=%PROJECT_ROOT%\fitness.db"
) else if exist "%SCRIPT_DIR%\fitness.db" (
    set "DB_FILE=%SCRIPT_DIR%\fitness.db"
) else (
    set "DB_FILE=%PROJECT_ROOT%\fitness.db"
)

set "DB_FILE_SLASH=%DB_FILE:\=/%"
set "DATABASE_URL=sqlite:///%DB_FILE_SLASH%"

echo  [*] Project Root: %PROJECT_ROOT%
echo  [*] Backend Dir:  %BACKEND_DIR%
echo  [*] Python Path:  %PYTHON_EXE%
echo  [*] Database:     %DB_FILE%
echo.
echo  -----------------------------------------------------------------------------
echo  Running Notion Synchronizer (checks every 5 minutes / 300 seconds)...
echo  See START-HERE-NOTION.txt for configuration requirements.
echo  Press CTRL+C anytime to stop.
echo  -----------------------------------------------------------------------------
echo.

cd /d "%BACKEND_DIR%"
"%PYTHON_EXE%" -m fitness.notion_worker --interval-seconds 300

if errorlevel 1 (
    echo.
    echo [ERROR] Notion Sync Worker stopped with error code %errorlevel%.
    pause
)
