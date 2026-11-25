#!/bin/bash
session_main() (
    set -Eeuo pipefail
    local state=${XDG_STATE_HOME:-$HOME/.local/state}/debian-workstation
    mkdir -p "$state"
    exec 8>"$state/session.lock"
    flock -n 8 || die 'Session continuation is already running.'
    python3 "$DW_ROOT/scripts/files.py" appearance "$DW_ROOT"
    theme=$(cat /var/lib/debian-workstation/cursor-theme)
    [[ $theme == Adwaita || $theme == Windows-Aero-Light ]] || die 'Invalid stored cursor theme'
    python3 "$DW_ROOT/scripts/files.py" cursor "$theme"
    python3 "$DW_ROOT/scripts/desktop/settings.py" "$theme"
    xrdb -merge "$HOME/.Xresources"
    "$HOME/.local/bin/mint-y-app-icons.py" apply
    "$HOME/.local/bin/mint-y-app-icons.py" verify
    # Follow main by default. The companion's own bootstrap resolves a consistent archive.
    local work
    work=$(mktemp -d)
    trap 'rm -rf -- "$work"' EXIT
    trap 'exit 130' INT
    trap 'exit 143' HUP TERM
    download "https://raw.githubusercontent.com/bobapplemac/nemo-grid-compensator/$NEMO_REF/install.sh" "$work/nemo-install.sh"
    bash "$work/nemo-install.sh" --ref "$NEMO_REF" --start
    # Keep Gear Lever's native portal request and settings, without a parallel updater.
    flatpak run --command=python3 it.mijorus.gearlever - < "$DW_ROOT/scripts/gearlever/background.py"
    if [[ $INSTALL_NOTEPADQQ == yes ]]; then
        bash "$DW_ROOT/scripts/notepadqq/install.sh"
    fi
    python3 "$DW_ROOT/scripts/repositories/notify.py"
    log 'Desktop configuration completed. Reopen applications to load decorations; log out and back in once to reload libraries and panel styling.'
)
