#!/bin/bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
while IFS= read -r -d '' script; do bash -n "$script"; done < <(find . -path './.git' -prune -o -path './.research' -prune -o -name '*.sh' -print0)
python3 -m unittest discover -s tests -v
python3 - <<'PY'
from pathlib import Path
for directory in ('scripts','tests'):
    for path in Path(directory).rglob('*.py'): compile(path.read_text(),str(path),'exec')
print('All Python sources compiled.')
PY
