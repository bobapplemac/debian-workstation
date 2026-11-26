#!/bin/bash
# SPDX-License-Identifier: 0BSD
# LightDM waits for this wrapper before tearing down the X server. Keep Debian's
# Xsession as the child; it runs every normal Xsession.d/environment/user hook.
set -uo pipefail

graphical_session() (
    local xsession=$1
    shift
    if [[ ${XDG_SESSION_TYPE:-} != x11 ]]; then
        exec "$xsession" "$@"
    fi
    [[ -n ${DISPLAY:-} && -n ${XDG_RUNTIME_DIR:-} ]] || {
        echo 'Workstation session: missing X11 display or user runtime directory.' >&2
        return 1
    }
    # Do not claim a target owned by another session/native session integration.
    if systemctl --user is-active --quiet graphical-session.target; then
        echo 'Workstation session: graphical-session.target already active; retaining its existing owner.' >&2
        exec "$xsession" "$@"
    fi
    # pam_systemd/dbus-user-session provide the user's bus before Xsession runs.
    export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=$XDG_RUNTIME_DIR/bus}
    local name child='' result names=()
    for name in DISPLAY XAUTHORITY XDG_CURRENT_DESKTOP XDG_SESSION_TYPE XDG_SESSION_DESKTOP DESKTOP_SESSION; do
        [[ -z ${!name:-} ]] || names+=("$name")
    done
    dbus-update-activation-environment --systemd "${names[@]}" || return 1
    systemctl --user daemon-reload || return 1
    # graphical-session.target has RefuseManualStart=yes and StopWhenUnneeded=yes.
    # A session-specific target must pull it in and retain the dependency.
    systemctl --user start debian-workstation-cinnamon-session.target || return 1
    cleanup() {
        # No reset-failed, ignored exit statuses or restart loop: stop services
        # through their existing PartOf=graphical-session.target relationships.
        if ! systemctl --user stop debian-workstation-cinnamon-session.target graphical-session.target; then
            echo 'Workstation session: could not stop graphical-session.target cleanly.' >&2
        fi
    }
    trap cleanup EXIT
    terminate() {
        local signal=$1 code=$2
        trap '' HUP INT TERM
        if [[ -n $child ]]; then
            kill -s "$signal" "$child" 2>/dev/null || true
            wait "$child" 2>/dev/null || true
        fi
        exit "$code"
    }
    trap 'terminate HUP 129' HUP
    trap 'terminate INT 130' INT
    trap 'terminate TERM 143' TERM
    "$xsession" "$@" &
    child=$!
    result=0
    wait "$child" || result=$?
    exit "$result"
)

if [[ ${BASH_SOURCE[0]} == "$0" ]]; then
    [[ $EUID != 0 ]] || { echo 'LightDM session wrapper must run as the logged-in user.' >&2; exit 1; }
    graphical_session /etc/X11/Xsession "$@"
fi
