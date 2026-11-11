# -*- coding: utf-8 -*-
"""Paper surface generation and compositing for WhiteFrame 3.5."""
from functools import lru_cache
import math
import random
import zlib

from PIL import Image, ImageChops, ImageDraw, ImageFilter

PAPER_PROFILES = {
    "\u7ec6\u68c9\u7eb9": {"coarse": 28, "mid": 24, "fine": 20, "fiber": 0.25, "contrast": 0.92, "ridge": 0.16},
    "\u7c97\u7eb9\u7eb8": {"coarse": 43, "mid": 35, "fine": 27, "fiber": 0.40, "contrast": 1.20, "ridge": 0.26},
    "\u753b\u5e03": {"coarse": 24, "mid": 19, "fine": 16, "fiber": 0.20, "contrast": 1.04, "ridge": 0.31},
}

def _field(size, divisor, spread, rng):
    width, height = size
    gw = max(4, min(1000, width // divisor))
    gh = max(4, min(1000, height // divisor))
    data = bytes(rng.randint(max(0, 128 - spread), min(255, 128 + spread))
                 for _ in range(gw * gh))
    return Image.frombytes("L", (gw, gh), data).resize(size, Image.Resampling.BICUBIC)


@lru_cache(maxsize=4)
def paper_texture(size, kind):
    """Return a deterministic, softly embossed paper grain at the requested size."""
    width, height = max(1, int(size[0])), max(1, int(size[1]))
    profile = PAPER_PROFILES.get(kind, PAPER_PROFILES["\u7ec6\u68c9\u7eb9"])
    seed = zlib.crc32(f"{width}x{height}:{kind}".encode("utf-8"))
    rng = random.Random(seed)

    texture = Image.new("L", (width, height), 128)
    for divisor, spread, mix in (
        (44, profile["coarse"], 0.42),
        (13, profile["mid"], 0.34),
        (3, profile["fine"], 0.30),
    ):
        texture = Image.blend(texture, _field((width, height), divisor, spread, rng), mix)

    fibers = Image.new("L", (width, height), 128)
    draw = ImageDraw.Draw(fibers)
    if kind == "\u753b\u5e03":
        sx, sy = max(4, width // 150), max(4, height // 150)
        for x in range(0, width, sx):
            shade = rng.randint(114, 142)
            draw.line((x, 0, x, height), fill=shade, width=1)
            draw.line((min(width - 1, x + 1), 0, min(width - 1, x + 1), height), fill=132)
        for y in range(0, height, sy):
            shade = rng.randint(114, 142)
            draw.line((0, y, width, y), fill=shade, width=1)
            draw.line((0, min(height - 1, y + 1), width, min(height - 1, y + 1)), fill=132)
        fibers = fibers.filter(ImageFilter.GaussianBlur(0.26))
        texture = Image.blend(texture, fibers, 0.32)
    else:
        count = min(2600, max(60, width * height // (1800 if kind == "\u7c97\u7eb9\u7eb8" else 3000)))
        short = min(width, height)
        for _ in range(count):
            x, y = rng.randrange(width), rng.randrange(height)
            length = rng.uniform(0.006, 0.060 if kind == "\u7c97\u7eb9\u7eb8" else 0.040) * short
            angle = rng.uniform(-0.55, 0.55) if rng.random() < 0.70 else rng.uniform(0, math.tau)
            dx, dy = math.cos(angle) * length, math.sin(angle) * length
            shade = rng.choice((rng.randint(103, 120), rng.randint(137, 151)))
            draw.line((x, y, x + dx, y + dy), fill=shade, width=1)
        fibers = fibers.filter(ImageFilter.GaussianBlur(0.24))
        texture = Image.blend(texture, fibers, profile["fiber"])

    # A low-frequency emboss pass gives the surface a believable pressed-paper relief.
    # Keep it subtle so the image window remains visually clean after compositing.
    ridge = texture.filter(ImageFilter.GaussianBlur(max(0.7, min(width, height) / 180.0)))
    ridge = ImageChops.subtract(texture, ridge, offset=128).point(lambda value: 128 + (value - 128) * 2)
    texture = Image.blend(texture, ridge, profile.get("ridge", 0.18))
    return texture.point(lambda value: max(0, min(255, round(128 + (value - 128) * profile["contrast"]))))


def apply_paper(canvas, style):
    """Tint and emboss only the empty frame canvas; the photo is pasted afterwards."""
    if style.paper_tone and style.mode == "solid":
        canvas = Image.new("RGB", canvas.size, style.paper_tone)
    else:
        canvas = canvas.convert("RGB")

    if style.paper in ("", "\u65e0") or style.paper_amt <= 0:
        return canvas

    texture = paper_texture(canvas.size, style.paper)
    mask = texture.point(lambda value: 255 if value >= 128 else 0)
    highlights = texture.point(lambda value: max(0, round((value - 128) * 0.92)))
    shadows = texture.point(lambda value: max(0, round((128 - value) * 0.92)))
    light_rgb = Image.merge("RGB", (highlights, highlights, highlights))
    shade_rgb = Image.merge("RGB", (shadows, shadows, shadows))
    bright = ImageChops.add(canvas, light_rgb)
    dark = ImageChops.subtract(canvas, shade_rgb)
    embossed = Image.composite(bright, dark, mask)
    strength = min(0.92, max(0.0, style.paper_amt / 100.0 * 1.08))
    return Image.blend(canvas, embossed, strength)
