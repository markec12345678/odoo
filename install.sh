#!/usr/bin/env bash
#
# One-click install script for SI/HR Tourism Suite
# Usage: curl -fsSL https://raw.githubusercontent.com/markec12345678/odoo/19.0/install.sh | bash
#
set -euo pipefail

BOLD='\033[1m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
NC='\033[0m'

echo -e "${BOLD}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║   SI/HR Tourism Suite for Odoo 19 — Installer        ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════════════════════╝${NC}"
echo ""

# Check prerequisites
echo -e "${BLUE}📋 Checking prerequisites...${NC}"
check_cmd() {
    if command -v "$1" &>/dev/null; then
        echo -e "  ${GREEN}✓${NC} $1 found"
    else
        echo -e "  ${YELLOW}✗${NC} $1 not found — installing..."
        return 1
    fi
}

MISSING=0
check_cmd git || MISSING=1
check_cmd python3 || MISSING=1
check_cmd docker || MISSING=1
check_cmd docker || MISSING=1

if [ "$MISSING" -eq 1 ]; then
    echo ""
    echo -e "${YELLOW}Please install missing prerequisites and re-run.${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}📥 Cloning repository...${NC}"
git clone -b 19.0 https://github.com/markec12345678/odoo.git si-hr-odoo 2>/dev/null || {
    echo "  Directory si-hr-odoo already exists, using existing clone"
}
cd si-hr-odoo

echo ""
echo -e "${BLUE}🐳 Starting Docker Compose (Odoo + PostgreSQL)...${NC}"
echo "  This will:"
echo "    1. Pull Odoo 19 image with SI/HR modules"
echo "    2. Start PostgreSQL 16 database"
echo "    3. Initialize Odoo with base module"
echo "    4. Make Odoo available at http://localhost:8069"
echo ""
echo -e "${YELLOW}  First startup takes 3-5 minutes for DB initialization.${NC}"
echo ""

docker compose -f docker-compose.prod.yml up -d

echo ""
echo -e "${GREEN}✅ Installation started!${NC}"
echo ""
echo -e "${BOLD}Odoo will be available at:${NC} http://localhost:8069"
echo -e "${BOLD}Default credentials:${NC} admin / admin"
echo ""
echo "Useful commands:"
echo "  docker compose -f docker-compose.prod.yml logs -f    # View logs"
echo "  docker compose -f docker-compose.prod.yml down       # Stop"
echo "  docker compose -f docker-compose.prod.yml up -d      # Start again"
echo ""
echo -e "${BLUE}To install SI/HR modules:${NC}"
echo "  1. Open http://localhost:8069 in browser"
echo "  2. Login: admin / admin"
echo "  3. Apps → Update Apps List"
echo "  4. Search 'l10n_si' or 'l10n_hr' → Install"
echo ""
echo -e "${BOLD}🇸🇮 FURS setup:${NC} See README.md → Quick Start → FURS Configuration"
echo -e "${BOLD}🇭🇷 CISF setup:${NC} See README.md → Quick Start → CISF Configuration"
echo ""
echo -e "${GREEN}Happy hosting! 🏨${NC}"
