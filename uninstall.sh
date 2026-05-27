#!/usr/bin/env bash
# Uninstallation script for Arch Package Backup and Recovery System
set -euo pipefail

DESTDIR="${DESTDIR:-}"
PREFIX="${PREFIX:-/usr/local}"

# 1. Check root privileges (skip if DESTDIR is set for testing/packaging)
if [ -z "$DESTDIR" ] && [ "${EUID:-$(id -u)}" -ne 0 ]; then
    echo "Error: This script must be run as root (using sudo)." >&2
    exit 1
fi

# Determine systemd unit folder based on prefix
if [ "$PREFIX" = "/usr" ]; then
    SYSTEMD_DIR="$DESTDIR/usr/lib/systemd/user"
else
    SYSTEMD_DIR="$DESTDIR/etc/systemd/system"
fi

# 2. Disable systemd units
if [ -z "$DESTDIR" ]; then
    echo "Disabling Systemd timer..."
    if [ "$PREFIX" = "/usr" ]; then
        if systemctl --user is-active --quiet cachyos-backup-extras.timer || systemctl --user is-enabled --quiet cachyos-backup-extras.timer 2>/dev/null; then
            systemctl --user disable --now cachyos-backup-extras.timer || true
        fi
    else
        if systemctl is-active --quiet cachyos-backup-extras.timer || systemctl is-enabled --quiet cachyos-backup-extras.timer 2>/dev/null; then
            systemctl disable --now cachyos-backup-extras.timer || true
        fi
    fi
else
    echo "Skipping systemctl commands in DESTDIR mode."
fi

# 3. Remove files
echo "Removing installed files..."
rm -f "$DESTDIR$PREFIX/bin/cachyos-backup"
rm -f "$DESTDIR$PREFIX/bin/cachyos-recovery"
rm -f "$DESTDIR$PREFIX/bin/arch-backup-tool"
rm -rf "$DESTDIR$PREFIX/share/arch-backup-tool"
rm -f "$DESTDIR$PREFIX/share/applications/arch-backup-tool.desktop"
rm -f "$DESTDIR/etc/pacman.d/hooks/cachyos-backup.hook"
rm -f "$SYSTEMD_DIR/cachyos-backup-extras.timer"
rm -f "$SYSTEMD_DIR/cachyos-backup-extras.service"

# 4. Reload systemd
if [ -z "$DESTDIR" ]; then
    if [ "$PREFIX" = "/usr" ]; then
        systemctl --user daemon-reload
    else
        systemctl daemon-reload
    fi
fi

echo "Uninstallation completed successfully."
echo "Note: Your local backup repository (default: ~/cachyos-backup) and"
echo "      configuration folder (default: ~/.config/cachyos-backup) have"
echo "      been preserved for your safety."
