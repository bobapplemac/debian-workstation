#!/bin/bash
# SPDX-License-Identifier: 0BSD
set -Eeuo pipefail
ref=main
remote=no
args=()
while (($#)); do
    case $1 in
        --ref) [[ $# -ge 2 && -n $2 && $2 != -* ]] || { echo '--ref needs a revision' >&2; exit 2; }; ref=$2; remote=yes; shift 2 ;;
        *) args+=("$1"); shift ;;
    esac
done
here=
if [[ -n ${BASH_SOURCE[0]:-} && -f ${BASH_SOURCE[0]} ]]; then
    here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
fi
if [[ $remote == yes || ! -f $here/lib/runner.sh ]]; then
    [[ ${DW_LOCAL_ONLY:-0} != 1 ]] || { echo 'Incomplete downloaded source' >&2; exit 1; }
    command -v python3 >/dev/null || { echo 'Install python3 and ca-certificates first.' >&2; exit 1; }
    work=$(mktemp -d)
    trap 'rm -rf -- "$work"' EXIT
    trap 'exit 130' INT
    trap 'exit 143' TERM HUP
    # The bootstrap is self contained. Validate every member before extraction.
    python3 - "$ref" "$work" <<'PY'
import gzip, io, json, pathlib, sys, tarfile, urllib.parse, urllib.request
ref, target = sys.argv[1:]
base = 'https://api.github.com/repos/bobapplemac/debian-workstation/'
def get(url, limit):
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'debian-workstation'}), timeout=60) as r:
        data = r.read(limit + 1)
    if len(data) > limit: raise ValueError('Download exceeds size limit')
    return data
commit = json.loads(get(base+'commits/'+urllib.parse.quote(ref, safe=''), 1048576))['sha']
if len(commit) != 40 or any(c not in '0123456789abcdef' for c in commit): raise ValueError('Invalid commit')
raw = get(base+'tarball/'+commit, 16*1024*1024)
with gzip.GzipFile(fileobj=io.BytesIO(raw)) as f: data = f.read(64*1024*1024+1)
if len(data) > 64*1024*1024: raise ValueError('Expanded archive too large')
with tarfile.open(fileobj=io.BytesIO(data)) as tar:
    members=tar.getmembers(); names=set(); roots=set(); total=0
    for m in members:
        parts=m.name.rstrip('/').split('/')
        if (not all(p and p not in ('.','..') for p in parts) or '\\' in m.name or ':' in m.name
            or m.name in names or not (m.isfile() or m.isdir())): raise ValueError('Unsafe archive member')
        names.add(m.name); roots.add(parts[0]); total+=m.size
    if len(roots)!=1 or len(members)>10000 or total>64*1024*1024: raise ValueError('Invalid archive inventory')
    root=roots.pop()
    if not all(root+'/'+p in names for p in ('install.sh','lib/runner.sh','scripts/config.py')): raise ValueError('Incomplete source')
    for m in members:
        relative=pathlib.PurePosixPath(m.name).parts[1:]
        if not relative: continue
        path=pathlib.Path(target,'source',*relative)
        if m.isdir(): path.mkdir(parents=True,exist_ok=True)
        else:
            path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(tar.extractfile(m).read()); path.chmod(0o644)
pathlib.Path(target,'source','REVISION').write_text(commit+'\n')
print('Downloaded revision '+commit)
PY
    DW_LOCAL_ONLY=1 bash "$work/source/install.sh" --input-dir "$PWD/input" "${args[@]}"
    exit
fi
DW_ROOT=$here
export DW_ROOT
source "$here/lib/runner.sh"
main "${args[@]}"
