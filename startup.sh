#!/bin/bash
# startup.sh - Start frontend and all backend agents at once

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Emergency Triage System - Full Startup           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating Python virtual environment...${NC}"
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies if needed
if ! python -c "import fastapi" 2>/dev/null; then
    echo -e "${YELLOW}Installing Python dependencies...${NC}"
    pip install -r requirements.txt
fi

# Install frontend dependencies if needed
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing frontend dependencies...${NC}"
    npm install
fi

echo -e "${GREEN}✓ Environment ready${NC}"
echo ""
echo -e "${BLUE}Starting frontend and backend agents...${NC}"
echo -e "${YELLOW}Note: Frontend and each agent runs in the background${NC}"
echo ""

# Function to run agent in background
run_agent() {
    local name=$1
    local module=$2
    local port=$3
    echo -e "${GREEN}▶ Launching $name on port $port...${NC}"
    if [[ $name == "Resource Prediction" ]]; then
        nohup python agents/resource_pred.py > logs/resource_pred.log 2>&1 &
    else
        nohup uvicorn $module:app --reload --port $port > logs/${module##*/}.log 2>&1 &
    fi
}

# Create logs directory
mkdir -p logs

# Start frontend first
echo -e "${GREEN}▶ Launching Frontend (React + Vite) on port 5173...${NC}"
nohup npm run dev > logs/frontend.log 2>&1 &
sleep 3

# Start all backend agents
run_agent "Triage Agent" "agents.triage" 8000
run_agent "Resource Prediction Agent" "agents.resource_pred" 5002
run_agent "Allocation Agent" "agents.allocation" 8001
run_agent "Monitoring Agent" "agents.monitoring" 8002

sleep 2

echo ""
echo -e "${BLUE}═════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ All services started!${NC}"
echo ""
echo -e "${BLUE}Frontend:${NC}"
echo -e "  Web Dashboard     → http://localhost:5173"
echo ""
echo -e "${BLUE}API Endpoints:${NC}"
echo -e "  Triage Agent      → http://127.0.0.1:8000"
echo -e "  Resource Predict  → http://127.0.0.1:5002"
echo -e "  Allocation Agent  → http://127.0.0.1:8001"
echo -e "  Monitoring Agent  → http://127.0.0.1:8002"
echo ""
echo -e "${YELLOW}To view logs:${NC}"
echo -e "  tail -f logs/frontend.log"
echo -e "  tail -f logs/triage.log"
echo -e "  tail -f logs/resource_pred.log"
echo -e "  tail -f logs/allocation.log"
echo ""
echo -e "${YELLOW}To stop all services:${NC}"
echo -e "  pkill -f 'npm run dev'"
echo -e "  pkill -f 'uvicorn agents'"
echo "/════════════════════════════════════════════════════"
