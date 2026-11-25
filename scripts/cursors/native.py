#!/usr/bin/env python3
import ctypes as C
from pathlib import Path

class CursorImage(C.Structure):
    _fields_ = [
        ("version", C.c_uint32),
        ("size", C.c_uint32),
        ("width", C.c_uint32),
        ("height", C.c_uint32),
        ("xhot", C.c_uint32),
        ("yhot", C.c_uint32),
        ("delay", C.c_uint32),
        ("pixels", C.POINTER(C.c_uint32)),
    ]

lib = C.CDLL("libXcursor.so.1")

lib.XcursorLibraryLoadImage.argtypes = [
    C.c_char_p,
    C.c_char_p,
    C.c_int,
]

lib.XcursorLibraryLoadImage.restype = (
    C.POINTER(CursorImage)
)

lib.XcursorImageDestroy.argtypes = [
    C.POINTER(CursorImage)
]

lib.XcursorImageDestroy.restype = None

sizes = [
    24, 30, 32, 36, 40, 42, 48, 54,
    56, 60, 64, 72, 80, 96, 112, 128,
]

themes = [
    "Windows-Aero-Light",
    "Windows-Black",
]

failures = 0
checks = 0

for theme in themes:
    root = Path("/usr/share/icons") / theme / "cursors"

    if not root.is_dir():
        raise SystemExit(f"Theme not installed: {theme}")

    for path in sorted(root.iterdir()):
        # Cinnamon preview artwork is not an XCursor binary.
        if path.name == "thumbnail.png":
            continue

        for size in sizes:
            checks += 1

            ptr = lib.XcursorLibraryLoadImage(
                path.name.encode(),
                theme.encode(),
                size,
            )

            if not ptr:
                print(f"FAIL: {theme}/{path.name} @ {size}")
                failures += 1
                continue

            img = ptr.contents

            if (
                img.size != size
                or img.xhot >= img.width
                or img.yhot >= img.height
            ):
                print(
                    f"FAIL: {theme}/{path.name} @ {size}"
                    f" (returned {img.size})"
                )
                failures += 1

            lib.XcursorImageDestroy(ptr)

    print(f"Checked: {theme}")

print(f"Total checks: {checks}")
print(f"Failures: {failures}")

if failures or not checks:
    raise SystemExit(1)
