#!/usr/bin/env bash
set -euo pipefail

# ==== BEÁLLÍTÁSOK ====
CONTAINER_NAME="vizsgaremek-postgresql-1"
DB_NAME="vizsgaremek"      
DB_USER="tician"    

if [ "$#" -ne 1 ]; then
  echo "Használat: $0 path/to/backup_file.dump"
  exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
  echo "Hiba: nem találom a fájlt: $BACKUP_FILE"
  exit 1
fi

# Ha nem fut a konténer, indítsuk el
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
  echo "Postgres konténer nem fut, indítom..."
  docker start "$CONTAINER_NAME" > /dev/null
fi

echo "FIGYELEM: A(z) '$DB_NAME' adatbázis tartalma felül fog íródni!"
read -p "Biztosan folytatod? (igen/nem): " ANSWER
if [ "$ANSWER" != "igen" ]; then
  echo "Megszakítva."
  exit 1
fi

echo "Adatbázis visszaállítása: $BACKUP_FILE -> $DB_NAME"

# A dump fájlt betoljuk a konténerben futó pg_restore-nak
cat "$BACKUP_FILE" | docker exec -i "$CONTAINER_NAME" pg_restore \
  --clean \
  --if-exists \
  -U "$DB_USER" \
  -d "$DB_NAME"

echo "Visszaállítás kész ✔"
