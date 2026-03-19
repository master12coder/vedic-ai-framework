#!/bin/bash
# DaivAI — Local backup of all non-git data
# Usage: bash scripts/backup/local_backup.sh

set -euo pipefail

BACKUP_DIR="$HOME/DaivAI-Backups/$(date +%Y-%m-%d_%H%M)"
PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"

mkdir -p "$BACKUP_DIR"

echo "Backing up DaivAI data to $BACKUP_DIR"

# .env (secrets)
cp "$PROJECT_DIR/.env" "$BACKUP_DIR/.env" 2>/dev/null && echo "  .env"

# Database
mkdir -p "$BACKUP_DIR/data"
cp "$PROJECT_DIR"/data/*.db "$BACKUP_DIR/data/" 2>/dev/null && echo "  database"
cp "$PROJECT_DIR"/data/*.sqlite3 "$BACKUP_DIR/data/" 2>/dev/null

# Charts (family birth data)
if [ -d "$PROJECT_DIR/charts" ]; then
    cp -r "$PROJECT_DIR/charts/" "$BACKUP_DIR/charts/"
    echo "  charts"
fi

# Generated outputs
if [ -d "$PROJECT_DIR/output" ]; then
    cp -r "$PROJECT_DIR/output/" "$BACKUP_DIR/output/"
    echo "  outputs"
fi

# Config
if [ -d "$PROJECT_DIR/config" ]; then
    cp -r "$PROJECT_DIR/config/" "$BACKUP_DIR/config/"
    echo "  config"
fi

# Compress
cd "$(dirname "$BACKUP_DIR")"
tar -czf "$(basename "$BACKUP_DIR").tar.gz" "$(basename "$BACKUP_DIR")"
rm -rf "$BACKUP_DIR"

ARCHIVE="$HOME/DaivAI-Backups/$(basename "$BACKUP_DIR").tar.gz"
echo ""
echo "Backup saved: $ARCHIVE"
echo "Size: $(du -sh "$ARCHIVE" | cut -f1)"
