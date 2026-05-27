#!/usr/bin/env bats

setup() {
    load '../helpers/setup.bash'
    load '../helpers/generators.bash'
}

# Feature: cachyos-package-backup, Property 4: Cargo install output parsing extracts correct crate names and versions
@test "Property 4: Cargo install output parsing extracts correct crate names and versions" {
    RANDOM=42
    
    for i in {1..30}; do
        local count=$(( 2 + RANDOM % 15 ))
        local input=""
        local expected=""
        for ((c=0; c<count; c++)); do
            local name="crate-$c-$(gen_package_name)"
            local v1=$(( RANDOM % 10 ))
            local v2=$(( RANDOM % 20 ))
            local v3=$(( RANDOM % 50 ))
            local version="${v1}.${v2}.${v3}"
            
            input+="${name} v${version}:
    binary-${name}
"
            expected+="${name} ${version}
"
        done
        
        expected=$(echo -e "$expected" | grep -v '^$' | LC_ALL=C sort)
        
        local result
        result=$(echo -e "$input" | awk '/^[^ ]+ v[0-9]+/ { name=$1; ver=$2; sub(/^v/, "", ver); sub(/:$/, "", ver); print name, ver }' | sed '/^$/d' | LC_ALL=C sort)
        
        [ "$result" = "$expected" ]
    done
}
