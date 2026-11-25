#!/bin/bash
set -Eeuo pipefail
gearlever() { flatpak run it.mijorus.gearlever "$@"; }
find_notepadqq() {
    gearlever --list-installed --json | python3 -c 'import json,sys; matches=[a["path"] for a in json.load(sys.stdin)["installed"] if a["name"].casefold()=="notepadqq"]; print(matches[0] if len(matches)==1 else ""); sys.exit(1 if len(matches)>1 else 0)'
}
path=$(find_notepadqq)
if [[ -z $path ]]; then
    work=$(mktemp -d)
    trap 'rm -rf -- "$work"' EXIT
    trap 'exit 130' INT
    trap 'exit 143' HUP TERM
    asset=notepadqq-latest-linux-x86_64.AppImage
    python3 "$(dirname "$0")/github-release.py" "$work/$asset"
    chmod 0755 "$work/$asset"
    gearlever --integrate "$work/$asset" --yes
    path=$(find_notepadqq)
fi
[[ -n $path && -f $path ]] || { echo 'Notepadqq was not integrated by Gear Lever' >&2; exit 1; }
gearlever --set-update-source "$path" --manager GithubUpdater repo=notepadqq/notepadqq 'repo_filename=notepadqq-v*-linux-x86_64.AppImage' allow_prereleases=0
gearlever --list-installed
gearlever --list-updates
