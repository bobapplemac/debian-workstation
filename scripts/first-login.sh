#!/bin/bash
set -Eeuo pipefail
root=/usr/local/lib/debian-workstation
state=${XDG_STATE_HOME:-$HOME/.local/state}/debian-workstation
mkdir -p "$state"
# Hash persisted implementation inputs, excluding generated Python bytecode.
signature=$({ find "$root/lib" "$root/scripts" "$root/modules" "$root/assets" -type d -name __pycache__ -prune -o -type f ! -name '*.pyc' -print0; printf '%s\0' "$root/install.sh" "$root/session.conf"; } | sort -z | xargs -0 sha256sum | sha256sum | cut -d' ' -f1)
if [[ -f $state/session.completed && $(cat "$state/session.completed") == "$signature" ]]; then
    python3 "$root/scripts/repositories/notify.py"
    exit
fi
if [[ ${1:-} != --terminal ]]; then
    exec gnome-terminal --wait --title='Debian Workstation setup' -- bash "$root/scripts/first-login.sh" --terminal
fi
echo 'Completing Debian Workstation setup in your Cinnamon session.'
echo 'A native portal permission dialog may ask to allow Gear Lever background checks.'
# Cinnamon applets may still be starting. Do not create an artificial D-Bus session.
for _attempt in {1..30}; do
    if gdbus call --session --dest org.Cinnamon --object-path /org/Cinnamon --method org.freedesktop.DBus.Peer.Ping >/dev/null 2>&1; then break; fi
    sleep 2
done
set +e
bash "$root/install.sh" --phase session --config "$root/session.conf" 2>&1 | tee "$state/session.log"
result=${PIPESTATUS[0]}
set -e
if ((result==0)); then
    printf '%s\n' "$signature" > "$state/session.completed"
    notify-send 'Debian Workstation' 'Desktop setup completed. Reopen applications; log out and back in to reload all styling.' || true
else
    echo "Setup needs attention (exit $result). Correct the error, then run:"
    echo "bash $root/scripts/first-login.sh --terminal"
    notify-send --urgency=critical 'Debian Workstation setup needs attention' "See $state/session.log and rerun the continuation." || true
fi
echo 'Press Enter to close this window.'
read -r _
exit "$result"
