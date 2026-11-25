#!/usr/bin/env python3
from pathlib import Path
import subprocess
import shutil
import sys

root = Path(sys.argv[1])

families = (
    "Segoe UI",
    "Tahoma",
    "Calibri",
    "Cambria",
    "Candara",
    "Consolas",
    "Constantia",
    "Corbel",
    "Aptos",
    "Cascadia Code",
    "Cascadia Mono",
    "Lucida Console",
    "Palatino Linotype",
    "Franklin Gothic Medium",
    "Bahnschrift",
    "Microsoft Sans Serif",
)

# Do not replace Debian's existing emoji and symbol fonts.
excluded = (
    "Segoe UI Emoji",
    "Segoe UI Symbol",
    "Segoe UI Historic",
    "Segoe UI Assets",
    "Segoe UI MDL2 Assets",
)

def matches(name, prefix):
    name = name.casefold()
    prefix = prefix.casefold()
    return name == prefix or name.startswith(prefix + " ")

count = 0

for path in sorted((root / "source").rglob("*")):

    if not path.is_file():
        continue

    if path.suffix.lower() not in (".ttf", ".otf", ".ttc", ".otc"):
        continue

    result = subprocess.run(
        ["fc-scan", "--format", "%{family}\n", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        print(f"Skipping invalid font: {path.name}")
        continue

    names = {
        name.strip()
        for line in result.stdout.splitlines()
        for name in line.split(",")
        if name.strip()
    }

    if any(matches(name, item)
           for name in names for item in excluded):
        continue

    if not any(matches(name, item)
               for name in names for item in families):
        continue

    target = root / "fonts" / path.name

    if target.exists():
        if target.read_bytes() != path.read_bytes():
            raise RuntimeError(f"Conflicting font: {path.name}")
        continue

    shutil.copyfile(path, target)

    print(f"Selected: {path.name} — {', '.join(sorted(names))}")
    count += 1

if not count:
    raise SystemExit("No eligible supplemental fonts found.")

print(f"Selected {count} supplemental font files.")
