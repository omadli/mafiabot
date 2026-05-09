# 🎲 Mafia Telegram Bot — `@MafGameUzBot`

Mafia Baku Black ([`@MafiaAzBot`](https://t.me/MafiaAzBot)) uslubidagi professional Telegram Mafia bot — o'zbekcha clone. Guruh chati orqali 4–30 kishilik o'yin, premium tizim (Telegram Stars + olmos), super admin paneli (`mafia.omadli.uz`), guruh adminlari uchun Telegram WebApp.

## ✨ Asosiy xususiyatlar

- **21 ta rol**: Tinch aholilar (10) + Mafiya (5) + Singletonlar (6) — har biri unikal mexanika bilan
- **3 valyuta**: 💎 Olmos (Telegram Stars), 💵 Dollar (o'yin), ⭐ XP (level)
- **Moslashuvchan i18n**: O'zbek/Rus/Ingliz, har qanday til qo'shish oson (Project Fluent)
- **Qurol va himoyalar**: 🛡 Himoya, ⛑ Qotildan himoya, ⚖️ Ovoz himoyasi, 🔫 Miltiq, 🎭 Maska, 📁 Soxta hujjat, 🃏 Maxsus rol
- **Giveaway tizimi**: 3 rejim — reply orqali, guruh inline tugma (harmonic taqsimot), o'yin bountisi
- **Statistika**: Global + Guruh ELO, kunlik/haftalik/oylik snapshot, 15+ achievement
- **AFK kuzatuv**: 2 navbat skip → avtomatik chiqarish, XP penalty
- **Onboarding**: Bot guruhga qo'shilganda til tanlash + admin huquqlari
- **Deeplink**: O'yinga qo'shilish bot bilan private chat orqali (1 user = 1 game)
- **Tungi atmosfera xabarlari**: Random shuffle, har rol uchun maxsus matn
- **Tun natijasi**: O'lim, himoya, Bo'ri transformatsiya, Kamikaze take, Sotqin reveal — to'liq oshkor xabarlar
- **So'nggi so'z**: O'lganlar private chatda yozadi → guruhga `"O'limidan oldin kimdir, {mention} ni qichqirganini eshitdi..."` formatida

## 🛠 Tech stack

| Sloj | Texnologiya |
|---|---|
| **Bot** | Python 3.12 · aiogram 3.x · Redis FSM (yoki Memory dev'da) |
| **API** | FastAPI · WebSocket · uvicorn |
| **ORM** | Tortoise ORM · Aerich migrations · PostgreSQL/SQLite |
| **Frontend** | React 18 · TypeScript · Vite · TanStack Query |
| **i18n** | `fluent.runtime` (Project Fluent) — uz/ru/en |
| **Logging** | loguru (JSON structured) |
| **Monitoring** | Sentry · `/health` endpoint |
| **Scheduler** | APScheduler (stats rollup, AFK, backup) |
| **Tests** | pytest · pytest-asyncio |
| **Quality** | ruff · mypy · pre-commit |
| **Container** | Docker Compose (production) |
| **Reverse proxy** | Tashqi (host) Nginx + LetsEncrypt |
| **Payments** | Telegram Stars (XTR) |

## 📁 Loyiha tuzilishi

```
backend/                    # Python backend
├── app/
│   ├── bot/                # aiogram handlers, FSM, middlewares
│   ├── api/                # FastAPI routers
│   ├── core/               # Game engine — domain logic
│   │   ├── engine, state   # GameState, PlayerState (Redis JSON)
│   │   ├── phases/         # Night/Day/Voting + PhaseManager
│   │   ├── roles/          # 21 ta rol (har biri alohida fayl)
│   │   ├── actions.py      # Action queue + resolver
│   │   ├── win_conditions  # G'olib tomon aniqlash
│   │   └── distribution    # 4-30 player rol taqsimoti
│   ├── db/models/          # Tortoise modellari
│   ├── services/           # Biznes logika (game, stats, payment, giveaway, ...)
│   ├── locales/{uz,ru,en}/ # Project Fluent .ftl fayllar
│   ├── workers/            # APScheduler crons
│   └── utils/
├── tests/
└── pyproject.toml

frontend/                   # React + TS + Vite (admin panel + WebApp)
├── src/
│   ├── modules/admin/      # Super admin paneli (/admin/*)
│   ├── modules/webapp/     # Telegram WebApp (/webapp/*)
│   └── shared/             # api, hooks, i18n, ui
└── package.json

nginx/                      # Tashqi host nginx config + deploy guide
scripts/                    # backup, build-frontend, run-dev
docker-compose.yml
```

## 🚀 Tezkor boshlash

### Lokal dev (Docker'siz, SQLite + Memory + Polling)

1. **Talablar**: Python 3.12+, Node.js 20+, Bot token ([@BotFather](https://t.me/BotFather))

2. **Setup:**
   ```bash
   cp .env.local.example .env.local
   # .env.local da BOT_TOKEN ni to'ldiring
   ```

3. **Backend:**
   ```bash
   cd backend
   python -m venv venv
   # Windows: venv\Scripts\activate
   # Linux/Mac: source venv/bin/activate
   pip install -e ".[dev]"
   python -m app.main
   ```

4. **Frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

5. **Yoki bir vaqtda (PowerShell):** `.\scripts\run-dev.ps1`

   Telegram'dan botingizga `/start`, guruhda `/game` bilan o'yin boshlang.

### Production (Docker)

```bash
cp .env.example .env
# Real qiymatlar bilan to'ldiring
docker compose up -d
docker compose exec backend aerich init -t app.db.tortoise_config.TORTOISE_ORM
docker compose exec backend aerich init-db
```

To'liq deploy qo'llanmasi: [`nginx/README.md`](./nginx/README.md)

## 📖 Hujjatlar

- [`Mafia o'yin qoidalari.md`](./Mafia%20o'yin%20qoidalari.md) — to'liq o'yin qoidalari (21 rol, items, AFK, giveaway, onboarding)
- [`nginx/README.md`](./nginx/README.md) — production deploy (certbot, document_root)

## 🧪 Sinov

```bash
# Backend
cd backend
ruff check .
ruff format --check .
mypy app/
pytest

# Frontend
cd frontend
npm run lint
npm run type-check
npm run build
```

## 🗺 Bosqichlar

| Bosqich | Holati | Asosiy ish |
|---|---|---|
| **Bosqich 1 (MVP)** | ✅ | 5 ta asosiy rol, to'liq o'yin loop, Redis state, Docker compose |
| **Bosqich 2** | ✅ | 21 ta to'liq rol, statistika (ELO + per-group), achievement, AFK, last words, items |
| **Bosqich 3** | 🚧 | Premium (Stars), giveaway, payment ✅; admin paneli backend/frontend, WebApp 🚧 |

## 🤝 Ishtirok etish

Bu shaxsiy loyiha. Pull request va Issuelar mamnuniyat bilan ko'rib chiqiladi.

---

🎮 **Reference**: [@MafiaAzBot](https://t.me/MafiaAzBot) (Mafia Baku Black) · [@MafiaAzBot_news](https://t.me/MafiaAzBot_news)
