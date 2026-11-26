#!/bin/bash
# SPDX-License-Identifier: 0BSD
# Targeted repair entry point; does not restart the display manager or live session.
set -Eeuo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
source "$root/lib/common.sh"
[[ $EUID == 0 ]] || die 'Run this system configuration step with sudo.'
platform
lightdm --show-config 2>&1 | python3 "$root/scripts/session/check-wrapper.py"
bash -n "$root/scripts/session/lightdm-session.sh"
atomic_install "$root/scripts/session/lightdm-session.sh" /usr/local/lib/debian-workstation/scripts/session/lightdm-session.sh 0755
atomic_install "$root/assets/debian-workstation-cinnamon-session.target" /etc/systemd/user/debian-workstation-cinnamon-session.target
atomic_install "$root/assets/xapp-session.conf" /etc/systemd/user/xdg-desktop-portal-xapp.service.d/10-debian-workstation-session.conf
atomic_install "$root/assets/lightdm-session.conf" /etc/lightdm/lightdm.conf.d/91-debian-workstation-session.conf
lightdm --show-config 2>&1 | python3 "$root/scripts/session/check-wrapper.py" --installed
log 'Graphical-session lifecycle installed. It applies at the next LightDM login; no running session was restarted.'
