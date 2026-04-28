#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageDraw
import subprocess
import math

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

    def line(points, width):
        draw.line(p(points), fill=mark, width=round(width * scale), joint="curve")

    # Analog-futurist outer instrument: a precise broken dial, not decoration.
    draw.arc(r((206, 206, 818, 818)), 208, 332, fill=mark, width=round(18 * scale))
    draw.arc(r((206, 206, 818, 818)), 28, 152, fill=mark, width=round(18 * scale))

    for i in range(24):
        angle = math.radians(i * 15 - 90)
        major = i % 6 == 0
        outer = 326
        inner = 292 if major else 306
        cx, cy = 512, 512
        x1 = cx + math.cos(angle) * inner
        y1 = cy + math.sin(angle) * inner
        x2 = cx + math.cos(angle) * outer
        y2 = cy + math.sin(angle) * outer
        line([(x1, y1), (x2, y2)], 12 if major else 7)

    # Abstract Tremotino: pointed cap + spindle. The fairy-tale figure is
    # encoded as an instrument silhouette rather than drawn literally.
    draw.polygon(p([
        (392, 312),
        (512, 198),
        (632, 312),
        (594, 352),
        (430, 352),
    ]), fill=mark)
    draw.polygon(p([
        (296, 378),
        (728, 378),
        (676, 452),
        (348, 452),
    ]), fill=mark)

    draw.polygon(p([
        (474, 430),
        (550, 430),
        (550, 690),
        (512, 796),
        (474, 690),
    ]), fill=mark)

    # Thread path: one taut white strand crossing the spindle, with black
    # counters to keep the mark mechanical and legible at Dock sizes.
    draw.polygon(p([
        (280, 652),
        (330, 590),
        (744, 590),
        (794, 652),
        (744, 714),
        (330, 714),
    ]), fill=mark)
    draw.rectangle(r((494, 510, 530, 735)), fill=field)
    draw.polygon(p([
        (346, 622),
        (370, 606),
        (664, 606),
        (688, 622),
        (664, 638),
        (370, 638),
    ]), fill=field)

    # Small hub and sightline: the analog part of the mark.
    draw.ellipse(r((474, 612, 550, 688)), fill=mark)
    draw.ellipse(r((497, 635, 527, 665)), fill=field)
    line([(512, 452), (512, 590)], 14)

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
