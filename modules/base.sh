#!/bin/bash
base_main() {
    apt-get update
    # Existing security mechanisms are retained; the base itself has no unattended policy.
    apt-get --no-remove -y full-upgrade
    apt_install sudo curl wget ca-certificates nano python3 gnupg
    usermod -aG sudo "$DESKTOP_USER"
    if [[ $PASSWORDLESS_SUDO == yes ]]; then
        local tmp
        tmp=$(mktemp)
        printf '%s ALL=(ALL:ALL) NOPASSWD: ALL\n' "$DESKTOP_USER" > "$tmp"
        visudo -cf "$tmp"
        atomic_install "$tmp" "/etc/sudoers.d/90-debian-workstation-$DESKTOP_USER" 0440
        rm -f "$tmp"
        visudo -c
    fi
}
