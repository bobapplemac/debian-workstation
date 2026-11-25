#!/bin/bash
repositories_main() (
    set -Eeuo pipefail
    apt_install gnupg ca-certificates curl python3-apt
    local_work=$(mktemp -d)
    changed=no
    committed=no
    paths=(/etc/apt/keyrings/debian-workstation-mint.gpg /etc/apt/preferences.d/debian-workstation-mint.pref /etc/apt/sources.list.d/debian-workstation-mint.sources)
    rollback() {
        if [[ $changed == yes && $committed == no ]]; then
            for i in 0 1 2; do
                if [[ -f $local_work/original-$i ]]; then cp -p "$local_work/original-$i" "${paths[$i]}"; else rm -f "${paths[$i]}"; fi
            done
            echo 'Repository configuration restored after failed validation.' >&2
        fi
        rm -rf -- "$local_work"
    }
    trap rollback EXIT
    trap 'exit 130' INT
    trap 'exit 143' TERM HUP
    for i in 0 1 2; do
        [[ ! -L ${paths[$i]} ]] || die "Refusing repository symlink ${paths[$i]}"
        if [[ -f ${paths[$i]} ]]; then cp -p "${paths[$i]}" "$local_work/original-$i"; fi
    done
    # Reject duplicate repository definitions rather than defeating a pre-existing policy.
    if grep -rlE 'fastly\.linuxmint\.io|packages\.linuxmint\.com' /etc/apt/sources.list /etc/apt/sources.list.d 2>/dev/null | grep -vFx "${paths[2]}"; then
        die 'Existing Mint source found. Reconcile it with docs/security-policy.md first.'
    fi
    fingerprint=302F0738F465C1535761F965A6616109451BBBF2
    mkdir -m 0700 "$local_work/gnupg"
    gpg --homedir "$local_work/gnupg" --batch --keyserver hkps://keyserver.ubuntu.com --recv-keys "$fingerprint"
    actual=$(gpg --homedir "$local_work/gnupg" --batch --with-colons --fingerprint "$fingerprint" | awk -F: '$1=="fpr" {print $10; exit}')
    [[ $actual == "$fingerprint" ]] || die 'Unexpected Linux Mint signing key'
    gpg --homedir "$local_work/gnupg" --batch --export "$fingerprint" > "$local_work/key.gpg"
    changed=yes
    atomic_install "$local_work/key.gpg" "${paths[0]}"
    atomic_install "$DW_ROOT/assets/linuxmint.pref" "${paths[1]}"
    atomic_install "$DW_ROOT/assets/linuxmint.sources" "${paths[2]}"
    apt-get update
    python3 "$DW_ROOT/scripts/repositories/policy.py" validate
    simulate mint-themes mint-x-icons mint-y-icons mint-cursor-themes libadwaita-1-0 gir1.2-adw-1 xdg-desktop-portal-xapp xapp-symbolic-icons
    apt-get -s full-upgrade > "$local_work/full-upgrade.txt"
    cat "$local_work/full-upgrade.txt"
    ! grep -q '^Remv ' "$local_work/full-upgrade.txt" || die 'Full upgrade would remove packages'
    # A security fallback may legitimately need a downgrade. Never authorize it implicitly.
    if python3 "$DW_ROOT/scripts/repositories/policy.py" security-fallback; then
        log 'Debian security libadwaita is selected; Mint accent integration may be reduced. See docs/security-policy.md.'
    fi
    apt_install mint-themes mint-x-icons mint-y-icons mint-cursor-themes libadwaita-1-0 gir1.2-adw-1 xdg-desktop-portal-xapp xapp-symbolic-icons
    committed=yes
    install -d /usr/local/lib/debian-workstation/scripts
    atomic_install "$DW_ROOT/scripts/repositories/policy.py" /usr/local/lib/debian-workstation/scripts/repositories/policy.py
    atomic_install "$DW_ROOT/assets/debian-workstation-security.service" /etc/systemd/system/debian-workstation-security.service
    atomic_install "$DW_ROOT/assets/debian-workstation-security.timer" /etc/systemd/system/debian-workstation-security.timer
    atomic_install "$DW_ROOT/assets/99debian-workstation-audit" /etc/apt/apt.conf.d/99debian-workstation-audit
    python3 "$DW_ROOT/scripts/repositories/policy.py" audit
    systemctl daemon-reload
    systemctl enable --now debian-workstation-security.timer
)
