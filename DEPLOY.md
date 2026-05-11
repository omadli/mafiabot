# Deployment Guide

## Server requirements

- Ubuntu 22.04+ with `docker` + `docker compose` + `nginx` installed
- `~/apps/mafiabot` cloned from `git@github.com:omadli/mafiabot.git`
- `/var/www/mafia/` (created by deploy)
- Domain `mafia.omadli.uz` → A record points to server IP
- `.env` and `.env.local` files in repo root (not committed) with real values

## Fresh deploy (first time)

```bash
# 1. Clone repo
cd ~/apps
git clone https://github.com/omadli/mafiabot.git
cd mafiabot

# 2. Create .env with real values (copy from .env.example)
cp .env.example .env
nano .env

# 3. Start containers
docker compose up -d

# 4. Wait for backend startup (~10 sec)
docker compose logs backend --tail 20

# 5. The lifespan auto-generates schema (Tortoise.generate_schemas safe=True).
#    NO need to run `aerich init-db` — that's only for generating initial
#    migration files (which we already have in git).

# 6. For migrating an EXISTING DB to new schema (after pull):
docker compose exec backend aerich upgrade

# 7. Build + deploy frontend (host-served via nginx)
cd frontend && npm install && npm run build
sudo cp -r dist/* /var/www/mafia/
sudo chown -R www-data:www-data /var/www/mafia
sudo systemctl reload nginx

# 8. SSL (one-time)
sudo certbot --nginx -d mafia.omadli.uz
```

## CI/CD via GitHub Actions

Push to `main` → workflow auto-deploys:

1. **Frontend build** on GitHub runner
2. **scp** dist to `/tmp/` on server
3. **ssh** runs: pull code → rebuild backend → `aerich upgrade` → extract frontend → reload nginx

Required secrets (Settings → Secrets and variables → Actions):

- `DEPLOY_HOST` — server IP or domain (e.g. `mafia.omadli.uz`)
- `DEPLOY_USER` — SSH user (e.g. `ubuntu`)
- `DEPLOY_KEY` — full SSH private key contents (PEM format)

Server-side setup for CI deploys:

```bash
# Add public key for the DEPLOY_KEY private key
ssh ubuntu@server
echo "ssh-rsa AAAA... user@local" >> ~/.ssh/authorized_keys

# Allow sudo for nginx + tar without password (so workflow doesn't hang)
sudo visudo
# Add this line:
# ubuntu ALL=(ALL) NOPASSWD: /usr/sbin/nginx, /bin/systemctl, /bin/tar, /bin/cp, /bin/chown, /bin/mkdir, /bin/rm
```

## Aerich migrations — when to use what

| Situation | Command |
|---|---|
| Fresh deploy (empty DB) | Just start docker — `generate_schemas` handles it |
| Existing DB + new model field | Locally: `aerich migrate --name <description>` → commit → deploy → `aerich upgrade` on server |
| Manual SQL migration | Create file `migrations/models/N_YYYYMMDDHHMMSS_<name>.py` with `upgrade()` and `downgrade()` |
| Re-init migrations (DESTRUCTIVE) | Delete `migrations/models/*.py` + run `aerich init-db` |

**Never run `aerich init-db` on a deployed server** — it errors out if migration files exist (which they always do in git).

## Troubleshooting

### Nginx → backend "Connection reset by peer" on `/api/*` or `/health`

```
nginx error.log:
  recv() failed (104: Connection reset by peer) while reading response header
  from upstream, upstream: "http://127.0.0.1:8002/health"
```

**Root cause:** Backend uvicorn bound to the wrong port inside the container.

Architecture:

- Nginx → host `127.0.0.1:8002` (the `BACKEND_PORT` env var)
- Docker maps host `8002` → container `8000` (per `ports: "${BACKEND_PORT}:8000"`)
- Container uvicorn MUST bind to `8000` internally

If uvicorn reads `BACKEND_PORT` from env (because `env_file: .env` is shared
with the container), it would also bind to `8002` inside the container —
breaking the port mapping. Result: TCP handshake succeeds (docker accepts),
but no process listens on container:8000 → RST sent back.

**Fix (already applied since commit XXXXXXX):**

- `docker-compose.yml` backend service sets `INTERNAL_PORT: "8000"` explicitly
- `backend/app/main.py` reads `INTERNAL_PORT` first, falls back to
  `settings.backend_port` for local-dev (no Docker)

Verification:

```bash
docker compose exec backend ss -tlnp | grep -E "8000|8002"
# Expected: only one line, listening on 0.0.0.0:8000

docker compose exec backend curl -sf http://localhost:8000/health
# Expected: {"status": "ok"}
```

If still failing, check the backend logs for crashes during lifespan:

```bash
docker compose logs backend --tail 100
```

### `aerich init-db` fails with "Inited models already"

This is expected. Use `aerich upgrade` instead — it applies pending migrations to existing DB.

### `tortoise.exceptions.ConfigurationError: DB configuration not initialised`

Tortoise wasn't initialized before being used. Usually a side-effect of aerich CLI failing earlier (the cleanup tries to close connections that were never opened). Not a real bug — fix the root cause (e.g. wrong tortoise_orm path in pyproject.toml).

### Backend port 8002 already in use

```bash
docker compose down
docker compose up -d
```

If a host process is bound:

```bash
sudo lsof -i :8002
sudo kill <PID>
```

### Frontend shows ECONNREFUSED on /api

Backend isn't running on the port the frontend expects. Check:

```bash
docker compose ps                # backend status
docker compose logs backend      # any startup errors?
echo $BACKEND_PORT               # should match nginx upstream
```

## Updating only frontend (no backend code change)

```bash
cd ~/apps/mafiabot
git pull
cd frontend && npm run build
sudo cp -r dist/* /var/www/mafia/
sudo systemctl reload nginx
```

## Database backup

```bash
docker compose exec postgres pg_dump -U mafia mafia > backup-$(date +%Y%m%d).sql
```

Restore:

```bash
cat backup.sql | docker compose exec -T postgres psql -U mafia mafia
```
