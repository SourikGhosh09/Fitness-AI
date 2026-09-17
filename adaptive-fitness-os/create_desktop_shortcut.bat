@echo off
setlocal
title Fitness AI - Create Desktop Shortcut
color 0B

echo ===============================================================================
echo                FITNESS AI - CREATE DESKTOP SHORTCUT
echo ===============================================================================
echo.

set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "TARGET_BAT=%SCRIPT_DIR%\open.bat"

powershell -NoProfile -ExecutionPolicy Bypass -Command "$ws = New-Object -ComObject WScript.Shell; $desktop = [System.Environment]::GetFolderPath('Desktop'); $sc = $ws.CreateShortcut((Join-Path $desktop 'Fitness AI.lnk')); $sc.TargetPath = '%TARGET_BAT%'; $sc.WorkingDirectory = '%SCRIPT_DIR%'; $sc.Description = 'One-Click Launcher for Fitness AI'; $sc.Save()"

if exist "%USERPROFILE%\Desktop\Fitness AI.lnk" (
    echo [SUCCESS] Shortcut created successfully on your Windows Desktop:
    echo           "%USERPROFILE%\Desktop\Fitness AI.lnk"
    echo.
    echo You can now double-click "Fitness AI" on your Desktop anytime to launch!
) else (
    echo [ERROR] Failed to create desktop shortcut.
)
echo.
pause
