#!/bin/bash
set -Eeuo pipefail
root=$1
cd "$2"
sizes=24,30,32,36,40,42,48,54,56,60,64,72,80,96,112,128
mkdir -p input output themes
python3 "$root/scripts/cursors/prepare.py" "$sizes"
for theme in Windows-Aero-Light Windows-Black; do
    ./converter "$PWD/input/$theme" --out "$PWD/output" --resample bilinear
    test -f "$PWD/output/$theme/xcursor/index.theme"
    cp -a "output/$theme/xcursor" "themes/$theme"
done
python3 "$root/scripts/cursors/structure.py" "$sizes"
