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

# Feature: cachyos-package-backup, Property 1: Package list output is sorted with one name per line
@test "Property 1: Package list output is sorted with one name per line" {
    mock_command "logger" "exit 0"
    RANDOM=42
    
    cd "$BATS_TEST_DIRNAME/../.."
    
    for i in {1..20}; do
        rm -rf "$TEST_TEMP_DIR/repo"
        local count=$(( 5 + RANDOM % 20 ))
        local raw_list=""
        for ((j=0; j<count; j++)); do
            raw_list+="$(gen_package_name)
"
        done
        # Add duplicate and empty lines
        raw_list+="
duplicate-pkg
duplicate-pkg
"
        
        mock_command "pacman" "
            if [[ \"\$*\" == *\"-Qqen\"* ]]; then
                echo -e \"$raw_list\"
            elif [[ \"\$*\" == *\"-Qqem\"* ]]; then
                echo \"\"
            else
                exit 1
            fi
        "
        
        run bash -c "export HOME='$HOME'; export PATH='$PATH'; source src/cachyos-backup && BACKUP_REPO='$TEST_TEMP_DIR/repo' && capture_baseline < /dev/null"
        [ "$status" -eq 0 ]
        
        local baseline_file="$TEST_TEMP_DIR/repo/baseline-official.txt"
        [ -f "$baseline_file" ]
        
        run cat "$baseline_file"
        
        # Deduplicate, remove empty lines, and sort in LC_ALL=C order
        local sorted_expected
        sorted_expected=$(echo -e "$raw_list" | grep -v '^$' | LC_ALL=C sort)
        
        [ "$output" = "$sorted_expected" ]
    done
}
