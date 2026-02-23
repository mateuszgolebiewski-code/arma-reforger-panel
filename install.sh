#!/bin/bash
# ============================================================
# Arma Reforger Panel — Installer
# https://github.com/mateuszgolebiewski/arma-reforger-panel
# ============================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

PANEL_DIR="/opt/arma-panel"

echo ""
echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${CYAN}║   Arma Reforger — Panel Installer v4.0   ║${NC}"
echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════╝${NC}"
echo ""

# ── Root check ────────────────────────────────────────────────────────────────
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Please run as root: sudo bash install.sh${NC}"
  exit 1
fi

# ── Collect user input ─────────────────────────────────────────────────────────
echo -e "${BOLD}Please answer a few questions to configure the panel:${NC}"
echo ""

read -p "  Panel password (for web login): " PANEL_PASSWORD
read -p "  Panel port [8888]: " PANEL_PORT
PANEL_PORT=${PANEL_PORT:-8888}

read -p "  Arma server directory [/home/arma/server]: " SERVER_DIR
SERVER_DIR=${SERVER_DIR:-/home/arma/server}

read -p "  Arma config.json path [${SERVER_DIR}/config.json]: " SERVER_CONFIG
SERVER_CONFIG=${SERVER_CONFIG:-${SERVER_DIR}/config.json}

read -p "  Arma log directory [/home/arma/.config/ArmaReforger/logs]: " LOG_DIR
LOG_DIR=${LOG_DIR:-/home/arma/.config/ArmaReforger/logs}

read -p "  Max FPS cap [60]: " MAX_FPS
MAX_FPS=${MAX_FPS:-60}

echo ""
echo -e "${BOLD}Installation directory: ${CYAN}${PANEL_DIR}${NC}"
echo ""

# ── Install dependencies ───────────────────────────────────────────────────────
echo -e "${YELLOW}[1/4] Installing Python dependencies...${NC}"
apt-get update -qq
apt-get install -y -qq python3 python3-pip
pip3 install flask --break-system-packages -q
echo -e "${GREEN}      Done.${NC}"

# ── Copy panel files ───────────────────────────────────────────────────────────
echo -e "${YELLOW}[2/4] Copying panel files to ${PANEL_DIR}...${NC}"
mkdir -p "${PANEL_DIR}/static"
cp app.py "${PANEL_DIR}/"
cp index.html "${PANEL_DIR}/"
cp login.html "${PANEL_DIR}/"
cp static/manifest.json "${PANEL_DIR}/static/"
cp static/service-worker.js "${PANEL_DIR}/static/"
cp static/icon-192.png "${PANEL_DIR}/static/"
cp static/icon-512.png "${PANEL_DIR}/static/"
echo -e "${GREEN}      Done.${NC}"

# ── Write config.env ──────────────────────────────────────────────────────────
echo -e "${YELLOW}[3/4] Writing configuration...${NC}"
cat > "${PANEL_DIR}/config.env" << EOF
PANEL_PASSWORD=${PANEL_PASSWORD}
PANEL_PORT=${PANEL_PORT}
SERVER_DIR=${SERVER_DIR}
SERVER_CONFIG=${SERVER_CONFIG}
LOG_DIR=${LOG_DIR}
MAX_FPS=${MAX_FPS}
EOF
chmod 600 "${PANEL_DIR}/config.env"
echo -e "${GREEN}      Done.${NC}"

# ── Create systemd service ─────────────────────────────────────────────────────
echo -e "${YELLOW}[4/4] Creating systemd service...${NC}"
cat > /etc/systemd/system/arma-panel.service << EOF
[Unit]
Description=Arma Reforger Management Panel
After=network.target

[Service]
Type=simple
WorkingDirectory=${PANEL_DIR}
ExecStart=/usr/bin/python3 ${PANEL_DIR}/app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable arma-panel
systemctl start arma-panel
echo -e "${GREEN}      Done.${NC}"

# ── Open firewall port ────────────────────────────────────────────────────────
iptables -I INPUT -p tcp --dport "${PANEL_PORT}" -j ACCEPT 2>/dev/null || true

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${GREEN}║          Installation complete!          ║${NC}"
echo -e "${BOLD}${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""
echo -e "  Panel URL : ${CYAN}http://YOUR_SERVER_IP:${PANEL_PORT}${NC}"
echo -e "  Password  : ${CYAN}${PANEL_PASSWORD}${NC}"
echo -e "  Config    : ${CYAN}${PANEL_DIR}/config.env${NC}"
echo ""
echo -e "  Useful commands:"
echo -e "    ${YELLOW}sudo systemctl status arma-panel${NC}   — check status"
echo -e "    ${YELLOW}sudo systemctl restart arma-panel${NC}  — restart panel"
echo -e "    ${YELLOW}sudo journalctl -u arma-panel -f${NC}   — live logs"
echo ""
