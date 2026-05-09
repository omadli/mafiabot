#!/usr/bin/env bash
# Build frontend (React+Vite) and deploy to /var/www/mafia
# Bosqich 3 da to'liq qo'llanadi (frontend skeleton hozir yo'q)

set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -d "frontend" ]; then
    echo "Frontend papkasi yo'q (Bosqich 3 da yaratiladi). Skip."
    exit 0
fi

DOCROOT="${FRONTEND_DOCROOT:-/var/www/mafia}"

echo "[$(date)] Installing frontend deps..."
cd frontend
npm install

echo "[$(date)] Building frontend..."
npm run build

echo "[$(date)] Deploying to $DOCROOT..."
sudo rm -rf "$DOCROOT"/*
sudo cp -r dist/* "$DOCROOT/"
sudo chown -R www-data:www-data "$DOCROOT"

echo "[$(date)] Frontend deployed → $DOCROOT"
