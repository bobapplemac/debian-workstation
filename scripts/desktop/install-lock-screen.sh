#!/bin/bash
# SPDX-License-Identifier: 0BSD
set -Eeuo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
source "$root/lib/common.sh"
[[ $EUID == 0 ]] || die 'Installing native lock-screen presentation requires root.'
platform
work=$(mktemp -d)
trap 'rm -rf -- "$work"' EXIT
python3 "$root/scripts/desktop/lock-screen.py" prepare --output "$work"
for name in clock.py unlock.py; do
    atomic_install "$work/$name" "/usr/share/cinnamon-screensaver/$name"
done
python3 "$root/scripts/desktop/lock-screen.py" verify
