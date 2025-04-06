#!/bin/bash

# Exit on error
set -e

# Colors for output
RED=\033[0;31m
GREEN=\033[0;32m
YELLOW=\033[0;33m
NC=\033[0m

echo -e "${GREEN}Starting CryptoBot installation...${NC}"

echo -e "${YELLOW}Updating system packages...${NC}"
sudo apt update && sudo apt upgrade -y

# Install system dependencies
echo -e "${YELLOW}Installing system dependencies...${NC}"
sudo apt install -y \
    python3-pip \
    python3-venv \
    nodejs \
    npm \
    apache2 \
    mariadb-server \
    build-essential \
    git \
    jq

# Create directories
echo -e "${YELLOW}Setting up directories...${NC}"
sudo mkdir -p /opt/cryptobot/{data,logs,models}
sudo mkdir -p /etc/cryptobot/{config,strategies}

# Clone repository if not exists
echo -e "${YELLOW}Cloning repository...${NC}"
if [ ! -d "/opt/cryptobot/src" ]; then
    sudo git clone https://github.com/yourusername/cryptobot.git /opt/cryptobot/src
fi

# Create virtual environment and install Python dependencies
echo -e "${YELLOW}Setting up Python environment...${NC}"
sudo python3 -m venv /opt/cryptobot/venv
source /opt/cryptobot/venv/bin/activate
sudo pip install -r /opt/cryptobot/src/requirements.txt

# Install Node.js dependencies
echo -e "${YELLOW}Installing frontend dependencies...${NC}"
cd /opt/cryptobot/src/frontend
sudo npm install

# Configure Apache
echo -e "${YELLOW}Configuring web server...${NC}"
sudo cp /opt/cryptobot/src/web/cryptobot.conf /etc/apache2/sites-available/
sudo a2ensite cryptobot
sudo a2enmod proxy proxy_http proxy_wstunnel
sudo systemctl restart apache2

# Configure database
echo -e "${YELLOW}Setting up database...${NC}"
sudo mysql < /opt/cryptobot/src/db/schema.sql

# Create systemd service
echo -e "${YELLOW}Setting up system service...${NC}"
sudo cp /opt/cryptobot/src/scripts/cryptobot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable cryptobot

# Create log rotation
echo -e "${YELLOW}Setting up log rotation...${NC}"
sudo cp /opt/cryptobot/src/scripts/cryptobot.logrotate /etc/logrotate.d/cryptobot

# Create resource manager service
echo -e "${YELLOW}Setting up resource manager...${NC}"
sudo cp /opt/cryptobot/src/scripts/resource_manager_service.sh /opt/cryptobot/bin/
chmod +x /opt/cryptobot/bin/resource_manager_service.sh

# Create startup script
echo -e "${YELLOW}Setting up startup script...${NC}"
sudo cp /opt/cryptobot/src/scripts/startup.sh /opt/cryptobot/bin/
chmod +x /opt/cryptobot/bin/startup.sh

# Create troubleshooting script
echo -e "${YELLOW}Setting up troubleshooting script...${NC}"
sudo cp /opt/cryptobot/src/scripts/troubleshoot_backend.sh /opt/cryptobot/bin/
chmod +x /opt/cryptobot/bin/troubleshoot_backend.sh

# Create paper trading script
echo -e "${YELLOW}Setting up paper trading...${NC}"
sudo cp /opt/cryptobot/src/scripts/paper_trading_cli.py /opt/cryptobot/bin/
chmod +x /opt/cryptobot/bin/paper_trading_cli.py

# Create configuration files
echo -e "${YELLOW}Setting up configuration...${NC}"
sudo cp /opt/cryptobot/src/config/* /etc/cryptobot/config/

# Set permissions
echo -e "${YELLOW}Setting permissions...${NC}"
sudo chown -R www-data:www-data /opt/cryptobot/{data,logs}
sudo chmod -R 755 /opt/cryptobot/bin

# Start services
echo -e "${YELLOW}Starting services...${NC}"
sudo systemctl start cryptobot
sudo systemctl start mariadb

# Create package management files
echo -e "${YELLOW}Setting up package management...${NC}"
sudo mkdir -p /opt/cryptobot/pkg
sudo cp /opt/cryptobot/src/pkg/* /opt/cryptobot/pkg/

# Create deb package
echo -e "${YELLOW}Creating DEB package...${NC}"
sudo dpkg-deb --build /opt/cryptobot/pkg /opt/cryptobot/pkg/cryptobot.deb

# Create Flatpak manifest
echo -e "${YELLOW}Creating Flatpak manifest...${NC}"
sudo cp /opt/cryptobot/src/flatpak/* /opt/cryptobot/pkg/

# Create PPA
echo -e "${YELLOW}Setting up PPA...${NC}"
sudo add-apt-repository ppa:cryptobot/ppa
sudo apt update

# Install package
echo -e "${YELLOW}Installing package...${NC}"
sudo apt install /opt/cryptobot/pkg/cryptobot.deb

# Verify installation
echo -e "${YELLOW}Verifying installation...${NC}"
if systemctl is-active --quiet cryptobot; then
    echo -e "${GREEN}CryptoBot is running successfully!${NC}"
else
    echo -e "${RED}Failed to start CryptoBot service${NC}"
fi

echo -e "${GREEN}Installation complete!${NC}"
echo -e "Access the web interface at: https://your-domain/cryptobot"
echo -e "Use the CLI with: cryptobot [command]"
echo -e "View logs with: journalctl -u cryptobot"
