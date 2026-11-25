#!/bin/bash
# SPDX-License-Identifier: 0BSD
log() { printf '\n[debian-workstation] %s\n' "$*"; }
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
platform() {
    [[ $(uname -s) == Linux ]] || die 'Requires Debian 13 amd64 Linux.'
    source /etc/os-release
    [[ $ID == debian && $VERSION_ID == 13 && $(dpkg --print-architecture) == amd64 ]] || die 'Only Debian 13 Trixie amd64 is supported.'
}
download() { curl --fail --location --proto '=https' --proto-redir '=https' --retry 3 --connect-timeout 20 --max-time 300 "$1" -o "$2"; }
atomic_install() {
    local source=$1 dest=$2 mode=${3:-0644} tmp backup
    python3 - "$dest" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1])
if any(q.is_symlink() for q in [p,*p.parents]): raise SystemExit(f'Refusing symlink in destination path: {p}')
PY
    [[ ! -L $dest ]] || die "Refusing symlink: $dest"
    [[ ! -e $dest || -f $dest ]] || die "Expected file: $dest"
    if [[ -f $dest ]] && cmp -s "$source" "$dest"; then chmod "$mode" "$dest"; chown root:root "$dest"; return; fi
    install -d -m 0755 "$(dirname "$dest")"
    backup=/var/lib/debian-workstation/backups$dest
    [[ ! -L $backup ]] || die "Refusing backup symlink: $backup"
    if [[ -f $dest && ! -e $backup ]]; then
        install -d -m 0700 "$(dirname "$backup")"
        cp -p -- "$dest" "$backup"
    fi
    tmp=$(mktemp "$(dirname "$dest")/.dw.XXXXXX")
    install -m "$mode" -- "$source" "$tmp"
    mv -fT -- "$tmp" "$dest"
}
as_user() { runuser -u "$DESKTOP_USER" -- env HOME="$DESKTOP_HOME" "$@"; }
apt_install() { DEBIAN_FRONTEND=noninteractive apt-get --no-remove -y install "$@"; }
simulate() {
    local output
    output=$(LC_ALL=C apt-get -s install "$@") || die 'APT simulation failed.'
    printf '%s\n' "$output"
    ! grep -q '^Remv ' <<<"$output" || die 'APT proposes removals; inspect the transaction.'
}
