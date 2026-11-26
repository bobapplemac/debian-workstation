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
    if [[ $kind == nvidia-open && ( -f /var/lib/debian-workstation/nvidia-debian.version || -f /var/lib/debian-workstation/nvidia-debian.pending || -f /var/lib/debian-workstation/graphics-consent-nvidia-debian ) ]]; then
        kind=nvidia-debian
    fi
    if [[ $kind == none ]]; then log 'Virtual or other graphics: retaining Debian kernel/Mesa drivers and guest integration.'; return; fi
    if [[ $GRAPHICS_DRIVERS == no ]]; then log 'Graphics driver changes explicitly skipped.'; return; fi
    if [[ $GRAPHICS_DRIVERS == ask && ! -f /var/lib/debian-workstation/graphics-consent-$kind ]]; then
        if [[ $kind == nvidia-debian ]]; then
            log 'Maintaining the previously selected Debian proprietary NVIDIA stack.'
        elif [[ $kind == nvidia-open ]]; then
            log 'NVIDIA detected. Offer: prefer the official signed open-module stack with matching proprietary libraries/runtime (no CUDA toolkit). If unsupported, separately offer a compatible Debian proprietary driver.'
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
        if bash "$DW_ROOT/scripts/graphics/install-nvidia.sh" "$work/devices.json"; then
            :
        else
            result=$?
            [[ $result == 42 ]] || exit "$result"
            log 'The open module does not support every detected NVIDIA GPU. Checking the native Debian proprietary fallback.'
            if bash "$DW_ROOT/scripts/graphics/install-debian-nvidia.sh" "$work/devices.json"; then kind=nvidia-debian;
            else result=$?; [[ $result == 43 ]] && return; exit "$result"; fi
        fi
    elif [[ $kind == nvidia-debian ]]; then
        if bash "$DW_ROOT/scripts/graphics/install-debian-nvidia.sh" "$work/devices.json"; then :;
        else result=$?; [[ $result == 43 ]] && return; exit "$result"; fi
    fi
    if ((${#native[@]})); then simulate "${native[@]}"; apt_install "${native[@]}"; fi
    touch "/var/lib/debian-workstation/graphics-consent-$kind"
)
