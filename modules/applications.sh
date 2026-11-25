#!/bin/bash
applications_main() (
    set -Eeuo pipefail
    apt_install gnome-software gnome-software-plugin-flatpak flatpak libfuse2t64
    flatpak remote-add --system --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
    flatpak install --system --noninteractive -y flathub it.mijorus.gearlever
    if [[ $INSTALL_1PASSWORD == no && $INSTALL_1PASSWORD_CLI == no ]]; then return; fi
    apt_install curl gnupg debsig-verify
    work=$(mktemp -d)
    trap 'rm -rf -- "$work"' EXIT
    trap 'exit 130' INT
    trap 'exit 143' HUP TERM
    base=https://downloads.1password.com/linux
    download "$base/keys/1password.asc" "$work/key.asc"
    actual=$(gpg --batch --show-keys --with-colons "$work/key.asc" | awk -F: '$1=="pub" {primary=1; next} $1=="fpr" && primary {print $10; primary=0}')
    [[ $actual == 3FEF9748469ADBE15DA7CA80AC2D62742012EA22 ]] || die 'Unexpected 1Password signing key fingerprint'
    gpg --batch --yes --dearmor --output "$work/key.gpg" "$work/key.asc"
    atomic_install "$work/key.gpg" /usr/share/keyrings/1password-archive-keyring.gpg
    # Current 1Password packages create this deb822 file themselves. Use the same
    # canonical path so installing the vendor package cannot duplicate our source.
    printf '%s\n' 'Types: deb' 'URIs: https://downloads.1password.com/linux/debian/amd64' 'Suites: stable' 'Components: main' 'Architectures: amd64' 'Signed-By: /usr/share/keyrings/1password-archive-keyring.gpg' > "$work/source"
    if [[ -f /etc/apt/sources.list.d/1password.list ]]; then
        die 'Legacy 1password.list exists; review it and move it outside sources.list.d before using the canonical 1password.sources file.'
    fi
    atomic_install "$work/source" /etc/apt/sources.list.d/1password.sources
    download "$base/debian/debsig/1password.pol" "$work/policy"
    python3 - "$work/policy" <<'PY'
import sys, xml.etree.ElementTree as ET
root=ET.parse(sys.argv[1]).getroot()
if not any('AC2D62742012EA22' in str(v) for node in root.iter() for v in node.attrib.values()):
    raise SystemExit('Unexpected debsig policy signing key')
PY
    atomic_install "$work/policy" /etc/debsig/policies/AC2D62742012EA22/1password.pol
    atomic_install "$work/key.gpg" /usr/share/debsig/keyrings/AC2D62742012EA22/debsig.gpg
    # Never let this application vendor become a source for unrelated packages.
    printf '%s\n' 'Package: 1password 1password-cli' 'Pin: origin "downloads.1password.com"' 'Pin-Priority: 500' '' 'Package: *' 'Pin: origin "downloads.1password.com"' 'Pin-Priority: -1' > "$work/pin"
    atomic_install "$work/pin" /etc/apt/preferences.d/debian-workstation-1password.pref
    apt-get update
    packages=()
    [[ $INSTALL_1PASSWORD == no ]] || packages+=(1password)
    [[ $INSTALL_1PASSWORD_CLI == no ]] || packages+=(1password-cli)
    simulate "${packages[@]}"
    # Verify package-level signatures before passing the selected exact packages to APT.
    changes=()
    for package in "${packages[@]}"; do
        candidate=$(LC_ALL=C apt-cache policy "$package" | awk '/Candidate:/ {print $2}')
        installed=$(dpkg-query -W -f='${Version}' "$package" 2>/dev/null || true)
        [[ $candidate == "$installed" ]] || changes+=("$package=$candidate")
    done
    if ((${#changes[@]}==0)); then log '1Password packages already match their APT candidates; skipping downloads.'; return; fi
    mkdir "$work/packages"
    chmod 0755 "$work" "$work/packages"
    (cd "$work/packages"; apt-get download "${changes[@]}")
    for package in "$work/packages/"*.deb; do debsig-verify "$package"; done
    apt_install "$work/packages/"*.deb
)
