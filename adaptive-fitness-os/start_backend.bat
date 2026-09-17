@echo off
setlocal enabledelayedexpansion
title Fitness AI - Backend Server [Port 8000]
color 0A

echo ===============================================================================
echo                   FITNESS AI - BACKEND API SERVER
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
    echo Please make sure this file is inside your Fitness AI project folder.
    echo.
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
echo  Starting FastAPI on http://localhost:8000 ...
echo  Interactive Swagger Documentation: http://localhost:8000/docs
echo  Press CTRL+C anytime to stop the server.
echo  -----------------------------------------------------------------------------
echo.

cd /d "%BACKEND_DIR%"
"%PYTHON_EXE%" -m uvicorn fitness.api:app --host 0.0.0.0 --port 8000

if errorlevel 1 (
    echo.
    echo [ERROR] Backend server stopped unexpectedly with error code %errorlevel%.
    pause
)
