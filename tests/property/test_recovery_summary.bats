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

# Feature: cachyos-package-recovery, Property 6: Recovery summary report includes all categories with correct counts
@test "Property 6: Recovery summary report includes all categories with correct counts" {
    # Mocks
    mock_command "sudo" '"$@"'
    mock_command "chezmoi" 'exit 0'
    
    mock_command "pacman" '
        if [[ "$*" == *"-Q"* ]]; then
            if [[ "$*" == *"skip"* ]]; then
                exit 0
            else
                exit 1
            fi
        elif [[ "$*" == *"-S"* ]]; then
            if [[ "$*" == *"fail"* ]]; then
                exit 1
            else
                exit 0
            fi
        else
            exit 0
        fi
    '
    
    mock_command "yay" '
        if [[ "$*" == *"-S"* ]]; then
            if [[ "$*" == *"fail"* ]]; then
                exit 1
            else
                exit 0
            fi
        else
            exit 0
        fi
    '
    
    mock_command "paru" '
        if [[ "$*" == *"-S"* ]]; then
            if [[ "$*" == *"fail"* ]]; then
                exit 1
            else
                exit 0
            fi
        else
            exit 0
        fi
    '
    
    mock_command "flatpak" '
        if [[ "$*" == *"info"* ]]; then
            if [[ "$*" == *"skip"* ]]; then
                exit 0
            else
                exit 1
            fi
        elif [[ "$*" == *"install"* ]]; then
            if [[ "$*" == *"fail"* ]]; then
                exit 1
            else
                exit 0
            fi
        else
            exit 0
        fi
    '
    
    mock_command "pip" '
        local req_file=""
        for arg in "$@"; do
            if [ -f "$arg" ]; then
                req_file="$arg"
            fi
        done
        if [ -n "$req_file" ] && grep -q "fail" "$req_file"; then
            exit 1
        else
            exit 0
        fi
    '
    
    mock_command "pip3" '
        local req_file=""
        for arg in "$@"; do
            if [ -f "$arg" ]; then
                req_file="$arg"
            fi
        done
        if [ -n "$req_file" ] && grep -q "fail" "$req_file"; then
            exit 1
        else
            exit 0
        fi
    '
    
    mock_command "cargo" '
        if [[ "$*" == *"install --list"* ]]; then
            local file
            file=$(find "$TEST_TEMP_DIR" -name "cargo-packages.txt" | head -n 1)
            if [ -n "$file" ] && [ -f "$file" ]; then
                grep "skip" "$file" | awk '\''{print $1 " v" $2 ":"}'\'' || true
            fi
        elif [[ "$*" == *"install"* ]]; then
            if [[ "$*" == *"fail"* ]]; then
                exit 1
            else
                exit 0
            fi
        else
            exit 0
        fi
    '
    
    mock_command "npm" '
        if [[ "$*" == *"list -g --depth=0"* ]]; then
            local pkg=""
            for arg in "$@"; do
                if [[ "$arg" == *"skip"* ]]; then
                    exit 0
                fi
            done
            exit 1
        elif [[ "$*" == *"install -g"* ]]; then
            if [[ "$*" == *"fail"* ]]; then
                exit 1
            else
                exit 0
            fi
        else
            exit 0
        fi
    '

    RANDOM=42
    cd "$BATS_TEST_DIRNAME/../.."

    # Run 30 randomized iterations
    for i in {1..30}; do
        local repo_dir="$TEST_TEMP_DIR/repo-$i"
        mkdir -p "$repo_dir"
        
        # 1. Official
        local off_inst=$(( RANDOM % 5 ))
        local off_skip=$(( RANDOM % 5 ))
        local off_fail=$(( RANDOM % 5 ))
        
        true > "$repo_dir/user-official.txt"
        for ((j=0; j<off_inst; j++)); do echo "off-inst-$j" >> "$repo_dir/user-official.txt"; done
        for ((j=0; j<off_skip; j++)); do echo "off-skip-$j" >> "$repo_dir/user-official.txt"; done
        for ((j=0; j<off_fail; j++)); do echo "off-fail-$j" >> "$repo_dir/user-official.txt"; done
        
        # 2. Foreign
        local for_inst=$(( RANDOM % 5 ))
        local for_skip=$(( RANDOM % 5 ))
        local for_fail=$(( RANDOM % 5 ))
        
        true > "$repo_dir/user-foreign.txt"
        for ((j=0; j<for_inst; j++)); do echo "for-inst-$j" >> "$repo_dir/user-foreign.txt"; done
        for ((j=0; j<for_skip; j++)); do echo "for-skip-$j" >> "$repo_dir/user-foreign.txt"; done
        for ((j=0; j<for_fail; j++)); do echo "for-fail-$j" >> "$repo_dir/user-foreign.txt"; done
        
        # 3. Flatpak
        local fp_inst=$(( RANDOM % 5 ))
        local fp_skip=$(( RANDOM % 5 ))
        local fp_fail=$(( RANDOM % 5 ))
        
        true > "$repo_dir/flatpak-packages.txt"
        for ((j=0; j<fp_inst; j++)); do echo "fp-inst-$j" >> "$repo_dir/flatpak-packages.txt"; done
        for ((j=0; j<fp_skip; j++)); do echo "fp-skip-$j" >> "$repo_dir/flatpak-packages.txt"; done
        for ((j=0; j<fp_fail; j++)); do echo "fp-fail-$j" >> "$repo_dir/flatpak-packages.txt"; done
        
        # 4. Pip
        local pip_total=$(( RANDOM % 5 ))
        local pip_should_fail=$(( RANDOM % 2 ))
        local pip_inst=0
        local pip_fail=0
        local pip_skip=0
        
        true > "$repo_dir/pip-packages.txt"
        for ((j=0; j<pip_total; j++)); do
            if [ "$pip_should_fail" -eq 1 ]; then
                echo "pip-fail-$j==1.0" >> "$repo_dir/pip-packages.txt"
            else
                echo "pip-inst-$j==1.0" >> "$repo_dir/pip-packages.txt"
            fi
        done
        if [ "$pip_total" -gt 0 ]; then
            if [ "$pip_should_fail" -eq 1 ]; then
                pip_fail=$pip_total
            else
                pip_inst=$pip_total
            fi
        fi
        
        # 5. Cargo
        local cg_inst=$(( RANDOM % 5 ))
        local cg_skip=$(( RANDOM % 5 ))
        local cg_fail=$(( RANDOM % 5 ))
        
        true > "$repo_dir/cargo-packages.txt"
        for ((j=0; j<cg_inst; j++)); do echo "cg-inst-$j 1.0" >> "$repo_dir/cargo-packages.txt"; done
        for ((j=0; j<cg_skip; j++)); do echo "cg-skip-$j 1.0" >> "$repo_dir/cargo-packages.txt"; done
        for ((j=0; j<cg_fail; j++)); do echo "cg-fail-$j 1.0" >> "$repo_dir/cargo-packages.txt"; done
        
        # 6. Npm
        local npm_inst=$(( RANDOM % 5 ))
        local npm_skip=$(( RANDOM % 5 ))
        local npm_fail=$(( RANDOM % 5 ))
        
        true > "$repo_dir/npm-packages.txt"
        for ((j=0; j<npm_inst; j++)); do echo "npm-inst-$j" >> "$repo_dir/npm-packages.txt"; done
        for ((j=0; j<npm_skip; j++)); do echo "npm-skip-$j" >> "$repo_dir/npm-packages.txt"; done
        for ((j=0; j<npm_fail; j++)); do echo "npm-fail-$j" >> "$repo_dir/npm-packages.txt"; done
        
        run ./src/cachyos-recovery --local "$repo_dir" --aur-helper yay --skip-dotfiles
        if [ "$status" -ne 0 ]; then
            echo "STATUS: $status" >&2
            echo "OUTPUT: $output" >&2
            [ "$status" -eq 0 ]
        fi
        
        # Validate output summary counts
        # Check Official
        [[ "$output" == *"Official: installed=$off_inst, skipped=$off_skip, failed=$off_fail"* ]]
        # Check Foreign
        [[ "$output" == *"Foreign: installed=$for_inst, skipped=$for_skip, failed=$for_fail"* ]]
        # Check Flatpak
        [[ "$output" == *"Flatpak: installed=$fp_inst, skipped=$fp_skip, failed=$fp_fail"* ]]
        # Check Pip
        [[ "$output" == *"Pip: installed=$pip_inst, skipped=$pip_skip, failed=$pip_fail"* ]]
        # Check Cargo
        [[ "$output" == *"Cargo: installed=$cg_inst, skipped=$cg_skip, failed=$cg_fail"* ]]
        # Check Npm
        [[ "$output" == *"Npm: installed=$npm_inst, skipped=$npm_skip, failed=$npm_fail"* ]]
    done
}
