@echo off
REM Quick Test Script for No-DB API (Windows)
REM ===========================================

echo ========================================
echo  Quick Test - No-DB File Management API
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python 3.11+
    pause
    exit /b 1
)

REM Change to project directory
cd /d "%~dp0.."

echo [1/3] Checking dependencies...
python -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo [WARN] requests not installed, installing...
    pip install requests
)

echo [2/3] Checking if server is running...
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo [WARN] Server not running!
    echo.
    echo Please start the server first:
    echo   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    echo.
    echo Or in a new terminal:
    echo   cd roster-mapper
    echo   .venv\Scripts\activate
    echo   uvicorn app.main:app --reload
    echo.
    pause
    exit /b 1
)

echo [OK] Server is running!
echo.

echo [3/3] Running tests...
echo.

REM Run test script
python scripts\test_no_db_api.py

echo.
echo ========================================
echo  Test completed!
echo ========================================
pause

