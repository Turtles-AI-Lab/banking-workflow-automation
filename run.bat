@echo off
REM Banking Workflow Automation - Quick Start Script for Windows

echo ====================================================
echo    Banking Workflow Automation Platform
echo ====================================================
echo.

REM Check Python version
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    echo Virtual environment created
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo.

REM Install dependencies
echo Installing dependencies...
pip install -q -r requirements.txt
echo Dependencies installed
echo.

REM Start the server
echo ====================================================
echo    Starting Banking Workflow Automation API
echo ====================================================
echo.
echo    Dashboard: http://localhost:8000
echo    API Docs:  http://localhost:8000/docs
echo    API JSON:  http://localhost:8000/openapi.json
echo.
echo    Press Ctrl+C to stop the server
echo ====================================================
echo.

cd backend
python app.py
