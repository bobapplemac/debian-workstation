#!/bin/bash
# SPDX-License-Identifier: 0BSD
graphics_main() (
    set -Eeuo pipefail
    work=$(mktemp -d)
    trap 'rm -rf -- "$work"' EXIT
    trap 'exit 130' INT
    trap 'exit 143' HUP TERM
    python3 "$DW_ROOT/scripts/graphics/hardware.py" detect > "$work/devices.json"
    log 'Detected graphics adapters'
    python3 "$DW_ROOT/scripts/graphics/hardware.py" report "$work/devices.json"
    kind=$(python3 "$DW_ROOT/scripts/graphics/hardware.py" kind "$work/devices.json")
    if [[ $kind == none ]]; then log 'Virtual or other graphics: retaining Debian kernel/Mesa drivers and guest integration.'; return; fi
    if [[ $GRAPHICS_DRIVERS == no ]]; then log 'Graphics driver changes explicitly skipped.'; return; fi
    if [[ $GRAPHICS_DRIVERS == ask && ! -f /var/lib/debian-workstation/graphics-consent-$kind ]]; then
        if [[ $kind == nvidia-open ]]; then
            log 'NVIDIA detected. Offer: official signed Debian 13 NVIDIA repository, open DKMS kernel modules, matching proprietary firmware/desktop libraries and driver runtime (no CUDA toolkit).'
        else
            log 'Intel/AMD detected. Offer: native Debian firmware and Mesa packages.'
        fi
        if ! { exec 6<>/dev/tty; } 2>/dev/null; then
            log 'No terminal for consent. Skipping optional drivers; set GRAPHICS_DRIVERS=yes to authorize a noninteractive install.'
            return
        fi
        printf 'Install these graphics drivers/firmware? [y/N] ' >&6
        read -r answer <&6
        case ${answer,,} in y|yes) :;; *) log 'Optional graphics installation declined.'; return;; esac
    fi
    mapfile -t native < <(python3 "$DW_ROOT/scripts/graphics/hardware.py" native-packages "$work/devices.json")
    # Empty Python output is one empty mapfile element, not a package name.
    if [[ ${native[0]:-} == '' ]]; then native=(); fi
    if [[ $kind == nvidia-open ]]; then
        bash "$DW_ROOT/scripts/graphics/install-nvidia.sh" "$work/devices.json"
    fi
    if ((${#native[@]})); then simulate "${native[@]}"; apt_install "${native[@]}"; fi
    touch "/var/lib/debian-workstation/graphics-consent-$kind"
)
