#!/usr/bin/env python3
from pathlib import Path
from collections import Counter
import struct
import sys

sizes = set(map(int, sys.argv[1].split(",")))

themes = [
    "Windows-Aero-Light",
    "Windows-Black",
]

# Supplement aliases already supplied by ani2xcursor
aliases = {
    "left_ptr": [
        "default",
        "arrow",
        "top_left_arrow",
    ],
    "help": [
        "question_arrow",
        "whats_this",
    ],
    "left_ptr_watch": [
        "progress",
        "half-busy",
        "08e8e1c95fe2fc01f976f1e063a24ccd",
        "3ecb610c1bf2410f44200f48c40d3599",
    ],
    "watch": [
        "wait",
        "clock",
    ],
    "crosshair": [
        "cross",
        "tcross",
        "precision",
    ],
    "xterm": [
        "text",
        "ibeam",
    ],
    "pencil": [
        "handwriting",
    ],
    "not-allowed": [
        "forbidden",
        "no-drop",
        "crossed_circle",
        "dnd-none",
        "03b6e0fcb3499374a867c041f52298f0",
    ],
    "sb_v_double_arrow": [
        "ns-resize",
        "size_ver",
        "n-resize",
        "s-resize",
        "top_side",
        "bottom_side",
        "row-resize",
        "00008160000006810000408080010102",
        "2870a09082c103050810ffdffffe0204",
    ],
    "sb_h_double_arrow": [
        "ew-resize",
        "size_hor",
        "e-resize",
        "w-resize",
        "left_side",
        "right_side",
        "col-resize",
        "028006030e0e7ebffc7f7070c0600140",
        "14fef782d02440884392942c11205230",
    ],
    "bd_double_arrow": [
        "nwse-resize",
        "size_fdiag",
        "nw-resize",
        "se-resize",
        "top_left_corner",
        "bottom_right_corner",
    ],
    "fd_double_arrow": [
        "nesw-resize",
        "size_bdiag",
        "ne-resize",
        "sw-resize",
        "top_right_corner",
        "bottom_left_corner",
    ],
    "fleur": [
        "move",
        "size_all",
        "all-scroll",
        "4498f0e0c1937ffe01fd06f973665830",
    ],
    "center_ptr": [
        "up-arrow",
        "up_arrow",
    ],
    "hand2": [
        "pointer",
        "hand",
        "hand1",
        "pointing_hand",
        "9d800788f1b08800ae810202380a0822",
        "e29285e634086352946a0e7090d73106",
    ],
}

# XCursor image chunk identifier
IMAGE_TYPE = 0xfffd0002


def verify_cursor(path):
    data = path.read_bytes()

    if len(data) < 16 or data[:4] != b"Xcur":
        raise ValueError(f"Invalid XCursor file: {path}")

    header, version, ntoc = struct.unpack_from(
        "<III", data, 4
    )

    if header < 16 or header + 12 * ntoc > len(data):
        raise ValueError(f"Invalid XCursor header: {path}")

    frames = Counter()

    for i in range(ntoc):
        kind, subtype, offset = struct.unpack_from(
            "<III", data, header + 12 * i
        )

        if kind != IMAGE_TYPE:
            continue

        if offset + 36 > len(data):
            raise ValueError(f"Truncated chunk: {path}")

        (
            chunk_header,
            chunk_type,
            nominal_size,
            chunk_version,
            width,
            height,
            xhot,
            yhot,
            delay,
        ) = struct.unpack_from("<9I", data, offset)

        if chunk_type != IMAGE_TYPE:
            raise ValueError(f"Invalid image chunk: {path}")

        if nominal_size != subtype:
            raise ValueError(f"Invalid nominal size: {path}")

        if not width or not height:
            raise ValueError(f"Invalid dimensions: {path}")

        if xhot >= width or yhot >= height:
            raise ValueError(f"Invalid hotspot: {path}")

        if chunk_header < 36:
            raise ValueError(f"Invalid chunk header: {path}")

        start = offset + chunk_header
        end = start + width * height * 4

        if end > len(data):
            raise ValueError(f"Truncated image: {path}")

        frames[nominal_size] += 1

    missing = sizes - set(frames)

    if missing:
        raise ValueError(
            f"{path.name}: missing sizes {sorted(missing)}"
        )

    return frames


for name in themes:
    theme = Path("themes") / name
    cursors = theme / "cursors"

    print(f"\n=== Verifying {name} ===")

    added = 0

    # Add supplementary cursor aliases
    for canonical, names in aliases.items():
        source = cursors / canonical

        if not source.is_file():
            raise ValueError(
                f"{name}: missing cursor {canonical}"
            )

        for alias in names:
            target = cursors / alias

            if target.is_file():
                continue

            if target.is_symlink():
                target.unlink()

            target.symlink_to(canonical)
            added += 1

    print(f"Added {added} supplementary aliases.")

    # Validate all real cursor files
    count = 0

    for path in sorted(cursors.iterdir()):
        if path.is_file() and not path.is_symlink():
            verify_cursor(path)
            count += 1

    if not count:
        raise ValueError(f"No cursor files found: {name}")

    # Aero has animated busy and working indicators.
    # Windows Black uses static indicators.
    expected_frames = 18 if name == "Windows-Aero-Light" else 1

    for cursor in ("watch", "left_ptr_watch"):
        frames = verify_cursor(cursors / cursor)

        for size in sizes:
            if frames[size] != expected_frames:
                raise ValueError(
                    f"{name}/{cursor}: unexpected frame "
                    f"count at {size}px: {frames[size]}"
                )

    # Validate symbolic links
    root = cursors.resolve()

    for path in root.iterdir():
        if path.is_symlink():
            if not path.is_file():
                raise ValueError(
                    f"Broken cursor alias: {path}"
                )

            if not path.resolve().is_relative_to(root):
                raise ValueError(
                    f"External cursor alias: {path}"
                )

    # Write final theme metadata
    (theme / "index.theme").write_text(
        "[Icon Theme]\n"
        f"Name={name}\n"
        "Comment=Original Microsoft Windows cursors\n"
        "Inherits=Adwaita\n"
    )

    # Metadata for Debian's x-cursor-theme alternatives
    (theme / "cursor.theme").write_text(
        "[Icon Theme]\n"
        f"Name={name}\n"
        f"Inherits={name}\n"
    )

    print(
        f"Verified: {name} "
        f"({count} cursor files, {len(sizes)} sizes)"
    )

print("\nBoth Microsoft cursor themes verified.")
