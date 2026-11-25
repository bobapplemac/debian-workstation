#!/usr/bin/env python3
from pathlib import Path
import shutil
import sys
import json

sizes = sys.argv[1]

schemes = {
    "Windows-Aero-Light": {
        "pointer":     "aero_arrow.cur",
        "help":        "aero_helpsel.cur",
        "working":     "aero_working.ani",
        "busy":        "aero_busy.ani",
        "precision":   "cross_r.cur",
        "text":        "beam_r.cur",
        "hand":        "aero_pen.cur",
        "unavailable": "aero_unavail.cur",
        "vert":        "aero_ns.cur",
        "horz":        "aero_ew.cur",
        "dgn1":        "aero_nwse.cur",
        "dgn2":        "aero_nesw.cur",
        "move":        "aero_move.cur",
        "alternate":   "aero_up.cur",
        "link":        "aero_link.cur",
        "person":      "aero_person.cur",
        "pin":         "aero_pin.cur",
    },
    "Windows-Black": {
        "pointer":     "arrow_r.cur",
        "help":        "help_r.cur",
        "working":     "wait_r.cur",
        "busy":        "busy_r.cur",
        "precision":   "cross_r.cur",
        "text":        "beam_r.cur",
        "hand":        "pen_r.cur",
        "unavailable": "no_r.cur",
        "vert":        "size4_r.cur",
        "horz":        "size3_r.cur",
        "dgn1":        "size2_r.cur",
        "dgn2":        "size1_r.cur",
        "move":        "move_r.cur",
        "alternate":   "up_r.cur",
        "link":        "aero_link.cur",
        "person":      "person_r.cur",
        "pin":         "pin_r.cur",
    },
}

source = {}
for p in Path('microsoft').rglob('*'):
    if p.is_file():
        name = p.name.lower()
        if name in source:
            raise ValueError(f'Duplicate cursor filename in archive: {name}')
        source[name] = p

for theme, roles in schemes.items():
    root = (Path("input") / theme).resolve()

    manifest_dir = root / "ani2xcursor"
    manifest_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n=== Preparing {theme} ===")

    for role, filename in roles.items():
        if filename.lower() not in source:
            raise SystemExit(
                f"Missing required cursor: {filename}"
            )

        shutil.copyfile(
            source[filename.lower()],
            root / filename
        )

        print(f"{role}: {filename}")

    # Generate ani2xcursor manifest
    lines = [
        "[input]",
        f'theme = "{theme}"',
        f"dir = {json.dumps(str(root))}",
        "",
        "[files]",
    ]

    for role, filename in roles.items():
        lines.append(f'{role} = "{filename}"')

    lines += ["", "[sizes]"]

    for role in roles:
        lines.append(f'{role} = "{sizes}"')

    manifest = manifest_dir / "manifest.toml"
    manifest.write_text("\n".join(lines) + "\n")

    print(f"Manifest generated: {theme}")
