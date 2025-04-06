#!/bin/bash
# CryptoBot Start Script
# This script starts the backend API and frontend server

# Colors for terminal output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}     Starting Crypto Trading Bot     ${NC}"
echo -e "${GREEN}======================================${NC}"

# Get the directory of the script
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ROOT_DIR=$(dirname "$SCRIPT_DIR")
BACKEND_DIR="${ROOT_DIR}/src/backend"
FRONTEND_DIR="${ROOT_DIR}/src/frontend"
LOGS_DIR="${ROOT_DIR}/logs"
CONFIG_DIR="${ROOT_DIR}/config"
DATA_DIR="${ROOT_DIR}/data"

# Make sure all directories exist
mkdir -p "$LOGS_DIR"
mkdir -p "$CONFIG_DIR"
mkdir -p "$DATA_DIR"

# Activate Python virtual environment
source "${ROOT_DIR}/venv/bin/activate"

# Check for existing processes and stop them if necessary
echo -e "${YELLOW}Checking for existing processes...${NC}"

# Check backend port (5001)
if lsof -Pi :5001 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${YELLOW}Port 5001 is already in use. Stopping existing process...${NC}"
    PID=$(lsof -t -i:5001)
    kill -9 $PID
    sleep 2
    echo -e "${GREEN}✓ Stopped process on port 5001${NC}"
fi

# Check frontend port (default is 5173, but it might use up to 5179 if ports are taken)
for PORT in {5173..5179}; do
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${YELLOW}Port $PORT is already in use. Stopping existing process...${NC}"
        PID=$(lsof -t -i:$PORT)
        kill -9 $PID
        sleep 1
        echo -e "${GREEN}✓ Stopped process on port $PORT${NC}"
    fi
done

# Start backend server
echo -e "${GREEN}Starting backend server...${NC}"
cd "$BACKEND_DIR"
python api.py > "${LOGS_DIR}/backend.log" 2>&1 &
BACKEND_PID=$!

# Check if backend started successfully
sleep 3
if ! ps -p $BACKEND_PID > /dev/null; then
    echo -e "${RED}Failed to start backend server! Check ${LOGS_DIR}/backend.log for details.${NC}"
    exit 1
fi

# Test if the backend server is actually responding
echo -e "${YELLOW}Verifying backend server connection...${NC}"
MAX_RETRIES=10
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s "http://localhost:5001/trading/status" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend server is responding correctly${NC}"
        break
    else
        RETRY_COUNT=$((RETRY_COUNT+1))
        if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
            echo -e "${RED}Backend server is not responding after $MAX_RETRIES attempts!${NC}"
            echo -e "${YELLOW}Checking backend log file for errors...${NC}"
            tail -n 20 "${LOGS_DIR}/backend.log"
            echo -e "${RED}Stopping due to backend issues...${NC}"
            exit 1
        fi
        echo -e "${YELLOW}Backend not responding yet, retrying in 2 seconds... ($RETRY_COUNT/$MAX_RETRIES)${NC}"
        sleep 2
    fi
done

# Start frontend server
echo -e "${GREEN}Starting frontend server...${NC}"
cd "$FRONTEND_DIR"
npm run dev > "${LOGS_DIR}/frontend.log" 2>&1 &
FRONTEND_PID=$!

# Check if frontend started successfully
sleep 5
if ! ps -p $FRONTEND_PID > /dev/null; then
    echo -e "${RED}Failed to start frontend server! Check ${LOGS_DIR}/frontend.log for details.${NC}"
    echo -e "${YELLOW}Last 20 lines of frontend log:${NC}"
    tail -n 20 "${LOGS_DIR}/frontend.log"
    exit 1
fi

# Wait for Vite server to be ready
echo -e "${YELLOW}Waiting for frontend server to be ready...${NC}"
MAX_WAIT=30
counter=0
while [ $counter -lt $MAX_WAIT ]; do
    if grep -q "ready in" "${LOGS_DIR}/frontend.log"; then
        # Extract the port from the frontend log
        FRONTEND_PORT=$(grep "Local:" "${LOGS_DIR}/frontend.log" | grep -oE 'http://localhost:[0-9]+' | cut -d ':' -f 3)
        if [ -z "$FRONTEND_PORT" ]; then
            FRONTEND_PORT=5173 # Default port if not found
        fi
        echo -e "${GREEN}✓ Frontend server started on port $FRONTEND_PORT (PID: $FRONTEND_PID)${NC}"
        break
    fi
    counter=$((counter+1))
    sleep 1
    if [ $counter -eq $MAX_WAIT ]; then
        echo -e "${YELLOW}Frontend server may still be starting up. Continuing anyway.${NC}"
        echo -e "${YELLOW}Last 20 lines of frontend log:${NC}"
        tail -n 20 "${LOGS_DIR}/frontend.log"
        FRONTEND_PORT=5173 # Assume default port
    fi
done

# Save PIDs to file for stop script
echo "BACKEND_PID=$BACKEND_PID" > "${ROOT_DIR}/.running.pid"
echo "FRONTEND_PID=$FRONTEND_PID" >> "${ROOT_DIR}/.running.pid"

# Print success message and URLs
echo -e "\n${GREEN}Crypto Trading Bot is now running!${NC}"
echo -e "${GREEN}------------------------------------${NC}"
echo -e "Backend API: http://localhost:5001/trading"
echo -e "Frontend UI: http://localhost:$FRONTEND_PORT"
echo
echo -e "${YELLOW}To access the Trading Dashboard, open your browser and navigate to:${NC}"
echo -e "${GREEN}http://localhost:$FRONTEND_PORT${NC}"
echo
echo -e "${YELLOW}To stop the servers, run:${NC}"
echo -e "${GREEN}./scripts/stop.sh${NC}"
echo
