#!/bin/bash

# Állítsd be az adatbázis nevét, felhasználónevét és a mentés helyét
DB_NAME="adatbazis_neve"
DB_USER="felhasznalonev"
BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"

# Adatbázis mentése
pg_dump -U "$DB_USER" "$DB_NAME" > "$BACKUP_FILE"

echo "Mentés elkészült: $BACKUP_FILE"

# Visszatöltéshez használd ezt a parancsot:
# psql -U felhasznalonev -d adatbazis_neve < backup_YYYYMMDD_HHMMSS.sql