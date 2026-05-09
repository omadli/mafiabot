# Local development — backend (polling) + frontend (Vite) parallel ishga tushirish
# Windows PowerShell uchun
#
# Usage: .\scripts\run-dev.ps1

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

if (-not (Test-Path ".env.local")) {
    Write-Host "❌ .env.local fayli topilmadi. .env.local.example ni nusxa olib BOT_TOKEN ni kiriting." -ForegroundColor Red
    Write-Host "   Copy-Item .env.local.example .env.local" -ForegroundColor Yellow
    exit 1
}

Write-Host "🚀 Backend va frontend parallel ishga tushirilmoqda..." -ForegroundColor Cyan

# Backend (polling mode) — yangi terminalda
$backendCmd = "cd '$ProjectRoot\backend'; if (Test-Path .venv) { .\.venv\Scripts\Activate.ps1 }; python -m app.main"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd -WindowStyle Normal

# Frontend (Vite dev server) — yangi terminalda
$frontendCmd = "cd '$ProjectRoot\frontend'; if (-not (Test-Path node_modules)) { npm install }; npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd -WindowStyle Normal

Write-Host "✅ Ishga tushdi! Tekshirib ko'ring:" -ForegroundColor Green
Write-Host "   Backend:  http://localhost:8001/health" -ForegroundColor Yellow
Write-Host "   Frontend: http://localhost:5173" -ForegroundColor Yellow
