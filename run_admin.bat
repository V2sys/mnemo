@echo off
cd /d "%~dp0"
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Requesting administrator privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)
if exist ".venv312\Scripts\activate.bat" (
    call .venv312\Scripts\activate.bat
) else (
    call .venv\Scripts\activate.bat
)
python -m mnemo
