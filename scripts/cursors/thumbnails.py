#!/usr/bin/env python3
import ctypes as C
from pathlib import Path
from PIL import Image

CANVAS_SIZE = 32
ARTWORK_SIZE = 28
SOURCE_SIZE = 128

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

lib.XcursorFilenameLoadImage.argtypes = [
    C.c_char_p, C.c_int
]
lib.XcursorFilenameLoadImage.restype = C.POINTER(CursorImage)

lib.XcursorImageDestroy.argtypes = [
    C.POINTER(CursorImage)
]
lib.XcursorImageDestroy.restype = None

for theme in ("Windows-Aero-Light", "Windows-Black"):
    root = Path("/usr/share/icons") / theme / "cursors"

    # Load high-resolution original artwork
    ptr = lib.XcursorFilenameLoadImage(
        str(root / "left_ptr").encode(),
        SOURCE_SIZE
    )

    if not ptr:
        raise RuntimeError(f"Cannot load cursor: {theme}")

    try:
        img = ptr.contents
        pixels = []

        # Convert premultiplied ARGB to straight RGBA
        for i in range(img.width * img.height):
            p = img.pixels[i]

            a = (p >> 24) & 255
            r = (p >> 16) & 255
            g = (p >> 8) & 255
            b = p & 255

            if a:
                r = min(255, round(r * 255 / a))
                g = min(255, round(g * 255 / a))
                b = min(255, round(b * 255 / a))
            else:
                r = g = b = 0

            pixels.append((r, g, b, a))

        artwork = Image.new(
            "RGBA", (img.width, img.height)
        )
        artwork.putdata(pixels)

    finally:
        lib.XcursorImageDestroy(ptr)

    # Remove transparent padding
    bounds = artwork.getchannel("A").getbbox()

    if bounds is None:
        raise ValueError(f"Empty cursor: {theme}")

    artwork = artwork.crop(bounds)

    # High-quality proportional downsampling
    artwork.thumbnail(
        (ARTWORK_SIZE, ARTWORK_SIZE),
        Image.Resampling.LANCZOS
    )

    # Center on transparent canvas
    canvas = Image.new(
        "RGBA",
        (CANVAS_SIZE, CANVAS_SIZE),
        (0, 0, 0, 0)
    )

    x = (CANVAS_SIZE - artwork.width) // 2
    y = (CANVAS_SIZE - artwork.height) // 2

    canvas.alpha_composite(artwork, (x, y))

    output = root / "thumbnail.png"
    canvas.save(output)
    output.chmod(0o644)

    print(f"Generated: {output}")
