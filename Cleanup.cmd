@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Cleanup-BuildEnvironment.ps1"
if errorlevel 1 (
  echo.
  echo CLEANUP FAILED. Review the error above.
  pause
  exit /b 1
)
echo.
pause
