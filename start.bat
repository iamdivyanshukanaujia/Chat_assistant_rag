@echo off
REM Quick Start Script for University Student Assistant
REM Windows Batch Script

echo ============================================================
echo University Student Information Assistant - Quick Start
echo ============================================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo [1/5] Creating virtual environment...
    python -m venv venv
) else (
    echo [1/5] Virtual environment already exists
)

echo [2/5] Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/5] Installing dependencies...
pip install -r requirements.txt --quiet

echo [4/5] Checking prerequisites...
echo.
echo Checking Redis...
redis-cli ping >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Redis is not running! Please start Redis server.
    echo Download from: https://github.com/tporadowski/redis/releases
    echo.
)

echo Checking Ollama...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Ollama is not running! Please start Ollama.
    echo Download from: https://ollama.ai/
    echo Then run: ollama pull mistral
    echo.
)

echo [5/5] Starting FastAPI backend...
echo.
echo Backend will start on http://localhost:8000
echo.
echo To start the Streamlit UI in another terminal, run:
echo    streamlit run frontend/app.py
echo.

python -m backend.main
