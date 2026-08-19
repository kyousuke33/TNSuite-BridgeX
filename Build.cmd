@echo off
setlocal
cd /d "%~dp0"
echo.
echo =====================================================================
echo   TNSuite BridgeX  v0.5-Build12-Hotfix16 Full  - Windows x64
echo =====================================================================
echo.
echo GUI       : redesigned BridgeX UI + Light/Dark + EN/VI + Automation
echo CLI       : SFTP batch automation via Windows OpenSSH
echo Installer : branded NSIS setup + Start Menu + uninstall
echo.
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0Build-TNSuiteBridgeX.ps1"
set "EXITCODE=%ERRORLEVEL%"
if not "%EXITCODE%"=="0" (
  echo.
  echo BUILD FAILED with exit code %EXITCODE%.
  echo If present, send dist\TNSuiteBridgeX_260818_v0.5-Build12-Hotfix16-Full-compile.log for diagnosis.
  echo Otherwise send the first ERROR section shown above.
  pause
  exit /b %EXITCODE%
)
echo.
echo BUILD COMPLETE.
pause
endlocal
