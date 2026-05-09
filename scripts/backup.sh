#!/usr/bin/env bash
# Daily PostgreSQL backup. Run via cron:
#   0 3 * * * /opt/mafia/scripts/backup.sh

set -euo pipefail

cd "$(dirname "$0")/.."

# Load env
set -a
source .env
set +a

BACKUP_DIR="./backups"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/mafia-${TIMESTAMP}.sql.gz"

mkdir -p "$BACKUP_DIR"

echo "[$(date)] Starting backup → ${BACKUP_FILE}"

docker compose exec -T postgres \
    pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --clean --if-exists \
    | gzip > "$BACKUP_FILE"

# Verify
if [ -s "$BACKUP_FILE" ]; then
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "[$(date)] Backup OK: $BACKUP_FILE ($SIZE)"
else
    echo "[$(date)] ❌ Backup FAILED: empty file"
    rm -f "$BACKUP_FILE"
    exit 1
fi

# Retention
echo "[$(date)] Cleaning backups older than ${RETENTION_DAYS} days..."
find "$BACKUP_DIR" -name "mafia-*.sql.gz" -mtime +"$RETENTION_DAYS" -delete

echo "[$(date)] Done."
