#!/bin/bash
set -e

export PATH="$HOME/.local/bin:$PATH"

PROJECT=/home/ubuntu/projects/methlab

echo "==> Pulling latest changes"
cd "$PROJECT"
git pull

echo "==> Building frontend"
cd "$PROJECT/frontend"
npm ci
npm run build

echo "==> Syncing backend dependencies"
cd "$PROJECT/backend"
uv pip install -e apps/api -e packages/common
# Pipeline deps (not editable — flat module layout)
uv pip install -r apps/tropomi/pyproject.toml -r apps/sentinel2/pyproject.toml 2>/dev/null || true

echo "==> Restarting services"
sudo systemctl restart methlab-frontend
sudo systemctl restart methlab-api
sudo systemctl restart methlab-ml

echo "==> Deploy complete"
systemctl --no-pager status methlab-frontend methlab-api methlab-ml
