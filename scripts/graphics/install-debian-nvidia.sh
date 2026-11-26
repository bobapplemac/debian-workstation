#!/bin/bash
# SPDX-License-Identifier: 0BSD
set -Eeuo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
source "$root/lib/common.sh"
source "$root/lib/graphics.sh"
[[ $EUID == 0 ]] || die 'Debian NVIDIA system installation requires root.'
platform
devices=$1
if [[ ${NVIDIA_LEGACY:-ask} == no ]]; then log 'Proprietary NVIDIA fallback explicitly declined.'; exit 43; fi
[[ ! -f /var/lib/debian-workstation/nvidia-open.version && ! -f /var/lib/debian-workstation/nvidia-open.pending ]] || die 'A project-managed upstream open stack already exists; driver-family switching requires an explicit migration.'
if [[ ! -f /var/lib/debian-workstation/nvidia-debian.version && ! -f /var/lib/debian-workstation/nvidia-debian.pending ]]; then
    for package in nvidia-driver nvidia-kernel-dkms nvidia-open-kernel-dkms nvidia-kernel-open-dkms cuda-drivers; do
        if dpkg-query -W -f='${db:Status-Status}' "$package" 2>/dev/null | grep -qx installed; then
            die "Existing unmanaged NVIDIA stack ($package); review migration before changing it."
        fi
    done
    [[ ! -e /usr/bin/nvidia-uninstall ]] || die 'A .run-installed NVIDIA stack needs its own reviewed removal first.'
fi
apt_install gnupg python3-apt
# The attempted open-driver probe has restored its temporary vendor source before
# this process runs. Require actual Debian origins; never mix the driver families.
version=$(python3 "$root/scripts/graphics/candidates.py" --debian)
work=$(mktemp -d)
trap 'rm -rf -- "$work"' EXIT
trap 'exit 130' INT
trap 'exit 143' HUP TERM
cache=/var/lib/debian-workstation/nvidia-debian-supported-$version.json
[[ ! -L $cache ]] || die "Refusing symlink: $cache"
if [[ -f $cache ]]; then
    cp "$cache" "$work/supported.json"
else
    mkdir "$work/packages"
    (cd "$work/packages"; apt-get download "nvidia-driver=$version")
    dpkg-deb --fsys-tarfile "$work/packages/"*.deb | tar -xOf - ./usr/share/doc/nvidia-driver/supported-gpus.json.gz | gzip -d > "$work/supported.json"
fi
python3 "$root/scripts/graphics/hardware.py" supported-debian "$devices" "$work/supported.json"
atomic_install "$work/supported.json" "$cache"
simulate "nvidia-driver=$version" "nvidia-kernel-dkms=$version" "nvidia-smi=$version"
if [[ ${NVIDIA_LEGACY:-ask} == ask && ! -f /var/lib/debian-workstation/graphics-consent-nvidia-debian ]]; then
    log "All detected NVIDIA adapters are supported by Debian's $version proprietary driver. This uses a closed kernel module, not the preferred open module."
    if ! { exec 6<>/dev/tty; } 2>/dev/null; then
        log 'No terminal for proprietary-driver consent. Skipping; NVIDIA_LEGACY=yes is required for unattended fallback.'
        exit 43
    fi
    printf 'Install the compatible Debian proprietary NVIDIA driver instead? [y/N] ' >&6
    read -r answer <&6
    case ${answer,,} in y|yes) :;; *) log 'Proprietary NVIDIA fallback declined; retaining native graphics.'; exit 43;; esac
fi
touch /var/lib/debian-workstation/graphics-consent-nvidia-debian
graphics_prepare_kernel
printf '%s\n' "$version" > /var/lib/debian-workstation/nvidia-debian.pending
apt_install "nvidia-driver=$version" "nvidia-kernel-dkms=$version" "nvidia-smi=$version"
graphics_verify_kernel debian "$version"
