#!/bin/bash
# SPDX-License-Identifier: 0BSD
set -Eeuo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
source "$root/lib/common.sh"
[[ $EUID == 0 ]] || die 'NVIDIA system installation requires root.'
platform
devices=$1
# Replacing an existing third-party/closed driver is a separate migration decision.
if [[ ! -f /var/lib/debian-workstation/nvidia-open.version && ! -f /var/lib/debian-workstation/nvidia-open.pending ]]; then
    for package in nvidia-driver nvidia-kernel-dkms nvidia-open-kernel-dkms nvidia-kernel-open-dkms cuda-drivers; do
        if dpkg-query -W -f='${db:Status-Status}' "$package" 2>/dev/null | grep -qx installed; then
            die "Existing unmanaged NVIDIA stack ($package). Review its removal/migration before opting into this installer."
        fi
    done
    [[ ! -e /usr/bin/nvidia-uninstall ]] || die 'A .run-installed NVIDIA stack was found; migrate it using its own removal procedure first.'
fi
apt_install gnupg python3-apt
work=$(mktemp -d)
changed=no
committed=no
paths=(/etc/apt/keyrings/debian-workstation-nvidia.gpg /etc/apt/preferences.d/debian-workstation-nvidia.pref /etc/apt/sources.list.d/debian-workstation-nvidia.sources)
cleanup() {
    if [[ $changed == yes && $committed == no ]]; then
        for i in 0 1 2; do
            if [[ -f $work/original-$i ]]; then cp -p "$work/original-$i" "${paths[$i]}"; else rm -f -- "${paths[$i]}"; fi
        done
        echo 'NVIDIA repository changes restored after failed pre-install validation.' >&2
    fi
    rm -rf -- "$work"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' HUP TERM
for i in 0 1 2; do
    [[ ! -L ${paths[$i]} ]] || die "Refusing repository symlink: ${paths[$i]}"
    if [[ -f ${paths[$i]} ]]; then cp -p "${paths[$i]}" "$work/original-$i"; fi
done
locations=(/etc/apt/sources.list.d)
[[ ! -f /etc/apt/sources.list ]] || locations+=(/etc/apt/sources.list)
if grep -rl --include='*.sources' --include='*.list' 'developer.download.nvidia.com' "${locations[@]}" | grep -vFx "${paths[2]}"; then
    die 'Existing NVIDIA/CUDA repository found; reconcile it before enabling another driver source.'
fi
base=https://developer.download.nvidia.com/compute/cuda/repos/debian13/x86_64
download "$base/8793F200.pub" "$work/key.asc"
actual=$(gpg --batch --show-keys --with-colons "$work/key.asc" | awk -F: '$1=="pub" {primary=1;next} $1=="fpr" && primary {print $10;primary=0}')
[[ $actual == 02182E60104FCDC26EAE1B8597A5D4CB8793F200 ]] || die 'NVIDIA Debian 13 signing key changed; review its identity before updating the expected fingerprint.'
gpg --batch --yes --dearmor --output "$work/key.gpg" "$work/key.asc"
changed=yes
atomic_install "$work/key.gpg" "${paths[0]}"
atomic_install "$root/assets/nvidia.pref" "${paths[1]}"
atomic_install "$root/assets/nvidia.sources" "${paths[2]}"
apt-get update
version=$(python3 "$root/scripts/graphics/candidates.py")
cache=/var/lib/debian-workstation/nvidia-supported-$version.json
[[ ! -L $cache ]] || die "Refusing symlink: $cache"
if [[ ! -f $cache ]]; then
    mkdir "$work/packages"
    (cd "$work/packages"; apt-get download "nvidia-driver=$version")
    # Read a fixed metadata member only, from the APT-authenticated package.
    dpkg-deb --fsys-tarfile "$work/packages/"*.deb | tar -xOf - ./usr/share/doc/nvidia-driver/supported-gpus.json.gz | gzip -d > "$work/supported.json"
else
    cp "$cache" "$work/supported.json"
fi
python3 "$root/scripts/graphics/hardware.py" supported "$devices" "$work/supported.json"
atomic_install "$work/supported.json" "$cache"
simulate "nvidia-open=$version" "nvidia-kernel-open-dkms=$version"
apt_install dkms mokutil linux-image-amd64 linux-headers-amd64
if [[ -d /sys/firmware/efi ]]; then
    secureboot=$(LC_ALL=C mokutil --sb-state) || die 'Cannot determine Secure Boot state; resolve EFI access before installing DKMS graphics.'
    if [[ $secureboot == *'SecureBoot enabled'* ]]; then
        dkms generate_mok
        if ! mokutil --test-key /var/lib/dkms/mok.pub; then
            die 'Secure Boot requires enrolling the DKMS key. Run sudo mokutil --import /var/lib/dkms/mok.pub, choose a temporary password, reboot and enroll it at the MOK screen, then rerun. Secure Boot has not been disabled.'
        fi
    elif [[ $secureboot != *'SecureBoot disabled'* ]]; then
        die "Unrecognized Secure Boot state: $secureboot"
    fi
fi
log "Installing NVIDIA open-module stack $version. Existing Xorg configuration is retained; changes take effect after the planned reboot."
# Once package installation begins, retain the repository for partial-run recovery.
committed=yes
printf '%s\n' "$version" > /var/lib/debian-workstation/nvidia-open.pending
apt_install "nvidia-open=$version" "nvidia-kernel-open-dkms=$version"
kernel=$(basename "$(readlink -f /vmlinuz)")
[[ $kernel == vmlinuz-*-amd64 ]] || die 'Cannot identify the Debian amd64 next-boot kernel from /vmlinuz; inspect DKMS status before reboot.'
kernel=${kernel#vmlinuz-}
[[ -d /lib/modules/$kernel/build ]] || die "Kernel headers missing for $kernel"
license=$(modinfo -k "$kernel" -F license nvidia)
[[ $license == *MIT*GPL* || $license == *GPL*MIT* ]] || die "Expected the NVIDIA open module, got license: $license"
built=$(modinfo -k "$kernel" -F version nvidia)
[[ $built == "${version%-*}" ]] || die "DKMS module version $built differs from user-space $version"
dkms status
printf '%s\n' "$version" > /var/lib/debian-workstation/nvidia-open.version
printf '%s\n' "$kernel" > /var/lib/debian-workstation/nvidia-open.kernel
rm -f /var/lib/debian-workstation/nvidia-open.pending
log "Verified open NVIDIA module for kernel $kernel. Reboot when provisioning is complete; then check nvidia-smi, modinfo -F license nvidia and glxinfo -B."
