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
    image = Image.new("RGBA", (canvas, canvas), (255, 255, 255, 255))
    draw = ImageDraw.Draw(image)
    black = (0, 0, 0, 255)
    mark = black
    field = (255, 255, 255, 255)

    def p(points):
        return [(round(x * scale), round(y * scale)) for x, y in points]

    def r(box):
        return tuple(round(v * scale) for v in box)

    # Minimal Tremotino mark: a single custom T with a spindle point.
    # The story reference stays implicit through the pointed axis and counter.
    draw.polygon(p([
        (320, 282),
        (704, 282),
        (656, 358),
        (368, 358),
    ]), fill=mark)

    draw.polygon(p([
        (462, 358),
        (562, 358),
        (562, 696),
        (512, 794),
        (462, 696),
    ]), fill=mark)

    # Small analog counter: enough instrument character without busy detail.
    draw.ellipse(r((486, 558, 538, 610)), fill=field)

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
