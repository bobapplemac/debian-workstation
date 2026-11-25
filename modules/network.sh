#!/bin/bash
network_main() {
    # Fail on unsupported input before installing or starting a new network owner.
    python3 "$DW_ROOT/scripts/network/migrate.py" inspect
    apt_install network-manager
    python3 "$DW_ROOT/scripts/network/migrate.py" stage
    atomic_install "$DW_ROOT/assets/debian-workstation-network.service" /etc/systemd/system/debian-workstation-network.service
    install -d /usr/local/lib/debian-workstation/scripts
    atomic_install "$DW_ROOT/scripts/network/migrate.py" /usr/local/lib/debian-workstation/scripts/network/migrate.py
    systemctl daemon-reload
    systemctl enable NetworkManager.service debian-workstation-network.service
    log 'NetworkManager profiles staged for next boot; current interfaces remain untouched.'
}
