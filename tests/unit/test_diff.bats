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

@test "missing baseline files exits with error" {
    mkdir -p "$TEST_TEMP_DIR/repo"
    run bash -c "export HOME='$HOME'; export PATH='$PATH'; source src/cachyos-backup && BACKUP_REPO='$TEST_TEMP_DIR/repo' && compute_diff"
    [ "$status" -eq 1 ]
    [[ "$output" == *"Baseline snapshot files not found"* ]]
}

@test "diff outputs files with correct names and content" {
    mkdir -p "$TEST_TEMP_DIR/repo"
    echo -e "base1\nbase2" > "$TEST_TEMP_DIR/repo/baseline-official.txt"
    echo -e "fbase1" > "$TEST_TEMP_DIR/repo/baseline-foreign.txt"
    
    mock_command "pacman" "
        if [[ \"\$*\" == *\"-Qqen\"* ]]; then
            echo -e \"base1\nbase2\nuser1\nuser2\"
        elif [[ \"\$*\" == *\"-Qqem\"* ]]; then
            echo -e \"fbase1\nfuser1\"
        else
            exit 1
        fi
    "
    
    run bash -c "export HOME='$HOME'; export PATH='$PATH'; source src/cachyos-backup && BACKUP_REPO='$TEST_TEMP_DIR/repo' && compute_diff"
    [ "$status" -eq 0 ]
    
    [ -f "$TEST_TEMP_DIR/repo/user-official.txt" ]
    [ -f "$TEST_TEMP_DIR/repo/user-foreign.txt" ]
    
    run cat "$TEST_TEMP_DIR/repo/user-official.txt"
    [ "${lines[0]}" = "user1" ]
    [ "${lines[1]}" = "user2" ]
    
    run cat "$TEST_TEMP_DIR/repo/user-foreign.txt"
    [ "${lines[0]}" = "fuser1" ]
}

@test "system update with no new packages produces unchanged diff" {
    mkdir -p "$TEST_TEMP_DIR/repo"
    echo -e "base1\nbase2" > "$TEST_TEMP_DIR/repo/baseline-official.txt"
    echo -e "fbase1" > "$TEST_TEMP_DIR/repo/baseline-foreign.txt"
    
    mock_command "pacman" "
        if [[ \"\$*\" == *\"-Qqen\"* ]]; then
            echo -e \"base1\nbase2\"
        elif [[ \"\$*\" == *\"-Qqem\"* ]]; then
            echo -e \"fbase1\"
        else
            exit 1
        fi
    "
    
    run bash -c "export HOME='$HOME'; export PATH='$PATH'; source src/cachyos-backup && BACKUP_REPO='$TEST_TEMP_DIR/repo' && compute_diff"
    [ "$status" -eq 0 ]
    
    run cat "$TEST_TEMP_DIR/repo/user-official.txt"
    [ "$output" = "" ]
    
    run cat "$TEST_TEMP_DIR/repo/user-foreign.txt"
    [ "$output" = "" ]
}
