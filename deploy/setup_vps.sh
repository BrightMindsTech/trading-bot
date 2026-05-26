#!/usr/bin/env bash
# Bootstrap Ubuntu VPS for trading-bot (Streamlit UI + Binance runner).
# Run on the server after cloning the repo:
#   bash deploy/setup_vps.sh
set -euo pipefail

APP_DIR="${APP_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
APP_USER="${APP_USER:-$(whoami)}"
SERVICE_NAME="${SERVICE_NAME:-trading-bot}"
STREAMLIT_PORT="${STREAMLIT_PORT:-8501}"

echo "==> App directory: $APP_DIR"
echo "==> User: $APP_USER"
echo "==> Port: $STREAMLIT_PORT"

if [[ ! -f "$APP_DIR/requirements.txt" ]]; then
  echo "ERROR: requirements.txt not found. Run this from the repo root or set APP_DIR."
  exit 1
fi

echo "==> Installing system packages..."
export DEBIAN_FRONTEND=noninteractive
sudo apt-get update -qq
sudo apt-get install -y -qq python3 python3-venv python3-pip git curl

echo "==> Creating virtualenv..."
cd "$APP_DIR"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q

if [[ ! -f "$APP_DIR/.env" ]]; then
  echo "==> Creating .env from .env.example (EDIT WITH YOUR KEYS)"
  cp .env.example .env
fi

mkdir -p "$APP_DIR/logs"

echo "==> Installing systemd service..."
sudo tee "/etc/systemd/system/${SERVICE_NAME}.service" > /dev/null <<EOF
[Unit]
Description=Trading Bot Streamlit UI
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${APP_USER}
WorkingDirectory=${APP_DIR}
EnvironmentFile=${APP_DIR}/.env
ExecStart=${APP_DIR}/.venv/bin/streamlit run interface.py \\
  --server.address=0.0.0.0 \\
  --server.port=${STREAMLIT_PORT} \\
  --server.headless=true
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable "${SERVICE_NAME}"

echo "==> Configuring firewall (ufw) if available..."
if command -v ufw >/dev/null 2>&1; then
  sudo ufw allow OpenSSH || true
  sudo ufw allow "${STREAMLIT_PORT}/tcp" || true
  echo "y" | sudo ufw enable || true
fi

echo ""
echo "=============================================="
echo "Setup complete."
echo "1) Edit secrets:  nano ${APP_DIR}/.env"
echo "2) Start service: sudo systemctl start ${SERVICE_NAME}"
echo "3) Check logs:    sudo journalctl -u ${SERVICE_NAME} -f"
echo "4) Open browser:  http://YOUR_SERVER_IP:${STREAMLIT_PORT}"
echo "=============================================="
