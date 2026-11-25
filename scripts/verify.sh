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
check 'Desktop packages' dpkg-query -W cinnamon nemo lightdm lightdm-gtk-greeter firefox-esr mint-themes mint-y-icons libadwaita-1-0 xdg-desktop-portal-xapp gnome-software flatpak
check 'Repository policy' python3 "$root/scripts/repositories/policy.py" validate
check 'APT full-upgrade simulation' bash -c 'output=$(LC_ALL=C apt-get -s full-upgrade) || exit; printf "%s\n" "$output"; ! grep -q "^Remv " <<< "$output"'
check 'GTK theme' bash -c '[[ $(gsettings get org.cinnamon.desktop.interface gtk-theme) == "'\''Mint-Y-Blue'\''" ]]'
check 'Application artwork and glyph resolution' "$HOME/.local/bin/mint-y-app-icons.py" verify
check 'Portal accent color' gdbus call --session --dest org.freedesktop.portal.Desktop --object-path /org/freedesktop/portal/desktop --method org.freedesktop.portal.Settings.Read org.freedesktop.appearance accent-color
check 'Grid compensator' systemctl --user is-active nemo-grid-compensator.service
check 'Gear Lever' flatpak info --system it.mijorus.gearlever
check 'Gear Lever background preference' bash -c '[[ $(flatpak run --command=gsettings it.mijorus.gearlever get it.mijorus.gearlever fetch-updates-in-background) == true ]]'
check 'Gear Lever autostart' bash -c 'find "$HOME/.config/autostart" -iname "*gearlever*" -type f -print -exec cat {} \; | grep -q fetch-updates'
check 'Graphical boot' bash -c '[[ $(systemctl get-default) == graphical.target ]]'
if [[ -f /usr/share/icons/Windows-Aero-Light/.debian-workstation ]]; then check 'Native Windows XCursor loading' python3 "$root/scripts/cursors/native.py"; fi
printf '\nFailures: %s\nVisual and interactive acceptance remains separate; see docs/acceptance.md.\n' "$failures"
((failures==0))
