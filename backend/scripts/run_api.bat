@echo off
REM Start MethLab API - wrapper for run_api.ps1
REM Usage: scripts\run_api.bat [stop|status]

set SCRIPT_DIR=%~dp0

if "%1"=="stop" (
    powershell -ExecutionPolicy Bypass -File "%SCRIPT_DIR%run_api.ps1" -Stop
) else if "%1"=="status" (
    powershell -ExecutionPolicy Bypass -File "%SCRIPT_DIR%run_api.ps1" -Status
) else (
    powershell -ExecutionPolicy Bypass -File "%SCRIPT_DIR%run_api.ps1"
)
