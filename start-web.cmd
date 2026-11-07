@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\hpa.exe" (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\install-web.ps1"
) else (
  ".venv\Scripts\hpa.exe" web
)
if errorlevel 1 pause
