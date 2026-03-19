#!/bin/bash
# DaivAI — Backup locally + upload to Google Drive
# Add to cron: 0 23 * * * cd /path/to/daivai && bash scripts/backup/auto_backup.sh

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
BACKUP_DIR="$HOME/DaivAI-Backups"

# Local backup
bash "$PROJECT_DIR/scripts/backup/local_backup.sh"

# Upload to Google Drive if rclone configured
if command -v rclone &> /dev/null; then
    if rclone listremotes 2>/dev/null | grep -q "gdrive:"; then
        echo "Uploading to Google Drive..."
        rclone copy "$BACKUP_DIR/" "gdrive:DaivAI-Backups/" --progress
        echo "Uploaded to Google Drive"
    else
        echo "rclone not configured. Run: bash scripts/backup/setup_gdrive_sync.sh"
    fi
else
    echo "rclone not installed. Backup is local only."
fi

# Clean old backups (keep 7 days)
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete 2>/dev/null
echo "Cleaned backups older than 7 days"
