"""Render docs/icon.ico — the app icon — from the logo geometry.

Needs cairosvg and Pillow:

    uv run --with cairosvg --with pillow python tools/make_icon.py

The logo itself is transparent; an icon is not, so this draws the same wave on
a dark rounded plate to stay legible at 16 px.
"""

import io
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))

import cairosvg
import make_logo
from PIL import Image

SIZES = [256, 128, 64, 48, 32, 16]
PLATE = "#0b1020"
WAVE = "#2dd4bf"

OUT = pathlib.Path(__file__).resolve().parent.parent / "docs" / "icon.ico"


def icon_svg():
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256">'
        f'<rect width="256" height="256" rx="56" fill="{PLATE}"/>'
        f'<polyline points="{make_logo.wave_points()}" fill="none" stroke="{WAVE}" '
        f'stroke-width="{make_logo.STROKE:.0f}" stroke-linecap="round" stroke-linejoin="round"/>'
        "</svg>"
    )


def main():
    png = cairosvg.svg2png(
        bytestring=icon_svg().encode("utf-8"), output_width=256, output_height=256
    )
    base = Image.open(io.BytesIO(png)).convert("RGBA")
    base.save(OUT, format="ICO", sizes=[(s, s) for s in SIZES])
    print("wrote", OUT, "sizes", SIZES)


if __name__ == "__main__":
    main()
