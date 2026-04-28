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
    image = Image.new("RGBA", (size, size), (0, 0, 0, 255))
    draw = ImageDraw.Draw(image)
    unit = size / 1024

    # Hyper-minimal Tremotino mark: a monoline T that also reads as a hinge/path.
    stroke = round(72 * unit)
    radius = stroke // 2
    white = (255, 255, 255, 255)
    left = round(282 * unit)
    right = round(742 * unit)
    top = round(302 * unit)
    mid = round(512 * unit)
    bottom = round(740 * unit)

    draw.rounded_rectangle((left, top, right, top + stroke), radius=radius, fill=white)
    draw.rounded_rectangle((mid - stroke // 2, top, mid + stroke // 2, bottom), radius=radius, fill=white)

    # Small offset cut-in gives the logo a less generic, more "agent path" feel.
    cut = round(118 * unit)
    draw.rounded_rectangle(
        (mid + stroke // 2, mid - stroke // 2, mid + stroke // 2 + cut, mid + stroke // 2),
        radius=radius,
        fill=white,
    )
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
