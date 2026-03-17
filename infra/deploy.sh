#!/usr/bin/env bash
# Deploy MethLab to production
#
# Usage:
#   ./infra/deploy.sh              # Full deploy (pull, install, build, restart)
#   ./infra/deploy.sh --restart    # Just restart the service
#
# First-time setup:
#   1. Clone repo:       git clone https://github.com/geoffosborn/methlab.git /home/ubuntu/projects/methlab
#   2. Install deps:     cd /home/ubuntu/projects/methlab && npm ci
#   3. Create .env:      cp .env.example .env && nano .env
#   4. Build:            npm run build
#   5. Install service:  sudo cp infra/methlab.service /etc/systemd/system/
#                        sudo systemctl daemon-reload && sudo systemctl enable methlab
#   6. Install caddy:    Add 'import /home/ubuntu/projects/methlab/infra/methlab.geosynergy.com.au.caddyfile'
#                        to /etc/caddy/Caddyfile, then: sudo systemctl restart caddy
#   7. DNS:              Create A record: methlab.geosynergy.com.au → server IP

set -euo pipefail

PROJECT_DIR="/home/ubuntu/projects/methlab"
SERVICE="methlab"

cd "$PROJECT_DIR"

if [[ "${1:-}" == "--restart" ]]; then
    echo "==> Restarting $SERVICE..."
    sudo systemctl restart "$SERVICE"
    echo "==> Done."
    exit 0
fi

echo "==> Pulling latest code..."
git pull --ff-only

echo "==> Installing dependencies..."
npm ci --production=false

echo "==> Building..."
npm run build

echo "==> Restarting service..."
sudo systemctl restart "$SERVICE"

echo "==> Checking health..."
sleep 3
if curl -sf http://localhost:3100 > /dev/null 2>&1; then
    echo "==> MethLab is up at https://methlab.geosynergy.com.au"
else
    echo "==> WARNING: Health check failed. Check: sudo journalctl -u $SERVICE -n 50"
fi
