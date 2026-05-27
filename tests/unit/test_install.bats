#!/usr/bin/env bats

setup() {
    load '../helpers/setup.bash'
    load '../helpers/mocks.bash'
    setup_test_env
}

teardown() {
    teardown_test_env
}

@test "root privilege check exits with error when not root" {
    # If we run install.sh without DESTDIR, it should enforce being root.
    # Since bats runs as normal user (non-root), it should fail.
    run ./install.sh
    [ "$status" -eq 1 ]
    [[ "$output" == *"must be run as root"* ]]
}

@test "dependency check reports missing dependencies" {
    # Mock pacman to be missing
    command() {
        if [[ "$1" == "-v" && "$2" == "pacman" ]]; then
            return 1
        fi
        builtin command "$@"
    }
    export -f command

    DESTDIR="$TEST_TEMP_DIR/sys" run ./install.sh
    [ "$status" -eq 1 ]
    [[ "$output" == *"dependency 'pacman' is missing"* ]]
}

@test "installation installs all files to correct locations" {
    # Ensure dependencies appear to be present
    command() {
        if [[ "$1" == "-v" && ( "$2" == "pacman" || "$2" == "git" || "$2" == "logger" ) ]]; then
            return 0
        fi
        builtin command "$@"
    }
    export -f command

    local sysdir="$TEST_TEMP_DIR/sys"
    DESTDIR="$sysdir" run ./install.sh
    [ "$status" -eq 0 ]
    
    [ -f "$sysdir/usr/local/bin/cachyos-backup" ]
    [ -f "$sysdir/usr/local/bin/cachyos-recovery" ]
    [ -f "$sysdir/etc/pacman.d/hooks/cachyos-backup.hook" ]
    [ -f "$sysdir/etc/systemd/system/cachyos-backup-extras.timer" ]
    [ -f "$sysdir/etc/systemd/system/cachyos-backup-extras.service" ]
}

@test "uninstall removes system files and preserves configuration" {
    # Ensure dependencies appear to be present
    command() {
        if [[ "$1" == "-v" && ( "$2" == "pacman" || "$2" == "git" || "$2" == "logger" ) ]]; then
            return 0
        fi
        builtin command "$@"
    }
    export -f command

    local sysdir="$TEST_TEMP_DIR/sys"
    DESTDIR="$sysdir" run ./install.sh
    [ "$status" -eq 0 ]
    
    # Verify files were created
    [ -f "$sysdir/usr/local/bin/cachyos-backup" ]
    
    # Create dummy user config and backup repo to verify preservation
    mkdir -p "$TEST_TEMP_DIR/home/.config/cachyos-backup"
    echo "DUMMY CONFIG" > "$TEST_TEMP_DIR/home/.config/cachyos-backup/config"
    mkdir -p "$TEST_TEMP_DIR/home/cachyos-backup"
    echo "DUMMY REPO FILE" > "$TEST_TEMP_DIR/home/cachyos-backup/file.txt"
    
    # Run uninstall
    DESTDIR="$sysdir" run ./uninstall.sh
    [ "$status" -eq 0 ]
    
    # Check that system files are removed
    [ ! -f "$sysdir/usr/local/bin/cachyos-backup" ]
    [ ! -f "$sysdir/usr/local/bin/cachyos-recovery" ]
    [ ! -f "$sysdir/etc/pacman.d/hooks/cachyos-backup.hook" ]
    [ ! -f "$sysdir/etc/systemd/system/cachyos-backup-extras.timer" ]
    [ ! -f "$sysdir/etc/systemd/system/cachyos-backup-extras.service" ]
    
    # Check that config and backup repo are preserved
    [ -f "$TEST_TEMP_DIR/home/.config/cachyos-backup/config" ]
    [ -f "$TEST_TEMP_DIR/home/cachyos-backup/file.txt" ]
}
