#!/usr/bin/env bats

setup() {
    load '../helpers/setup.bash'
    load '../helpers/mocks.bash'
    setup_test_env
    mock_command "logger" "exit 0"
    cd "$BATS_TEST_DIRNAME/../.."
}

teardown() {
    teardown_test_env
}

@test "missing config file applies defaults and logs warning" {
    rm -f "$HOME/.config/cachyos-backup/config"
    
    run bash -c "export HOME='$HOME'; export PATH='$PATH'; source src/cachyos-backup && load_config && echo \"\$BACKUP_REPO\""
    [ "$status" -eq 0 ]
    # The default contains /cachyos-backup
    [[ "$output" == *"/cachyos-backup"* ]]
    
    # Check if warning was logged
    run cat "$TEST_TEMP_DIR/logger_invocations.txt"
    [[ "$output" == *"Configuration file not found"* ]]
}

@test "init creates config file with defaults" {
    run bash -c "export HOME='$HOME'; export PATH='$PATH'; ./src/cachyos-backup --init < /dev/null"
    [ "$status" -eq 0 ]
    
    [ -f "$HOME/.config/cachyos-backup/config" ]
    run cat "$HOME/.config/cachyos-backup/config"
    [[ "$output" == *"BACKUP_REPO="* ]]
    [[ "$output" == *"AUR_HELPER=\"yay\""* ]]
}

@test "validation rejects empty or malformed parameters" {
    # 1. Test empty BACKUP_REPO
    echo "BACKUP_REPO=\"\"" > "$HOME/.config/cachyos-backup/config"
    run bash -c "export HOME='$HOME'; export PATH='$PATH'; source src/cachyos-backup && load_config && validate_config"
    [ "$status" -eq 1 ]
    [[ "$output" == *"BACKUP_REPO is empty"* ]]
    
    # 2. Test invalid GITHUB_REMOTE
    echo "BACKUP_REPO=\"$HOME/cachyos-backup\"" > "$HOME/.config/cachyos-backup/config"
    echo "GITHUB_REMOTE=\"not_a_git_url\"" >> "$HOME/.config/cachyos-backup/config"
    run bash -c "export HOME='$HOME'; export PATH='$PATH'; source src/cachyos-backup && load_config && validate_config"
    [ "$status" -eq 1 ]
    [[ "$output" == *"GITHUB_REMOTE"* ]]
    
    # 3. Test invalid AUR_HELPER
    echo "BACKUP_REPO=\"$HOME/cachyos-backup\"" > "$HOME/.config/cachyos-backup/config"
    echo "AUR_HELPER=\"apt\"" >> "$HOME/.config/cachyos-backup/config"
    run bash -c "export HOME='$HOME'; export PATH='$PATH'; source src/cachyos-backup && load_config && validate_config"
    [ "$status" -eq 1 ]
    [[ "$output" == *"AUR_HELPER must be 'yay' or 'paru'"* ]]
    
    # 4. Test invalid EXTRAS_ENABLED
    echo "BACKUP_REPO=\"$HOME/cachyos-backup\"" > "$HOME/.config/cachyos-backup/config"
    echo "EXTRAS_ENABLED=\"flatpak invalid_manager\"" >> "$HOME/.config/cachyos-backup/config"
    run bash -c "export HOME='$HOME'; export PATH='$PATH'; source src/cachyos-backup && load_config && validate_config"
    [ "$status" -eq 1 ]
    [[ "$output" == *"Invalid extra manager"* ]]
}
