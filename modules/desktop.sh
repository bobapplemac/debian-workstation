#!/bin/bash
desktop_main() {
    local packages=() exclusions=() line
    while IFS= read -r line; do [[ -z $line || $line == \#* ]] || packages+=("$line"); done < "$DW_ROOT/assets/packages.txt"
    # Prevent task recommendations from selecting alternative mail/torrent/office providers.
    # Fail instead of removing any existing excluded application.
    while IFS= read -r line; do
        [[ -z $line || $line == \#* ]] && continue
        if dpkg-query -W -f='${db:Status-Status}' "$line" 2>/dev/null | grep -qx installed; then
            die "Excluded application already installed: $line. Review before provisioning this non-fresh machine."
        fi
        # Unknown obsolete providers should not make modern APT fail.
        if apt-cache show "$line" >/dev/null 2>&1; then exclusions+=("$line-"); fi
    done < "$DW_ROOT/assets/exclusions.txt"
    simulate "${packages[@]}" "${exclusions[@]}"
    apt_install "${packages[@]}" "${exclusions[@]}"
    local hypervisor=$HYPERVISOR
    [[ $hypervisor != auto ]] || hypervisor=$(systemd-detect-virt || true)
    case $hypervisor in
        vmware) apt_install open-vm-tools-desktop ;;
        kvm|qemu) apt_install qemu-guest-agent spice-vdagent; systemctl enable qemu-guest-agent ;;
        microsoft) apt_install hyperv-daemons ;;
        none|'') : ;;
        *) log "No guest integration profile for $hypervisor" ;;
    esac
    atomic_install "$DW_ROOT/assets/lightdm.conf" /etc/lightdm/lightdm.conf.d/90-debian-workstation.conf
    bash "$DW_ROOT/scripts/session/install.sh"
    systemctl set-default graphical.target
}
