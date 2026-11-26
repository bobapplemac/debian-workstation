#!/bin/bash
# SPDX-License-Identifier: 0BSD
graphics_prepare_kernel() {
    local secureboot
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
}

graphics_verify_kernel() {
    local flavor=$1 version=$2 kernel license built upstream
    kernel=$(basename "$(readlink -f /vmlinuz)")
    [[ $kernel == vmlinuz-*-amd64 ]] || die 'Cannot identify the Debian amd64 next-boot kernel from /vmlinuz; inspect DKMS status before reboot.'
    kernel=${kernel#vmlinuz-}
    [[ -d /lib/modules/$kernel/build ]] || die "Kernel headers missing for $kernel"
    license=$(modinfo -k "$kernel" -F license nvidia)
    if [[ $flavor == open ]]; then
        [[ $license == *MIT*GPL* || $license == *GPL*MIT* ]] || die "Expected NVIDIA open module, got license: $license"
    else
        [[ $license == NVIDIA ]] || die "Expected the Debian proprietary NVIDIA module, got license: $license"
    fi
    built=$(modinfo -k "$kernel" -F version nvidia)
    upstream=${version#*:}
    upstream=${upstream%%-*}
    [[ $built == "$upstream" ]] || die "DKMS module version $built differs from user-space $version"
    dkms status
    printf '%s\n' "$version" > "/var/lib/debian-workstation/nvidia-$flavor.version"
    printf '%s\n' "$kernel" > "/var/lib/debian-workstation/nvidia-$flavor.kernel"
    rm -f "/var/lib/debian-workstation/nvidia-$flavor.pending"
    log "Verified NVIDIA $flavor module for kernel $kernel. Reboot after provisioning; then check nvidia-smi and glxinfo -B."
}
