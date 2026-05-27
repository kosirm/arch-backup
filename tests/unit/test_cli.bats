#!/usr/bin/env bats

setup() {
    load '../helpers/setup.bash'
    load '../helpers/mocks.bash'
    setup_test_env
    mock_command "logger" "exit 0"
    mock_command "pacman" "echo 'pkg'"
    mock_command "git" "exit 0"
    mock_command "chezmoi" "exit 0"
    cd "$BATS_TEST_DIRNAME/../.."
}

teardown() {
    teardown_test_env
}

@test "help flag prints usage" {
    run ./src/cachyos-backup --help
    [ "$status" -eq 0 ]
    [[ "$output" == *"Usage: cachyos-backup"* ]]
}

@test "invalid flag prints error and usage" {
    run ./src/cachyos-backup --invalid-flag
    [ "$status" -eq 1 ]
    [[ "$output" == *"Unknown option: --invalid-flag"* ]]
}

@test "backup flag triggers full flow" {
    echo "BACKUP_REPO=\"$TEST_TEMP_DIR/repo\"" > "$HOME/.config/cachyos-backup/config"
    echo "GITHUB_REMOTE=\"git@github.com:test/repo.git\"" >> "$HOME/.config/cachyos-backup/config"
    mkdir -p "$TEST_TEMP_DIR/repo/.git"
    
    echo "pkg1" > "$TEST_TEMP_DIR/repo/baseline-official.txt"
    echo "pkg2" > "$TEST_TEMP_DIR/repo/baseline-foreign.txt"
    
    mock_command "pacman" "echo 'pkg1'"
    
    run ./src/cachyos-backup --backup
    [ "$status" -eq 0 ]
    
    run cat "$TEST_TEMP_DIR/logger_invocations.txt"
    [[ "$output" == *"Starting backup"* ]]
    [[ "$output" == *"Completed. Tracked official"* ]]
}
