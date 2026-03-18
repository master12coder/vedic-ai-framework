#!/bin/bash
# Daily SQLite backup — run via cron at 3 AM
# Keeps 7 days of backups locally, optionally syncs to Google Drive

set -euo pipefail

DB_PATH="/opt/jyotish/data/jyotish.db"
BACKUP_DIR="/opt/jyotish/data/backups"
DATE=$(date +%Y%m%d)

mkdir -p "$BACKUP_DIR"

# Create backup
if [ -f "$DB_PATH" ]; then
    cp "$DB_PATH" "$BACKUP_DIR/jyotish-${DATE}.db"
    echo "Backup created: jyotish-${DATE}.db"
fi

# Clean old backups (keep 7 days)
find "$BACKUP_DIR" -name "jyotish-*.db" -mtime +7 -delete

# Optional: sync to Google Drive via rclone
if command -v rclone &> /dev/null; then
    rclone copy "$BACKUP_DIR" gdrive:jyotish-backups/ 2>/dev/null || true
fi
