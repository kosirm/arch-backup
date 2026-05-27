#!/usr/bin/env bats

setup() {
    load '../helpers/setup.bash'
    load '../helpers/mocks.bash'
    load '../helpers/generators.bash'
    setup_test_env
}

teardown() {
    teardown_test_env
}

# Feature: cachyos-package-backup, Property 2: Package diff computes correct set difference
@test "Property 2: Package diff computes correct set difference" {
    mock_command "logger" "exit 0"
    RANDOM=42
    
    cd "$BATS_TEST_DIRNAME/../.."
    
    for i in {1..20}; do
        local baseline_count=$(( 10 + RANDOM % 20 ))
        local baseline_list
        baseline_list=$(gen_package_list "$baseline_count")
        
        local added_count=$(( 2 + RANDOM % 10 ))
        local added_list
        added_list=$(gen_package_list "$added_count")
        
        local current_list
        current_list=$(printf "%s\n%s" "$baseline_list" "$added_list" | LC_ALL=C sort -u)
        
        rm -rf "$TEST_TEMP_DIR/repo"
        mkdir -p "$TEST_TEMP_DIR/repo"
        
        echo "$baseline_list" > "$TEST_TEMP_DIR/repo/baseline-official.txt"
        echo "" > "$TEST_TEMP_DIR/repo/baseline-foreign.txt"
        
        mock_command "pacman" "
            if [[ \"\$*\" == *\"-Qqen\"* ]]; then
                echo -e \"$current_list\"
            elif [[ \"\$*\" == *\"-Qqem\"* ]]; then
                echo \"\"
            else
                exit 1
            fi
        "
        
        run bash -c "export HOME='$HOME'; export PATH='$PATH'; source src/cachyos-backup && BACKUP_REPO='$TEST_TEMP_DIR/repo' && compute_diff"
        [ "$status" -eq 0 ]
        
        local user_official="$TEST_TEMP_DIR/repo/user-official.txt"
        [ -f "$user_official" ]
        
        run cat "$user_official"
        
        local expected_diff
        expected_diff=$(LC_ALL=C comm -23 <(echo "$current_list") <(echo "$baseline_list"))
        
        [ "$output" = "$expected_diff" ]
    done
}
