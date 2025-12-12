#!/bin/bash
# Quick Test Script for No-DB API (Linux/Mac)
# ============================================

echo "========================================"
echo " Quick Test - No-DB File Management API"
echo "========================================"
echo

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 not found! Please install Python 3.11+"
    exit 1
fi

# Change to project directory
cd "$(dirname "$0")/.."

echo "[1/3] Checking dependencies..."
if ! python3 -c "import requests" 2>/dev/null; then
    echo "[WARN] requests not installed, installing..."
    pip install requests
fi

echo "[2/3] Checking if server is running..."
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "[WARN] Server not running!"
    echo
    echo "Please start the server first:"
    echo "  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
    echo
    echo "Or in a new terminal:"
    echo "  cd roster-mapper"
    echo "  source .venv/bin/activate"
    echo "  uvicorn app.main:app --reload"
    echo
    exit 1
fi

echo "[OK] Server is running!"
echo

echo "[3/3] Running tests..."
echo

# Run test script
python3 scripts/test_no_db_api.py

echo
echo "========================================"
echo " Test completed!"
echo "========================================"

