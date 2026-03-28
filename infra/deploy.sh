#!/bin/bash
set -e
cd /home/ubuntu/projects/methlab
git pull
npm ci
npm run build
sudo systemctl restart methlab
echo "Deploy complete"
