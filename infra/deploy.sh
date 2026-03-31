#!/bin/bash
set -e

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
uv sync

echo "==> Restarting services"
sudo systemctl restart methlab-frontend
sudo systemctl restart methlab-api
sudo systemctl restart methlab-ml

echo "==> Deploy complete"
systemctl --no-pager status methlab-frontend methlab-api methlab-ml
