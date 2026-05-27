# Random input generators for property-based tests

gen_package_name() {
    local chars="abcdefghijklmnopqrstuvwxyz0123456789-."
    local len=$(( 5 + RANDOM % 10 ))
    local name=""
    for ((i=0; i<len; i++)); do
        name="${name}${chars:$(( RANDOM % ${#chars} )):1}"
    done
    # Clean leading/trailing hyphens/dots in pure Bash
    while [[ "$name" == [-.]* ]]; do
        name="${name#?}"
    done
    while [[ "$name" == *[-.] ]]; do
        name="${name%?}"
    done
    # If name ended up empty, return a default
    if [ -z "$name" ]; then
        name="package-default"
    fi
    echo "$name"
}

gen_package_list() {
    local count="$1"
    local list=()
    for ((j=0; j<count; j++)); do
        list+=("$(gen_package_name)")
    done
    # Deduplicate and sort in LC_ALL=C order
    printf "%s\n" "${list[@]}" | LC_ALL=C sort -u
}

gen_config() {
    local valid="$1" # true or false
    local backup_repo="/home/milan/cachyos-backup"
    local git_remote="git@github.com:milan/cachyos-backup.git"
    local helper="yay"
    local extras="flatpak pip"
    
    if [ "$valid" = "false" ]; then
        # Pick one of the fields to corrupt
        case $(( RANDOM % 4 )) in
            0) backup_repo="" ;; # empty path
            1) git_remote="invalid-url" ;; # invalid remote URL
            2) helper="invalid_helper" ;; # invalid helper
            3) extras="flatpak invalid_extra" ;; # invalid extra manager
        esac
    fi
    
    cat <<EOF
BACKUP_REPO="$backup_repo"
GITHUB_REMOTE="$git_remote"
AUR_HELPER="$helper"
EXTRAS_ENABLED="$extras"
CHEZMOI_SOURCE=""
TIMER_INTERVAL="daily"
EOF
}

gen_cargo_output() {
    local count="$1"
    for ((c=0; c<count; c++)); do
        local name="$(gen_package_name)"
        local v1=$(( RANDOM % 10 ))
        local v2=$(( RANDOM % 20 ))
        local v3=$(( RANDOM % 50 ))
        echo "${name} v${v1}.${v2}.${v3}:"
        echo "    ${name}"
    done
}

gen_npm_output() {
    local count="$1"
    echo "/usr/lib"
    for ((n=0; n<count; n++)); do
        local name="$(gen_package_name)"
        local v1=$(( RANDOM % 10 ))
        local v2=$(( RANDOM % 20 ))
        local v3=$(( RANDOM % 50 ))
        local prefix="├──"
        if [ "$n" -eq $(( count - 1 )) ]; then
            prefix="└──"
        fi
        echo "${prefix} ${name}@${v1}.${v2}.${v3}"
    done
}

gen_counts() {
    local succ=$(( RANDOM % 50 ))
    local skip=$(( RANDOM % 50 ))
    local fail=$(( RANDOM % 5 ))
    echo "$succ $skip $fail"
}
