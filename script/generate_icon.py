#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageDraw
import subprocess

ROOT = Path(__file__).resolve().parents[1]
resources = ROOT / "Resources"
iconset = resources / "Tremotino.iconset"
resources.mkdir(exist_ok=True)
iconset.mkdir(exist_ok=True)


def draw_icon(size: int) -> Image.Image:
    scale = 4
    canvas = 1024 * scale
    image = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 255))
    draw = ImageDraw.Draw(image)
    white = (255, 255, 255, 255)

    def p(points):
        return [(round(x * scale), round(y * scale)) for x, y in points]

    def r(box):
        return tuple(round(v * scale) for v in box)

    # Tremotino mark: an industrial T/spindle glyph with a pointed cap.
    # The reference to the Grimm figure is reduced to geometry, avoiding
    # illustration while keeping the name-specific silhouette.
    draw.polygon(p([
        (318, 260),
        (512, 128),
        (706, 260),
        (656, 322),
        (368, 322),
    ]), fill=white)

    # Horizontal crossbar with hard chamfered ends.
    draw.polygon(p([
        (246, 342),
        (778, 342),
        (724, 426),
        (300, 426),
    ]), fill=white)

    # Central spindle/stem.
    draw.polygon(p([
        (464, 398),
        (560, 398),
        (560, 762),
        (512, 824),
        (464, 762),
    ]), fill=white)

    # Thread path: a single angular diagonal that breaks the rigid monogram.
    draw.polygon(p([
        (324, 610),
        (372, 554),
        (700, 554),
        (748, 610),
        (702, 666),
        (374, 666),
    ]), fill=white)

    # Black counter-cut restores the spindle through the thread band.
    draw.rectangle(r((486, 508, 538, 718)), fill=(0, 0, 0, 255))

    # Small white pin at the center, like an instrument detail.
    draw.ellipse(r((489, 573, 535, 619)), fill=white)

    image = image.resize((size, size), Image.Resampling.LANCZOS)
    return image


sizes = [
    (16, "icon_16x16.png"),
    (32, "icon_16x16@2x.png"),
    (32, "icon_32x32.png"),
    (64, "icon_32x32@2x.png"),
    (128, "icon_128x128.png"),
    (256, "icon_128x128@2x.png"),
    (256, "icon_256x256.png"),
    (512, "icon_256x256@2x.png"),
    (512, "icon_512x512.png"),
    (1024, "icon_512x512@2x.png"),
]

for size, filename in sizes:
    draw_icon(size).save(iconset / filename)

draw_icon(1024).save(resources / "Tremotino.png")
subprocess.run(["iconutil", "-c", "icns", str(iconset), "-o", str(resources / "Tremotino.icns")], check=True)
