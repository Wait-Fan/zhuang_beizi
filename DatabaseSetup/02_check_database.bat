@echo off
setlocal
chcp 65001 >nul
set "PYTHONUTF8=1"
set "PACKING_PYTHON=%~dp0..\PackingPortable\python\python.exe"
if not exist "%PACKING_PYTHON%" (
  echo [ERROR] Put DatabaseSetup beside PackingPortable and packing-system.
  pause
  exit /b 1
)
"%PACKING_PYTHON%" "%~dp0initialize_database.py" --project "%~dp0..\packing-system"
if errorlevel 1 (
  echo [ERROR] Database check did not pass. Check the message above.
  pause
  exit /b 1
)
pause
