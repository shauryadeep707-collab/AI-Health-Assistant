@echo off
echo =========================================
echo   AI Health Assistant - Starting...
echo =========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt --quiet

REM Copy .env.example to .env if .env doesn't exist
if not exist ".env" (
    echo Creating .env from .env.example...
    copy .env.example .env >nul
    echo Please edit .env with your settings, or run: python scripts/setup_wizard.py
)

REM Start the application
echo.
echo Starting AI Health Assistant...
echo Open http://localhost:5000 in your browser
echo.
python run.py
