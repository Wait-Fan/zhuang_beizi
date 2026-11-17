@echo off
rem Launch the current source project, using its bundled Python runtime.
if /I "%~1"=="--check" (
    call "%~dp0packing-system\tools\windows\start_realtime_dashboard_v3_clean.bat" --check
) else (
    call "%~dp0packing-system\tools\windows\start_realtime_dashboard_v3_clean.bat"
)
exit /b %ERRORLEVEL%
