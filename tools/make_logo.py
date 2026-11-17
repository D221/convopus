"""Generate docs/logo.svg — the convopus mark, from maths.

The mark is one Gaussian-windowed sine wave:

    y(t) = A · exp(-((t - 0.5)^2) / (2σ²)) · sin(2π·cycles·t)

sampled across the canvas, drawn as a single round-capped stroke. No
background, no gradients, no external assets — just the curve.

Run:  uv run python tools/make_logo.py
"""

import math
import pathlib

WIDTH = 256.0
AMPLITUDE = 72.0
CYCLES = 4
SIGMA = 0.22
STROKE = 16.0
PAD = 34.0
SAMPLES = 96
COLOUR = "#14b8a6"

OUT = pathlib.Path(__file__).resolve().parent.parent / "docs" / "logo.svg"


def wave_points():
    points = []
    for i in range(SAMPLES + 1):
        t = i / SAMPLES
        envelope = math.exp(-((t - 0.5) ** 2) / (2 * SIGMA**2))
        y = WIDTH / 2 - AMPLITUDE * envelope * math.sin(2 * math.pi * CYCLES * t)
        x = PAD + (WIDTH - 2 * PAD) * t
        points.append(
            f"{x:.2f}".rstrip("0").rstrip(".")
            + ","
            + f"{y:.2f}".rstrip("0").rstrip(".")
        )
    return " ".join(points)


def render():
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH:.0f} {WIDTH:.0f}"
     width="{WIDTH:.0f}" height="{WIDTH:.0f}" role="img" aria-labelledby="title">
  <title id="title">convopus</title>
  <!-- convopus logo. Dedicated to the public domain under CC0 1.0 (see LICENSE). -->
  <polyline points="{wave_points()}"
            fill="none" stroke="{COLOUR}" stroke-width="{STROKE:.0f}"
            stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render(), encoding="utf-8")
    print("wrote", OUT)
