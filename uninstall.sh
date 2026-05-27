#!/usr/bin/env bash
# Uninstallation script for CachyOS Package Backup and Recovery System
set -euo pipefail

DESTDIR="${DESTDIR:-}"

# 1. Check root privileges (skip if DESTDIR is set for testing/packaging)
if [ -z "$DESTDIR" ] && [ "${EUID:-$(id -u)}" -ne 0 ]; then
    echo "Error: This script must be run as root (using sudo)." >&2
    exit 1
fi

# 2. Disable systemd units
if [ -z "$DESTDIR" ]; then
    echo "Disabling Systemd timer..."
    if systemctl is-active --quiet cachyos-backup-extras.timer || systemctl is-enabled --quiet cachyos-backup-extras.timer 2>/dev/null; then
        systemctl disable --now cachyos-backup-extras.timer || true
    fi
else
    echo "Skipping systemctl commands in DESTDIR mode."
fi

# 3. Remove files
echo "Removing installed files..."
rm -f "$DESTDIR/usr/local/bin/cachyos-backup"
rm -f "$DESTDIR/usr/local/bin/cachyos-recovery"
rm -f "$DESTDIR/usr/local/bin/arch-backup-tool"
rm -rf "$DESTDIR/usr/local/share/arch-backup-tool"
rm -f "$DESTDIR/etc/pacman.d/hooks/cachyos-backup.hook"
rm -f "$DESTDIR/etc/systemd/system/cachyos-backup-extras.timer"
rm -f "$DESTDIR/etc/systemd/system/cachyos-backup-extras.service"

# 4. Reload systemd
if [ -z "$DESTDIR" ]; then
    systemctl daemon-reload
fi

echo "Uninstallation completed successfully."
echo "Note: Your local backup repository (default: ~/cachyos-backup) and"
echo "      configuration folder (default: ~/.config/cachyos-backup) have"
echo "      been preserved for your safety."
