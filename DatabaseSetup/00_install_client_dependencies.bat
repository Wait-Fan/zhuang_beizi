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
"%PACKING_PYTHON%" -m pip install "PyMySQL[rsa]" PyYAML
if errorlevel 1 (
  echo [ERROR] Client dependencies were not installed. Check the message above.
  pause
  exit /b 1
)
echo [OK] Python client dependencies are ready. This does not install MySQL Server.
pause
