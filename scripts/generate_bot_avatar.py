"""Generate bot profile photos for @MafGameUzBot — pure Pillow, no AI.

Outputs (upload via @BotFather):
  scripts/output/bot_avatar.png        — 1024×1024 square profile photo
  scripts/output/bot_description.png   — 1280×720 landscape description picture

Run:
  python scripts/generate_bot_avatar.py
"""

from __future__ import annotations

import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

# Windows console UTF-8 fix
for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

OUT_DIR = Path(__file__).resolve().parents[1] / "scripts" / "output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# --- noir palette ---
BG_INNER = (28, 14, 18)       # near the centre — warm dark crimson
BG_OUTER = (4, 3, 5)          # at the edges — near black
CREAM = (240, 230, 208)
WHITE = (255, 255, 255)
BLOOD = (175, 30, 40)
BLOOD_DEEP = (96, 12, 18)
GOLD = (200, 168, 92)
RIBBON_BLACK = (12, 8, 10)

# --- night-scene palette ---
SKY_TOP = (6, 8, 22)
SKY_BOTTOM = (32, 18, 32)
CITY = (3, 2, 5)
MOON = (236, 232, 215)
MOON_GLOW = (110, 90, 60)
STAR = (240, 235, 220)

WIN_FONTS = Path("C:/Windows/Fonts")
SERIF_BOLD = [WIN_FONTS / "georgiab.ttf", WIN_FONTS / "timesbd.ttf"]
SANS_BOLD = [WIN_FONTS / "arialbd.ttf", WIN_FONTS / "segoeuib.ttf"]
SANS = [WIN_FONTS / "arial.ttf", WIN_FONTS / "segoeui.ttf"]


def font(candidates: list[Path], size: int) -> ImageFont.FreeTypeFont:
    for p in candidates:
        if p.exists():
            return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def radial_gradient(size: tuple[int, int], inner: tuple[int, int, int],
                    outer: tuple[int, int, int], falloff: float = 1.4) -> Image.Image:
    """Soft radial gradient via concentric ellipses (fast and smooth at 96 steps)."""
    w, h = size
    img = Image.new("RGB", (w, h), outer)
    draw = ImageDraw.Draw(img)
    cx, cy = w // 2, h // 2
    max_r = int(math.hypot(cx, cy)) + 2
    steps = 96
    for i in range(steps, 0, -1):
        frac = i / steps
        t = frac ** falloff
        r = int(max_r * frac)
        col = (
            int(inner[0] * (1 - t) + outer[0] * t),
            int(inner[1] * (1 - t) + outer[1] * t),
            int(inner[2] * (1 - t) + outer[2] * t),
        )
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
    return img


def vertical_gradient(size: tuple[int, int], top: tuple[int, int, int],
                      bottom: tuple[int, int, int]) -> Image.Image:
    w, h = size
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(h - 1, 1)
        col = (
            int(top[0] * (1 - t) + bottom[0] * t),
            int(top[1] * (1 - t) + bottom[1] * t),
            int(top[2] * (1 - t) + bottom[2] * t),
        )
        draw.line([(0, y), (w, y)], fill=col)
    return img


def fedora_layer(size: tuple[int, int], color: tuple[int, int, int]) -> Image.Image:
    """Render a clean fedora silhouette at supersampled resolution then downscale."""
    SS = 3
    w, h = size
    W, H = w * SS, h * SS
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = W / 2

    # Brim — wide flat ellipse spanning the bottom half
    brim_h = int(H * 0.16)
    brim_top = int(H * 0.60)
    brim_left = int(W * 0.02)
    brim_right = int(W * 0.98)
    d.ellipse([brim_left, brim_top, brim_right, brim_top + brim_h * 2], fill=(*color, 255))

    # Crown — rounded rectangle
    crown_w = int(W * 0.46)
    crown_h = int(H * 0.58)
    crown_top = int(H * 0.08)
    crown_left = int(cx - crown_w / 2)
    radius = int(W * 0.08)
    d.rounded_rectangle(
        [crown_left, crown_top, crown_left + crown_w, crown_top + crown_h],
        radius=radius,
        fill=(*color, 255),
    )

    # Centre pinch — slight dark indent on top of crown (classic fedora crease)
    darker = (max(color[0] - 60, 0), max(color[1] - 60, 0), max(color[2] - 60, 0), 255)
    pinch_w = int(crown_w * 0.30)
    pinch_h = int(crown_h * 0.22)
    pinch_x = int(cx - pinch_w / 2)
    pinch_y = crown_top + int(crown_h * 0.03)
    d.rounded_rectangle(
        [pinch_x, pinch_y, pinch_x + pinch_w, pinch_y + pinch_h],
        radius=int(pinch_w * 0.40),
        fill=darker,
    )

    # Ribbon — dark band around the crown base
    ribbon_h = int(crown_h * 0.16)
    ribbon_top = crown_top + crown_h - ribbon_h
    d.rectangle(
        [crown_left, ribbon_top, crown_left + crown_w, ribbon_top + ribbon_h],
        fill=(*RIBBON_BLACK, 255),
    )

    # Small gold buckle on the ribbon
    buckle_w = int(crown_w * 0.08)
    bx = int(cx - buckle_w / 2)
    d.rectangle(
        [bx, ribbon_top + int(ribbon_h * 0.18), bx + buckle_w, ribbon_top + int(ribbon_h * 0.82)],
        fill=(*GOLD, 255),
    )

    return img.resize((w, h), Image.LANCZOS)


def text_with_shadow(base: Image.Image, xy: tuple[int, int], text: str,
                     fnt: ImageFont.FreeTypeFont, fill: tuple[int, int, int],
                     shadow_offset: tuple[int, int] = (0, 4),
                     shadow_color: tuple[int, int, int] = BLOOD_DEEP,
                     shadow_blur: int = 8, anchor: str = "mm") -> None:
    """Paint text with a soft-blurred shadow underneath."""
    if shadow_blur > 0:
        shadow = Image.new("RGBA", base.size, (0, 0, 0, 0))
        ImageDraw.Draw(shadow).text(
            (xy[0] + shadow_offset[0], xy[1] + shadow_offset[1]),
            text, font=fnt, fill=(*shadow_color, 220), anchor=anchor,
        )
        shadow = shadow.filter(ImageFilter.GaussianBlur(shadow_blur))
        base.alpha_composite(shadow)
    ImageDraw.Draw(base).text(xy, text, font=fnt, fill=(*fill, 255), anchor=anchor)


def build_avatar() -> Image.Image:
    """1024×1024 — noir gradient + fedora + MAFIA wordmark + @MafGameUzBot tag."""
    W = H = 1024
    bg = radial_gradient((W, H), BG_INNER, BG_OUTER, falloff=1.5)

    # Faint noir film-grain via random speckle (kept subtle)
    grain = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grain)
    rng = random.Random(42)
    for _ in range(2200):
        x, y = rng.randint(0, W - 1), rng.randint(0, H - 1)
        a = rng.randint(8, 22)
        gd.point((x, y), fill=(255, 240, 220, a))
    grain = grain.filter(ImageFilter.GaussianBlur(0.6))

    canvas = bg.convert("RGBA")
    canvas.alpha_composite(grain)

    # Fedora — centred upper half
    hat_w, hat_h = 720, 520
    hat = fedora_layer((hat_w, hat_h), CREAM)
    canvas.alpha_composite(hat, (int((W - hat_w) / 2), int(H * 0.10)))

    # Wordmark — bold serif "MAFIA"
    fnt_mafia = font(SERIF_BOLD, 168)
    text_with_shadow(
        canvas, (W // 2, int(H * 0.78)), "MAFIA", fnt_mafia,
        fill=CREAM, shadow_offset=(0, 6), shadow_color=BLOOD, shadow_blur=14,
    )

    # Tag — small uppercase "TELEGRAM GURUH O'YINI"
    fnt_tag = font(SANS_BOLD, 38)
    text_with_shadow(
        canvas, (W // 2, int(H * 0.90)), "TELEGRAM GURUH O'YINI", fnt_tag,
        fill=GOLD, shadow_offset=(0, 2), shadow_color=(0, 0, 0), shadow_blur=4,
    )

    # Thin gold border ring for polish
    border = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(border)
    inset = 14
    bd.rounded_rectangle(
        [inset, inset, W - inset, H - inset], radius=46, outline=(*GOLD, 110), width=3,
    )
    canvas.alpha_composite(border)

    return canvas.convert("RGB")


def night_skyline(width: int, height: int) -> Image.Image:
    """Procedural skyline silhouette occupying the bottom 35% of the canvas."""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    rng = random.Random(7)
    horizon = int(height * 0.62)
    x = 0
    # Distant back layer — taller, narrower buildings, faded
    while x < width:
        bw = rng.randint(30, 70)
        bh = rng.randint(int(height * 0.10), int(height * 0.32))
        top = horizon - bh
        d.rectangle([x, top, x + bw, height], fill=(10, 9, 16, 200))
        # window dots
        for wy in range(top + 8, height - 6, 14):
            for wx in range(x + 6, x + bw - 4, 10):
                if rng.random() < 0.18:
                    d.rectangle([wx, wy, wx + 2, wy + 4], fill=(218, 196, 130, 160))
        x += bw - rng.randint(0, 6)
    # Foreground layer — chunkier silhouettes overlay (pure black)
    x = -20
    while x < width:
        bw = rng.randint(70, 150)
        bh = rng.randint(int(height * 0.14), int(height * 0.34))
        top = horizon + 10 - bh
        d.rectangle([x, top, x + bw, height], fill=(*CITY, 255))
        # rooftop fixture
        if rng.random() < 0.5:
            fw = rng.randint(12, 28)
            d.rectangle([x + bw // 2 - fw // 2, top - 14, x + bw // 2 + fw // 2, top], fill=(*CITY, 255))
        # rare lit window
        for wy in range(top + 14, height - 14, 22):
            for wx in range(x + 10, x + bw - 8, 18):
                if rng.random() < 0.10:
                    d.rectangle([wx, wy, wx + 3, wy + 6], fill=(230, 210, 140, 220))
        x += bw - rng.randint(8, 16)
    return img


def build_description() -> Image.Image:
    """1280×720 — night sky + skyline + moon + giant MAFIA wordmark."""
    W, H = 1280, 720
    bg = vertical_gradient((W, H), SKY_TOP, SKY_BOTTOM).convert("RGBA")

    # Stars
    star_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(star_layer)
    rng = random.Random(11)
    for _ in range(280):
        x = rng.randint(0, W - 1)
        y = rng.randint(0, int(H * 0.55))
        a = rng.randint(60, 200)
        size = 1 if rng.random() < 0.85 else 2
        sd.rectangle([x, y, x + size, y + size], fill=(*STAR, a))
    bg.alpha_composite(star_layer)

    # Moon with halo (top-right)
    moon = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    md = ImageDraw.Draw(moon)
    mx, my, mr = W - 220, 160, 70
    # halo
    for i, alpha in [(60, 22), (40, 40), (22, 70)]:
        md.ellipse([mx - mr - i, my - mr - i, mx + mr + i, my + mr + i], fill=(*MOON_GLOW, alpha))
    moon = moon.filter(ImageFilter.GaussianBlur(6))
    bg.alpha_composite(moon)
    ImageDraw.Draw(bg).ellipse([mx - mr, my - mr, mx + mr, my + mr], fill=(*MOON, 255))

    # Skyline
    skyline = night_skyline(W, H)
    bg.alpha_composite(skyline)

    # Title — huge MAFIA wordmark, centred
    fnt_mafia = font(SERIF_BOLD, 200)
    text_with_shadow(
        bg, (W // 2, int(H * 0.36)), "MAFIA", fnt_mafia,
        fill=CREAM, shadow_offset=(0, 8), shadow_color=BLOOD, shadow_blur=22,
    )
    # Subtitle
    fnt_sub = font(SANS_BOLD, 40)
    text_with_shadow(
        bg, (W // 2, int(H * 0.55)), "Telegram guruh o'yini", fnt_sub,
        fill=GOLD, shadow_offset=(0, 3), shadow_color=(0, 0, 0), shadow_blur=6,
    )
    # Bot handle bottom-centre
    fnt_handle = font(SANS_BOLD, 30)
    text_with_shadow(
        bg, (W // 2, H - 32), "@MafGameUzBot", fnt_handle,
        fill=CREAM, shadow_offset=(0, 2), shadow_color=(0, 0, 0), shadow_blur=4,
    )

    return bg.convert("RGB")


def main() -> None:
    avatar = build_avatar()
    avatar_path = OUT_DIR / "bot_avatar.png"
    avatar.save(avatar_path, "PNG", optimize=True)
    print(f"✅ {avatar_path}  ({avatar.size[0]}×{avatar.size[1]})")

    desc = build_description()
    desc_path = OUT_DIR / "bot_description.png"
    desc.save(desc_path, "PNG", optimize=True)
    print(f"✅ {desc_path}  ({desc.size[0]}×{desc.size[1]})")

    print()
    print("Upload via @BotFather:")
    print("  /mybots → @MafGameUzBot → Edit Bot → Edit Botpic              → bot_avatar.png")
    print("  /mybots → @MafGameUzBot → Edit Bot → Edit Description Picture → bot_description.png")


if __name__ == "__main__":
    main()
