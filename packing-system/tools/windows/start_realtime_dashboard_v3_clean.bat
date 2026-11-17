@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul

rem Use the bundled runtime first, with the current source project.
for %%I in ("%~dp0..\..") do set "PROJECT_DIR=%%~fI"
set "APP_ENTRY=%PROJECT_DIR%\ui\realtime_dashboard_v3_clean.py"
set "PY_EXE=%PROJECT_DIR%\..\PackingPortable\python\python.exe"
set "PY_ARGS="
set "PYTHONNOUSERSITE=1"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

if exist "%PY_EXE%" goto runtime_found
set "PY_EXE=python"
python -c "import yaml, pandas, ortools, pyqtgraph, OpenGL, openpyxl, requests; from PyQt5 import QtWidgets" >nul 2>&1
if not errorlevel 1 goto runtime_found
set "PY_EXE=py"
set "PY_ARGS=-3"
py -3 -c "import yaml, pandas, ortools, pyqtgraph, OpenGL, openpyxl, requests; from PyQt5 import QtWidgets" >nul 2>&1
if not errorlevel 1 goto runtime_found
echo [ERROR] No usable Python runtime found. Restore PackingPortable\python.
if /I not "%~1"=="--check" pause
exit /b 2

:runtime_found
if not exist "%APP_ENTRY%" (
    echo [ERROR] GUI entry point is missing.
    if /I not "%~1"=="--check" pause
    exit /b 3
)
pushd "%PROJECT_DIR%"
if errorlevel 1 exit /b 4
echo [INFO] Project: %PROJECT_DIR%
echo [INFO] Python: %PY_EXE% %PY_ARGS%
if /I "%~1"=="--check" goto check_only
"%PY_EXE%" %PY_ARGS% "%APP_ENTRY%" --project "%PROJECT_DIR%"
set "APP_EXIT=%ERRORLEVEL%"
popd
if not "%APP_EXIT%"=="0" (
    echo [ERROR] Application exited with code %APP_EXIT%.
    pause
)
exit /b %APP_EXIT%

:check_only
"%PY_EXE%" %PY_ARGS% -c "import sys, yaml, pandas, ortools, pyqtgraph, OpenGL, openpyxl, requests; from PyQt5 import QtWidgets; print('[OK] Dependencies loaded: ' + sys.executable)"
set "CHECK_EXIT=%ERRORLEVEL%"
if not "%CHECK_EXIT%"=="0" goto check_finished
"%PY_EXE%" %PY_ARGS% "%APP_ENTRY%" --help
set "CHECK_EXIT=%ERRORLEVEL%"
:check_finished
popd
exit /b %CHECK_EXIT%
