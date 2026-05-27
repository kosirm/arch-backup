# Mocks for external commands

mock_command() {
    local cmd="$1"
    local mock_body="$2"
    cat <<EOF > "$MOCK_BIN_DIR/$cmd"
#!/usr/bin/env bash
# Record invocation
echo "\$@" >> "$TEST_TEMP_DIR/${cmd}_invocations.txt"
# Run mock body
$mock_body
EOF
    chmod +x "$MOCK_BIN_DIR/$cmd"
}

get_mock_invocations() {
    local cmd="$1"
    if [ -f "$TEST_TEMP_DIR/${cmd}_invocations.txt" ]; then
        cat "$TEST_TEMP_DIR/${cmd}_invocations.txt"
    else
        return 0
    fi
}

clear_mock_invocations() {
    local cmd="$1"
    rm -f "$TEST_TEMP_DIR/${cmd}_invocations.txt"
}
