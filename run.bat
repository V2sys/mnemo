@echo off
cd /d "%~dp0"
if exist ".venv312\Scripts\activate.bat" (
    call .venv312\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    echo No virtual environment found.
    echo Run: python install.py
    pause
    exit /b 1
)
python -m mnemo
pause
