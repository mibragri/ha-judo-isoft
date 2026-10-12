"""Render the integration's brand icon: an original water-drop mark, not the JUDO logo.

Usage: python brand_icon.py <output-dir>   (needs Pillow)
Writes icon.png (256 px) and icon@2x.png (512 px), the sizes Home Assistant expects.
"""
import math
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

SIZE = 512  # design grid; drawn 4x oversampled, then scaled down
SCALE = 4
TOP, BOTTOM = (79, 195, 247), (2, 119, 189)  # light blue to deep blue


def _bezier(p0, p1, p2, p3, steps=64):
    for i in range(steps + 1):
        t = i / steps
        a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t**2, t**3
        yield (a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1])


def _drop() -> list[tuple[float, float]]:
    """Outline of the drop: a tip at the top, a half circle of radius 156 below."""
    cx, cy, r = 256, 322, 156
    right = list(_bezier((cx, 36), (cx + 34, 96), (cx + r, 216), (cx + r, cy)))
    arc = [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for a in range(0, 181, 2)]
    left = list(_bezier((cx - r, cy), (cx - r, 216), (cx - 34, 96), (cx, 36)))
    return right + arc + left


def _wave(y: float, thickness: float, amplitude: float = 20, x0: int = 60, x1: int = 452) -> list[tuple[float, float]]:
    """A wavy band across the drop, as a closed outline."""
    upper = [(x, y + amplitude * math.sin((x - x0) / 196 * 2 * math.pi)) for x in range(x0, x1 + 1, 2)]
    return upper + [(x, wy + thickness) for x, wy in reversed(upper)]


def up(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    return [(x * SCALE, y * SCALE) for x, y in points]


def render() -> Image.Image:
    big = SIZE * SCALE

    gradient = Image.new("RGB", (1, big))
    for y in range(big):
        t = y / (big - 1)
        gradient.putpixel((0, y), tuple(round(a + (b - a) * t) for a, b in zip(TOP, BOTTOM)))
    gradient = gradient.resize((big, big))

    mask = Image.new("L", (big, big), 0)
    ImageDraw.Draw(mask).polygon(up(_drop()), fill=255)

    # Two waves cut out of the drop, so the mark reads the same on light and dark backgrounds.
    waves = Image.new("L", (big, big), 0)
    draw = ImageDraw.Draw(waves)
    for y in (304, 378):
        draw.polygon(up(_wave(y, 30)), fill=255)
    mask = ImageChops.subtract(mask, waves)

    icon = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    icon.paste(gradient, (0, 0), mask)
    return icon.resize((SIZE, SIZE), Image.LANCZOS)


def main() -> None:
    target = Path(sys.argv[1])
    target.mkdir(parents=True, exist_ok=True)
    icon = render()
    icon.save(target / "icon@2x.png", optimize=True)
    icon.resize((256, 256), Image.LANCZOS).save(target / "icon.png", optimize=True)


if __name__ == "__main__":
    main()
