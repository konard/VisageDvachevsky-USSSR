@echo off
REM USSR Leaders Platform - Startup Script for Windows

echo Starting USSR Leaders Platform...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r backend\requirements.txt

REM Check if videos directory exists
if not exist "videos" (
    echo Warning: videos directory not found. Please add video files (1.mp4 - 7.mp4) to the videos directory.
)

REM Run the application
echo Starting Flask application...
python backend\app.py
