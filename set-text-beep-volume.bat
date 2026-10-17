@echo off
setlocal EnableExtensions
cd /d "%~dp0"

rem TGAAC text-beep volume — Windows
rem Drop the text-beep-patcher folder into your TGAAC install, then double-click
rem this file, or run:  set-text-beep-volume.bat 0

set "SCRIPT=%~dp0set-text-beep-volume.py"

where py >nul 2>&1
if %ERRORLEVEL%==0 (
  py -3 "%SCRIPT%" %*
  goto :finish
)

where python >nul 2>&1
if %ERRORLEVEL%==0 (
  python "%SCRIPT%" %*
  goto :finish
)

where python3 >nul 2>&1
if %ERRORLEVEL%==0 (
  python3 "%SCRIPT%" %*
  goto :finish
)

echo error: Python 3 is required.
echo Install from https://www.python.org/downloads/
echo (check "Add python.exe to PATH" during setup)
set EXITCODE=1
goto :pause

:finish
set EXITCODE=%ERRORLEVEL%

:pause
echo.
if "%~1"=="" (
  echo Press any key to close...
  pause >nul
)
exit /b %EXITCODE%
