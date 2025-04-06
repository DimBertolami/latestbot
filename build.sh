#!/bin/bash

# Exit on error
set -e

# Colors for output
RED=\033[0;31m
GREEN=\033[0;32m
YELLOW=\033[0;33m
NC=\033[0m

echo -e "${GREEN}Starting package build...${NC}"

echo -e "${YELLOW}Creating DEB package structure...${NC}"
mkdir -p pkg/DEBIAN
mkdir -p pkg/opt/cryptobot/{bin,lib,share}

# Copy files
echo -e "${YELLOW}Copying files...${NC}"
cp -r bin/* pkg/opt/cryptobot/bin/
cp -r lib/* pkg/opt/cryptobot/lib/
cp -r web/* pkg/opt/cryptobot/share/

echo -e "${YELLOW}Building DEB package...${NC}"
dpkg-deb --build pkg cryptobot.deb

# Create Flatpak build directory
echo -e "${YELLOW}Creating Flatpak build directory...${NC}"
mkdir -p flatpak-build

# Build Flatpak
echo -e "${YELLOW}Building Flatpak...${NC}"
flatpak-builder --force-clean flatpak-build org.cryptobot.App.json

# Create package archive
echo -e "${YELLOW}Creating package archive...${NC}"
tar -czf cryptobot-package.tar.gz cryptobot.deb flatpak-build

# Clean up
echo -e "${YELLOW}Cleaning up...${NC}"
rm -rf pkg flatpak-build

# Verify package
echo -e "${YELLOW}Verifying package...${NC}"
if [ -f cryptobot-package.tar.gz ]; then
    echo -e "${GREEN}Package created successfully!${NC}"
    echo -e "Package available at: ${YELLOW}cryptobot-package.tar.gz${NC}"
else
    echo -e "${RED}Failed to create package${NC}"
    exit 1
fi

echo -e "${GREEN}Build complete!${NC}"
