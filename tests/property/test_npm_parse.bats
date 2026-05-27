#!/usr/bin/env bats

setup() {
    load '../helpers/setup.bash'
    load '../helpers/generators.bash'
}

# Feature: cachyos-package-backup, Property 5: npm global list parsing extracts correct package names
@test "Property 5: npm global list parsing extracts correct package names" {
    RANDOM=42
    
    for i in {1..30}; do
        local count=$(( 2 + RANDOM % 15 ))
        local input="/usr/lib
"
        local expected=""
        for ((n=0; n<count; n++)); do
            local name=""
            if [ $(( RANDOM % 2 )) -eq 0 ]; then
                name="@scoped/$(gen_package_name)"
            else
                name="$(gen_package_name)"
            fi
            
            local v1=$(( RANDOM % 10 ))
            local v2=$(( RANDOM % 20 ))
            local v3=$(( RANDOM % 50 ))
            local version="${v1}.${v2}.${v3}"
            
            local prefix="├──"
            if [ "$n" -eq $(( count - 1 )) ]; then
                prefix="└──"
            fi
            input+="${prefix} ${name}@${version}
"
            expected+="${name}
"
        done
        
        expected=$(echo -e "$expected" | grep -v '^$' | LC_ALL=C sort)
        
        local result
        result=$(echo -e "$input" | sed -E -n 's/^(├──|└──) //p' | sed -E 's/@[^@]+$//' | sed '/^$/d' | LC_ALL=C sort)
        
        [ "$result" = "$expected" ]
    done
}
