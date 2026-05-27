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

# Feature: cachyos-package-backup, Property 7: Config validation accepts valid configs and rejects invalid configs
@test "Property 7: Config validation accepts valid configs and rejects invalid configs" {
    mock_command "logger" "exit 0"
    RANDOM=42
    
    # We run the test in the root of the project to find src/cachyos-backup
    cd "$BATS_TEST_DIRNAME/../.."

    # 1. Test 30 valid configurations
    for i in {1..30}; do
        gen_config "true" > "$HOME/.config/cachyos-backup/config"
        run bash -c "export HOME='$HOME'; export PATH='$PATH'; source src/cachyos-backup && load_config && validate_config"
        [ "$status" -eq 0 ]
    done

    # 2. Test 20 invalid configurations
    for i in {1..20}; do
        gen_config "false" > "$HOME/.config/cachyos-backup/config"
        run bash -c "export HOME='$HOME'; export PATH='$PATH'; source src/cachyos-backup && load_config && validate_config"
        [ "$status" -eq 1 ]
    done
}
