@echo off
setlocal

cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" arduino_gui_controller.py
) else (
    python arduino_gui_controller.py
)

endlocal
