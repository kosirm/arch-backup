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

@test "missing pacman exits with error" {
    local bin_no_pacman="$TEST_TEMP_DIR/bin_no_pacman"
    mkdir -p "$bin_no_pacman"
    for cmd in env bash logger mkdir sh; do
        ln -sf "$(command -v $cmd)" "$bin_no_pacman/$cmd"
    done
    run bash -c "export HOME='$HOME'; export PATH='$bin_no_pacman'; ./src/cachyos-backup --baseline"
    [ "$status" -eq 1 ]
    [[ "$output" == *"pacman command not found"* ]]
}

@test "baseline files are created with correct names and sorted content" {
    mock_command "pacman" "
        if [[ \"\$*\" == *\"-Qqen\"* ]]; then
            echo -e \"z-pkg\na-pkg\nm-pkg\"
        elif [[ \"\$*\" == *\"-Qqem\"* ]]; then
            echo -e \"foreign-z\nforeign-a\"
        else
            exit 1
        fi
    "
    
    run bash -c "export HOME='$HOME'; export PATH='$PATH'; source src/cachyos-backup && BACKUP_REPO='$TEST_TEMP_DIR/repo' && capture_baseline < /dev/null"
    [ "$status" -eq 0 ]
    
    [ -f "$TEST_TEMP_DIR/repo/baseline-official.txt" ]
    [ -f "$TEST_TEMP_DIR/repo/baseline-foreign.txt" ]
    
    run cat "$TEST_TEMP_DIR/repo/baseline-official.txt"
    [ "${lines[0]}" = "a-pkg" ]
    [ "${lines[1]}" = "m-pkg" ]
    [ "${lines[2]}" = "z-pkg" ]
    
    run cat "$TEST_TEMP_DIR/repo/baseline-foreign.txt"
    [ "${lines[0]}" = "foreign-a" ]
    [ "${lines[1]}" = "foreign-z" ]
}

@test "baseline overwrite confirmation works - declined" {
    mock_command "pacman" "echo 'pkg'"
    
    mkdir -p "$TEST_TEMP_DIR/repo"
    echo "old-official" > "$TEST_TEMP_DIR/repo/baseline-official.txt"
    echo "old-foreign" > "$TEST_TEMP_DIR/repo/baseline-foreign.txt"
    
    run bash -c "export HOME='$HOME'; export PATH='$PATH'; source src/cachyos-backup && BACKUP_REPO='$TEST_TEMP_DIR/repo' && (echo 'n' | capture_baseline)"
    [ "$status" -eq 0 ]
    
    run cat "$TEST_TEMP_DIR/repo/baseline-official.txt"
    [[ "$output" == *"old-official"* ]]
}

@test "baseline overwrite confirmation works - accepted" {
    mock_command "pacman" "
        if [[ \"\$*\" == *\"-Qqen\"* ]]; then
            echo \"new-official\"
        else
            echo \"new-foreign\"
        fi
    "
    
    mkdir -p "$TEST_TEMP_DIR/repo"
    echo "old-official" > "$TEST_TEMP_DIR/repo/baseline-official.txt"
    echo "old-foreign" > "$TEST_TEMP_DIR/repo/baseline-foreign.txt"
    
    run bash -c "export HOME='$HOME'; export PATH='$PATH'; source src/cachyos-backup && BACKUP_REPO='$TEST_TEMP_DIR/repo' && (echo 'y' | capture_baseline)"
    [ "$status" -eq 0 ]
    
    run cat "$TEST_TEMP_DIR/repo/baseline-official.txt"
    [[ "$output" == *"new-official"* ]]
}
