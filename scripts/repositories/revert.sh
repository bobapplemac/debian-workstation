#!/bin/bash
set -Eeuo pipefail
[[ $EUID == 0 ]] || { echo 'Run as root with sudo.' >&2; exit 1; }
root=$(cd "$(dirname "$0")/../.." && pwd)
source "$root/lib/common.sh"
platform
work=$(mktemp -d)
trap 'rm -rf -- "$work"' EXIT
trap 'exit 130' INT
trap 'exit 143' HUP TERM
python3 - > "$work/versions" <<'PY'
import apt, apt_pkg, functools
cache=apt.Cache()
family='libadwaita-1-0 gir1.2-adw-1 libadwaita-1-dev libadwaita-1-doc libadwaita-1-examples'.split()
for name in family:
    if name not in cache or not cache[name].installed: continue
    versions=[v for v in cache[name].versions if any(o.origin=='Debian' and o.trusted for o in v.origins)]
    if not versions: raise SystemExit('No trusted native Debian version available for '+name)
    versions.sort(key=functools.cmp_to_key(lambda a,b:apt_pkg.version_compare(a.version,b.version)))
    print(name+'='+versions[-1].version)
PY
mapfile -t packages < "$work/versions"
((${#packages[@]})) || die 'No installed libadwaita family members found.'
simulate "${packages[@]}"
if [[ ${1:-} == --simulate ]]; then exit; fi
[[ $# == 0 ]] || die 'Usage: revert.sh [--simulate]'
printf '%s\n' 'Package: libadwaita-1-0 gir1.2-adw-1 libadwaita-1-dev libadwaita-1-doc libadwaita-1-examples' 'Pin: release o=Debian' 'Pin-Priority: 1001' > "$work/pin"
atomic_install "$work/pin" /etc/apt/preferences.d/00-debian-workstation-native-adwaita.pref
apt-get --no-remove --allow-downgrades -y install "${packages[@]}"
python3 "$root/scripts/repositories/policy.py" audit
echo 'Native Debian library family selected. Log out and back in; accent styling can change.'
