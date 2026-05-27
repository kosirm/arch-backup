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

@test "git repo not initialized exits with error" {
    mkdir -p "$TEST_TEMP_DIR/repo"
    run bash -c "export HOME='$HOME'; export PATH='$PATH'; source src/cachyos-backup && BACKUP_REPO='$TEST_TEMP_DIR/repo' && git_commit_push"
    [ "$status" -eq 1 ]
    [[ "$output" == *"not initialized as a git repository"* ]]
}

@test "no changes detected skips commit and push" {
    mkdir -p "$TEST_TEMP_DIR/repo/.git"
    mock_command "git" "
        if [[ \"\$*\" == *\"status --porcelain\"* ]]; then
            echo \"\"
        fi
    "
    run bash -c "export HOME='$HOME'; export PATH='$PATH'; source src/cachyos-backup && BACKUP_REPO='$TEST_TEMP_DIR/repo' && git_commit_push"
    [ "$status" -eq 0 ]
    
    run cat "$TEST_TEMP_DIR/git_invocations.txt"
    [[ "$output" != *"commit"* ]]
}

@test "git push failure logs error and exits non-zero" {
    mkdir -p "$TEST_TEMP_DIR/repo/.git"
    mock_command "git" "
        if [[ \"\$*\" == *\"status --porcelain\"* ]]; then
            echo \"M user-official.txt\"
        elif [[ \"\$*\" == *\"push\"* ]]; then
            echo \"Fatal: network error\" >&2
            exit 1
        else
            exit 0
        fi
    "
    run bash -c "export HOME='$HOME'; export PATH='$PATH'; source src/cachyos-backup && BACKUP_REPO='$TEST_TEMP_DIR/repo' && GITHUB_REMOTE='git@github.com:test.git' && git_commit_push"
    [ "$status" -eq 1 ]
    
    run cat "$TEST_TEMP_DIR/logger_invocations.txt"
    [[ "$output" == *"Git push failed: Fatal: network error"* ]]
}
