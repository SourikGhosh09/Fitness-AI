@echo off
setlocal enabledelayedexpansion
title Fitness AI - Mobile App [Expo Metro]
color 0E

echo ===============================================================================
echo                   FITNESS AI - MOBILE APP (EXPO)
echo ===============================================================================
echo.

set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

if exist "%SCRIPT_DIR%\adaptive-fitness-os\apps\mobile" (
    set "PROJECT_ROOT=%SCRIPT_DIR%\adaptive-fitness-os"
) else if exist "%SCRIPT_DIR%\apps\mobile" (
    set "PROJECT_ROOT=%SCRIPT_DIR%"
) else (
    echo [ERROR] Mobile directory not found!
    echo Please make sure this file is inside your Fitness AI project folder.
    echo.
    pause
    exit /b 1
)

set "MOBILE_DIR=%PROJECT_ROOT%\apps\mobile"

echo  [*] Project Root: %PROJECT_ROOT%
echo  [*] Mobile Dir:   %MOBILE_DIR%
echo.
echo  -----------------------------------------------------------------------------
echo  Starting Expo Metro Bundler on port 8081...
echo  - Scan the QR code using Expo Go on your mobile phone.
echo  - Press 'a' to open Android emulator (if installed).
echo  - Press 'w' to open in Web browser.
echo  - Press 'r' to reload the app.
echo  - Press CTRL+C to stop the bundler.
echo  -----------------------------------------------------------------------------
echo.

cd /d "%MOBILE_DIR%"
call npx expo start

if errorlevel 1 (
    echo.
    echo [ERROR] Expo bundler stopped unexpectedly with error code %errorlevel%.
    pause
)
