#!/usr/bin/env bash
set -euo pipefail

# ==== BEÁLLÍTÁSOK ====
CONTAINER_NAME="vizsgaremek-postgresql-1"
DB_NAME="vizsgaremek"      # pl. "vizsgaremek"
DB_USER="tician"    # pl. "postgres"

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%F_%H-%M-%S)
BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_${TIMESTAMP}.dump"

mkdir -p "$BACKUP_DIR"

# Ha nem fut a konténer, indítsuk el
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
  echo "Postgres konténer nem fut, indítom..."
  docker start "$CONTAINER_NAME" > /dev/null
fi

echo "Adatbázis mentése: $BACKUP_FILE"

# pg_dump a konténeren BELÜL, adat a hoston lesz elmentve
docker exec -i "$CONTAINER_NAME" pg_dump \
  -U "$DB_USER" \
  -d "$DB_NAME" \
  -Fc \
  > "$BACKUP_FILE"

echo "Mentés kész ✔"
