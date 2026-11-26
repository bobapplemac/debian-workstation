#!/bin/bash
# Read-only workstation checks. Run as the desktop user in Cinnamon X11.
set -uo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
failures=0
check() {
    printf '\n=== %s ===\n' "$1"; shift
    if "$@"; then echo PASS; else echo FAIL; failures=$((failures+1)); fi
}
check 'Debian 13 amd64' bash -c 'source /etc/os-release; [[ $ID == debian && $VERSION_ID == 13 && $(dpkg --print-architecture) == amd64 ]]'
check 'Cinnamon X11 session' bash -c '[[ ${XDG_SESSION_TYPE:-} == x11 && ${XDG_CURRENT_DESKTOP,,} == *cinnamon* && $EUID != 0 ]]'
check 'Graphical session lifecycle' systemctl --user is-active graphical-session.target
check 'No failed system services' bash -c 'units=$(systemctl --failed --no-legend --plain --no-pager) || exit; printf "%s\n" "$units"; [[ -z $units ]]'
check 'No failed user services' bash -c 'units=$(systemctl --user --failed --no-legend --plain --no-pager) || exit; printf "%s\n" "$units"; [[ -z $units ]]'
check 'Desktop packages' dpkg-query -W cinnamon nemo lightdm lightdm-gtk-greeter firefox-esr mint-themes mint-y-icons libadwaita-1-0 xdg-desktop-portal-xapp gnome-software flatpak
check 'Repository policy' python3 "$root/scripts/repositories/policy.py" validate
check 'APT full-upgrade simulation' bash -c 'output=$(LC_ALL=C apt-get -s full-upgrade) || exit; printf "%s\n" "$output"; ! grep -q "^Remv " <<< "$output"'
check 'GTK theme' bash -c '[[ $(gsettings get org.cinnamon.desktop.interface gtk-theme) == "'\''Mint-Y-Blue'\''" ]]'
check '12-hour clock preference' bash -c '[[ $(gsettings get org.cinnamon.desktop.interface clock-use-24h) == false ]]'
check '12-hour lock-screen clock' bash -c '[[ $(gsettings get org.cinnamon.desktop.screensaver use-custom-format) == true && $(gsettings get org.cinnamon.desktop.screensaver time-format) == "'\''%-I:%M %p'\''" ]]'
check 'Native login/lock-screen display name' python3 -c 'import os,pwd; a=pwd.getpwuid(os.getuid()); name=a.pw_gecos.split(",",1)[0].strip(); print(name); assert name, "Account display name is empty; rerun the desktop module to apply the username fallback"'
check 'Native lock-screen text alignment' python3 "$root/scripts/desktop/lock-screen.py" verify
check 'Application artwork and glyph resolution' "$HOME/.local/bin/mint-y-app-icons.py" verify
check 'Portal accent color' gdbus call --session --dest org.freedesktop.portal.Desktop --object-path /org/freedesktop/portal/desktop --method org.freedesktop.portal.Settings.Read org.freedesktop.appearance accent-color
check 'Grid compensator' systemctl --user is-active nemo-grid-compensator.service
check 'Gear Lever' flatpak info --system it.mijorus.gearlever
check 'Gear Lever background preference' bash -c '[[ $(flatpak run --command=gsettings it.mijorus.gearlever get it.mijorus.gearlever fetch-updates-in-background) == true ]]'
check 'Gear Lever autostart' bash -c 'find "$HOME/.config/autostart" -iname "*gearlever*" -type f -print -exec cat {} \; | grep -q fetch-updates'
check 'Graphical boot' bash -c '[[ $(systemctl get-default) == graphical.target ]]'
check 'No pending NVIDIA installation' test ! -e /var/lib/debian-workstation/nvidia-open.pending
check 'No pending Debian NVIDIA installation' test ! -e /var/lib/debian-workstation/nvidia-debian.pending
if [[ -f /var/lib/debian-workstation/nvidia-open.version ]]; then
    check 'Loaded NVIDIA open kernel module' bash -c '[[ -d /sys/module/nvidia ]] && license=$(modinfo -F license nvidia) && [[ $license == *MIT*GPL* || $license == *GPL*MIT* ]]'
    check 'NVIDIA driver and detected GPUs' nvidia-smi
    check 'OpenGL renderer' glxinfo -B
fi
if [[ -f /var/lib/debian-workstation/nvidia-debian.version ]]; then
    check 'Loaded Debian proprietary NVIDIA module' bash -c '[[ -d /sys/module/nvidia && $(modinfo -F license nvidia) == NVIDIA ]]'
    check 'Debian NVIDIA driver and detected GPUs' nvidia-smi
    check 'OpenGL renderer' glxinfo -B
fi
if [[ -f /usr/share/icons/Windows-Aero-Light/.debian-workstation ]]; then check 'Native Windows XCursor loading' python3 "$root/scripts/cursors/native.py"; fi
printf '\nFailures: %s\nVisual and interactive acceptance remains separate; see docs/acceptance.md.\n' "$failures"
((failures==0))
