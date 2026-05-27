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

@test "chezmoi not installed logs warning and continues" {
    run bash -c "export HOME='$HOME'; export PATH='$MOCK_BIN_DIR'; source src/cachyos-backup && BACKUP_REPO='$TEST_TEMP_DIR/repo' && sync_dotfiles && echo \"\$DOTFILES_CHANGED\""
    [ "$status" -eq 0 ]
    [ "$output" = "skipped" ]
    
    run cat "$TEST_TEMP_DIR/logger_invocations.txt"
    [[ "$output" == *"chezmoi is not installed"* ]]
}

@test "chezmoi re-add executes if installed" {
    mock_command "chezmoi" "
        if [[ \"\$*\" == *\"status\"* ]]; then
            echo 'M somefile'
        elif [[ \"\$*\" == *\"re-add\"* ]]; then
            exit 0
        fi
    "
    run bash -c "export HOME='$HOME'; export PATH='$PATH'; source src/cachyos-backup && BACKUP_REPO='$TEST_TEMP_DIR/repo' && sync_dotfiles && echo \"\$DOTFILES_CHANGED\""
    [ "$status" -eq 0 ]
    [ "$output" = "changed" ]
    
    run cat "$TEST_TEMP_DIR/chezmoi_invocations.txt"
    [[ "$output" == *"status"* ]]
    [[ "$output" == *"re-add"* ]]
}

@test "missing non-pacman manager logs warning and continues" {
    echo "BACKUP_REPO=\"$TEST_TEMP_DIR/repo\"" > "$HOME/.config/cachyos-backup/config"
    echo "EXTRAS_ENABLED=\"flatpak pip cargo npm\"" >> "$HOME/.config/cachyos-backup/config"
    
    run bash -c "export HOME='$HOME'; export PATH='$MOCK_BIN_DIR'; source src/cachyos-backup && load_config && track_extras && echo \"\$EXTRAS_TRACKED\""
    [ "$status" -eq 0 ]
    [ "$output" = "unchanged" ]
    
    run cat "$TEST_TEMP_DIR/logger_invocations.txt"
    [[ "$output" == *"flatpak is enabled but not installed"* ]]
    [[ "$output" == *"pip is enabled but not installed"* ]]
    [[ "$output" == *"cargo is enabled but not installed"* ]]
    [[ "$output" == *"npm is enabled but not installed"* ]]
}

@test "track_extras generates correct files and content" {
    echo "BACKUP_REPO=\"$TEST_TEMP_DIR/repo\"" > "$HOME/.config/cachyos-backup/config"
    echo "EXTRAS_ENABLED=\"flatpak pip cargo npm\"" >> "$HOME/.config/cachyos-backup/config"
    mkdir -p "$TEST_TEMP_DIR/repo"
    
    mock_command "flatpak" "echo 'org.mozilla.firefox'"
    mock_command "pip" "echo 'requests==2.31.0'"
    mock_command "cargo" "echo -e 'ripgrep v14.1.0:\n    rg'"
    mock_command "npm" "echo -e '/usr/lib\n├── typescript@5.3.3'"
    
    run bash -c "export HOME='$HOME'; export PATH='$PATH'; source src/cachyos-backup && load_config && track_extras && echo \"\$EXTRAS_TRACKED\""
    [ "$status" -eq 0 ]
    [[ "$output" == *"flatpak"* ]]
    [[ "$output" == *"pip"* ]]
    [[ "$output" == *"cargo"* ]]
    [[ "$output" == *"npm"* ]]
    
    [ -f "$TEST_TEMP_DIR/repo/flatpak-packages.txt" ]
    run cat "$TEST_TEMP_DIR/repo/flatpak-packages.txt"
    [ "$output" = "org.mozilla.firefox" ]
    
    [ -f "$TEST_TEMP_DIR/repo/pip-packages.txt" ]
    run cat "$TEST_TEMP_DIR/repo/pip-packages.txt"
    [ "$output" = "requests==2.31.0" ]
    
    [ -f "$TEST_TEMP_DIR/repo/cargo-packages.txt" ]
    run cat "$TEST_TEMP_DIR/repo/cargo-packages.txt"
    [ "$output" = "ripgrep 14.1.0" ]
    
    [ -f "$TEST_TEMP_DIR/repo/npm-packages.txt" ]
    run cat "$TEST_TEMP_DIR/repo/npm-packages.txt"
    [ "$output" = "typescript" ]
}
