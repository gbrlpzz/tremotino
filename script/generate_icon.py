#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import math

ROOT = Path(__file__).resolve().parents[1]
resources = ROOT / "Resources"
iconset = resources / "Tremotino.iconset"
resources.mkdir(exist_ok=True)
iconset.mkdir(exist_ok=True)


def draw_icon(size: int) -> Image.Image:
    scale = 4
    canvas = 1024 * scale
    image = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    def r(box):
        return tuple(round(v * scale) for v in box)

    def polar(radius, degrees):
        angle = math.radians(degrees)
        return 512 + math.cos(angle) * radius, 512 + math.sin(angle) * radius

    def scaled_point(point):
        return tuple(round(v * scale) for v in point)

    def lerp(a, b, t):
        return round(a + (b - a) * t)

    def gradient_rect(box, top, bottom, mask):
        layer = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0))
        layer_draw = ImageDraw.Draw(layer)
        y1 = round(box[1] * scale)
        y2 = round(box[3] * scale)
        for y in range(y1, y2):
            t = (y - y1) / max(1, y2 - y1)
            color = tuple(lerp(top[i], bottom[i], t) for i in range(4))
            layer_draw.line([(round(box[0] * scale), y), (round(box[2] * scale), y)], fill=color)
        image.alpha_composite(Image.composite(layer, Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0)), mask))

    def rounded_segment(start, end, width, fill):
        x1, y1 = start
        x2, y2 = end
        draw.line([scaled_point((x1, y1)), scaled_point((x2, y2))], fill=fill, width=round(width * scale))
        radius = width / 2
        for x, y in (start, end):
            draw.ellipse(r((x - radius, y - radius, x + radius, y + radius)), fill=fill)

    def tremotino_tick(degrees, fill):
        tangent = degrees + 90
        outer = polar(286, degrees)
        rounded_segment(polar(190, degrees), polar(272, degrees), 25, fill)
        tx = math.cos(math.radians(tangent))
        ty = math.sin(math.radians(tangent))
        half = 27
        rounded_segment(
            (outer[0] - tx * half, outer[1] - ty * half),
            (outer[0] + tx * half, outer[1] + ty * half),
            23,
            fill,
        )

    def radial_soft_shadow(box, fill, blur):
        layer = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0))
        layer_draw = ImageDraw.Draw(layer)
        layer_draw.rounded_rectangle(r(box), radius=round(206 * scale), fill=fill)
        image.alpha_composite(layer.filter(ImageFilter.GaussianBlur(radius=blur * scale)))

    # macOS-style app tile: transparent canvas, soft cast shadow, quiet depth.
    radial_soft_shadow((92, 112, 932, 948), (0, 0, 0, 42), 30)
    shadow = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle(r((82, 74, 942, 934)), radius=round(204 * scale), fill=(0, 0, 0, 18))
    image.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(radius=12 * scale)))

    tile_mask = Image.new("L", (canvas, canvas), 0)
    tile_mask_draw = ImageDraw.Draw(tile_mask)
    tile_box = (76, 66, 948, 938)
    tile_radius = round(204 * scale)
    tile_mask_draw.rounded_rectangle(r(tile_box), radius=tile_radius, fill=255)
    gradient_rect(tile_box, (252, 252, 253, 255), (235, 238, 242, 255), tile_mask)

    draw = ImageDraw.Draw(image)

    # Native progress spinner with a quiet Tremotino trace: each tick is a tiny
    # radial T, softened by the same opacity sweep as a macOS loading indicator.
    for index in range(12):
        degrees = -90 + index * 30
        t = index / 11
        alpha = lerp(30, 224, t)
        value = lerp(132, 30, t)
        tremotino_tick(degrees, (value, value, value, alpha))

    # A restrained leading mark keeps the small-size icon crisp.
    tremotino_tick(240, (18, 18, 20, 238))

    # Glassy top edge and hairline border, clipped to the macOS squircle.
    edge = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0))
    edge_draw = ImageDraw.Draw(edge)
    edge_draw.rounded_rectangle(r(tile_box), radius=tile_radius, outline=(255, 255, 255, 112), width=round(2 * scale))
    edge_draw.rounded_rectangle(r((78, 68, 946, 936)), radius=tile_radius, outline=(176, 182, 191, 34), width=round(1 * scale))
    edge_draw.arc(r((126, 96, 898, 868)), 205, 335, fill=(255, 255, 255, 56), width=round(4 * scale))
    image.alpha_composite(Image.composite(edge, Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0)), tile_mask))

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

master_icon = draw_icon(1024)
master_icon.save(resources / "Tremotino.png")
master_icon.save(
    resources / "Tremotino.icns",
    sizes=[(16, 16), (32, 32), (64, 64), (128, 128), (256, 256), (512, 512), (1024, 1024)],
)
