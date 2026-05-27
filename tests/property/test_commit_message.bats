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

# Feature: cachyos-package-backup, Property 3: Commit message contains timestamp and accurate change counts
@test "Property 3: Commit message contains timestamp and accurate change counts" {
    mock_command "logger" "exit 0"
    mock_command "git" "/usr/bin/git \"\$@\""
    
    RANDOM=42
    
    cd "$BATS_TEST_DIRNAME/../.."
    
    for i in {1..30}; do
        rm -rf "$TEST_TEMP_DIR/repo"
        mkdir -p "$TEST_TEMP_DIR/repo"
        
        run git -C "$TEST_TEMP_DIR/repo" init
        run git -C "$TEST_TEMP_DIR/repo" config user.email "test@example.com"
        run git -C "$TEST_TEMP_DIR/repo" config user.name "Test User"
        
        local counts1=($(gen_counts))
        local add_off=${counts1[0]}
        local rem_off=${counts1[1]}
        
        local counts2=($(gen_counts))
        local add_for=${counts2[0]}
        local rem_for=${counts2[1]}
        
        local df_status="changed"
        if [ $(( RANDOM % 2 )) -eq 0 ]; then df_status="unchanged"; fi
        local ext_status="flatpak"
        if [ $(( RANDOM % 2 )) -eq 0 ]; then ext_status="unchanged"; fi
        
        local base_off=""
        for ((j=0; j<rem_off; j++)); do base_off+="rem-off-$j\n"; done
        for ((j=0; j<10; j++)); do base_off+="common-off-$j\n"; done
        
        local base_for=""
        for ((j=0; j<rem_for; j++)); do base_for+="rem-for-$j\n"; done
        for ((j=0; j<10; j++)); do base_for+="common-for-$j\n"; done
        
        echo -e "$base_off" | LC_ALL=C sort > "$TEST_TEMP_DIR/repo/user-official.txt"
        echo -e "$base_for" | LC_ALL=C sort > "$TEST_TEMP_DIR/repo/user-foreign.txt"
        
        run git -C "$TEST_TEMP_DIR/repo" add -A
        run git -C "$TEST_TEMP_DIR/repo" commit -m "initial"
        
        local new_off=""
        for ((j=0; j<add_off; j++)); do new_off+="add-off-$j\n"; done
        for ((j=0; j<10; j++)); do new_off+="common-off-$j\n"; done
        
        local new_for=""
        for ((j=0; j<add_for; j++)); do new_for+="add-for-$j\n"; done
        for ((j=0; j<10; j++)); do new_for+="common-for-$j\n"; done
        
        echo -e "$new_off" | LC_ALL=C sort > "$TEST_TEMP_DIR/repo/user-official.txt"
        echo -e "$new_for" | LC_ALL=C sort > "$TEST_TEMP_DIR/repo/user-foreign.txt"
        
        run bash -c "export HOME='$HOME'; export PATH='$PATH'; source src/cachyos-backup && BACKUP_REPO='$TEST_TEMP_DIR/repo' && GITHUB_REMOTE='' && DOTFILES_CHANGED='$df_status' && EXTRAS_TRACKED='$ext_status' && git_commit_push"
        [ "$status" -eq 0 ]
        
        local commit_msg
        commit_msg=$(git -C "$TEST_TEMP_DIR/repo" log -1 --pretty=%B)
        
        [[ "$commit_msg" == *"Packages: +$add_off -$rem_off official, +$add_for -$rem_for foreign"* ]]
        [[ "$commit_msg" == *"Dotfiles: $df_status"* ]]
        [[ "$commit_msg" == *"Extras: $ext_status"* ]]
        [[ "$commit_msg" =~ [0-9]{4}-[0-9]{2}-[0-9]{2}\ [0-9]{2}:[0-9]{2}:[0-9]{2} ]]
    done
}
