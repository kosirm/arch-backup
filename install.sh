#!/usr/bin/env bash
# Installation script for CachyOS Package Backup and Recovery System
set -euo pipefail

DESTDIR="${DESTDIR:-}"

# 1. Check root privileges (skip if DESTDIR is set for testing/packaging)
if [ -z "$DESTDIR" ] && [ "${EUID:-$(id -u)}" -ne 0 ]; then
    echo "Error: This script must be run as root (using sudo)." >&2
    exit 1
fi

# 2. Check dependencies
echo "Checking dependencies..."
missing_deps=0
for dep in git pacman logger; do
    if ! command -v "$dep" >/dev/null 2>&1; then
        echo "Error: Required dependency '$dep' is missing." >&2
        missing_deps=1
    fi
done

if [ "$missing_deps" -eq 1 ]; then
    exit 1
fi

if ! command -v chezmoi >/dev/null 2>&1; then
    echo "Warning: 'chezmoi' is not installed. Dotfile syncing will be skipped." >&2
fi

# 3. Create necessary directories
mkdir -p "$DESTDIR/usr/local/bin"
mkdir -p "$DESTDIR/usr/local/share/arch-backup-tool/gui"
mkdir -p "$DESTDIR/etc/pacman.d/hooks"
mkdir -p "$DESTDIR/etc/systemd/system"

# 4. Copy files to system locations
echo "Installing scripts..."
cp src/cachyos-backup "$DESTDIR/usr/local/bin/cachyos-backup"
chmod 755 "$DESTDIR/usr/local/bin/cachyos-backup"

cp src/cachyos-recovery "$DESTDIR/usr/local/bin/cachyos-recovery"
chmod 755 "$DESTDIR/usr/local/bin/cachyos-recovery"

cp src/arch-backup-tool "$DESTDIR/usr/local/bin/arch-backup-tool"
chmod 755 "$DESTDIR/usr/local/bin/arch-backup-tool"

cp src/gui/__init__.py "$DESTDIR/usr/local/share/arch-backup-tool/gui/__init__.py"
cp src/gui/main.py "$DESTDIR/usr/local/share/arch-backup-tool/gui/main.py"
cp src/gui/wizard.py "$DESTDIR/usr/local/share/arch-backup-tool/gui/wizard.py"
cp src/gui/dashboard.py "$DESTDIR/usr/local/share/arch-backup-tool/gui/dashboard.py"
cp src/gui/utils.py "$DESTDIR/usr/local/share/arch-backup-tool/gui/utils.py"
chmod 644 "$DESTDIR/usr/local/share/arch-backup-tool/gui/"*.py

echo "Installing Pacman hook..."
cp config/cachyos-backup.hook "$DESTDIR/etc/pacman.d/hooks/cachyos-backup.hook"
chmod 644 "$DESTDIR/etc/pacman.d/hooks/cachyos-backup.hook"

echo "Installing Systemd units..."
cp config/cachyos-backup-extras.timer "$DESTDIR/etc/systemd/system/cachyos-backup-extras.timer"
chmod 644 "$DESTDIR/etc/systemd/system/cachyos-backup-extras.timer"

cp config/cachyos-backup-extras.service "$DESTDIR/etc/systemd/system/cachyos-backup-extras.service"
chmod 644 "$DESTDIR/etc/systemd/system/cachyos-backup-extras.service"

# 5. Reload systemd and enable timer
if [ -z "$DESTDIR" ]; then
    echo "Enabling Systemd timer..."
    systemctl daemon-reload
    systemctl enable --now cachyos-backup-extras.timer
else
    echo "Skipping systemctl commands in DESTDIR mode."
fi

echo "Installation completed successfully."
