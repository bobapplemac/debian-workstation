#!/bin/bash
set -Eeuo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
gearlever() { flatpak run it.mijorus.gearlever "$@"; }
find_notepadqq() {
    gearlever --list-installed --json | python3 "$here/find-installed.py"
}
path=$(find_notepadqq)
if [[ -z $path ]]; then
    work=$(mktemp -d)
    trap 'rm -rf -- "$work"' EXIT
    trap 'exit 130' INT
    trap 'exit 143' HUP TERM
    asset=notepadqq-latest-linux-x86_64.AppImage
    python3 "$here/github-release.py" "$work/$asset"
    chmod 0755 "$work/$asset"
    gearlever --integrate "$work/$asset" --yes --replace
    path=$(find_notepadqq)
fi
[[ -n $path && -f $path ]] || {
    echo 'Gear Lever did not return an existing managed Notepadqq file after integration.' >&2
    echo 'Inspect: flatpak run it.mijorus.gearlever --list-installed --json' >&2
    exit 1
}
gearlever --set-update-source "$path" --manager GithubUpdater repo=notepadqq/notepadqq 'repo_filename=notepadqq-v*-linux-x86_64.AppImage' allow_prereleases=0
gearlever --list-installed
gearlever --list-updates
