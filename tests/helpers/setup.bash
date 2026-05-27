# Test setup and teardown helpers
export TEST_TEMP_DIR=""

setup_test_env() {
    TEST_TEMP_DIR="$(mktemp -d)"
    export HOME="$TEST_TEMP_DIR/home"
    mkdir -p "$HOME/.config/cachyos-backup"
    
    export MOCK_BIN_DIR="$TEST_TEMP_DIR/bin"
    mkdir -p "$MOCK_BIN_DIR"
    ln -sf "$(command -v env)" "$MOCK_BIN_DIR/env"
    ln -sf "$(command -v bash)" "$MOCK_BIN_DIR/bash"
    export PATH="$MOCK_BIN_DIR:$PATH"
}

teardown_test_env() {
    if [ -n "${TEST_TEMP_DIR:-}" ] && [ -d "$TEST_TEMP_DIR" ]; then
        rm -rf "$TEST_TEMP_DIR"
    fi
}

# Simple assertions in case bats-assert/bats-support are not available
assert_success() {
    if [ "$status" -ne 0 ]; then
        echo "Expected success (exit code 0), but got exit code $status" >&2
        echo "Output: $output" >&2
        return 1
    fi
}

assert_failure() {
    local expected_code="${1:-}"
    if [ "$status" -eq 0 ]; then
        echo "Expected failure, but command succeeded" >&2
        return 1
    fi
    if [ -n "$expected_code" ] && [ "$status" -ne "$expected_code" ]; then
        echo "Expected exit code $expected_code, but got $status" >&2
        return 1
    fi
}

assert_output_contains() {
    local expected="$1"
    if [[ "$output" != *"$expected"* ]]; then
        echo "Expected output to contain: '$expected'" >&2
        echo "Actual output: '$output'" >&2
        return 1
    fi
}

assert_equal() {
    local val1="$1"
    local val2="$2"
    if [ "$val1" != "$val2" ]; then
        echo "Expected '$val1' to equal '$val2'" >&2
        return 1
    fi
}
