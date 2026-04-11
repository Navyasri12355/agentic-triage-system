@echo off
REM startup.bat - Start all backend agents and frontend on Windows

echo.
echo ╔════════════════════════════════════════════════════╗
echo ║   Emergency Triage System - Full Startup           ║
echo ╚════════════════════════════════════════════════════╝
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies if needed
python -m pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo Installing Python dependencies...
    pip install -r requirements.txt
)

REM Install frontend dependencies if needed
if not exist "node_modules" (
    echo Installing frontend dependencies...
    call npm install
)

echo ✓ Environment ready
echo.
echo Starting frontend and backend agents...
echo Note: Frontend and each agent runs in a separate command prompt window
echo.

REM Create logs directory
if not exist "logs" mkdir logs

REM Start frontend in a separate window
echo ▶ Launching Frontend (React + Vite) on port 5173...
start "Frontend (5173)" cmd /k "npm run dev"

timeout /t 3 /nobreak

REM Start all agents in separate windows
echo ▶ Launching Triage Agent on port 8000...
start "Triage Agent (8000)" cmd /k "venv\Scripts\activate && uvicorn agents.triage:app --reload --port 8000"

timeout /t 2 /nobreak

echo ▶ Launching Resource Prediction Agent on port 5002...
start "Resource Agent (5002)" cmd /k "venv\Scripts\activate && python agents/resource_pred.py"

timeout /t 2 /nobreak

echo ▶ Launching Allocation Agent on port 8001...
start "Allocation Agent (8001)" cmd /k "venv\Scripts\activate && uvicorn agents.allocation:app --reload --port 8001"

timeout /t 2 /nobreak

echo ▶ Launching Monitoring Agent on port 8002...
start "Monitoring Agent (8002)" cmd /k "venv\Scripts\activate && uvicorn agents.monitoring:app --reload --port 8002"

echo.
echo ═════════════════════════════════════════════════════
echo ✓ All services started!
echo.
echo Frontend:
echo    Web Dashboard     ^> http://localhost:5173
echo.
echo API Endpoints:
echo    Triage Agent      ^> http://127.0.0.1:8000
echo    Resource Predict  ^> http://127.0.0.1:5002
echo    Allocation Agent  ^> http://127.0.0.1:8001
echo    Monitoring Agent  ^> http://127.0.0.1:8002
echo.
echo ═════════════════════════════════════════════════════
pause
