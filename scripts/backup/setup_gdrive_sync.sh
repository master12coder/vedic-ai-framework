#!/bin/bash
# DaivAI — One-time Google Drive setup via rclone
# Usage: bash scripts/backup/setup_gdrive_sync.sh

set -euo pipefail

echo "Setting up Google Drive backup with rclone"
echo ""

if ! command -v rclone &> /dev/null; then
    echo "Installing rclone..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install rclone
    else
        curl https://rclone.org/install.sh | sudo bash
    fi
fi

echo "Run: rclone config"
echo ""
echo "Steps:"
echo "  1. n (new remote)"
echo "  2. Name: gdrive"
echo "  3. Storage: drive (Google Drive)"
echo "  4. Client ID: (Enter to skip)"
echo "  5. Client Secret: (Enter to skip)"
echo "  6. Scope: 1 (full access)"
echo "  7. Root folder: (Enter)"
echo "  8. Service account: (Enter)"
echo "  9. Auto config: y"
echo "  10. Browser opens → sign in → authorize"
echo "  11. Team drive: n"
echo "  12. Confirm: y"
echo ""
echo "After setup, test: rclone ls gdrive:/"
echo ""

rclone config
