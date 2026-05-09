#!/usr/bin/env bash
# Local development — backend (polling) + frontend (Vite) parallel
# Linux/Mac uchun
#
# Usage: bash ./scripts/run-dev.sh

set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f ".env.local" ]; then
    echo "❌ .env.local fayli topilmadi. Avval .env.local.example dan nusxa oling:"
    echo "   cp .env.local.example .env.local"
    exit 1
fi

echo "🚀 Backend va frontend parallel ishga tushirilmoqda..."

# Cleanup on exit
cleanup() {
    echo "🛑 Stopping..."
    kill "${BACKEND_PID:-}" "${FRONTEND_PID:-}" 2>/dev/null || true
    wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# Backend
(
    cd backend
    if [ -d ".venv" ]; then
        # shellcheck disable=SC1091
        source .venv/bin/activate
    fi
    python -m app.main
) &
BACKEND_PID=$!

# Frontend
(
    cd frontend
    if [ ! -d "node_modules" ]; then
        npm install
    fi
    npm run dev
) &
FRONTEND_PID=$!

echo "✅ Backend (PID $BACKEND_PID): http://localhost:8001/health"
echo "✅ Frontend (PID $FRONTEND_PID): http://localhost:5173"
echo "Ctrl+C bilan to'xtatish"

wait
