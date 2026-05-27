#!/usr/bin/env bash
# Installation script for Arch Package Backup and Recovery System
set -euo pipefail

DESTDIR="${DESTDIR:-}"
PREFIX="${PREFIX:-/usr/local}"

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
mkdir -p "$DESTDIR$PREFIX/bin"
mkdir -p "$DESTDIR$PREFIX/share/arch-backup-tool/gui"
mkdir -p "$DESTDIR$PREFIX/share/applications"
mkdir -p "$DESTDIR/etc/pacman.d/hooks"

# Determine systemd unit folder based on prefix
if [ "$PREFIX" = "/usr" ]; then
    SYSTEMD_DIR="$DESTDIR/usr/lib/systemd/user"
else
    SYSTEMD_DIR="$DESTDIR/etc/systemd/system"
fi
mkdir -p "$SYSTEMD_DIR"

# 4. Copy files to system locations
echo "Installing scripts..."
cp src/cachyos-backup "$DESTDIR$PREFIX/bin/cachyos-backup"
chmod 755 "$DESTDIR$PREFIX/bin/cachyos-backup"

cp src/cachyos-recovery "$DESTDIR$PREFIX/bin/cachyos-recovery"
chmod 755 "$DESTDIR$PREFIX/bin/cachyos-recovery"

cp src/arch-backup-tool "$DESTDIR$PREFIX/bin/arch-backup-tool"
chmod 755 "$DESTDIR$PREFIX/bin/arch-backup-tool"

cp src/gui/__init__.py "$DESTDIR$PREFIX/share/arch-backup-tool/gui/__init__.py"
cp src/gui/main.py "$DESTDIR$PREFIX/share/arch-backup-tool/gui/main.py"
cp src/gui/wizard.py "$DESTDIR$PREFIX/share/arch-backup-tool/gui/wizard.py"
cp src/gui/dashboard.py "$DESTDIR$PREFIX/share/arch-backup-tool/gui/dashboard.py"
cp src/gui/utils.py "$DESTDIR$PREFIX/share/arch-backup-tool/gui/utils.py"
chmod 644 "$DESTDIR$PREFIX/share/arch-backup-tool/gui/"*.py

echo "Installing Desktop entry launcher..."
cp config/arch-backup-tool.desktop "$DESTDIR$PREFIX/share/applications/arch-backup-tool.desktop"
chmod 644 "$DESTDIR$PREFIX/share/applications/arch-backup-tool.desktop"

echo "Installing Pacman hook..."
sed "s|/usr/local/bin|$PREFIX/bin|g" config/cachyos-backup.hook > "$DESTDIR/etc/pacman.d/hooks/cachyos-backup.hook"
chmod 644 "$DESTDIR/etc/pacman.d/hooks/cachyos-backup.hook"

echo "Installing Systemd units..."
cp config/cachyos-backup-extras.timer "$SYSTEMD_DIR/cachyos-backup-extras.timer"
chmod 644 "$SYSTEMD_DIR/cachyos-backup-extras.timer"

if [ "$PREFIX" = "/usr" ]; then
    # For user systemd unit, strip User=%I
    sed -e "s|/usr/local/bin|$PREFIX/bin|g" -e "/User=%I/d" config/cachyos-backup-extras.service > "$SYSTEMD_DIR/cachyos-backup-extras.service"
else
    sed "s|/usr/local/bin|$PREFIX/bin|g" config/cachyos-backup-extras.service > "$SYSTEMD_DIR/cachyos-backup-extras.service"
fi
chmod 644 "$SYSTEMD_DIR/cachyos-backup-extras.service"

# 5. Reload systemd and enable timer
if [ -z "$DESTDIR" ]; then
    echo "Enabling Systemd timer..."
    if [ "$PREFIX" = "/usr" ]; then
        systemctl --user daemon-reload
        systemctl --user enable --now cachyos-backup-extras.timer
    else
        systemctl daemon-reload
        systemctl enable --now cachyos-backup-extras.timer
    fi
else
    echo "Skipping systemctl commands in DESTDIR mode."
fi

echo "Installation completed successfully."
