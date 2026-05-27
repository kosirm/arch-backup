#!/usr/bin/env bats

setup() {
    load '../helpers/setup.bash'
    load '../helpers/mocks.bash'
    setup_test_env
}

teardown() {
    teardown_test_env
}

@test "missing AUR helper prints error with package list" {
    # Export a mock command function to simulate absence of yay and paru
    command() {
        if [[ "$1" == "-v" && ( "$2" == "yay" || "$2" == "paru" ) ]]; then
            return 1
        fi
        builtin command "$@"
    }
    export -f command

    mkdir -p "$TEST_TEMP_DIR/repo"
    echo "foreign-pkg1" > "$TEST_TEMP_DIR/repo/user-foreign.txt"
    echo "foreign-pkg2" >> "$TEST_TEMP_DIR/repo/user-foreign.txt"
    
    run ./src/cachyos-recovery --local "$TEST_TEMP_DIR/repo" --skip-dotfiles --skip-extras
    if [ "$status" -ne 1 ]; then
        echo "STATUS: $status" >&2
        echo "OUTPUT: $output" >&2
        [ "$status" -eq 1 ]
    fi
    [[ "$output" == *"AUR helper is not available"* ]]
    [[ "$output" == *"foreign-pkg1"* ]]
    [[ "$output" == *"foreign-pkg2"* ]]
}

@test "unavailable package logs warning and continues" {
    mock_command "sudo" '"$@"'
    mock_command "pacman" '
        if [[ "$*" == *"-Q"* ]]; then
            exit 1
        elif [[ "$*" == *"-S"* ]]; then
            if [[ "$*" == *"badpkg"* ]]; then
                exit 1
            else
                exit 0
            fi
        else
            exit 0
        fi
    '
    
    mkdir -p "$TEST_TEMP_DIR/repo"
    echo "goodpkg" > "$TEST_TEMP_DIR/repo/user-official.txt"
    echo "badpkg" >> "$TEST_TEMP_DIR/repo/user-official.txt"
    
    run ./src/cachyos-recovery --local "$TEST_TEMP_DIR/repo" --skip-dotfiles --skip-extras
    [ "$status" -eq 0 ]
    [[ "$output" == *"Failed to install official package 'badpkg'"* ]]
    [[ "$output" == *"Official: installed=1, skipped=0, failed=1"* ]]
}

@test "dry-run shows what would be installed without installing" {
    # If dry-run is on, we do not call pacman or yay.
    # We mock pacman and yay to return 1 on -Q so they appear not installed.
    mock_command "pacman" '
        if [[ "$*" == *"-Q"* ]]; then
            exit 1
        else
            echo "pacman run"
        fi
    '
    mock_command "yay" '
        if [[ "$*" == *"-Q"* ]]; then
            exit 1
        else
            echo "yay run"
        fi
    '
    
    mkdir -p "$TEST_TEMP_DIR/repo"
    echo "pkg1" > "$TEST_TEMP_DIR/repo/user-official.txt"
    echo "pkg2" > "$TEST_TEMP_DIR/repo/user-foreign.txt"
    
    run ./src/cachyos-recovery --local "$TEST_TEMP_DIR/repo" --aur-helper yay --skip-dotfiles --skip-extras --dry-run
    [ "$status" -eq 0 ]
    [[ "$output" == *"[DRY RUN] Would install official package: pkg1"* ]]
    [[ "$output" == *"[DRY RUN] Would install foreign package: pkg2 using yay"* ]]
    
    # Verify no actual install commands were run
    run cat "$TEST_TEMP_DIR/pacman_invocations.txt"
    [[ "$output" != *"-S"* ]]
    
    # Since yay was not run, there should be no invocations file or it shouldn't contain -S
    if [ -f "$TEST_TEMP_DIR/yay_invocations.txt" ]; then
        run cat "$TEST_TEMP_DIR/yay_invocations.txt"
        [[ "$output" != *"-S"* ]]
    fi
}

@test "skip-dotfiles and skip-extras flags skip their steps" {
    mock_command "chezmoi" 'echo "chezmoi run"'
    mock_command "flatpak" 'echo "flatpak run"'
    mock_command "pip" 'echo "pip run"'
    mock_command "pip3" 'echo "pip3 run"'
    mock_command "cargo" 'echo "cargo run"'
    mock_command "npm" 'echo "npm run"'
    
    mkdir -p "$TEST_TEMP_DIR/repo"
    echo "flatpak-app" > "$TEST_TEMP_DIR/repo/flatpak-packages.txt"
    echo "pip-pkg==1.0" > "$TEST_TEMP_DIR/repo/pip-packages.txt"
    echo "cargo-pkg v1.0:" > "$TEST_TEMP_DIR/repo/cargo-packages.txt"
    echo "npm-pkg" > "$TEST_TEMP_DIR/repo/npm-packages.txt"
    
    run ./src/cachyos-recovery --local "$TEST_TEMP_DIR/repo" --skip-dotfiles --skip-extras
    [ "$status" -eq 0 ]
    
    # Assert that no dotfile/extras tools were invoked
    [ ! -f "$TEST_TEMP_DIR/chezmoi_invocations.txt" ]
    [ ! -f "$TEST_TEMP_DIR/flatpak_invocations.txt" ]
    [ ! -f "$TEST_TEMP_DIR/pip_invocations.txt" ]
    [ ! -f "$TEST_TEMP_DIR/pip3_invocations.txt" ]
    [ ! -f "$TEST_TEMP_DIR/cargo_invocations.txt" ]
    [ ! -f "$TEST_TEMP_DIR/npm_invocations.txt" ]
}
