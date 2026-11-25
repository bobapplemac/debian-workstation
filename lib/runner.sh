#!/bin/bash
# shellcheck disable=SC1090
source "$DW_ROOT/lib/common.sh"
main() {
    local original_args=("$@")
    local config='' user='' phase=system module=all input_dir=$DW_ROOT/input
    while (($#)); do
        case $1 in
            --config|--user|--phase|--module|--input-dir)
                [[ $# -ge 2 ]] || die "Missing value: $1"
                case $1 in --config) config=$2;; --user) user=$2;; --phase) phase=$2;; --module) module=$2;; --input-dir) input_dir=$2;; esac
                shift 2 ;;
            --help) echo 'Usage: bash install.sh [--ref REV] [--config FILE] [--user USER] [--input-dir DIR] [--phase system|session] [--module all|base|network|repositories|desktop|assets|applications]'; return ;;
            *) die "Unknown argument: $1" ;;
        esac
    done
    platform
    [[ $phase == system || $phase == session ]] || die 'Invalid phase'
    [[ $module =~ ^(all|base|network|repositories|desktop|assets|applications)$ ]] || die 'Unknown module'
    if [[ $phase == system && $EUID != 0 ]]; then
        command -v sudo >/dev/null || die 'sudo is required; ask root to install it and grant this account sudo access.'
        log 'Checking sudo access for workstation provisioning.'
        sudo -n true 2>/dev/null || sudo -v || die 'Cannot elevate with sudo. Ask the administrator to grant this account sudo access.'
        [[ -n $user ]] || user=$(id -un)
        exec sudo -- bash "$DW_ROOT/install.sh" "${original_args[@]}" --user "$user"
    fi
    local parsed key value
    parsed=$(mktemp)
    if [[ -n $config ]]; then python3 "$DW_ROOT/scripts/config.py" "$config" > "$parsed"; else python3 "$DW_ROOT/scripts/config.py" > "$parsed"; fi
    while IFS= read -r -d '' key && IFS= read -r -d '' value; do printf -v "$key" '%s' "$value"; export "${key?}"; done < "$parsed"
    rm -f "$parsed"
    [[ -z $user ]] || DESKTOP_USER=$user
    if [[ $phase == session ]]; then
        [[ $EUID != 0 && ${XDG_SESSION_TYPE:-} == x11 && ${XDG_CURRENT_DESKTOP,,} == *cinnamon* && -n ${DISPLAY:-} && -n ${DBUS_SESSION_BUS_ADDRESS:-} ]] || die 'Run in the owning Cinnamon X11 session as the desktop user.'
        [[ -z $DESKTOP_USER || $DESKTOP_USER == "$(id -un)" ]] || die 'Wrong desktop user'
        source "$DW_ROOT/modules/session.sh"
        session_main
        return
    fi
    [[ -n $DESKTOP_USER ]] || DESKTOP_USER=${SUDO_USER:-}
    if [[ -z $DESKTOP_USER ]]; then
        if ! { exec 7<>/dev/tty; } 2>/dev/null; then die 'Root account setup requires a terminal; alternatively supply --user USER for an existing account.'; fi
        printf 'Regular workstation username (new or existing): ' >&7
        read -r DESKTOP_USER <&7
    fi
    [[ $DESKTOP_USER =~ ^[a-z_][a-z0-9_-]{0,31}$ && $DESKTOP_USER != root ]] || die 'Choose --user USER; the reference base creates only root.'
    install -d -m 0755 /var/lib/debian-workstation
    exec 9>/var/lib/debian-workstation/install.lock
    flock -n 9 || die 'Another installation is running.'
    trap 'echo "Installation failed at line $LINENO; correct the error and rerun. Completed work is retained." >&2' ERR
    if ! id "$DESKTOP_USER" >/dev/null 2>&1; then
        [[ $CREATE_USER == yes ]] || die 'Desktop user does not exist.'
        if ! { exec 7<>/dev/tty; } 2>/dev/null; then die 'Creating a user requires a terminal for the password. Connect with ssh -t or use the VM console.'; fi
        adduser --disabled-password --gecos '' "$DESKTOP_USER"
        touch "/var/lib/debian-workstation/$DESKTOP_USER.password-pending"
    fi
    if [[ -f /var/lib/debian-workstation/$DESKTOP_USER.password-pending ]]; then
        if ! { exec 7<>/dev/tty; } 2>/dev/null; then die 'Complete the new account password setup through a terminal, then rerun.'; fi
        passwd "$DESKTOP_USER" <&7 >&7
        rm -f "/var/lib/debian-workstation/$DESKTOP_USER.password-pending"
    fi
    DESKTOP_HOME=$(getent passwd "$DESKTOP_USER" | cut -d: -f6)
    [[ $(id -u "$DESKTOP_USER") -ge 1000 && $DESKTOP_HOME == /* && -d $DESKTOP_HOME && ! -L $DESKTOP_HOME ]] || die 'Expected a regular desktop account and real home directory.'
    export DESKTOP_HOME
    [[ -n $CURSOR_ARCHIVE ]] || CURSOR_ARCHIVE=$input_dir/Windows-Cursors.zip
    [[ -n $FONT_ARCHIVE ]] || FONT_ARCHIVE=$input_dir/Windows-Fonts.zip
    for key in CURSOR_ARCHIVE FONT_ARCHIVE; do
        if [[ ! -f ${!key} ]]; then
            log "WARNING: optional $key not found: ${!key}. Skipping this customization."
            printf -v "$key" ''
        fi
        export "${key?}"
    done
    # Persist before invoking helpers as the desktop user. A root-owned remote
    # mktemp source directory is deliberately inaccessible to other accounts.
    local installed=/usr/local/lib/debian-workstation
    python3 "$DW_ROOT/scripts/persist.py" "$DW_ROOT" "$installed"
    DW_ROOT=$installed
    export DW_ROOT
    for name in base network repositories desktop assets applications; do
        if [[ $module == all || $module == "$name" ]]; then
            log "Running $name"
            source "$DW_ROOT/modules/$name.sh"
            "${name}_main"
            printf '%s\n' "$(date -Is)" > "/var/lib/debian-workstation/$name.completed"
        fi
    done
    # Persist public options only. Optional proprietary archives are system-phase inputs.
    printf 'DESKTOP_USER=%s\nINSTALL_NOTEPADQQ=%s\nNEMO_REF=%s\n' "$DESKTOP_USER" "$INSTALL_NOTEPADQQ" "$NEMO_REF" > "$installed/session.conf"
    chown -R root:root "$installed"
    chmod -R go-w "$installed"
    as_user python3 "$installed/scripts/files.py" autostart "$installed"
    log 'System phase complete. Reboot when ready, then log in to Cinnamon (X11). First-login continuation will display its result.'
    log 'No reboot or display-manager restart has been initiated.'
}
