# -*- coding: utf-8 -*-
"""2.0 核心：纯色 / 取色 / 模糊延伸边框 + 水印 + 相机参数条（含 EXIF）。"""
import math
import os
import random
from collections import Counter
from functools import lru_cache
from dataclasses import dataclass, field
from datetime import datetime

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

from paperfx40 import apply_paper, paper_texture as _paper_tex

EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}
SKIP_DIR = "白边输出"

BRANDS = {
    "xiaomi": "Xiaomi", "redmi": "Redmi", "apple": "Apple", "sony": "SONY", "canon": "Canon",
    "nikon": "Nikon", "fujifilm": "FUJIFILM", "leica": "LEICA", "dji": "DJI",
    "hasselblad": "Hasselblad", "oppo": "OPPO", "vivo": "vivo", "huawei": "HUAWEI",
    "samsung": "SAMSUNG", "panasonic": "Panasonic", "ricoh": "RICOH", "gopro": "GoPro",
    "oneplus": "OnePlus", "honor": "HONOR", "google": "Google", "sigma": "SIGMA",
    "om digital": "OM SYSTEM", "olympus": "OLYMPUS", "pentax": "PENTAX", "motorola": "motorola",
}

FONT_BOLD = "C:/Windows/Fonts/msyhbd.ttc"
FONT_REG = "C:/Windows/Fonts/msyh.ttc"
_fonts = {}


def font(size, bold=True):
    size = max(8, int(size))
    key = (size, bold)
    if key not in _fonts:
        path = FONT_BOLD if bold else FONT_REG
        try:
            _fonts[key] = ImageFont.truetype(path, size)
        except Exception:
            _fonts[key] = ImageFont.load_default()
    return _fonts[key]


@dataclass
class Style:
    mode: str = "solid"          # solid | sample | blur
    color: str = "#ffffff"
    pad: float = 0.06
    ratio: float | None = None
    blur: float = 0.05           # 模糊半径 = 短边 × blur
    darken: float = 0.0          # 模糊底图压暗 0~0.6
    max_side: int | None = None
    fmt: str = "jpg"
    # 水印
    wm_text: str = ""
    wm_pos: str = "br"
    wm_size: float = 0.030
    wm_alpha: int = 170
    wm_color: str = "#ffffff"
    # 参数条
    bar: bool = False
    bar_model: str = ""          # 留空 => 从 EXIF 读
    bar_params: str = ""         # 留空 => 从 EXIF 拼
    logo: str = ""               # 自定义品牌图标 png，留空 => 品牌文字
    bar_color: str = "#111111"
    bar_alpha: int = 235
    bar_auto: bool = True        # 按底色深浅自动选黑/白文字
    wm_auto: bool = True
    # 拼图
    collage: bool = False
    cols: int = 0                # 0 = 自动
    gap: float = 0.012           # 格间距，占格子边长
    # 细边线（照片与白边之间的一圈线）
    line: float = 0.0            # 线宽，相对短边
    line_color: str = "#111111"
    # 阴影
    shadow: bool = False
    sh_dir: int = 7              # DIRS 下标，7 = 正下方
    sh_dist: float = 0.018
    sh_blur: float = 0.022
    sh_strength: int = 95
    # 文本字段
    fields: dict = field(default_factory=dict)
    enabled: dict = field(default_factory=dict)
    cam_prefix: str = ""
    lens_prefix: str = ""
    # 双图画布
    twin: bool = False
    twin_top: float = 0.54
    twin_zoom: tuple = (1.0, 1.0)
    twin_px: tuple = (0.0, 0.0)
    twin_py: tuple = (0.0, 0.0)
    # 调色（值域 -100..100，0 为不变）
    grade: dict = field(default_factory=dict)
    # 胶片
    film: str = "关闭"
    film_grain: int = 0
    film_vig: int = 0
    film_fade: int = 0
    film_roll: int = 0
    # 光晕
    halo: int = 0
    halo_thr: int = 200
    halo_radius: float = 0.018
    halo_tint: str = "#ff7a50"
    glow: int = 0
    # 随机漏光
    leak: int = 0
    leak_seed: int = 7
    leak_tint: str = "#ff9a5a"
    # 纸张质感 / 卡纸压边
    paper: str = "无"
    paper_amt: int = 35
    paper_tone: str = ""
    recess: int = 0
    film_strength: int = 100
    # 渐变滤镜
    grad_kind: str = "关闭"
    grad_dir: str = "上→下"
    grad_amt: int = 0
    grad_feather: int = 60
    grad_x: int = 50
    grad_y: int = 45
    radius: int = 0
    # 胶片条
    strip: bool = False
    strip_h: int = 7
    strip_tone: str = "#141414"
    strip_label: str = "KODAK 400"
    strip_no: str = "12A"
    strip_fmt: str = "135 全画幅"
    # 推冲 / 拉冲
    push: int = 0
    # 相纸冲印
    paper_finish: str = "光面"
    cc_m: int = 0
    cc_y: int = 0
    # 拍立得
    polaroid: bool = False
    polaroid_title: str = ""
    # 日期背印
    ds_on: bool = False
    ds_text: str = ""
    ds_size: int = 4
    ds_color: str = "#ff5a2a"
    ds_pos: str = "br"
    ds_alpha: int = 230
    # 撕纸边
    torn: int = 0
    torn_seed: int = 11
    # 曲线（0~255 控制点，空 = 不启用）
    curve_m: list = field(default_factory=list)
    curve_r: list = field(default_factory=list)
    curve_g: list = field(default_factory=list)
    curve_b: list = field(default_factory=list)
    # 网点印刷（Riso）
    riso_on: bool = False
    riso_cell: int = 8
    riso_angle: int = 45
    riso_ink1: str = "#22201e"
    riso_ink2: str = "#ff5a4a"
    riso_amt: int = 75
    # 双重曝光
    de_image: str = ""
    de_mode: str = "滤色"
    de_amt: int = 0


# ---------------- EXIF ----------------
def read_exif(im):
    d = {"make": "", "model": "", "lens": "", "fnum": None, "exp": None,
         "iso": None, "focal": None, "focal35": None, "date": "", "time": ""}
    try:
        ex = im.getexif()
        sub = ex.get_ifd(0x8769) or {}
    except Exception:
        return d

    def pick(tag, *sources):
        for s in sources:
            try:
                v = s.get(tag)
            except Exception:
                v = None
            if v not in (None, "", 0):
                return v
        return None

    d["make"] = str(pick(271, ex) or "").strip()
    d["model"] = str(pick(272, ex) or "").strip()
    d["lens"] = str(pick(42036, sub, ex) or "").strip()
    d["fnum"] = pick(33437, sub, ex)
    d["exp"] = pick(33434, sub, ex)
    d["iso"] = pick(34855, sub, ex) or pick(34867, sub, ex)
    d["focal"] = pick(37386, sub, ex)
    d["focal35"] = pick(41989, sub, ex)
    raw = str(pick(36867, sub, ex) or "").strip()
    if len(raw) >= 10:
        d["date"] = raw[:10].replace(":", "/")
    d["time"] = raw[11:16] if len(raw) >= 16 else ""
    return d


FIELD_DEFS = [
    ("camera", "相机"), ("lens", "镜头"), ("focal", "35mm 焦距"), ("aperture", "光圈"),
    ("shutter", "快门速度"), ("iso", "ISO"), ("title", "标题"),
    ("author", "摄影师"), ("place", "地点"),
    ("date", "拍摄日期"), ("time", "时间"),
]
DIRS = [(-1, -1), (0, -1), (1, -1), (-1, 0), (0, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]


def field_auto(key, d):
    """没手填时，从 EXIF 自动生成显示值。"""
    d = d or {}

    def f(v):
        return _num(v)

    if key == "camera":
        return d.get("model") or d.get("make") or ""
    if key == "lens":
        return d.get("lens") or ""
    if key == "focal":
        v = f(d.get("focal35")) or f(d.get("focal"))
        return f"{round(v)}mm" if v else ""
    if key == "aperture":
        v = f(d.get("fnum"))
        return f"F{v:g}" if v else ""
    if key == "shutter":
        v = f(d.get("exp"))
        if not v:
            return ""
        return f"1/{round(1 / v)}s" if 0 < v < 1 else f"{v:g}s"
    if key == "iso":
        v = f(d.get("iso"))
        return f"ISO{int(v)}" if v else ""
    if key == "date":
        return d.get("date") or ""
    if key == "time":
        return d.get("time") or ""
    return ""


def bar_lines(st, d):
    """参数条三行：机型 / 曝光参数 / 元信息。"""
    def val(k):
        return (st.fields or {}).get(k, "").strip() or field_auto(k, d)

    def on(k):
        return (st.enabled or {}).get(k, False) and val(k)

    head = []
    if on("camera"):
        head.append((st.cam_prefix.strip() + " " if st.cam_prefix.strip() else "") + on("camera"))
    if on("lens"):
        head.append((st.lens_prefix.strip() + " " if st.lens_prefix.strip() else "") + on("lens"))
    expo = [on(k) for k in ("focal", "aperture", "shutter", "iso") if on(k)]
    meta = [on(k) for k in ("title", "author", "place") if on(k)]
    dt = [on(k) for k in ("date", "time") if on(k)]
    if dt:
        meta.append("  ".join(dt))
    return ("   ".join(head), "  ".join(expo), "  ·  ".join(meta))


def brand_of(make):
    m = (make or "").lower()
    for k, v in BRANDS.items():
        if k in m:
            return v
    return (make or "").strip()


def _num(v):
    try:
        return float(v)
    except Exception:
        try:
            return v.numerator / v.denominator
        except Exception:
            return None


def fmt_params(d):
    out = []
    f = _num(d.get("fnum"))
    if f:
        s = f"{f:.2f}".rstrip("0").rstrip(".")
        out.append(f"f/{s}")
    e = _num(d.get("exp"))
    if e:
        out.append(f"1/{round(1 / e)}s" if 0 < e < 1 else f"{e:g}s")
    try:
        if d.get("iso"):
            out.append(f"ISO {int(_num(d['iso']))}")
    except Exception:
        pass
    fl = _num(d.get("focal")) or _num(d.get("focal35"))
    if fl:
        out.append(f"{round(fl)}mm")
    return "  ".join(out)


# ---------------- 取色 / 背景 ----------------
def edge_color(im):
    """从照片四周取样，返回出现最多的中间调颜色。"""
    w, h = im.size
    b = max(2, int(min(w, h) * 0.05))
    parts = [im.crop((0, 0, w, b)), im.crop((0, h - b, w, h)),
             im.crop((0, 0, b, h)), im.crop((w - b, 0, w, h))]
    cnt = Counter()
    for part in parts:
        q = part.convert("RGB").resize((48, 48)).quantize(colors=8)
        pal = q.getpalette()
        for n, idx in (q.getcolors() or []):
            rgb = tuple(pal[idx * 3: idx * 3 + 3])
            cnt[rgb] += n
    if not cnt:
        return "#ffffff"
    for rgb, _ in cnt.most_common():
        lum = 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]
        if 18 < lum < 242:
            return "#%02x%02x%02x" % rgb
    return "#%02x%02x%02x" % cnt.most_common(1)[0][0]


def backdrop(im, W, H, st, sample_color=None):
    if st.mode == "blur":
        bg = ImageOps.fit(im.convert("RGB"), (W, H), method=Image.LANCZOS)
        r = max(2, int(min(W, H) * st.blur))
        bg = bg.filter(ImageFilter.GaussianBlur(r))
        if st.darken:
            bg = ImageEnhance.Brightness(bg).enhance(max(0.2, 1 - st.darken))
        return bg
    if st.mode == "sample":
        return Image.new("RGB", (W, H), sample_color or edge_color(im))
    return Image.new("RGB", (W, H), st.color)


# ---------------- 参数条 ----------------
def _luma(im, box):
    """区域平均亮度，用来决定文字用黑还是白。"""
    try:
        x0, y0, x1, y1 = [int(v) for v in box]
        x1, y1 = max(x0 + 1, x1), max(y0 + 1, y1)
        g = im.crop((x0, y0, x1, y1)).convert("L").resize((1, 1), Image.Resampling.BOX)
        return g.getpixel((0, 0))
    except Exception:
        return 255


def auto_ink(lum):
    return "#111111" if lum > 148 else "#ffffff"


def draw_bar(canvas, area, st, d):
    """多行参数条：机型 / 曝光 / 元信息，字段可逐项开关。"""
    x0, y0, x1, y1 = area
    h = y1 - y0
    if h < 10 or x1 - x0 < 40:
        return
    rows = [r for r in bar_lines(st, d) if r]
    if not rows:
        return
    scales = [1.0, 0.78, 0.68][:len(rows)]
    fs = (h * 0.90) / (sum(scales) * 1.40)
    col = auto_ink(_luma(canvas, area)) if st.bar_auto else st.bar_color
    draw = ImageDraw.Draw(canvas)
    x = x0
    logo = None
    if st.logo and os.path.exists(st.logo):
        try:
            logo = Image.open(st.logo).convert("RGBA")
        except Exception:
            logo = None

    # 超宽就整体缩字号
    for _ in range(12):
        widest = max(draw.textlength(t, font=font(fs * sc, i == 0))
                     for i, (t, sc) in enumerate(zip(rows, scales)))
        if widest <= (x1 - x) - (fs * 3 if logo is not None else 0) or fs <= 9:
            break
        fs *= 0.90

    cy = (y0 + y1) / 2
    total = sum(scales) * 1.40 * fs
    if logo is not None:
        lh = min(h * 0.60, total * 0.60)
        lw = max(1, int(logo.width / max(1, logo.height) * lh))
        logo = logo.resize((lw, max(1, int(lh))), Image.LANCZOS)
        canvas.paste(logo, (int(x), int(cy - lh / 2)), logo)
        x += lw + fs * 0.45
    y = cy - total / 2
    for i, (txt, sc) in enumerate(zip(rows, scales)):
        rh = fs * sc * 1.40
        draw.text((x, y + rh / 2), txt, font=font(fs * sc, i == 0), fill=col, anchor="lm")
        y += rh


# ---------------- 调色 ----------------
GRADE_KEYS = ["temp", "tint", "exposure", "contrast", "highlights", "shadows",
              "whites", "blacks", "texture", "clarity", "dehaze", "vibrance", "saturation"]


def _cl(v):
    return 0 if v < 0 else (255 if v > 255 else int(v))


def apply_grade(im, st: Style):
    g = st.grade or {}

    def val(k):
        try:
            return (g.get(k) or 0) / 100.0
        except Exception:
            return 0.0

    t, ti = val("temp"), val("tint")
    if t or ti:
        r, gg, b = im.split()
        r = r.point(lambda v: _cl(v * (1 + 0.28 * t)))
        b = b.point(lambda v: _cl(v * (1 - 0.28 * t)))
        gg = gg.point(lambda v: _cl(v * (1 + 0.14 * ti)))
        im = Image.merge("RGB", (r, gg, b))

    ev = val("exposure") * 2
    if ev:
        im = ImageEnhance.Brightness(im).enhance(max(0.05, 2.0 ** ev))

    hi, sh, wh, bl = val("highlights"), val("shadows"), val("whites"), val("blacks")
    if hi or sh or wh or bl:
        lut = []
        for i in range(256):
            v = i / 255.0
            v += sh * 0.42 * math.exp(-((v - 0.20) ** 2) / (2 * 0.17 ** 2))
            v += hi * 0.42 * math.exp(-((v - 0.84) ** 2) / (2 * 0.17 ** 2))
            v += wh * 0.20 * (v ** 2)
            v += bl * 0.20 * ((1 - v) ** 2)
            lut.append(_cl(v * 255))
        im = im.point(lut * 3)

    c = val("contrast")
    if c:
        im = ImageEnhance.Contrast(im).enhance(max(0.05, 1 + c))

    dh = val("dehaze")
    if dh:
        im = ImageEnhance.Contrast(im).enhance(max(0.1, 1 + 0.35 * dh))
        im = ImageEnhance.Color(im).enhance(max(0.1, 1 + 0.22 * dh))

    for key, rad, pct in (("texture", 700, 85), ("clarity", 220, 130)):
        v = val(key)
        if not v:
            continue
        r = max(1, im.width // rad)
        if v > 0:
            im = im.filter(ImageFilter.UnsharpMask(radius=r, percent=int(v * pct), threshold=3))
        else:
            im = im.filter(ImageFilter.GaussianBlur(r * abs(v) * 1.6))

    sa, vi = val("saturation"), val("vibrance")
    if sa:
        im = ImageEnhance.Color(im).enhance(max(0.0, 1 + sa))
    if vi:
        im = ImageEnhance.Color(im).enhance(max(0.0, 1 + vi * 0.55))
    return im


# ---------------- 胶片 ----------------
# rgain, ggain, bgain, gamma, sat, contrast
FILMS = {
    "关闭": None,
    # 彩色负片
    "Portra 160": (1.04, 1.00, 0.96, 1.00, 0.92, 0.97),
    "Portra 400": (1.07, 1.00, 0.93, 0.98, 0.94, 0.98),
    "Portra 800": (1.08, 1.00, 0.92, 0.97, 0.98, 1.03),
    "Gold 200": (1.10, 1.02, 0.88, 0.96, 1.06, 1.00),
    "Ektar 100": (1.04, 1.00, 0.98, 1.02, 1.18, 1.10),
    "Pro 400H": (1.02, 1.02, 1.00, 0.99, 0.90, 0.96),
    "Superia 400": (1.03, 1.01, 0.96, 1.00, 1.08, 1.02),
    "Lomo 400": (1.09, 1.00, 0.90, 1.03, 1.16, 1.08),
    # 反转片
    "Velvia 50": (1.02, 1.00, 1.03, 1.04, 1.30, 1.12),
    "Provia 100F": (1.01, 1.00, 1.02, 1.02, 1.10, 1.05),
    "Ektachrome E100": (0.99, 1.00, 1.06, 1.01, 1.08, 1.06),
    # 电影卷
    "CineStill 800T": (0.95, 1.00, 1.12, 1.00, 0.98, 1.06),
    # 黑白
    "HP5 Plus": (1.00, 1.00, 1.00, 1.00, 0.00, 1.14),
    "Tri-X 400": (1.00, 1.00, 1.00, 0.98, 0.00, 1.22),
    # 3.1 新增
    "Kodachrome 64": (1.06, 0.99, 0.92, 1.02, 1.15, 1.10),
    "Ultramax 400": (1.06, 1.01, 0.95, 1.01, 1.10, 1.04),
    "ColorPlus 200": (1.09, 1.02, 0.90, 0.97, 1.05, 1.02),
    "Fuji C200": (1.02, 1.02, 0.99, 1.00, 1.02, 1.00),
    "Astia 100F": (1.02, 1.00, 1.01, 1.01, 1.03, 0.98),
    "Vista 400": (1.07, 1.00, 0.94, 1.00, 1.12, 1.05),
    "Delta 3200": (1.00, 1.00, 1.00, 0.92, 0.00, 1.10),
    "Acros 100": (1.00, 1.00, 1.00, 1.02, 0.00, 1.08),
    "Pan F 50": (1.00, 1.00, 1.00, 1.04, 0.00, 1.16),
    "Retro 80S": (1.00, 1.00, 1.00, 0.96, 0.00, 1.28),
    "Cross Process": (1.00, 1.00, 1.00, 1.00, 1.45, 1.32),
    "Bleach Bypass": (1.00, 1.00, 1.00, 1.00, 0.42, 1.52),
    # 4.0 新增：参考 darktable_filmsim / ComfyUI-Darkroom 的胶片型号表
    "Vision3 250D": (1.02, 1.00, 0.98, 1.00, 1.02, 0.95),
    "Vision3 500T": (0.96, 1.00, 1.10, 1.00, 1.04, 0.96),
    "Eterna 500T": (0.97, 1.02, 1.05, 1.00, 0.90, 0.94),
    "Superia Reala": (1.02, 1.02, 1.00, 1.00, 1.06, 1.02),
    "Natura 1600": (1.03, 1.02, 0.97, 0.98, 1.04, 0.98),
    "Agfa Vista 100": (1.08, 1.00, 0.93, 1.00, 1.12, 1.04),
    "T-Max 400": (1.00, 1.00, 1.00, 1.02, 0.00, 1.10),
    "Acros II 100": (1.00, 1.00, 1.00, 1.03, 0.00, 1.06),
}
SPECIAL_FILMS = {"Cross Process", "Bleach Bypass"}


def film_point(name, r, g, b):
    """归一化 RGB(0~1) 的纯函数版本，用于烘焙 3D LUT（与界面渲染语义一致）。"""
    p = FILMS.get(name)
    if not p:
        return r, g, b
    rg, gg, bg, gamma, sat, con = p
    if name == "Cross Process":
        r, g, b = r ** 0.80, g ** 1.06, b ** 1.32
    else:
        r = min(1.0, (r ** gamma) * rg)
        g = min(1.0, (g ** gamma) * gg)
        b = min(1.0, (b ** gamma) * bg)
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    r = lum + (r - lum) * sat
    g = lum + (g - lum) * sat
    b = lum + (b - lum) * sat
    r = (r - 0.5) * con + 0.5
    g = (g - 0.5) * con + 0.5
    b = (b - 0.5) * con + 0.5
    if name == "Bleach Bypass":
        r += (16 / 255.0) * max(0.0, r) ** 3
        g += (16 / 255.0) * max(0.0, g) ** 3
        b += (16 / 255.0) * max(0.0, b) ** 3
    return (min(1.0, max(0.0, r)), min(1.0, max(0.0, g)), min(1.0, max(0.0, b)))


def export_cube(name, path, size=33):
    """.cube 3D LUT，size=33 即 33x33x33。数据顺序：R 变化最快。"""
    n = size - 1.0
    out = ['TITLE "%s"' % name,
           "# Film emulation baked by 白边相框 4.0",
           "# channel curve -> saturation -> contrast (no image statistics)",
           "LUT_3D_SIZE %d" % size,
           "DOMAIN_MIN 0.0 0.0 0.0",
           "DOMAIN_MAX 1.0 1.0 1.0"]
    for bi in range(size):
        b = bi / n
        for gi in range(size):
            g = gi / n
            for ri in range(size):
                R, G, B = film_point(name, ri / n, g, b)
                out.append("%.6f %.6f %.6f" % (R, G, B))
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out) + "\n")
    return path


def draw_datestamp(canvas, st: Style):
    """胶片机身日期背印：橙红 LED 字 + 轻微发光。"""
    if not st.ds_on:
        return canvas
    W, H = canvas.size
    txt = (st.ds_text or "").strip()
    if not txt:
        txt = datetime.now().strftime("%y %m %d")
    fs = max(8, min(W, H) * max(1, st.ds_size) / 100.0)
    f = None
    for path in ("C:/Windows/Fonts/consola.ttf", "C:/Windows/Fonts/cour.ttf",
                 "C:/Windows/Fonts/msyh.ttc"):
        try:
            f = ImageFont.truetype(path, int(fs))
            break
        except Exception:
            continue
    if f is None:
        f = font(fs, False)
    c = st.ds_color.lstrip("#")
    rgb = tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    tw = d.textlength(txt, font=f)
    m = min(W, H) * 0.045
    x = {"l": m, "c": (W - tw) / 2, "r": W - tw - m}[st.ds_pos[1]]
    y = {"t": m, "m": (H - fs) / 2, "b": H - fs - m}[st.ds_pos[0]]
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).text((x, y), txt, font=f, fill=rgb + (150,))
    glow = glow.filter(ImageFilter.GaussianBlur(max(1.0, fs * 0.32)))
    layer = Image.alpha_composite(layer, glow)
    ImageDraw.Draw(layer).text((x, y), txt, font=f, fill=rgb + (max(10, st.ds_alpha),))
    return Image.alpha_composite(canvas.convert("RGBA"), layer).convert("RGB")


def torn_edge(canvas, st: Style):
    """撕纸边：多频噪声叠出连续毛边，再压一道纸芯阴影。

    PNG 输出真透明，JPEG 露出浅灰桌面色。
    """
    amt = st.torn
    if amt <= 0:
        return canvas
    W, H = canvas.size
    rnd = random.Random(st.torn_seed)
    a = max(2.0, min(W, H) * amt / 100.0 * 0.055)

    def profile(n, phase):
        # 三个频率叠加：大起伏 + 中频撕裂 + 细纤维
        base = [0.0] * n
        for k, freq in ((0.55, 2.1), (0.30, 7.3), (0.15, 19.7)):
            ph = phase + rnd.uniform(0, 6.28)
            for i in range(n):
                base[i] += k * math.sin(i / n * 6.283 * freq + ph)
        noise = [rnd.uniform(-1, 1) for _ in range(n)]
        for _ in range(2):                      # 轻微平滑，避免锯齿
            for i in range(1, n - 1):
                noise[i] = (noise[i - 1] + noise[i] * 2 + noise[i + 1]) / 4.0
        out = []
        for i in range(n):
            v = 0.55 + 0.45 * base[i] + 0.55 * noise[i]
            # 偶尔来一个深口子，像真撕开
            if rnd.random() < 0.012:
                v -= rnd.uniform(0.5, 1.4)
            out.append(max(0.05, min(1.6, v)) * a)
        return out

    mask = Image.new("L", (W, H), 255)
    d = ImageDraw.Draw(mask)
    left, right = profile(H, 0.0), profile(H, 2.0)
    top, bottom = profile(W, 4.0), profile(W, 6.0)
    for y in range(H):
        d.line([(0, y), (left[y], y)], fill=0)
        d.line([(W - right[y], y), (W, y)], fill=0)
    for x in range(W):
        d.line([(x, 0), (x, top[x])], fill=0)
        d.line([(x, H - bottom[x]), (x, H)], fill=0)
    soft = mask.filter(ImageFilter.GaussianBlur(max(0.6, a * 0.08)))

    if st.fmt == "png":
        out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        out.paste(canvas.convert("RGBA"), (0, 0), soft)
        return out

    # JPEG：撕口露出桌面；再沿毛边压一圈灰影，呈现纸张厚度
    paper = Image.new("RGB", (W, H), (232, 229, 223))
    paper.paste(canvas.convert("RGB"), (0, 0), soft)
    edge = ImageChops.subtract(mask, mask.filter(ImageFilter.MinFilter(7)))
    edge = edge.filter(ImageFilter.GaussianBlur(max(1.6, a * 0.45)))
    shade = Image.new("RGB", (W, H), (150, 146, 138))
    paper = Image.composite(shade, paper, edge.point(lambda v: int(v * 0.45)))
    return paper


def _special_film(im, name):
    """强风格化：交叉冲洗 / 漂白旁路。"""
    if name == "Cross Process":
        r, g, b = im.split()
        r = r.point([_cl(255 * ((i / 255.0) ** 0.80)) for i in range(256)])
        b = b.point([_cl(255 * ((i / 255.0) ** 1.32)) for i in range(256)])
        g = g.point([_cl(255 * ((i / 255.0) ** 1.06)) for i in range(256)])
        out = Image.merge("RGB", (r, g, b))
        out = ImageEnhance.Contrast(out).enhance(1.30)
        return ImageEnhance.Color(out).enhance(1.42)
    # Bleach Bypass：低饱和 + 高反差 + 高光微溢
    out = ImageEnhance.Color(im).enhance(0.40)
    out = ImageEnhance.Contrast(out).enhance(1.55)
    return out.point([_cl(i + 16 * (i / 255.0) ** 3) for i in range(256)] * 3)


def _film_once(im, p):
    rg, gg, bg, gamma, sat, con = p
    r, g, b = im.split()

    def ch(x, gain):
        lut = [_cl(255 * min(1.0, ((i / 255.0) ** gamma) * gain)) for i in range(256)]
        return x.point(lut)

    out = Image.merge("RGB", (ch(r, rg), ch(g, gg), ch(b, bg)))
    if sat != 1.0:
        out = ImageEnhance.Color(out).enhance(sat)
    if con != 1.0:
        out = ImageEnhance.Contrast(out).enhance(con)
    return out


def apply_film(im, st: Style):
    """film_strength 0~200：100 = 标准，>100 继续加压（叠两次曲线）。"""
    if st.film in XMP_FILMS:
        one = apply_xmp(im, st.film, 1.0)
        k = max(0, st.film_strength) / 100.0
        return Image.blend(im, one, min(1.0, k)) if k < 1 else one
    p = FILMS.get(st.film)
    k = max(0, st.film_strength) / 100.0
    if not p and not (st.film_fade or st.film_roll):
        return im
    if p and k > 0 and st.film in SPECIAL_FILMS:
        one = _special_film(im, st.film)
        im = Image.blend(im, one, min(1.0, k))
    elif p and k > 0:
        one = _film_once(im, p)
        if k <= 1.0:
            im = Image.blend(im, one, k)
        else:
            im = Image.blend(one, _film_once(one, p), min(1.0, k - 1.0))
    kk = min(1.0, k)
    if st.film_roll:                       # 高光柔和滚降
        r = st.film_roll / 100.0 * kk
        im = im.point([_cl(i - 26 * r * (i / 255.0) ** 4) for i in range(256)] * 3)
    if st.film_fade:                       # 黑位抬升（胶片褪色感）
        f = st.film_fade / 100.0 * kk
        im = im.point([_cl(v * (1 - 0.30 * f) + 255 * 0.20 * f) for v in range(256)] * 3)
    return im


def gradient_filter(im, st: Style):
    """渐变滤镜：线性/径向蒙版 + 提亮或压暗（Lightroom 渐变滤镜的简化版）。"""
    if st.grad_kind == "关闭" or st.grad_amt == 0:
        return im
    W, H = im.size
    sm = 200
    m = Image.new("L", (sm, sm), 0)
    px = m.load()
    if st.grad_kind == "线性":
        d = st.grad_dir
        for y in range(sm):
            for x in range(sm):
                t = {"上→下": y, "下→上": sm - 1 - y,
                     "左→右": x, "右→左": sm - 1 - x}.get(d, y) / (sm - 1.0)
                px[x, y] = _cl(255 * t)
    else:
        cx = st.grad_x / 100.0 * sm
        cy = st.grad_y / 100.0 * sm
        hard = max(0.08, 1 - st.grad_feather / 100.0)
        for y in range(sm):
            for x in range(sm):
                dd = (((x - cx) ** 2 + (y - cy) ** 2) ** 0.5) / (sm * 0.74)
                t = 1.0 - min(1.0, max(0.0, (dd - hard * 0.35) / max(0.06, hard)))
                px[x, y] = _cl(255 * t)
    m = m.resize((W, H), Image.BILINEAR)
    amt = st.grad_amt / 100.0
    adj = ImageEnhance.Brightness(im).enhance(1 + 0.95 * amt if amt > 0 else 1 + 0.55 * amt)
    return Image.composite(adj, im, m)


PAPER_FINISH = ("光面", "绒面", "金属", "哑光")


def push_pull(im, st: Style):
    """推冲(+)/拉冲(-)：每档 +0.13 反差、+5.5% 饱和、轻微暖移，黑位压实。"""
    k = float(st.push)
    if not k:
        return im
    im = ImageEnhance.Contrast(im).enhance(1 + 0.10 * k)
    im = ImageEnhance.Color(im).enhance(max(0.0, 1 + 0.055 * k))
    r, g, b = im.split()
    r = r.point([_cl(v * (1 + 0.012 * k)) for v in range(256)])
    b = b.point([_cl(v * (1 - 0.016 * k)) for v in range(256)])
    im = Image.merge("RGB", (r, g, b))
    lift = -3.0 * k
    return im.point([_cl(v + lift * (1 - v / 255.0)) for v in range(256)] * 3)


def print_stage(im, st: Style):
    """相纸冲印：相纸质感（Dmax/反差）+ 放大机品红/黄滤色片。"""
    fin = st.paper_finish
    if fin == "绒面":
        im = im.point([_cl(6 + v * 0.972) for v in range(256)] * 3)
    elif fin == "金属":
        im = ImageEnhance.Contrast(im).enhance(1.16)
        im = ImageEnhance.Color(im).enhance(1.10)
    elif fin == "哑光":
        im = im.point([_cl(12 + v * 0.945) for v in range(256)] * 3)

    m, y = st.cc_m / 100.0, st.cc_y / 100.0
    if m or y:
        r, g, b = im.split()
        r = r.point([_cl(v * (1 + 0.10 * m + 0.06 * y)) for v in range(256)])
        g = g.point([_cl(v * (1 - 0.16 * m + 0.02 * y)) for v in range(256)])
        b = b.point([_cl(v * max(0.0, 1 + 0.06 * m - 0.20 * y)) for v in range(256)])
        im = Image.merge("RGB", (r, g, b))
    return im


def add_grain(im, amt):
    """亮度耦合的单色颗粒：中间调最明显（less in deep shadow / highlight）。"""
    if amt <= 0:
        return im
    W, H = im.size
    n = Image.effect_noise((W, H), 32)
    noisy = ImageChops.add(im, Image.merge("RGB", (n, n, n)), 1.0, -128)
    w = im.convert("L").point(
        lambda v: int(max(0.0, 1 - abs(v - 128) / 150.0) * (amt / 100.0) * 210))
    return Image.composite(noisy, im, w)


@lru_cache(maxsize=32)
def _vig_mask(size, amt):
    sm = 256
    m = Image.new("L", (sm, sm), 0)
    px = m.load()
    c = sm / 2.0
    for y in range(sm):
        for x in range(sm):
            d = (((x - c) ** 2 + (y - c) ** 2) ** 0.5) / (c * 1.4142)
            v = max(0.0, (d - 0.32) / 0.68) ** 1.6
            px[x, y] = _cl(255 * v * amt)
    return m.resize(size, Image.BICUBIC)


def add_vignette(im, amt):
    if amt <= 0:
        return im
    mask = _vig_mask(im.size, amt / 100.0 * 0.88)
    return Image.composite(Image.new("RGB", im.size, (0, 0, 0)), im, mask)


def add_halation(im, st: Style):
    W, H = im.size
    if st.halo > 0:                        # 高光溢色（halation）
        amt = st.halo / 100.0
        l = im.convert("L")
        thr = max(60, min(250, st.halo_thr))
        mask = l.point(lambda v: 0 if v < thr else _cl(v / 255.0 * ((v - thr) / (255 - thr)) * 255))
        mask = mask.filter(ImageFilter.GaussianBlur(max(2, st.halo_radius * min(W, H))))
        mask = mask.point(lambda v: _cl(v * amt))
        im = Image.composite(Image.new("RGB", (W, H), st.halo_tint), im, mask)
    if st.glow > 0:                        # 柔光雾感
        soft = im.filter(ImageFilter.GaussianBlur(max(2, min(W, H) * 0.010)))
        im = Image.blend(im, soft, 0.42 * st.glow / 100.0)
    return im


def add_light_leak(im, st: Style):
    """胶片漏光：从一侧片边渗入的暖光，指数衰减 + 片轴反光条纹。"""
    amt = st.leak / 100.0
    if amt <= 0:
        return im
    rnd = random.Random(st.leak_seed)
    W, H = im.size
    sm = 160
    side = rnd.choice("lrtb")
    freq = rnd.uniform(1.1, 2.6)
    decay = rnd.uniform(2.0, 4.0)
    m = Image.new("L", (sm, sm), 0)
    px = m.load()
    for y in range(sm):
        for x in range(sm):
            if side == "l":
                dist, along = x / (sm - 1.0), y / (sm - 1.0)
            elif side == "r":
                dist, along = 1 - x / (sm - 1.0), y / (sm - 1.0)
            elif side == "t":
                dist, along = y / (sm - 1.0), x / (sm - 1.0)
            else:
                dist, along = 1 - y / (sm - 1.0), x / (sm - 1.0)
            band = 0.30 + 0.70 * abs(math.sin(along * math.pi * freq))
            px[x, y] = _cl(255 * math.exp(-dist * decay) * band)
    soft = m.resize((W, H), Image.BICUBIC)
    soft = soft.point(lambda v: _cl(v * amt * 0.92))
    hot = m.resize((W, H), Image.BICUBIC).point(lambda v: _cl(v * amt * 1.55))
    c = st.leak_tint.lstrip("#")
    warm = tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))
    lay1 = Image.composite(Image.new("RGB", (W, H), warm),
                           Image.new("RGB", (W, H), (0, 0, 0)), soft)
    lay2 = Image.composite(Image.new("RGB", (W, H), (255, 64, 26)),
                           Image.new("RGB", (W, H), (0, 0, 0)), hot)
    lit = ImageChops.screen(ImageChops.screen(im, lay1), lay2)
    return Image.blend(im, lit, min(1.0, amt * 0.88))


STRIP_TONES = {"黑": "#141414", "暗棕": "#1c1611", "米白": "#efe9dd"}

# 画幅名: (宽mm, 高mm, 是否有过片孔)
STRIP_FORMATS = {
    "135 全画幅": (36.0, 24.0, True),
    "135 半格": (18.0, 24.0, True),
    "XPan": (65.0, 24.0, True),
    "645": (56.0, 41.5, False),
    "6×6": (56.0, 56.0, False),
    "6×7": (70.0, 56.0, False),
    "6×9": (84.0, 56.0, False),
    "6×12": (112.0, 56.0, False),
    "6×17": (168.0, 56.0, False),
}


def apply_film_strip(canvas, st: Style, exif=None):
    """按画幅规格加片边：135 系带过片孔，120 系是背纸边与画幅框线。"""
    if not st.strip:
        return canvas
    tone = st.strip_tone or "#141414"
    dark = tone.lower() not in ("#efe9dd", "#f5f0e6")
    fw, fh, holes = STRIP_FORMATS.get(st.strip_fmt, STRIP_FORMATS["135 全画幅"])

    # 按画幅规格裁切铺满（同真实底片：画幅外的东西本来就不会被记录）
    W, H = canvas.size
    ratio = fw / fh
    if W / H > ratio:
        Wc, Hc = max(1, round(H * ratio)), H
    else:
        Wc, Hc = W, max(1, round(W / ratio))
    framed = ImageOps.fit(canvas, (Wc, Hc), Image.LANCZOS, centering=(0.5, 0.5))
    W, H = framed.size

    # 片边高度按短边百分比；135 有孔、120 无孔但边更窄
    bh = max(8, int(min(W, H) * max(2, st.strip_h) / 100 * (1.0 if holes else 0.80)))
    out = Image.new("RGB", (W, H + 2 * bh), tone)
    out.paste(framed, (0, bh))
    d = ImageDraw.Draw(out)
    hole = (232, 227, 216) if dark else (58, 54, 48)
    ink = "#e6c078" if dark else "#585047"

    bar_on = bool(st.bar and bh > 26)
    fm = st.strip_fmt.replace(" ", "")

    if holes:
        n = max(4, round(W / (bh * 1.55)))
        pw, ph = bh * 0.48, bh * 0.30
        for i in range(n):
            cx = (i + 0.5) * W / n
            for y0 in (bh * 0.10, bh + H + bh * 0.10):
                d.rounded_rectangle([cx - pw / 2, y0, cx + pw / 2, y0 + ph],
                                    radius=ph * 0.34, fill=hole)
    else:
        d.rectangle([1, bh, W - 2, bh + H - 1], outline=hole, width=max(1, int(bh * 0.05)))

    if not holes:
        f_tag = font(bh * 0.40, True)
        if bar_on:      # 参数条占了下片边，规格字样居中印在上片边
            d.text((W * 0.5, bh * 0.55), fm, font=f_tag, fill=ink, anchor="mm")
        else:
            d.text((W * 0.012, bh + H + bh * 0.52), fm, font=f_tag, fill=ink, anchor="lm")

    if st.strip_label or st.strip_no:
        f = font(bh * 0.26, False)
        if st.strip_label:
            d.text((W * 0.035, bh * 0.74), st.strip_label.upper(), font=f, fill=ink,
                   anchor="lm")
        if st.strip_no:
            sy = bh * 0.74 if bar_on else bh + H + bh * 0.72
            d.text((W * 0.978, sy), st.strip_no.upper(), font=f, fill=ink, anchor="rm")

    if bar_on:
        draw_bar(out, (W * 0.035, bh + H + bh * 0.04, W * 0.965, bh + H + bh * 0.96),
                 st, exif or {})
    return out


def recess_shadow(canvas, box, amt):
    """卡纸压边：照片外圈一道内凹阴影，像挖孔卡纸。"""
    if amt <= 0:
        return canvas
    x, y, w, h = [int(v) for v in box]
    pad = max(4, int(min(w, h) * 0.02))
    lay = Image.new("L", canvas.size, 0)
    d = ImageDraw.Draw(lay)
    d.rectangle([x - pad, y - pad, x + w + pad, y + h + pad], fill=int(amt * 2.4))
    d.rectangle([x, y, x + w, y + h], fill=0)
    lay = lay.filter(ImageFilter.GaussianBlur(pad * 0.7))
    return Image.composite(Image.new("RGB", canvas.size, (0, 0, 0)), canvas, lay)


_de_cache = {}


def _load_overlay(path, size):
    key = (path, size)
    if key not in _de_cache:
        with Image.open(path) as ov:
            img = ImageOps.fit(ImageOps.exif_transpose(ov).convert("RGB"), size,
                               Image.LANCZOS)
        if len(_de_cache) > 6:
            _de_cache.clear()
        _de_cache[key] = img
    return _de_cache[key]


def double_exposure(im, st: Style):
    """双重曝光：把一张叠加图与原片按混合模式叠在一起。"""
    if st.de_amt <= 0 or not st.de_image or not os.path.exists(st.de_image):
        return im
    try:
        ov = _load_overlay(st.de_image, im.size)
    except Exception:
        return im
    if st.de_mode == "正片叠底":
        mixed = ImageChops.multiply(im, ov)
    elif st.de_mode == "叠加":
        mixed = ImageChops.overlay(im, ov)
    elif st.de_mode == "强光":
        mixed = ImageChops.hard_light(im, ov)
    else:
        mixed = ImageChops.screen(im, ov)
    return Image.blend(im, mixed, st.de_amt / 100.0)


def process_look(im, st: Style):
    im = apply_grade(im, st)
    im = apply_curves(im, st)
    im = apply_film(im, st)
    im = push_pull(im, st)
    if st.film_grain:
        im = add_grain(im, st.film_grain * (1 + 0.28 * st.push))
    im = print_stage(im, st)
    if st.riso_on:
        im = riso_print(im, st.riso_cell, st.riso_angle, st.riso_ink1,
                        st.riso_ink2, st.riso_amt)
    if st.film_vig:
        im = add_vignette(im, st.film_vig)
    im = add_halation(im, st)
    im = add_light_leak(im, st)
    return double_exposure(im, st)


# ---------------- 水印 ----------------
def draw_watermark(canvas, st, d=None, avoid=0):
    if not st.wm_text.strip():
        return canvas
    W, H = canvas.size
    fs = max(10, min(W, H) * st.wm_size)
    f = font(fs, False)
    d = d or {}
    txt = (st.wm_text.replace("{date}", d.get("date", ""))
           .replace("{model}", d.get("model", ""))).strip()
    if not txt:
        return canvas
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(layer)
    tw = dr.textlength(txt, font=f)
    m = min(W, H) * 0.035
    pos = st.wm_pos
    x = {"l": m, "c": (W - tw) / 2, "r": W - tw - m}[pos[1]]
    y = {"t": m, "m": (H - fs) / 2, "b": H - fs - m}[pos[0]]
    if avoid and pos[0] == "b":      # 避开底部相机参数条
        y = max(m, y - avoid)
    if st.wm_auto:
        ink = auto_ink(_luma(canvas, (x, y, x + tw, y + fs * 1.2))).lstrip("#")
        rgb = tuple(int(ink[i:i + 2], 16) for i in (0, 2, 4))
    else:
        c = st.wm_color.lstrip("#")
        rgb = tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))
    shade = (0, 0, 0) if sum(rgb) > 380 else (255, 255, 255)
    dr.text((x + max(1, fs * 0.04), y + max(1, fs * 0.04)), txt, font=f,
            fill=shade + (min(110, st.wm_alpha),))
    dr.text((x, y), txt, font=f, fill=rgb + (st.wm_alpha,))
    return Image.alpha_composite(canvas.convert("RGBA"), layer)


# ---------------- 主流程 ----------------
def compose(src, st: Style, exif=None):
    d = exif or read_exif(src)
    im = ImageOps.exif_transpose(src)
    w, h = im.size
    p = st.pad * min(w, h)
    rows = [r for r in bar_lines(st, d) if r] if st.bar else []
    if st.polaroid:                      # 拍立得：底部留出大片相纸
        bar_h = 0
        W, H = w + 2 * p, h + p * 0.9 + p * 3.1
    else:
        bar_h = (0 if st.strip else
                 min(w, h) * (0.072 + 0.046 * max(0, len(rows) - 1)) if rows else 0)
        W, H = w + 2 * p, h + 2 * p + bar_h
    if st.ratio:
        if W / H > st.ratio:
            H = W / st.ratio
        else:
            W = H * st.ratio
    k = 1.0
    if st.max_side and max(W, H) > st.max_side:
        k = st.max_side / max(W, H)
    W, H = max(1, round(W * k)), max(1, round(H * k))
    cw, ch = max(1, round(w * k)), max(1, round(h * k))
    bh = round(bar_h * k)

    # Sample the frame color before grading so photo adjustments never tint the border.
    sample_color = edge_color(im) if st.mode == "sample" else None
    bg_src = im.resize((cw, ch), Image.LANCZOS) if k < 1 else im
    bg_src = process_look(bg_src.convert("RGB"), st)
    canvas = apply_paper(backdrop(bg_src, W, H, st, sample_color), st)

    if st.polaroid:
        ox, oy = (W - cw) // 2, max(0, round(p * 0.9 * k))
    else:
        area_h = H - bh
        ox, oy = (W - cw) // 2, max(0, (area_h - ch) // 2)

    # 阴影：画在背景上，再叠照片
    if st.shadow:
        md = Image.new("L", (W, H), 0)
        dr = ImageDraw.Draw(md)
        dx, dy = DIRS[st.sh_dir]
        off = st.sh_dist * min(cw, ch) * (0.7071 if (dx and dy) else 1.0)
        bx, by = ox + dx * off, oy + dy * off
        dr.rectangle([bx, by, bx + cw, by + ch], fill=st.sh_strength)
        md = md.filter(ImageFilter.GaussianBlur(max(1, st.sh_blur * min(cw, ch))))
        canvas = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), canvas, md)

    corner = None
    if st.radius > 0:
        r = int(round(min(cw, ch) * 0.5 * min(1.0, st.radius / 100.0)))
        if r > 0:
            corner = Image.new("L", (cw, ch), 0)
            ImageDraw.Draw(corner).rounded_rectangle([0, 0, cw - 1, ch - 1],
                                                     radius=r, fill=255)
    if bg_src.mode in ("RGBA", "LA", "P"):
        tmp = bg_src.convert("RGBA")
        canvas = canvas.convert("RGBA")
        canvas.paste(tmp, (ox, oy), corner if corner else tmp)
        canvas = canvas.convert("RGB")
    else:
        canvas.paste(bg_src.convert("RGB"), (ox, oy), corner)

    if st.recess:
        canvas = recess_shadow(canvas, (ox, oy, cw, ch), st.recess)

    # 细边线：照片与白边之间的一圈线
    if st.line > 0:
        lw = max(1, int(round(st.line * min(cw, ch))))
        ImageDraw.Draw(canvas).rectangle(
            [ox, oy, ox + cw - 1, oy + ch - 1], outline=st.line_color, width=lw)

    if st.bar and bh > 8 and rows:
        pad_k = round(p * k)
        top = H - bh - pad_k * 0.25
        bottom = H - pad_k * 0.25
        draw_bar(canvas, (ox + max(4, pad_k * 0.1), top, ox + cw, bottom), st, d)

    canvas = draw_watermark(canvas, st, d, avoid=(bh + round(p * k) * 0.8) if st.bar else 0)

    if st.polaroid and st.polaroid_title.strip():     # 拍立得底部手写标题
        bot = p * 3.1 * k
        fs = max(10, bot * 0.27)
        try:
            fnt = ImageFont.truetype("C:/Windows/Fonts/simsun.ttc", int(fs))
        except Exception:
            fnt = font(fs, False)
        dr = ImageDraw.Draw(canvas)
        txt = st.polaroid_title.strip()
        tw = dr.textlength(txt, font=fnt)
        dr.text(((W - tw) / 2, H - bot * 0.66), txt, font=fnt, fill="#3b3733")
    canvas = draw_datestamp(canvas, st)
    if canvas.mode != "RGB":
        canvas = canvas.convert("RGB")
    canvas = apply_film_strip(canvas, st, d)
    return torn_edge(canvas, st)


def _save(out, dst, st):
    if st.fmt == "png":
        out.save(dst, "PNG", optimize=True)
    else:
        out.save(dst, "JPEG", quality=95, subsampling=0, optimize=True, progressive=True)
    return dst


def out_path(base, outdir, ext, taken):
    name, i = base + ext, 1
    while name in taken or os.path.exists(os.path.join(outdir, name)):
        name = f"{base}_{i}{ext}"
        i += 1
    taken.add(name)
    return os.path.join(outdir, name)


def out_name(src, outdir, ext, taken):
    base = os.path.splitext(os.path.basename(src))[0] + "_bordered"
    return out_path(base, outdir, ext, taken)


def process_one(path, outdir, st: Style, taken):
    os.makedirs(outdir, exist_ok=True)
    with Image.open(path) as im:
        out = compose(im, st)
    ext = ".png" if st.fmt == "png" else ".jpg"
    return _save(out, out_name(path, outdir, ext, taken), st)


def collage(imgs, cols=0, gap=0.012, bg="#ffffff", cell=1000):
    """多张图拼成网格：每格 cover 裁切铺满，不拉伸变形。"""
    n = len(imgs)
    if n == 0:
        raise ValueError("no image")
    if n == 1:
        return imgs[0].convert("RGB")
    if cols <= 0:
        cols = n if n <= 3 else (2 if n == 4 else (3 if n <= 9 else 4))
    cols = max(1, min(cols, n))
    rows = math.ceil(n / cols)
    g = max(2, int(cell * gap))
    W = cols * cell + (cols - 1) * g
    H = rows * cell + (rows - 1) * g
    canvas = Image.new("RGB", (W, H), bg)
    for i, im in enumerate(imgs):
        r, c = divmod(i, cols)
        tile = ImageOps.fit(im.convert("RGB"), (cell, cell), method=Image.LANCZOS)
        canvas.paste(tile, (c * (cell + g), r * (cell + g)))
    return canvas


def fit_place(canvas, im, box, zoom=1.0, px=0.0, py=0.0):
    """把一个格子按 cover 放图，zoom 缩放、px/py (-1~1) 平移。"""
    x, y, w, h = [int(v) for v in box]
    if w <= 0 or h <= 0:
        return
    s = max(w / im.width, h / im.height) * max(0.2, zoom)
    nw, nh = max(1, int(im.width * s)), max(1, int(im.height * s))
    ox = x + (w - nw) // 2 + int(px * max(0, nw - w) / 2)
    oy = y + (h - nh) // 2 + int(py * max(0, nh - h) / 2)
    tile = Image.new("RGB", (w, h), "#ffffff")
    tile.paste(im.resize((nw, nh), Image.LANCZOS), (ox - x, oy - y))
    canvas.paste(tile, (x, y))


def twin_canvas(imgs, st: Style):
    """双图画布：上下两张，各自缩放与平移。"""
    ar = st.ratio or 1.5
    W = 1200
    H = max(1, int(W / ar))
    g = max(2, int(W * st.gap))
    top = int(H * max(0.2, min(0.8, st.twin_top)))
    canvas = Image.new("RGB", (W, H), st.color)
    boxes = [(0, 0, W, top - g // 2), (0, top + g // 2, W, H - (top + g // 2))]
    for i in range(2):
        if i < len(imgs):
            fit_place(canvas, imgs[i], boxes[i],
                      st.twin_zoom[i], st.twin_px[i], st.twin_py[i])
    return canvas


def collage_name(outdir, ext, taken):
    return out_path("拼图_" + datetime.now().strftime("%Y%m%d_%H%M%S"), outdir, ext, taken)


def collect(paths):
    found = []
    for path in paths:
        if os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                dirs[:] = [x for x in dirs if x != SKIP_DIR and not x.startswith(".")]
                for f in files:
                    if f.endswith("_bordered" + os.path.splitext(f)[1]):
                        continue
                    if os.path.splitext(f)[1].lower() in EXTS:
                        found.append(os.path.join(root, f))
        elif os.path.splitext(path)[1].lower() in EXTS:
            found.append(path)
    return sorted(set(found))

# ---------------- 扫描胶片条自动分割 ----------------

def _down(im, max_w=900):
    W, H = im.size
    sw = max(48, min(max_w, W))
    sh = max(32, min(max_w, round(H * sw / float(W))))
    g = im.convert("L").resize((sw, sh), Image.BILINEAR)
    return sw, sh, list(g.getdata())


def _row_stats(sw, sh, px):
    """每行亮像素占比（>55）与行标准差。"""
    rf, rm = [0.0] * sh, [0.0] * sh
    for y in range(sh):
        base = y * sw
        bright = 0
        s1 = s2 = 0
        for x in range(sw):
            v = px[base + x]
            if v > 55:
                bright += 1
            s1 += v
            s2 += v * v
        rf[y] = bright / sw
        m = s1 / sw
        rm[y] = max(0.0, s2 / sw - m * m) ** 0.5
    return rf, rm


def _col_stats(sw, px, y0, y1):
    n = max(1, y1 - y0)
    cm, cs = [0.0] * sw, [0.0] * sw
    for x in range(sw):
        s1 = s2 = 0
        for y in range(y0, y1):
            v = px[y * sw + x]
            s1 += v
            s2 += v * v
        m = s1 / n
        cm[x] = m
        cs[x] = max(0.0, s2 / n - m * m) ** 0.5
    return cm, cs


def _runs(mask):
    out, start = [], None
    for i, v in enumerate(mask):
        if v and start is None:
            start = i
        elif not v and start is not None:
            out.append((start, i))
            start = None
    if start is not None:
        out.append((start, len(mask)))
    return out


def strip_boxes(im, min_w=10, sens=50, pad=2.0, count=0):
    """检测扫描条上的单张画幅。

    两步：先找"整行都亮"的画幅带（片基是黑底 + 白齿孔，亮像素只占三四成，
    画幅内几乎整行都亮），再在这条带内按列标准差找画幅之间的间隙。
    min_w：最小画幅占条长百分比；sens 0~100 越大越容易切开；
    pad：上下左右内缩百分比。
    """
    W, H = im.size
    rot = H > W * 1.35              # 竖着扫的条先转横
    src = im.transpose(Image.ROTATE_90) if rot else im
    sw, sh, px = _down(src, 1200)
    rf, rm = _row_stats(sw, sh, px)

    # 1) 纵向画幅带
    y0, y1 = 0, sh
    for th in (0.82, 0.70, 0.55):
        runs = [r for r in _runs([v >= th for v in rf]) if r[1] - r[0] >= sh * 0.25]
        if runs:
            y0, y1 = max(runs, key=lambda r: r[1] - r[0])
            break
    else:
        rpeak = max(rm) or 1.0
        rows = [i for i, v in enumerate(rm) if v > max(3.5, 0.10 * rpeak)]
        if rows:
            y0, y1 = rows[0], rows[-1] + 1

    # 2) 横向切分
    cm, cs = _col_stats(sw, px, y0, y1)
    if count and count >= 2:
        # 指定张数：等距切，适合间隙看不见的扫描
        step = sw / float(count)
        spans = [(int(i * step), int((i + 1) * step)) for i in range(count)]
    else:
        # 自动：片基间隙在画幅带里是"纯色或很暗"的窄列
        med_s = sorted(cs)[len(cs) // 2]
        med_m = sorted(cm)[len(cm) // 2]
        st_th = max(1.5, med_s * (0.05 + (sens / 100.0) * 0.12))
        mk_th = max(28.0, med_m * (0.45 - (sens / 100.0) * 0.15))
        gapmask = [(cs[x] < st_th) or (cm[x] < mk_th) for x in range(sw)]

        hole = max(1, int(sw * 0.004))
        i = 0
        while i < sw:
            if not gapmask[i]:
                j = i
                while j < sw and not gapmask[j]:
                    j += 1
                if 0 < i and j < sw and (j - i) <= hole:
                    for x in range(i, j):
                        gapmask[x] = True
                i = j
            else:
                i += 1

        gaps = [g for g in _runs(gapmask) if g[1] - g[0] <= sw * 0.12]
        spans, prev = [], 0
        for a, b in gaps:
            if a > prev:
                spans.append((prev, a))
            prev = max(prev, b)
        if prev < sw:
            spans.append((prev, sw))
        min_px0 = max(6, int(sw * max(1, min_w) / 100.0))
        spans = [(a, b) for a, b in spans if b - a >= min_px0]
        # 相邻两幅粘在一起时（间隙被污渍/笔迹盖住），按中位宽拆开
        if len(spans) >= 2:
            ws = sorted(b - a for a, b in spans)
            med_w = ws[len(ws) // 2]
            fixed = []
            for a, b in spans:
                k = int(round((b - a) / float(med_w)))
                if k >= 2 and (b - a) > med_w * 1.5:
                    stp = (b - a) / float(k)
                    for i in range(k):
                        fixed.append((int(a + i * stp), int(a + (i + 1) * stp)))
                else:
                    fixed.append((a, b))
            spans = fixed
    if not spans:
        return [], rot

    m = max(0.0, pad) / 100.0 * sh
    y0i, y1i = int(y0 + m), int(y1 - m)
    if y1i - y0i < 4:
        y0i, y1i = y0, y1
    kx, ky = src.width / float(sw), src.height / float(sh)
    out = [(int(a * kx), int(y0i * ky), int(b * kx), int(y1i * ky)) for a, b in spans]
    return out, rot


def split_strip(im, min_w=10, sens=50, pad=2.0, count=0):
    """按检测结果切成单张，自动还原方向。count>1 时等距等分。"""
    boxes, rot = strip_boxes(im, min_w, sens, pad, count)
    base = im.transpose(Image.ROTATE_90) if rot else im
    out = []
    for b in boxes:
        piece = base.crop(b)
        if rot:
            piece = piece.transpose(Image.ROTATE_270)
        out.append(piece)
    return out


def draw_strip_boxes(im, boxes, rot, max_w=780):
    """预览用：在条上画出检测框。"""
    base = im.transpose(Image.ROTATE_90) if rot else im
    prev = base.copy()
    prev.thumbnail((max_w, max_w), Image.LANCZOS)
    k = prev.width / float(base.width)
    d = ImageDraw.Draw(prev)
    for i, (x0, y0, x1, y1) in enumerate(boxes, 1):
        d.rectangle([x0 * k, y0 * k, x1 * k, y1 * k], outline=(255, 92, 60), width=3)
        d.text((x0 * k + 6, y0 * k + 4), str(i), fill=(255, 92, 60))
    return prev


# ---------------- XMP（Lightroom 预设） ----------------
XMP_FILMS = {}          # 名称 -> {"r": [(x,y)...], "g":..., "b":..., "m":..., "sat": float, "gray": bool}


def _curve_lut(points):
    """把 (x,y) 折线采样成 256 项查找表。"""
    pts = sorted(points) or [(0, 0), (255, 255)]
    lut = [0] * 256
    for i in range(256):
        if i <= pts[0][0]:
            lut[i] = pts[0][1]
            continue
        if i >= pts[-1][0]:
            lut[i] = pts[-1][1]
            continue
        for k in range(len(pts) - 1):
            x0, y0 = pts[k]
            x1, y1 = pts[k + 1]
            if x0 <= i <= x1 and x1 > x0:
                lut[i] = int(round(y0 + (y1 - y0) * (i - x0) / float(x1 - x0)))
                break
    return [max(0, min(255, v)) for v in lut]


def parse_xmp(path):
    """读取 Lightroom / Camera Raw 的 .xmp 预设（曲线 + 饱和度 + 黑白）。"""
    import re
    txt = open(path, "r", encoding="utf-8", errors="ignore").read()
    name = None
    m = re.search(r'crs:Name="([^"]+)"', txt)
    if m:
        name = m.group(1)
    if not name:
        m = re.search(r'<rdf:li[^>]*xml:lang="x-default"[^>]*>([^<]+)</rdf:li>', txt)
        name = m.group(1) if m else os.path.splitext(os.path.basename(path))[0]
    curves = {}
    for key, tag in (("m", "ToneCurvePV2012"), ("r", "ToneCurvePV2012Red"),
                     ("g", "ToneCurvePV2012Green"), ("b", "ToneCurvePV2012Blue")):
        m = re.search(r"<crs:%s>\s*<rdf:Seq>(.*?)</rdf:Seq>" % tag, txt, re.S)
        if not m:
            continue
        pts = [(int(x), int(y)) for x, y in
               re.findall(r"<rdf:li>\s*(\d+)\s*,\s*(\d+)\s*</rdf:li>", m.group(1))]
        if len(pts) >= 2:
            curves[key] = pts
    sat = 0.0
    m = re.search(r'crs:Saturation="([+-]?[0-9.]+)"', txt)
    if m:
        sat = float(m.group(1)) / 100.0
    gray = 'ConvertToGrayscale="True"' in txt
    if not curves and abs(sat) < 0.01 and not gray:
        return None
    return {"name": name.strip(), "curves": curves, "sat": sat, "gray": gray}


def register_xmp(preset):
    """把解析结果登记为可用预设，返回名称。"""
    luts = {k: _curve_lut(v) for k, v in preset["curves"].items()}
    XMP_FILMS[preset["name"]] = {"lut": luts, "sat": preset["sat"], "gray": preset["gray"]}
    return preset["name"]


def apply_xmp(im, name, strength=1.0):
    pr = XMP_FILMS.get(name)
    if not pr:
        return im
    out = im.convert("RGB")
    luts = pr["lut"]
    if pr["gray"]:
        out = ImageOps.grayscale(out).convert("RGB")
    if "m" in luts:
        out = out.point(luts["m"] * 3)
    for key, ch in (("r", 0), ("g", 1), ("b", 2)):
        if key in luts:
            bands = list(out.split())
            bands[ch] = bands[ch].point(luts[key])
            out = Image.merge("RGB", bands)
    if abs(pr["sat"]) > 0.005:
        out = ImageEnhance.Color(out).enhance(max(0.0, 1 + pr["sat"]))
    if strength < 1.0:
        out = Image.blend(im.convert("RGB"), out, max(0.0, strength))
    return out


# ---------------- 网点印刷（Riso 双色） ----------------

def riso_print(im, cell=8, angle=45, ink1="#22201e", ink2="#ff5a4a", amount=100):
    """两套网点各按不同角度压印：ink1 走暗部，ink2 走亮部，中间叠色。"""
    amt = max(0, min(100, amount)) / 100.0
    if amt <= 0:
        return im
    W, H = im.size
    cell = max(3, int(cell))
    scale = 2 if max(W, H) < 1400 else 1        # 小图放大画，边缘更顺
    cw, ch = int(W * scale), int(H * scale)
    src = im.convert("RGB").resize((cw, ch), Image.LANCZOS)
    g = src.convert("L")

    def dots(ink, angle_deg, mode):
        layer = Image.new("RGB", (cw, ch), (255, 255, 255))
        dr = ImageDraw.Draw(layer)
        a = math.radians(angle_deg)
        ca, sa = math.cos(a), math.sin(a)
        step = cell * scale
        rmax = step * 0.58
        span = int(math.hypot(cw, ch) / step) + 2
        for i in range(-span, span):
            for j in range(-span, span):
                x = i * step * ca - j * step * sa + cw / 2
                y = i * step * sa + j * step * ca + ch / 2
                if not (-step < x < cw + step and -step < y < ch + step):
                    continue
                v = g.getpixel((min(cw - 1, max(0, int(x))),
                                min(ch - 1, max(0, int(y))))) / 255.0
                if mode == "dark":
                    r = rmax * (1 - v) ** 0.85
                else:
                    r = rmax * max(0.0, (v - 0.72)) / 0.28 * 0.55
                if r < 0.4:
                    continue
                dr.ellipse([x - r, y - r, x + r, y + r], fill=ink)
        return layer

    l1 = dots(ink1, angle, "dark")
    l2 = dots(ink2, angle + 30, "light")
    out = ImageChops.multiply(l1, l2)          # 两色叠印
    if scale > 1:
        out = out.resize((W, H), Image.LANCZOS)
    return Image.blend(im.convert("RGB"), out, amt)


def _row_bands(sw, sh, px):
    """按行标准差找"有内容的横带"（多条胶片叠扫时用）。"""
    rm = [0.0] * sh
    for y in range(sh):
        base = y * sw
        s1 = s2 = 0
        for x in range(sw):
            v = px[base + x]
            s1 += v
            s2 += v * v
        m = s1 / sw
        rm[y] = max(0.0, s2 / sw - m * m) ** 0.5
    peak = max(rm) or 1.0
    mask = [v > max(4.0, 0.16 * peak) for v in rm]
    return [(a, b) for a, b in _runs(mask) if b - a >= sh * 0.08]


def split_sheet(im, min_w=8, sens=50, pad=2.0, count=0):
    """支持一次扫多条（上下叠放）：先按行切成条，再逐条按画幅切。"""
    W, H = im.size
    sw, sh, px = _down(im, 900)
    bands = _row_bands(sw, sh, px)
    if len(bands) <= 1:
        return split_strip(im, min_w, sens, pad, count)
    ky = H / float(sh)
    out = []
    for y0, y1 in bands:
        top, bot = int(y0 * ky), int(y1 * ky)
        if bot - top < 24:
            continue
        out.extend(split_strip(im.crop((0, top, W, bot)), min_w, sens, pad, count))
    return out if out else split_strip(im, min_w, sens, pad, count)


# ---------------- 曲线 ----------------

def curve_lut(points):
    """控制点 -> 256 项查找表（端点外取端值，中间线性插值）。"""
    if not points or len(points) < 2:
        return None
    pts = sorted((float(x), float(y)) for x, y in points)
    lut = []
    for i in range(256):
        if i <= pts[0][0]:
            lut.append(int(round(pts[0][1])))
            continue
        if i >= pts[-1][0]:
            lut.append(int(round(pts[-1][1])))
            continue
        for k in range(len(pts) - 1):
            x0, y0 = pts[k]
            x1, y1 = pts[k + 1]
            if x0 <= i <= x1 and x1 > x0:
                lut.append(int(round(y0 + (y1 - y0) * (i - x0) / (x1 - x0))))
                break
    return [max(0, min(255, v)) for v in lut]


def apply_curves(im, st: Style):
    lm = curve_lut(getattr(st, "curve_m", None))
    if lm:
        im = im.point(lm * 3)
    for key, ch in (("curve_r", 0), ("curve_g", 1), ("curve_b", 2)):
        lc = curve_lut(getattr(st, key, None))
        if lc:
            bands = list(im.split())
            bands[ch] = bands[ch].point(lc)
            im = Image.merge("RGB", bands)
    return im


# ---------------- 自动调色 ----------------

def auto_params(im):
    """按图像统计给出曝光/白平衡/反差/高光阴影，返回 grade 字典。"""
    small = im.convert("RGB")
    small.thumbnail((420, 420), Image.LANCZOS)
    px = list(small.getdata())
    n = float(len(px))
    if not n:
        return {}
    lum = [0.299 * r + 0.587 * g + 0.114 * b for r, g, b in px]
    order = sorted(lum)
    p50 = order[int(n * 0.50)] / 255.0
    p05 = order[int(n * 0.05)] / 255.0
    p95 = order[min(len(order) - 1, int(n * 0.95))] / 255.0
    if p50 <= 0.01:
        return {}

    # 曝光：把中位亮度推到 0.46（≈18% 灰在 sRGB 的位置）
    ev = math.log(max(0.02, 0.46) / max(0.02, p50), 2)
    ev = max(-1.1, min(1.1, ev))

    # 白平衡：取较亮的那部分像素求通道均值（避开暗部色偏）
    thr = order[int(n * 0.70)]
    acc = [0.0, 0.0, 0.0]
    cnt = 0
    for r, g, b in px:
        if 0.299 * r + 0.587 * g + 0.114 * b >= thr:
            acc[0] += r
            acc[1] += g
            acc[2] += b
            cnt += 1
    if cnt:
        rm, gm, bm = [a / cnt for a in acc]
        gray = (rm + gm + bm) / 3.0 or 1.0
        # temp 滑块正数=偏暖：画面偏蓝时 rm<bm → 需要加暖
        temp = (bm - rm) / gray * 1.6
        tint = (gm - (rm + bm) / 2.0) / gray * 1.6
        temp = max(-0.15, min(0.15, temp))
        tint = max(-0.12, min(0.12, tint))
    else:
        temp = tint = 0.0

    # 反差：动态范围窄就补一点，宽就收一点
    span = max(0.05, p95 - p05)
    con = (0.72 - span) * 90
    con = max(-18, min(28, con))

    hi = -18 if p95 > 0.96 else 0
    sh = 16 if p05 < 0.05 else 0

    return {
        "exposure": int(round(ev / 2.0 * 100)),
        "contrast": int(round(con)),
        "highlights": hi,
        "shadows": sh,
        "whites": 0,
        "blacks": 0,
        "temp": int(round(max(-100, min(100, temp / 0.28 * 100)))),
        "tint": int(round(max(-100, min(100, tint / 0.14 * 100)))),
        "saturation": 0,
        "vibrance": 0,
    }
