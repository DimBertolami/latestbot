#!/bin/bash
# CryptoBot Stop Script
# This script stops all CryptoBot processes

# Colors for terminal output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}     Stopping Crypto Trading Bot     ${NC}"
echo -e "${GREEN}======================================${NC}"

# Get the directory of the script
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ROOT_DIR=$(dirname "$SCRIPT_DIR")
PID_FILE="${ROOT_DIR}/.running.pid"

# Try to use the PID file if it exists
if [ -f "$PID_FILE" ]; then
    echo -e "${YELLOW}Found running processes...${NC}"
    source "$PID_FILE"
    
    # Stop backend process
    if [ ! -z "$BACKEND_PID" ] && ps -p $BACKEND_PID > /dev/null; then
        echo -e "${YELLOW}Stopping backend process (PID: $BACKEND_PID)...${NC}"
        kill $BACKEND_PID
        sleep 2
        # Force kill if still running
        if ps -p $BACKEND_PID > /dev/null; then
            echo -e "${YELLOW}Force stopping backend process...${NC}"
            kill -9 $BACKEND_PID
        fi
        echo -e "${GREEN}✓ Backend stopped${NC}"
    else
        echo -e "${YELLOW}Backend process not found or already stopped${NC}"
    fi
    
    # Stop frontend process
    if [ ! -z "$FRONTEND_PID" ] && ps -p $FRONTEND_PID > /dev/null; then
        echo -e "${YELLOW}Stopping frontend process (PID: $FRONTEND_PID)...${NC}"
        kill $FRONTEND_PID
        sleep 2
        # Force kill if still running
        if ps -p $FRONTEND_PID > /dev/null; then
            echo -e "${YELLOW}Force stopping frontend process...${NC}"
            kill -9 $FRONTEND_PID
        fi
        echo -e "${GREEN}✓ Frontend stopped${NC}"
    else
        echo -e "${YELLOW}Frontend process not found or already stopped${NC}"
    fi
    
    # Remove PID file
    rm "$PID_FILE"
else
    echo -e "${YELLOW}No PID file found. Searching for running processes...${NC}"
    
    # Check backend port (5001)
    if lsof -Pi :5001 -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${YELLOW}Found backend process running on port 5001...${NC}"
        PID=$(lsof -t -i:5001)
        echo -e "${YELLOW}Stopping process with PID: $PID...${NC}"
        kill -9 $PID
        sleep 2
        echo -e "${GREEN}✓ Backend stopped${NC}"
    else
        echo -e "${YELLOW}No backend process found running on port 5001${NC}"
    fi
    
    # Check frontend ports (default is 5173, but it might use up to 5179 if ports are taken)
    FRONTEND_STOPPED=false
    for PORT in {5173..5179}; do
        if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
            echo -e "${YELLOW}Found frontend process running on port $PORT...${NC}"
            PID=$(lsof -t -i:$PORT)
            echo -e "${YELLOW}Stopping process with PID: $PID...${NC}"
            kill -9 $PID
            sleep 1
            FRONTEND_STOPPED=true
            echo -e "${GREEN}✓ Frontend stopped${NC}"
        fi
    done
    
    if [ "$FRONTEND_STOPPED" = false ] ; then
        echo -e "${YELLOW}No frontend process found running on ports 5173-5179${NC}"
    fi
fi

echo -e "\n${GREEN}All CryptoBot processes have been stopped.${NC}"
