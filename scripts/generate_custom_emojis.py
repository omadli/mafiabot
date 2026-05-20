"""Generate animated custom-emoji WebMs for the Mafia bot pack.

Each clip is 100×100, VP9 with alpha (yuva420p), loopable, ≤256 KB
(Telegram custom-emoji limits).

Outputs to scripts/output/emoji/<name>.webm

Run:
  python scripts/generate_custom_emojis.py
  python scripts/generate_custom_emojis.py --only card,moon,skull
"""

from __future__ import annotations

import argparse
import functools
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import httpx
from PIL import Image, ImageDraw, ImageFilter, ImageFont

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "scripts" / "output" / "emoji"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Final resolution that Telegram requires.
W = H = 100
# Render at 3× then Lanczos-downscale for crisp anti-aliasing.
SS = 3
SW, SH = W * SS, H * SS

FPS = 30
DURATION_S = 1.5
FRAMES = int(FPS * DURATION_S)
SIZE_LIMIT_KB = 256

# --- palette -------------------------------------------------------------
CREAM = (240, 230, 208)
WHITE = (255, 255, 255)
BLOOD = (200, 30, 40)
BLOOD_DEEP = (130, 14, 22)
GOLD = (224, 184, 78)
GOLD_HOT = (255, 220, 130)
GOLD_DARK = (140, 100, 30)
NAVY = (52, 78, 162)
NAVY_DEEP = (28, 42, 96)
CYAN = (130, 200, 255)
SKY_DEEP = (12, 16, 50)
BONE = (236, 232, 220)
SHADOW = (12, 8, 10)
SILVER = (210, 215, 225)
STEEL = (140, 150, 165)
RIBBON_BLACK = (12, 8, 10)
SPARKLE = (255, 240, 160)

WIN_FONTS = Path("C:/Windows/Fonts")
SERIF_BOLD = [WIN_FONTS / "georgiab.ttf", WIN_FONTS / "timesbd.ttf"]


def font(candidates: list[Path], size: int) -> ImageFont.FreeTypeFont:
    for p in candidates:
        if p.exists():
            return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


# --- helpers -------------------------------------------------------------

def new_canvas() -> Image.Image:
    return Image.new("RGBA", (SW, SH), (0, 0, 0, 0))


def finalize(canvas: Image.Image) -> Image.Image:
    return canvas.resize((W, H), Image.LANCZOS)


def glow(layer: Image.Image, color: tuple[int, int, int], radius: int,
         alpha: int = 200) -> Image.Image:
    """Return a blurred coloured silhouette of `layer` for soft-glow underlay."""
    mask = layer.split()[3]
    coloured = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    coloured.paste((*color, alpha), mask=mask)
    return coloured.filter(ImageFilter.GaussianBlur(radius))


def composite_glow(canvas: Image.Image, fg: Image.Image,
                   color: tuple[int, int, int], radius: int,
                   intensity: float) -> None:
    """Lay `fg` on `canvas` with a blurred coloured glow behind it."""
    alpha = max(0, min(255, int(255 * intensity)))
    if alpha > 0:
        canvas.alpha_composite(glow(fg, color, radius, alpha))
    canvas.alpha_composite(fg)


# ========================================================================
# Twemoji base — fetch authentic Unicode-style emoji PNGs for use as the
# recognisable foundation, then layer animation effects on top.
# ========================================================================

EMOJI_CACHE = ROOT / "scripts" / "cache" / "twemoji"
EMOJI_CACHE.mkdir(parents=True, exist_ok=True)
TWEMOJI_CDN = "https://cdn.jsdelivr.net/gh/jdecked/twemoji@latest/assets/72x72"


def _codepoint_variants(emoji: str) -> list[str]:
    """Twemoji filename conventions: ZWJ sequences with gender signs keep
    the FE0F variation selector, simple emoji drop it — and there's no single
    rule. Try the most likely variants in order."""
    cps = [f"{ord(c):x}" for c in emoji]
    no_vs = [c for c in cps if c != "fe0f"]
    seen: list[str] = []
    for v in ["-".join(no_vs), "-".join(cps), "-".join(no_vs + ["fe0f"])]:
        if v and v not in seen:
            seen.append(v)
    return seen


@functools.lru_cache(maxsize=None)
def fetch_twemoji(emoji: str) -> Image.Image:
    """Download (with on-disk cache) and return RGBA copy of Twemoji PNG."""
    variants = _codepoint_variants(emoji)
    # Cache hit on any variant?
    for cp_str in variants:
        cache_path = EMOJI_CACHE / f"{cp_str}.png"
        if cache_path.exists():
            return Image.open(cache_path).convert("RGBA")
    # Try each variant URL until one works
    with httpx.Client(timeout=30) as client:
        for cp_str in variants:
            url = f"{TWEMOJI_CDN}/{cp_str}.png"
            r = client.get(url)
            if r.status_code == 200:
                cache_path = EMOJI_CACHE / f"{cp_str}.png"
                cache_path.write_bytes(r.content)
                return Image.open(cache_path).convert("RGBA")
    raise FileNotFoundError(
        f"Twemoji not found for {emoji!r}; tried codepoints {variants}"
    )


def load_emoji(emoji: str, size: int) -> Image.Image:
    """Twemoji resized to a square (size, size) with Lanczos antialiasing."""
    return fetch_twemoji(emoji).resize((size, size), Image.LANCZOS)


# ========================================================================
# Animation primitives — stronger, more visible motion than the old set.
# ========================================================================

def composite_at(canvas: Image.Image, fg: Image.Image,
                 x_offset: int = 0, y_offset: int = 0) -> None:
    """Paste fg centred on canvas, optionally shifted by (x_offset, y_offset)."""
    px = (canvas.width - fg.width) // 2 + x_offset
    py = (canvas.height - fg.height) // 2 + y_offset
    canvas.alpha_composite(fg, (px, py))


def soft_glow(canvas: Image.Image, fg: Image.Image,
              x_offset: int, y_offset: int,
              color: tuple[int, int, int], radius: int,
              intensity: float) -> None:
    """Drop a blurred coloured silhouette of fg behind it as a glow halo."""
    alpha = max(0, min(255, int(255 * intensity)))
    if alpha <= 0:
        return
    mask = fg.split()[3]
    coloured = Image.new("RGBA", fg.size, (0, 0, 0, 0))
    coloured.paste((*color, alpha), mask=mask)
    blurred = coloured.filter(ImageFilter.GaussianBlur(radius))
    px = (canvas.width - fg.width) // 2 + x_offset
    py = (canvas.height - fg.height) // 2 + y_offset
    canvas.alpha_composite(blurred, (px, py))


def pulse_scale(base: Image.Image, t: float, amplitude: float = 0.10) -> Image.Image:
    """Sinusoidal scale of base by 1 ± amplitude over the loop."""
    scale = 1 + amplitude * math.sin(t * 2 * math.pi)
    return base.resize(
        (max(2, int(base.width * scale)), max(2, int(base.height * scale))),
        Image.LANCZOS,
    )


def tilt_oscillate(base: Image.Image, t: float, max_deg: float = 8.0,
                   cycles: float = 1.0) -> Image.Image:
    """Sway base left-right within ±max_deg over `cycles` cycles per loop."""
    deg = max_deg * math.sin(t * 2 * math.pi * cycles)
    return base.rotate(deg, resample=Image.BICUBIC, expand=False)


def rotate_full(base: Image.Image, t: float) -> Image.Image:
    """Continuous full rotation of base over the loop."""
    return base.rotate(t * 360.0, resample=Image.BICUBIC, expand=False)


def bounce_y(t: float, height: int, cycles: float = 1.0) -> int:
    """Returns vertical offset for a bouncing motion. Bounces `cycles` times.

    Positive `height` produces upward (negative-y) bounces, peak at sin=1.
    """
    return -int(abs(math.sin(t * 2 * math.pi * cycles)) * height)


def shake_x(t: float, amplitude: int, cycles: float = 4.0) -> int:
    """Fast left-right shake offset."""
    return int(math.sin(t * 2 * math.pi * cycles) * amplitude)


def orbit_position(t: float, cx: int, cy: int, radius_x: int, radius_y: int,
                   phase: float = 0.0) -> tuple[int, int]:
    """A point orbiting (cx, cy) with an elliptical orbit."""
    a = t * 2 * math.pi + phase
    return (cx + int(math.cos(a) * radius_x), cy + int(math.sin(a) * radius_y))


def draw_sparkle(canvas: Image.Image, x: int, y: int, size: int,
                 color: tuple[int, int, int] = SPARKLE,
                 alpha: int = 255) -> None:
    """4-point sparkle/star shape centred at (x, y)."""
    d = ImageDraw.Draw(canvas)
    d.rectangle([x - size, y - 1, x + size, y + 1], fill=(*color, alpha))
    d.rectangle([x - 1, y - size, x + 1, y + size], fill=(*color, alpha))
    # Diagonals for fuller sparkle look
    diag = size // 2
    d.line([(x - diag, y - diag), (x + diag, y + diag)],
           fill=(*color, alpha), width=1)
    d.line([(x - diag, y + diag), (x + diag, y - diag)],
           fill=(*color, alpha), width=1)


def draw_floating_particle(canvas: Image.Image, x: int, y: int, radius: int,
                            color: tuple[int, int, int], alpha: int) -> None:
    """Soft circular particle (with subtle blur applied by caller)."""
    d = ImageDraw.Draw(canvas)
    d.ellipse([x - radius, y - radius, x + radius, y + radius],
              fill=(*color, alpha))


# --- 1. spinning M card --------------------------------------------------

def render_card(i: int) -> Image.Image:
    """Pulsing Mafia card with an M and gentle 3D wobble."""
    t = i / FRAMES
    pulse = 1 + 0.04 * math.sin(t * 2 * math.pi)
    wobble = 0.06 * math.sin(t * 2 * math.pi)  # squish x ±6 %
    canvas = new_canvas()

    card_w = int(54 * SS * pulse * (1 - wobble))
    card_h = int(80 * SS * pulse)
    cx, cy = SW // 2, SH // 2
    x0, y0 = cx - card_w // 2, cy - card_h // 2
    x1, y1 = cx + card_w // 2, cy + card_h // 2

    # Card body — blood border + cream face
    d = ImageDraw.Draw(canvas)
    r = int(9 * SS * pulse)
    d.rounded_rectangle([x0, y0, x1, y1], radius=r, fill=(*BLOOD, 255))
    inset = int(3 * SS)
    d.rounded_rectangle([x0 + inset, y0 + inset, x1 - inset, y1 - inset],
                        radius=max(2, r - inset), fill=(*CREAM, 255))

    # "M" centred
    if card_w > 16 * SS:
        m_size = int(42 * SS * pulse)
        fnt = font(SERIF_BOLD, m_size)
        d.text((cx, cy + int(2 * SS)), "M", font=fnt, fill=(*BLOOD_DEEP, 255), anchor="mm")
        # Tiny corner spades
        small = font(SERIF_BOLD, int(11 * SS))
        d.text((x0 + int(7 * SS), y0 + int(8 * SS)), "M", font=small,
               fill=(*BLOOD_DEEP, 255))
        d.text((x1 - int(7 * SS), y1 - int(8 * SS)), "M", font=small,
               fill=(*BLOOD_DEEP, 255), anchor="rd")

    # Soft drop shadow underneath card
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle([x0 + int(2 * SS), y0 + int(5 * SS),
                          x1 + int(2 * SS), y1 + int(5 * SS)],
                         radius=r, fill=(0, 0, 0, 120))
    shadow = shadow.filter(ImageFilter.GaussianBlur(int(6 * SS / 2)))
    out = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    out.alpha_composite(shadow)
    out.alpha_composite(canvas)
    return finalize(out)


# --- 2. moon (Twemoji 🌙 + twinkling stars + blue glow pulse) ------------

_STAR_POSITIONS = [
    (16, 16, 0.0), (82, 22, 0.30), (88, 64, 0.60),
    (12, 56, 0.15), (62, 8, 0.45),  (40, 88, 0.75),
    (90, 86, 0.50), (8, 84, 0.85),
]  # (x, y, phase_offset) in 100×100 space


def render_moon(i: int) -> Image.Image:
    """🌙 Twemoji crescent — cool blue glow pulse + twinkling sparkles."""
    t = i / FRAMES
    canvas = new_canvas()
    pulse = 0.5 + 0.5 * math.sin(t * 2 * math.pi)
    base = load_emoji("🌙", int(72 * SS))
    # Subtle scale breath
    base = pulse_scale(base, t, amplitude=0.06)
    # Cool blue glow halo behind the moon
    soft_glow(canvas, base, 0, 0,
              color=(130, 175, 240), radius=int(SW * 0.10),
              intensity=0.30 + 0.55 * pulse)
    composite_at(canvas, base)
    # Twinkling sparkles around
    for sx, sy, phase in _STAR_POSITIONS:
        local = (t + phase) % 1.0
        twk = max(0.0, 1 - abs(local - 0.5) * 2)
        if twk < 0.05:
            continue
        size = max(3, int(SW * 0.030 * twk * 1.8))
        a = int(180 * twk + 70)
        draw_sparkle(canvas, sx * SS, sy * SS, size,
                     color=(245, 240, 220), alpha=a)
    return finalize(canvas)


# --- 3. sun (Twemoji ☀️ — slowly rotating + warm glow + scale breath) ---

def render_sun(i: int) -> Image.Image:
    """☀️ Twemoji sun — slow continuous rotation + bright warm glow pulse."""
    t = i / FRAMES
    canvas = new_canvas()
    pulse = 0.5 + 0.5 * math.sin(t * 2 * math.pi)
    base = load_emoji("☀️", int(80 * SS))
    # Rotation is the dominant motion — full turn each loop
    rotated = rotate_full(base, t)
    # Gentle scale breath layered on top
    rotated = pulse_scale(rotated, t, amplitude=0.05)
    # Warm orange glow halo
    soft_glow(canvas, rotated, 0, 0,
              color=(255, 200, 90), radius=int(SW * 0.13),
              intensity=0.45 + 0.45 * pulse)
    composite_at(canvas, rotated)
    return finalize(canvas)


# --- 4. flickering skull -------------------------------------------------

def render_skull(i: int) -> Image.Image:
    t = i / FRAMES
    canvas = new_canvas()
    d = ImageDraw.Draw(canvas)
    cx, cy = SW // 2, int(SH * 0.46)

    # Cranium
    head_r = int(28 * SS)
    d.ellipse([cx - head_r, cy - head_r, cx + head_r, cy + head_r], fill=(*BONE, 255))

    # Jaw (smaller rounded rect below)
    jaw_w, jaw_h = int(34 * SS), int(20 * SS)
    jaw_top = cy + head_r - int(6 * SS)
    d.rounded_rectangle([cx - jaw_w // 2, jaw_top,
                         cx + jaw_w // 2, jaw_top + jaw_h],
                        radius=int(7 * SS), fill=(*BONE, 255))

    # Teeth — vertical dark lines on jaw
    teeth_y0 = jaw_top + int(7 * SS)
    teeth_y1 = jaw_top + jaw_h - int(3 * SS)
    for k in range(-2, 3):
        tx = cx + k * int(6 * SS)
        d.rectangle([tx - 1, teeth_y0, tx + 1, teeth_y1], fill=(*SHADOW, 160))

    # Eye sockets — dark with pulsing red ember
    ember = 0.5 + 0.5 * math.sin(t * 2 * math.pi)
    for ex in (-int(10 * SS), int(10 * SS)):
        eye_x = cx + ex
        eye_y = cy - int(2 * SS)
        eye_r = int(7 * SS)
        d.ellipse([eye_x - eye_r, eye_y - eye_r, eye_x + eye_r, eye_y + eye_r],
                  fill=(*SHADOW, 255))
        # Ember glow
        glow_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        ImageDraw.Draw(glow_layer).ellipse(
            [eye_x - eye_r + 1, eye_y - eye_r + 1,
             eye_x + eye_r - 1, eye_y + eye_r - 1],
            fill=(*BLOOD, int(180 * ember + 40)),
        )
        canvas.alpha_composite(glow_layer.filter(ImageFilter.GaussianBlur(2 * SS)))

    # Nose triangle
    nose_top = (cx, cy + int(2 * SS))
    nose_l = (cx - int(3 * SS), cy + int(10 * SS))
    nose_r = (cx + int(3 * SS), cy + int(10 * SS))
    d.polygon([nose_top, nose_l, nose_r], fill=(*SHADOW, 200))

    return finalize(canvas)


# --- 5. pulsing shield ---------------------------------------------------

def render_shield(i: int) -> Image.Image:
    t = i / FRAMES
    pulse = 0.5 + 0.5 * math.sin(t * 2 * math.pi)  # 0..1
    canvas = new_canvas()

    cx, cy = SW // 2, int(SH * 0.52)
    # Shield shape — pointed bottom, rounded top
    top = int(SH * 0.18)
    side = int(28 * SS)
    bottom = int(SH * 0.86)
    points = [
        (cx - side, top + int(6 * SS)),
        (cx - side, top),
        (cx, top - int(2 * SS)),
        (cx + side, top),
        (cx + side, top + int(6 * SS)),
        (cx + int(side * 0.85), int(SH * 0.60)),
        (cx, bottom),
        (cx - int(side * 0.85), int(SH * 0.60)),
    ]
    shield_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(shield_layer).polygon(points, fill=(*NAVY, 255), outline=(*GOLD, 255))
    # Inner highlight band
    inner_pts = [
        (cx - int(side * 0.6), top + int(10 * SS)),
        (cx + int(side * 0.6), top + int(10 * SS)),
        (cx + int(side * 0.5), int(SH * 0.58)),
        (cx, int(SH * 0.78)),
        (cx - int(side * 0.5), int(SH * 0.58)),
    ]
    ImageDraw.Draw(shield_layer).polygon(inner_pts, fill=(*NAVY_DEEP, 255))
    # Cross emblem
    arm = int(8 * SS)
    th = int(4 * SS)
    d2 = ImageDraw.Draw(shield_layer)
    d2.rectangle([cx - arm, cy - th, cx + arm, cy + th], fill=(*GOLD, 255))
    d2.rectangle([cx - th, cy - arm, cx + th, cy + arm], fill=(*GOLD, 255))

    # Cyan pulse halo behind shield
    halo_radius = int((5 + 6 * pulse) * SS)
    halo_alpha = int(80 + 140 * pulse)
    halo = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    h_layer = shield_layer.copy()
    # Grow alpha via dilation: blur + threshold not easy; just expand polygon
    expanded_pts = []
    for px, py in points:
        dx, dy = px - cx, py - cy
        dist = math.hypot(dx, dy)
        if dist == 0:
            expanded_pts.append((px, py))
        else:
            f = (dist + halo_radius) / dist
            expanded_pts.append((cx + dx * f, cy + dy * f))
    ImageDraw.Draw(halo).polygon(expanded_pts, fill=(*CYAN, halo_alpha))
    halo = halo.filter(ImageFilter.GaussianBlur(4 * SS))
    canvas.alpha_composite(halo)
    canvas.alpha_composite(shield_layer)
    return finalize(canvas)


# --- 6. glowing trophy ---------------------------------------------------

def render_trophy(i: int) -> Image.Image:
    t = i / FRAMES
    pulse = 0.5 + 0.5 * math.sin(t * 2 * math.pi)
    canvas = new_canvas()
    cx = SW // 2

    fg = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(fg)

    # Cup body — trapezoid + curved bottom
    cup_top = int(22 * SS)
    cup_bottom_y = int(58 * SS)
    cup_top_w = int(36 * SS)
    cup_bot_w = int(24 * SS)
    cup_pts = [
        (cx - cup_top_w // 2, cup_top),
        (cx + cup_top_w // 2, cup_top),
        (cx + cup_bot_w // 2, cup_bottom_y),
        (cx - cup_bot_w // 2, cup_bottom_y),
    ]
    d.polygon(cup_pts, fill=(*GOLD, 255))
    # Rim highlight
    d.rectangle([cx - cup_top_w // 2, cup_top, cx + cup_top_w // 2, cup_top + int(4 * SS)],
                fill=(*GOLD_HOT, 255))
    # Handles — half-ellipses sticking out either side of the cup
    handle_thickness = int(4 * SS)
    handle_h = int(20 * SS)
    handle_w = int(12 * SS)
    handle_top = cup_top + int(2 * SS)
    # Left handle: arc opens to the right (cup-facing side), 90°..270°
    left_outer = cx - cup_top_w // 2 - int(2 * SS)
    d.arc([left_outer - handle_w, handle_top,
           left_outer, handle_top + handle_h],
          start=90, end=270, fill=(*GOLD, 255), width=handle_thickness)
    # Right handle: arc opens to the left, 270°..90° (i.e. -90°..90°)
    right_outer = cx + cup_top_w // 2 + int(2 * SS)
    d.arc([right_outer, handle_top,
           right_outer + handle_w, handle_top + handle_h],
          start=270, end=90, fill=(*GOLD, 255), width=handle_thickness)
    # Neck
    d.rectangle([cx - int(8 * SS), cup_bottom_y, cx + int(8 * SS), cup_bottom_y + int(6 * SS)],
                fill=(*GOLD_DARK, 255))
    # Base
    base_y = cup_bottom_y + int(8 * SS)
    d.rounded_rectangle([cx - int(18 * SS), base_y, cx + int(18 * SS), base_y + int(10 * SS)],
                        radius=int(3 * SS), fill=(*GOLD_DARK, 255))
    # Star on cup
    star_size = int(8 * SS)
    sx, sy = cx, int(40 * SS)
    pts = []
    for k in range(10):
        angle = -math.pi / 2 + k * math.pi / 5
        r = star_size if k % 2 == 0 else star_size // 2
        pts.append((sx + r * math.cos(angle), sy + r * math.sin(angle)))
    d.polygon(pts, fill=(*GOLD_HOT, 255))

    # Pulsing gold halo
    canvas.alpha_composite(glow(fg, GOLD_HOT, int(6 * SS), int(80 + 150 * pulse)))
    canvas.alpha_composite(fg)
    return finalize(canvas)


# --- 7. knife with dripping blood ---------------------------------------

def render_knife(i: int) -> Image.Image:
    t = i / FRAMES
    canvas = new_canvas()
    d = ImageDraw.Draw(canvas)
    cx = SW // 2

    # Blade — pointing down
    blade_top = int(10 * SS)
    blade_tip = int(60 * SS)
    blade_w = int(8 * SS)
    blade_pts = [
        (cx - blade_w, blade_top),
        (cx + blade_w, blade_top),
        (cx + blade_w, blade_tip - int(6 * SS)),
        (cx, blade_tip),
        (cx - blade_w, blade_tip - int(6 * SS)),
    ]
    d.polygon(blade_pts, fill=(*SILVER, 255))
    # Edge highlight
    d.polygon([(cx, blade_top), (cx + 1, blade_top), (cx + 1, blade_tip - int(5 * SS)),
               (cx, blade_tip)], fill=(*WHITE, 200))
    # Steel shadow on left
    d.polygon([(cx - blade_w, blade_top), (cx - blade_w + int(3 * SS), blade_top),
               (cx - blade_w + int(3 * SS), blade_tip - int(6 * SS)),
               (cx, blade_tip), (cx - blade_w, blade_tip - int(6 * SS))],
              fill=(*STEEL, 180))

    # Crossguard
    guard_y = blade_top - int(2 * SS)
    d.rounded_rectangle([cx - int(14 * SS), guard_y, cx + int(14 * SS), guard_y + int(4 * SS)],
                        radius=int(2 * SS), fill=(*GOLD_DARK, 255))

    # Handle
    handle_top = guard_y + int(4 * SS)
    handle_bot = handle_top - int(28 * SS)  # extends upward
    # Wait — knife points down so handle goes upward (negative direction in PIL)
    # Let me redo: handle above guard
    handle_y0 = guard_y - int(28 * SS)
    handle_y1 = guard_y
    d.rounded_rectangle([cx - int(5 * SS), handle_y0, cx + int(5 * SS), handle_y1],
                        radius=int(2 * SS), fill=(*SHADOW, 255))
    # Wood grain accent
    for off in range(-int(20 * SS), 0, int(8 * SS)):
        d.line([(cx - int(5 * SS), handle_y1 + off), (cx + int(5 * SS), handle_y1 + off)],
               fill=(40, 28, 22, 200), width=1)
    # Pommel
    d.ellipse([cx - int(6 * SS), handle_y0 - int(4 * SS),
               cx + int(6 * SS), handle_y0 + int(4 * SS)], fill=(*GOLD_DARK, 255))

    # Blood smear on lower blade
    blood_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    bd = ImageDraw.Draw(blood_layer)
    bd.polygon([
        (cx - int(6 * SS), blade_tip - int(20 * SS)),
        (cx + int(6 * SS), blade_tip - int(18 * SS)),
        (cx + blade_w, blade_tip - int(6 * SS)),
        (cx, blade_tip),
        (cx - blade_w, blade_tip - int(6 * SS)),
    ], fill=(*BLOOD, 255))
    canvas.alpha_composite(blood_layer)

    # Falling drop cycle
    drop_t = (t * 1.0) % 1.0
    drop_y = blade_tip + int(drop_t * 35 * SS)
    drop_alpha = int(255 * (1 - drop_t * 0.6))
    drop_r = int(3 * SS * (1 + drop_t * 0.4))
    if drop_y < SH:
        drop_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        # Tear-drop shape: circle + triangle on top
        dd = ImageDraw.Draw(drop_layer)
        dd.ellipse([cx - drop_r, drop_y - drop_r, cx + drop_r, drop_y + drop_r],
                   fill=(*BLOOD, drop_alpha))
        dd.polygon([(cx - drop_r + 1, drop_y),
                    (cx + drop_r - 1, drop_y),
                    (cx, drop_y - drop_r * 2)],
                   fill=(*BLOOD, drop_alpha))
        canvas.alpha_composite(drop_layer)

    return finalize(canvas)


# =========================================================================
# ROLE EMOJIS (21 of them — civilians, mafia, singletons)
# =========================================================================
#
# Shared design language:
#   • icon-centred at canvas centre, 60-80% of frame
#   • micro-animation per emoji (pulse / twinkle / sway / flash)
#   • single-loop, 1.5 s @ 30 fps — last frame ≈ first frame
#
# All renderers work in supersampled coordinates (SW × SH = 300 × 300),
# then `finalize()` downscales to 100 × 100.

# --- extra palette ------------------------------------------------------

SKIN = (236, 200, 168)
SKIN_DARK = (180, 130, 90)
HAIR_DARK = (44, 28, 28)
EYE_DARK = (28, 22, 28)
RED_LIPS = (210, 30, 60)
HEART_RED = (220, 50, 70)
GREEN_CLOVER = (60, 160, 80)
GREEN_DARK = (28, 90, 40)
WIZARD_BLUE = (60, 70, 150)
WIZARD_PURPLE = (80, 50, 130)
FLAME_ORANGE = (255, 140, 30)
FLAME_YELLOW = (255, 220, 80)
FLAME_RED = (210, 40, 30)
SMOKE = (220, 220, 220)
WOOD = (110, 70, 40)
WOOD_LIGHT = (170, 120, 70)
PAPER = (242, 235, 220)
WOLF_GREY = (95, 95, 105)
WOLF_DARK = (40, 40, 50)
MASK_WHITE = (240, 234, 218)


# --- small reusable primitives ------------------------------------------

def _draw_face(canvas: Image.Image, cx: int, cy: int, r: int,
               skin: tuple[int, int, int] = SKIN,
               mouth: str = "smile",
               eye_state: str = "open") -> None:
    """Round face with eyes + mouth. mouth in {'smile','flat','frown'}."""
    d = ImageDraw.Draw(canvas)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(*skin, 255))
    # Eyes
    eye_dx = r // 3
    eye_y = cy - r // 5
    eye_r = max(1, r // 10)
    if eye_state == "open":
        for sign in (-1, 1):
            ex = cx + sign * eye_dx
            d.ellipse([ex - eye_r, eye_y - eye_r, ex + eye_r, eye_y + eye_r],
                      fill=(*EYE_DARK, 255))
    elif eye_state == "x":
        for sign in (-1, 1):
            ex = cx + sign * eye_dx
            w = max(2, r // 8)
            d.line([(ex - eye_r, eye_y - eye_r), (ex + eye_r, eye_y + eye_r)],
                   fill=(*EYE_DARK, 255), width=w)
            d.line([(ex - eye_r, eye_y + eye_r), (ex + eye_r, eye_y - eye_r)],
                   fill=(*EYE_DARK, 255), width=w)
    elif eye_state == "closed":
        for sign in (-1, 1):
            ex = cx + sign * eye_dx
            d.line([(ex - eye_r, eye_y), (ex + eye_r, eye_y)],
                   fill=(*EYE_DARK, 255), width=max(2, r // 12))
    # Mouth
    mouth_y = cy + r // 3
    mouth_w = r // 2
    if mouth == "smile":
        d.arc([cx - mouth_w, mouth_y - mouth_w // 2,
               cx + mouth_w, mouth_y + mouth_w // 2],
              start=20, end=160, fill=(*EYE_DARK, 255), width=max(2, r // 12))
    elif mouth == "flat":
        d.line([(cx - mouth_w, mouth_y), (cx + mouth_w, mouth_y)],
               fill=(*EYE_DARK, 255), width=max(2, r // 12))
    elif mouth == "frown":
        d.arc([cx - mouth_w, mouth_y,
               cx + mouth_w, mouth_y + mouth_w],
              start=200, end=340, fill=(*EYE_DARK, 255), width=max(2, r // 12))


def _draw_fedora_mini(canvas: Image.Image, cx: int, cy: int, w: int,
                      color: tuple[int, int, int],
                      band_color: tuple[int, int, int] = RIBBON_BLACK) -> None:
    """Compact fedora — fits in bounding box around (cx, cy) with given width."""
    h = int(w * 0.7)
    d = ImageDraw.Draw(canvas)
    # Brim
    brim_h = max(4, h // 6)
    brim_y = cy + h // 6
    d.ellipse([cx - w // 2, brim_y, cx + w // 2, brim_y + brim_h * 2],
              fill=(*color, 255))
    # Crown
    crown_w = int(w * 0.55)
    crown_h = int(h * 0.7)
    crown_x = cx - crown_w // 2
    crown_y = cy - h // 2
    d.rounded_rectangle([crown_x, crown_y, crown_x + crown_w, crown_y + crown_h],
                        radius=max(3, crown_w // 8), fill=(*color, 255))
    # Band
    band_h = max(2, crown_h // 6)
    band_y = crown_y + crown_h - band_h - max(1, crown_h // 16)
    d.rectangle([crown_x, band_y, crown_x + crown_w, band_y + band_h],
                fill=(*band_color, 255))


def _layered_glow(canvas: Image.Image, fg: Image.Image,
                  color: tuple[int, int, int], radius: int, intensity: float) -> None:
    alpha = max(0, min(255, int(255 * intensity)))
    if alpha > 0:
        canvas.alpha_composite(glow(fg, color, radius, alpha))


# =========================================================================
# CIVILIANS (10)
# =========================================================================

def render_citizen(i: int) -> Image.Image:
    """👨🏼 — gentle breath pulse + soft cream halo."""
    t = i / FRAMES
    canvas = new_canvas()
    base = load_emoji("👨🏼", int(82 * SS))
    sized = pulse_scale(base, t, amplitude=0.06)
    soft_glow(canvas, sized, 0, 0, color=CREAM, radius=int(SW * 0.08),
              intensity=0.25 + 0.20 * (0.5 + 0.5 * math.sin(t * 2 * math.pi)))
    composite_at(canvas, sized)
    return finalize(canvas)


def render_detective(i: int) -> Image.Image:
    """🕵🏻‍♂ detective + 🔍 magnifying glass orbiting around him."""
    t = i / FRAMES
    canvas = new_canvas()
    base = load_emoji("🕵🏻‍♂", int(78 * SS))
    # Detective sways gently
    swayed = tilt_oscillate(base, t, max_deg=4)
    # Cool cyan investigative glow
    soft_glow(canvas, swayed, 0, 0,
              color=(140, 200, 240), radius=int(SW * 0.09),
              intensity=0.25 + 0.25 * (0.5 + 0.5 * math.sin(t * 2 * math.pi)))
    composite_at(canvas, swayed)
    # Magnifying glass orbits — front side at the bottom of orbit, back at top
    glass = load_emoji("🔍", int(34 * SS))
    cx, cy = SW // 2, SH // 2
    orbit_t = t  # one full orbit per loop
    ox, oy = orbit_position(orbit_t, cx, cy,
                             radius_x=int(SW * 0.36),
                             radius_y=int(SH * 0.18))
    # Behind / in front of detective depending on orbit phase
    in_front = oy >= cy - int(SH * 0.05)
    if in_front:
        canvas.alpha_composite(glass, (ox - glass.width // 2, oy - glass.height // 2))
    else:
        # Behind — draw faded version
        faded = glass.copy()
        a = faded.split()[3].point(lambda v: int(v * 0.55))
        faded.putalpha(a)
        canvas.alpha_composite(faded, (ox - faded.width // 2, oy - faded.height // 2))
    return finalize(canvas)


def render_sergeant(i: int) -> Image.Image:
    """👮🏻‍♂ police officer + gold star ⭐ orbiting + authority halo."""
    t = i / FRAMES
    canvas = new_canvas()
    base = load_emoji("👮🏻‍♂", int(78 * SS))
    sized = pulse_scale(base, t, amplitude=0.05)
    # Authoritative blue glow
    soft_glow(canvas, sized, 0, 0,
              color=(90, 130, 220), radius=int(SW * 0.09),
              intensity=0.30 + 0.25 * (0.5 + 0.5 * math.sin(t * 2 * math.pi)))
    composite_at(canvas, sized)
    # Two stars orbiting at offset phase, in elliptical orbit
    star = load_emoji("⭐", int(28 * SS))
    cx, cy = SW // 2, SH // 2
    for phase in (0.0, math.pi):
        ox, oy = orbit_position(t, cx, cy,
                                 radius_x=int(SW * 0.34),
                                 radius_y=int(SH * 0.16),
                                 phase=phase)
        in_front = oy >= cy - int(SH * 0.05)
        a_scale = 1.0 if in_front else 0.45
        s = star
        if not in_front:
            s = star.copy()
            a = s.split()[3].point(lambda v: int(v * a_scale))
            s.putalpha(a)
        canvas.alpha_composite(s, (ox - s.width // 2, oy - s.height // 2))
    return finalize(canvas)


def render_mayor(i: int) -> Image.Image:
    """Tri-coloured ribbon + gold medal that sways gently."""
    t = i / FRAMES
    canvas = new_canvas()
    sway = math.sin(t * 2 * math.pi) * 12
    cx = SW // 2 + int(sway * 0.4)
    d = ImageDraw.Draw(canvas)
    # Ribbon — two triangles meeting at a point (top), trapezoid at bottom
    rib_top_y = int(SH * 0.10)
    rib_apex_y = int(SH * 0.45)
    rib_left_x = SW // 2 - int(SW * 0.18)
    rib_right_x = SW // 2 + int(SW * 0.18)
    apex_x = SW // 2 + int(sway)
    # Left half — blue
    d.polygon([(rib_left_x, rib_top_y), (apex_x - 10, rib_apex_y),
               (apex_x + 10, rib_apex_y), (rib_left_x + 30, rib_top_y)],
              fill=(40, 80, 180, 255))
    # Right half — red
    d.polygon([(rib_right_x, rib_top_y), (apex_x + 10, rib_apex_y),
               (apex_x - 10, rib_apex_y), (rib_right_x - 30, rib_top_y)],
              fill=(*BLOOD, 255))
    # Centre — white stripe
    d.polygon([(apex_x - 12, rib_apex_y - 6), (apex_x + 12, rib_apex_y - 6),
               (apex_x + 8, rib_apex_y), (apex_x - 8, rib_apex_y)],
              fill=(*CREAM, 255))
    # Medal — gold disc with star
    medal_y = rib_apex_y + int(SW * 0.18)
    medal_r = int(SW * 0.18)
    d.ellipse([apex_x - medal_r, medal_y - medal_r,
               apex_x + medal_r, medal_y + medal_r],
              fill=(*GOLD, 255), outline=(*GOLD_DARK, 255), width=3)
    d.ellipse([apex_x - medal_r + 8, medal_y - medal_r + 8,
               apex_x + medal_r - 8, medal_y + medal_r - 8],
              fill=(*GOLD_HOT, 255))
    # Star on medal
    s_r = int(medal_r * 0.55)
    pts = []
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5
        r = s_r if k % 2 == 0 else s_r // 2
        pts.append((apex_x + r * math.cos(a), medal_y + r * math.sin(a)))
    d.polygon(pts, fill=(*GOLD_DARK, 255))
    return finalize(canvas)


def render_doctor(i: int) -> Image.Image:
    """👨🏻‍⚕ Doctor — clean Twemoji + gentle white-medical glow + breath."""
    t = i / FRAMES
    pulse = 0.5 + 0.5 * math.sin(t * 2 * math.pi)
    canvas = new_canvas()
    base = load_emoji("👨🏻‍⚕", int(82 * SS))
    sized = pulse_scale(base, t, amplitude=0.06)
    # Soft white-clinical glow halo
    soft_glow(canvas, sized, 0, 0,
              color=(245, 245, 245), radius=int(SW * 0.09),
              intensity=0.30 + 0.35 * pulse)
    composite_at(canvas, sized)
    return finalize(canvas)


def render_hooker(i: int) -> Image.Image:
    """💃 dancing woman + rhythmic sway + pink glow + floating hearts."""
    t = i / FRAMES
    canvas = new_canvas()
    base = load_emoji("💃", int(80 * SS))
    # Rhythmic side-to-side sway (2 cycles per loop — dance feel)
    sway = int(math.sin(t * 2 * math.pi * 2) * SW * 0.04)
    # Lean tilt matching sway direction
    tilted = tilt_oscillate(base, t, max_deg=6, cycles=2.0)
    # Warm magenta/pink glow
    soft_glow(canvas, tilted, sway, 0,
              color=(240, 90, 160), radius=int(SW * 0.10),
              intensity=0.35 + 0.30 * (0.5 + 0.5 * math.sin(t * 2 * math.pi)))
    composite_at(canvas, tilted, x_offset=sway)
    # Two hearts floating up at offset phases
    cx = SW // 2
    for k, base_x in enumerate((-int(SW * 0.24), int(SW * 0.24))):
        local = (t + k * 0.5) % 1.0
        # Sway side as heart rises
        hx = cx + base_x + int(math.sin(local * 4 + k) * SW * 0.04)
        hy = int(SH * 0.50) - int(local * SH * 0.45)
        hsize = int(SW * 0.040 * (1 - local * 0.3))
        ha = int(255 * (1 - local))
        if hsize <= 0 or ha < 30 or hy < 0:
            continue
        # Heart: two circles + downward triangle
        hd = ImageDraw.Draw(canvas)
        hd.ellipse([hx - hsize, hy - hsize, hx, hy], fill=(*HEART_RED, ha))
        hd.ellipse([hx, hy - hsize, hx + hsize, hy], fill=(*HEART_RED, ha))
        hd.polygon([(hx - hsize, hy - 1),
                    (hx + hsize, hy - 1),
                    (hx, hy + hsize)],
                   fill=(*HEART_RED, ha))
    return finalize(canvas)


def render_hobo(i: int) -> Image.Image:
    """🚶‍♂ wanderer (hobo visits players at night) — drifts L→R with dust."""
    t = i / FRAMES
    canvas = new_canvas()
    base = load_emoji("🚶‍♂", int(78 * SS))
    # Drifting left-right (slow continuous sweep, full cycle per loop)
    drift = int(math.sin(t * 2 * math.pi) * SW * 0.10)
    # Slight vertical step bounce (twice per loop)
    bob = bounce_y(t, height=int(SH * 0.03), cycles=2.0)
    # Subtle dust trail behind: small particles spaced behind walker
    cx = SW // 2 + drift
    for k in range(4):
        local = (t + k * 0.18) % 1.0
        # Dust fades out as it rises
        dy = SH - int(SH * 0.10) - int(local * SH * 0.12)
        dx = cx - int(drift * 1.4) - int((1 - local) * SW * 0.08)
        a = int(180 * (1 - local))
        r = max(2, int(SW * 0.025 * (1 + local)))
        if a > 30:
            dust_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
            ImageDraw.Draw(dust_layer).ellipse(
                [dx - r, dy - r, dx + r, dy + r],
                fill=(180, 165, 140, a),
            )
            canvas.alpha_composite(dust_layer.filter(ImageFilter.GaussianBlur(SS)))
    # Soft purple-mystic glow (still keeping the "wandering soul" vibe)
    soft_glow(canvas, base, drift, bob,
              color=(160, 130, 200), radius=int(SW * 0.07),
              intensity=0.20 + 0.20 * (0.5 + 0.5 * math.sin(t * 2 * math.pi)))
    composite_at(canvas, base, x_offset=drift, y_offset=bob)
    return finalize(canvas)


def render_lucky(i: int) -> Image.Image:
    """Spinning four-leaf clover."""
    t = i / FRAMES
    canvas = new_canvas()
    angle = t * 2 * math.pi  # full spin
    # Render clover at SW, then rotate. Use 4 heart-shaped leaves.
    leaf_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(leaf_layer)
    cx, cy = SW // 2, SH // 2
    leaf_r = int(SW * 0.22)
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4  # diagonals
        lx = cx + int(leaf_r * 0.55 * math.cos(a))
        ly = cy + int(leaf_r * 0.55 * math.sin(a))
        ld.ellipse([lx - leaf_r // 2, ly - leaf_r // 2,
                    lx + leaf_r // 2, ly + leaf_r // 2],
                   fill=(*GREEN_CLOVER, 255), outline=(*GREEN_DARK, 255), width=2)
    # Stem
    ld.line([(cx, cy), (cx, cy + int(SH * 0.3))], fill=(*GREEN_DARK, 255),
            width=int(SW * 0.025))
    # Centre highlight
    ld.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=(*GREEN_DARK, 255))
    leaf_layer = leaf_layer.rotate(math.degrees(angle), resample=Image.BICUBIC,
                                    center=(cx, cy))
    canvas.alpha_composite(leaf_layer)
    return finalize(canvas)


def render_suicide(i: int) -> Image.Image:
    """🤦🏼 facepalm — head shake despair + falling teardrops."""
    t = i / FRAMES
    canvas = new_canvas()
    base = load_emoji("🤦🏼", int(80 * SS))
    # Slow despondent shake — full cycle per loop
    shaken = tilt_oscillate(base, t, max_deg=3, cycles=2.0)
    # Cool blue sorrow glow
    soft_glow(canvas, shaken, 0, 0,
              color=(80, 130, 180), radius=int(SW * 0.08), intensity=0.30)
    composite_at(canvas, shaken)
    # Two teardrops falling at offset phases
    cx, cy = SW // 2, SH // 2
    for k, x_off in enumerate((-int(SW * 0.20), int(SW * 0.20))):
        local = (t + k * 0.5) % 1.0
        ty = cy + int(local * SH * 0.45)
        ta = int(255 * (1 - local * 0.6))
        if ta < 40:
            continue
        tr = int(SW * 0.030)
        tx = cx + x_off
        # Teardrop = circle + triangle
        td = ImageDraw.Draw(canvas)
        td.ellipse([tx - tr, ty - tr, tx + tr, ty + tr],
                   fill=(80, 160, 230, ta))
        td.polygon([(tx - tr + 1, ty),
                    (tx + tr - 1, ty),
                    (tx, ty - tr * 2)],
                   fill=(80, 160, 230, ta))
    return finalize(canvas)


def render_kamikaze(i: int) -> Image.Image:
    """💣 bomb — urgent red pulse + violent flickering fuse spark on top."""
    t = i / FRAMES
    canvas = new_canvas()
    base = load_emoji("💣", int(80 * SS))
    # Tense pulse — quick, twice per loop, suggesting heartbeat
    sized = pulse_scale(base, t, amplitude=0.10)
    # Danger-red urgent glow throbbing
    danger = 0.5 + 0.5 * math.sin(t * 2 * math.pi * 2)  # 2x per loop
    soft_glow(canvas, sized, 0, 0,
              color=(220, 60, 40), radius=int(SW * 0.10),
              intensity=0.30 + 0.55 * danger)
    composite_at(canvas, sized)
    # Bright violent spark above the bomb (where the fuse tip would be)
    # Twemoji bomb has the fuse curling to upper-right; aim spark there
    spark_x = SW // 2 + int(SW * 0.24)
    spark_y = int(SH * 0.12)
    flicker = 0.5 + 0.5 * math.sin(t * 2 * math.pi * 6)  # very fast flicker
    sr = int(SW * 0.08 * (0.7 + 0.5 * flicker))
    spark_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(spark_layer).ellipse(
        [spark_x - sr, spark_y - sr, spark_x + sr, spark_y + sr],
        fill=(*FLAME_ORANGE, 220),
    )
    canvas.alpha_composite(spark_layer.filter(ImageFilter.GaussianBlur(SS * 2)))
    # Bright yellow core
    cr = int(SW * 0.04 * (0.7 + 0.5 * flicker))
    ImageDraw.Draw(canvas).ellipse(
        [spark_x - cr, spark_y - cr, spark_x + cr, spark_y + cr],
        fill=(*FLAME_YELLOW, 255),
    )
    # Radiating tiny sparks
    rng_phase = int(t * FRAMES) % FRAMES
    for k in range(6):
        a = rng_phase * 0.7 + k * math.pi / 3
        dist = int(SW * (0.06 + 0.07 * ((rng_phase + k * 7) % 10) / 10))
        sx = spark_x + int(math.cos(a) * dist)
        sy = spark_y + int(math.sin(a) * dist)
        ImageDraw.Draw(canvas).ellipse(
            [sx - 2, sy - 2, sx + 2, sy + 2], fill=(*FLAME_YELLOW, 230),
        )
    return finalize(canvas)


# =========================================================================
# MAFIA (5)
# =========================================================================

def render_don(i: int) -> Image.Image:
    """Black fedora + lit cigar with rising smoke wisp (v1 — user-approved)."""
    t = i / FRAMES
    canvas = new_canvas()
    cx = SW // 2
    # Fedora — black, upper third
    _draw_fedora_mini(canvas, cx, int(SH * 0.30), int(SW * 0.78), color=(20, 16, 22))
    d = ImageDraw.Draw(canvas)
    # Cigar — small brown rounded bar at bottom-right
    cigar_x = cx + int(SW * 0.12)
    cigar_y = int(SH * 0.65)
    cigar_w = int(SW * 0.22)
    cigar_h = int(SW * 0.05)
    d.rounded_rectangle([cigar_x, cigar_y, cigar_x + cigar_w, cigar_y + cigar_h],
                        radius=cigar_h // 2, fill=(120, 70, 30, 255))
    # Burning tip
    tip_w = int(SW * 0.04)
    d.ellipse([cigar_x + cigar_w - tip_w, cigar_y - 1,
               cigar_x + cigar_w + tip_w, cigar_y + cigar_h + 1],
              fill=(*FLAME_ORANGE, 255))
    # Smoke wisp — three puffs rising at staggered phases
    smoke_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(smoke_layer)
    for k in range(3):
        local = (t + k * 0.33) % 1.0
        sx = cigar_x + cigar_w + int(math.sin(local * 6 + k) * SW * 0.04)
        sy = cigar_y - int(local * SH * 0.40)
        sr = int(SW * 0.04 * (0.5 + local * 0.8))
        a = int(180 * (1 - local))
        if a > 0 and sy > 0:
            sd.ellipse([sx - sr, sy - sr, sx + sr, sy + sr],
                       fill=(*SMOKE, a))
    canvas.alpha_composite(smoke_layer.filter(ImageFilter.GaussianBlur(SS)))
    return finalize(canvas)


def render_mafia(i: int) -> Image.Image:
    """Fedora over a face with black eye-mask — subtle nod (v1 — user-approved)."""
    t = i / FRAMES
    canvas = new_canvas()
    nod = int(math.sin(t * 2 * math.pi) * 4)
    cx = SW // 2
    # Fedora
    _draw_fedora_mini(canvas, cx, int(SH * 0.32) + nod, int(SW * 0.72),
                      color=(28, 22, 28))
    d = ImageDraw.Draw(canvas)
    # Face — round, skin-tone
    face_y = int(SH * 0.62) + nod
    face_r = int(SW * 0.26)
    d.ellipse([cx - face_r, face_y - face_r, cx + face_r, face_y + face_r],
              fill=(*SKIN, 255))
    # Eye mask
    mask_y = face_y - int(SW * 0.04)
    mask_w = int(face_r * 1.05)
    mask_h = int(SW * 0.10)
    d.rounded_rectangle([cx - mask_w, mask_y - mask_h, cx + mask_w, mask_y + mask_h],
                        radius=mask_h, fill=(*EYE_DARK, 255))
    # Eye holes — white
    for sign in (-1, 1):
        ex = cx + sign * int(face_r * 0.5)
        d.ellipse([ex - 6, mask_y - 4, ex + 6, mask_y + 4], fill=(*WHITE, 255))
    # Mouth — flat
    d.line([(cx - int(face_r * 0.4), face_y + int(face_r * 0.45)),
            (cx + int(face_r * 0.4), face_y + int(face_r * 0.45))],
           fill=(*EYE_DARK, 255), width=4)
    return finalize(canvas)


def render_lawyer(i: int) -> Image.Image:
    """Wooden gavel that pounds down once per loop."""
    t = i / FRAMES
    canvas = new_canvas()
    d = ImageDraw.Draw(canvas)
    # Gavel rises then falls (one pound per loop)
    pound = math.sin(t * 2 * math.pi)
    offset = int(-8 * pound) if pound > 0 else int(-16 * pound)  # asymmetric
    cx = SW // 2
    base_y = int(SH * 0.78)
    # Sound block (where gavel hits)
    d.rounded_rectangle([cx - int(SW * 0.30), base_y,
                         cx + int(SW * 0.30), base_y + int(SH * 0.10)],
                        radius=8, fill=(*WOOD, 255))
    d.rounded_rectangle([cx - int(SW * 0.30), base_y,
                         cx + int(SW * 0.30), base_y + 8],
                        radius=4, fill=(*WOOD_LIGHT, 255))
    # Gavel rotated -30°: head on top-right, handle to lower-left
    gavel_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(gavel_layer)
    head_cx = cx + int(SW * 0.08)
    head_cy = int(SH * 0.40) + offset
    head_w = int(SW * 0.40)
    head_h = int(SW * 0.16)
    # Hammer head — cylinder
    gd.rounded_rectangle([head_cx - head_w // 2, head_cy - head_h // 2,
                          head_cx + head_w // 2, head_cy + head_h // 2],
                         radius=head_h // 2, fill=(*WOOD, 255))
    # Caps darker
    gd.ellipse([head_cx - head_w // 2 - 2, head_cy - head_h // 2,
                head_cx - head_w // 2 + head_h, head_cy + head_h // 2],
               fill=(*WOOD_LIGHT, 255))
    gd.ellipse([head_cx + head_w // 2 - head_h, head_cy - head_h // 2,
                head_cx + head_w // 2 + 2, head_cy + head_h // 2],
               fill=(*WOOD_LIGHT, 255))
    # Handle
    handle_thick = int(SW * 0.06)
    gd.rounded_rectangle([head_cx - handle_thick // 2, head_cy + head_h // 2,
                          head_cx + handle_thick // 2, head_cy + head_h // 2 + int(SH * 0.30)],
                         radius=handle_thick // 2, fill=(*WOOD_LIGHT, 255))
    # Tilt the whole gavel slightly
    gavel_layer = gavel_layer.rotate(-25, resample=Image.BICUBIC, center=(head_cx, head_cy))
    canvas.alpha_composite(gavel_layer)
    # Impact spark when pound==-1 (bottom of swing) — short window
    if 0.40 < t < 0.55:
        spark_alpha = int(255 * (1 - abs(t - 0.475) * 12))
        sl = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        ImageDraw.Draw(sl).ellipse(
            [cx - int(SW * 0.18), base_y - int(SH * 0.06),
             cx + int(SW * 0.18), base_y + int(SH * 0.04)],
            fill=(*GOLD_HOT, max(0, spark_alpha)),
        )
        canvas.alpha_composite(sl.filter(ImageFilter.GaussianBlur(SS * 2)))
    return finalize(canvas)


def render_journalist(i: int) -> Image.Image:
    """📸 camera with flash — periodic intense white flash bursts."""
    t = i / FRAMES
    canvas = new_canvas()
    base = load_emoji("📸", int(80 * SS))
    sized = pulse_scale(base, t, amplitude=0.04)
    composite_at(canvas, sized)
    # Two flash bursts per loop: at t≈0.20 and t≈0.65
    flash_peaks = (0.20, 0.65)
    flash_window = 0.18  # how wide each burst is
    cx, cy = SW // 2, SH // 2
    for peak in flash_peaks:
        if abs(t - peak) < flash_window / 2 or abs(t - peak + 1) < flash_window / 2:
            envelope = max(0, 1 - abs(t - peak) * 2 / flash_window)
            burst_alpha = int(255 * envelope)
            burst_r = int(SW * 0.35 * envelope)
            bl = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
            ImageDraw.Draw(bl).ellipse(
                [cx - burst_r, cy - burst_r, cx + burst_r, cy + burst_r],
                fill=(255, 252, 235, burst_alpha),
            )
            canvas.alpha_composite(bl.filter(ImageFilter.GaussianBlur(SS * 4)))
            # White overlay flash on subject (intense white halo)
            soft_glow(canvas, sized, 0, 0,
                      color=(255, 255, 255), radius=int(SW * 0.06),
                      intensity=envelope * 0.8)
            # Diagonal star spikes
            d = ImageDraw.Draw(canvas)
            for ang in (0, math.pi / 4, math.pi / 2, 3 * math.pi / 4,
                        math.pi, 5 * math.pi / 4, 3 * math.pi / 2, 7 * math.pi / 4):
                length = int(burst_r * 1.5)
                slx = cx + int(math.cos(ang) * length)
                sly = cy + int(math.sin(ang) * length)
                d.line([(cx, cy), (slx, sly)],
                       fill=(255, 252, 235, int(burst_alpha * 0.9)), width=3)
    return finalize(canvas)


def render_ninja(i: int) -> Image.Image:
    """🥷 ninja + spinning steel shurikens orbiting around him."""
    t = i / FRAMES
    canvas = new_canvas()
    base = load_emoji("🥷", int(76 * SS))
    sized = pulse_scale(base, t, amplitude=0.04)
    # Stealthy dark glow
    soft_glow(canvas, sized, 0, 0,
              color=(60, 60, 80), radius=int(SW * 0.10),
              intensity=0.35 + 0.20 * (0.5 + 0.5 * math.sin(t * 2 * math.pi)))
    composite_at(canvas, sized)
    # Two shurikens orbit at offset phases, each spinning on its own axis
    cx, cy = SW // 2, SH // 2
    for k, phase in enumerate((0.0, math.pi)):
        ox, oy = orbit_position(t, cx, cy,
                                 radius_x=int(SW * 0.36),
                                 radius_y=int(SH * 0.18),
                                 phase=phase)
        in_front = oy >= cy - int(SH * 0.05)
        # Draw shuriken — 4-point star, spinning fast on its own axis
        spin = (t + k * 0.5) * 2 * math.pi * 3
        R = int(SW * 0.07)
        r = int(SW * 0.025)
        pts = []
        for j in range(8):
            a = spin + j * math.pi / 4
            rad = R if j % 2 == 0 else r
            pts.append((ox + rad * math.cos(a), oy + rad * math.sin(a)))
        shur = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        alpha_v = 255 if in_front else 130
        ImageDraw.Draw(shur).polygon(
            pts, fill=(*STEEL, alpha_v), outline=(*WHITE, alpha_v),
        )
        hub_r = int(SW * 0.015)
        ImageDraw.Draw(shur).ellipse(
            [ox - hub_r, oy - hub_r, ox + hub_r, oy + hub_r],
            fill=(20, 22, 28, alpha_v),
        )
        canvas.alpha_composite(shur)
    return finalize(canvas)


# =========================================================================
# SINGLETONS (6)
# =========================================================================

def render_maniac(i: int) -> Image.Image:
    """👹 ogre — fierce red demon mask with throbbing red glow + tremor shake."""
    t = i / FRAMES
    canvas = new_canvas()
    base = load_emoji("👹", int(82 * SS))
    # Subtle creepy tremor (high-frequency tiny shake)
    shake = shake_x(t, amplitude=int(SW * 0.012), cycles=6.0)
    # Pulse scale slightly + creepy tilt
    sized = pulse_scale(base, t, amplitude=0.06)
    tilted = tilt_oscillate(sized, t, max_deg=4)
    # Intense violent red glow
    danger = 0.5 + 0.5 * math.sin(t * 2 * math.pi * 2)
    soft_glow(canvas, tilted, shake, 0,
              color=(220, 30, 30), radius=int(SW * 0.12),
              intensity=0.45 + 0.45 * danger)
    composite_at(canvas, tilted, x_offset=shake)
    return finalize(canvas)


def render_werewolf(i: int) -> Image.Image:
    """🐺 wolf face with 🌕 full moon glowing behind + howling red eye flare."""
    t = i / FRAMES
    canvas = new_canvas()
    # Full moon halo behind wolf — pulsing cold glow
    moon = load_emoji("🌕", int(60 * SS))
    moon_pulse = 0.5 + 0.5 * math.sin(t * 2 * math.pi)
    moon_x_off = int(SW * 0.18)  # behind/right of wolf
    moon_y_off = -int(SH * 0.18)
    soft_glow(canvas, moon, moon_x_off, moon_y_off,
              color=(200, 215, 240), radius=int(SW * 0.13),
              intensity=0.30 + 0.40 * moon_pulse)
    # Faded moon disc (semi-transparent so wolf reads as foreground)
    faded_moon = moon.copy()
    a = faded_moon.split()[3].point(lambda v: int(v * 0.85))
    faded_moon.putalpha(a)
    composite_at(canvas, faded_moon, x_offset=moon_x_off, y_offset=moon_y_off)
    # Wolf base — slight tilt as if howling skyward
    base = load_emoji("🐺", int(78 * SS))
    tilted = base.rotate(-4 + math.sin(t * 2 * math.pi) * 2,
                          resample=Image.BICUBIC, expand=False)
    # Menacing red glow throbbing behind wolf
    danger = 0.5 + 0.5 * math.sin(t * 2 * math.pi * 2)
    soft_glow(canvas, tilted, 0, 0,
              color=(180, 30, 40), radius=int(SW * 0.10),
              intensity=0.35 + 0.45 * danger)
    composite_at(canvas, tilted)
    # Red ember eyes glowing on top of the wolf — small bright dots
    cx = SW // 2
    eye_y = int(SH * 0.46)
    eye_dx = int(SW * 0.10)
    for sign in (-1, 1):
        ex = cx + sign * eye_dx
        # Strong red ember
        em_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        em_r = int(SW * 0.04 * (0.8 + 0.4 * danger))
        ImageDraw.Draw(em_layer).ellipse(
            [ex - em_r, eye_y - em_r, ex + em_r, eye_y + em_r],
            fill=(255, 60, 50, int(220 * danger + 35)),
        )
        canvas.alpha_composite(em_layer.filter(ImageFilter.GaussianBlur(SS)))
    return finalize(canvas)


def render_mage(i: int) -> Image.Image:
    """🧙 mage + multi-coloured sparkle vortex orbiting around them."""
    t = i / FRAMES
    canvas = new_canvas()
    base = load_emoji("🧙", int(76 * SS))
    sized = pulse_scale(base, t, amplitude=0.05)
    # Magical purple glow
    soft_glow(canvas, sized, 0, 0,
              color=(170, 90, 230), radius=int(SW * 0.10),
              intensity=0.35 + 0.30 * (0.5 + 0.5 * math.sin(t * 2 * math.pi)))
    composite_at(canvas, sized)
    # Sparkle orbits — 6 sparkles at offset phases, elliptical orbit
    cx, cy = SW // 2, int(SH * 0.50)
    sparkle_colors = [
        (255, 240, 160), (190, 130, 240), (140, 200, 255),
        (255, 240, 160), (190, 130, 240), (140, 200, 255),
    ]
    for k in range(6):
        phase = k * math.pi / 3
        sx, sy = orbit_position(t, cx, cy,
                                 radius_x=int(SW * 0.38),
                                 radius_y=int(SH * 0.20),
                                 phase=phase)
        depth = 0.5 + 0.5 * math.sin(t * 2 * math.pi + phase)
        size = max(3, int(SW * 0.028 * (0.6 + depth)))
        a = int(160 + 90 * depth)
        draw_sparkle(canvas, sx, sy, size, color=sparkle_colors[k], alpha=a)
    return finalize(canvas)


def render_arsonist(i: int) -> Image.Image:
    """🔥 fire — strong flickering pulse + orange glow + rising sparks."""
    t = i / FRAMES
    canvas = new_canvas()
    base = load_emoji("🔥", int(82 * SS))
    # Fast asymmetric flicker — non-uniform scale on X vs Y
    flicker = math.sin(t * 2 * math.pi * 3)
    sx = 1 + 0.08 * flicker
    sy = 1 + 0.12 * abs(flicker)
    flickered = base.resize(
        (max(2, int(base.width * sx)), max(2, int(base.height * sy))),
        Image.LANCZOS,
    )
    # Intense orange glow halo
    soft_glow(canvas, flickered, 0, 0,
              color=(255, 140, 30), radius=int(SW * 0.14),
              intensity=0.55 + 0.35 * (0.5 + 0.5 * math.sin(t * 2 * math.pi * 2)))
    composite_at(canvas, flickered)
    # Rising sparks/embers — 4 small particles at phase offsets
    cx = SW // 2
    for k in range(4):
        local = (t + k * 0.25) % 1.0
        sx = cx + int(math.sin(local * 6 + k * 1.7) * SW * 0.10)
        sy = int(SH * 0.30) - int(local * SH * 0.32)
        r = max(2, int(SW * 0.020 * (1 - local * 0.5)))
        a = int(220 * (1 - local))
        if a > 30 and sy > 0:
            colour = FLAME_YELLOW if local < 0.5 else FLAME_ORANGE
            ImageDraw.Draw(canvas).ellipse(
                [sx - r, sy - r, sx + r, sy + r],
                fill=(*colour, a),
            )
    return finalize(canvas)


def render_crook(i: int) -> Image.Image:
    """🤹 juggler + spinning 🃏 playing cards orbiting overhead."""
    t = i / FRAMES
    canvas = new_canvas()
    base = load_emoji("🤹", int(76 * SS))
    sized = pulse_scale(base, t, amplitude=0.05)
    # Trickster green glow (like swindler money colour)
    soft_glow(canvas, sized, 0, 0,
              color=(120, 200, 120), radius=int(SW * 0.08),
              intensity=0.25 + 0.20 * (0.5 + 0.5 * math.sin(t * 2 * math.pi)))
    composite_at(canvas, sized)
    # Three cards orbiting overhead at offset phases
    card = load_emoji("🃏", int(28 * SS))
    cx = SW // 2
    cy = int(SH * 0.32)  # orbit centered above the juggler
    for k in range(3):
        phase = k * 2 * math.pi / 3
        ox, oy = orbit_position(t, cx, cy,
                                 radius_x=int(SW * 0.30),
                                 radius_y=int(SH * 0.12),
                                 phase=phase)
        # Each card also spins on its own axis
        spun = rotate_full(card, t + k * 0.33)
        # Depth fade
        in_front = oy >= cy
        c = spun
        if not in_front:
            c = spun.copy()
            a = c.split()[3].point(lambda v: int(v * 0.55))
            c.putalpha(a)
        canvas.alpha_composite(c, (ox - c.width // 2, oy - c.height // 2))
    return finalize(canvas)


def render_snitch(i: int) -> Image.Image:
    """🐀 rat darting left-right with motion blur trail."""
    t = i / FRAMES
    canvas = new_canvas()
    base = load_emoji("🐀", int(80 * SS))
    # Fast dart motion — 2 darts per loop, asymmetric easing
    dart_t = (t * 2) % 1.0  # 2 cycles per loop
    direction = 1 if (t * 2) % 2 < 1 else -1
    dart_x = int(math.sin(dart_t * math.pi) * SW * 0.18) * direction
    # Slight tilt matching motion direction
    tilt = math.sin(dart_t * math.pi) * 7 * direction
    rotated = base.rotate(tilt, resample=Image.BICUBIC, expand=False)
    # Sneaky dim glow (greenish-grey)
    soft_glow(canvas, rotated, dart_x, 0,
              color=(120, 140, 110), radius=int(SW * 0.07), intensity=0.30)
    # Motion blur trail — render 2 fading copies behind
    for k in (1, 2):
        trail_x = dart_x - k * int(SW * 0.04) * direction
        trail = rotated.copy()
        a = trail.split()[3].point(lambda v, k=k: int(v * (0.30 / k)))
        trail.putalpha(a)
        composite_at(canvas, trail, x_offset=trail_x)
    composite_at(canvas, rotated, x_offset=dart_x)
    return finalize(canvas)


# --- registry ------------------------------------------------------------

EMOJIS: dict[str, tuple[str, callable]] = {
    # Scene / shared
    "card":       ("🃏", render_card),
    "moon":       ("🌙", render_moon),
    "sun":        ("🌅", render_sun),
    "skull":      ("💀", render_skull),
    "shield":     ("🛡", render_shield),
    "trophy":     ("🏆", render_trophy),
    "knife":      ("🔪", render_knife),
    # Civilians (10)
    "citizen":    ("👨🏼", render_citizen),
    "detective":  ("🕵🏻‍♂", render_detective),
    "sergeant":   ("👮🏻‍♂", render_sergeant),
    "mayor":      ("🎖", render_mayor),
    "doctor":     ("👨🏻‍⚕", render_doctor),
    "hooker":     ("💃", render_hooker),
    "hobo":       ("🚶‍♂", render_hobo),
    "lucky":      ("🤞🏼", render_lucky),
    "suicide":    ("🤦🏼", render_suicide),
    "kamikaze":   ("💣", render_kamikaze),
    # Mafia (5)
    "don":        ("🤵🏻", render_don),
    "mafia":      ("🤵🏼", render_mafia),
    "lawyer":     ("👨‍💼", render_lawyer),
    "journalist": ("📸", render_journalist),
    "ninja":      ("🥷", render_ninja),
    # Singletons (6)
    "maniac":     ("👹", render_maniac),
    "werewolf":   ("🐺", render_werewolf),
    "mage":       ("🧙", render_mage),
    "arsonist":   ("🔥", render_arsonist),
    "crook":      ("🤹", render_crook),
    "snitch":     ("🐀", render_snitch),
}


# --- ffmpeg encoding ----------------------------------------------------

def encode_webm(frames: list[Image.Image], out_path: Path) -> int:
    """Encode RGBA frames to VP9+alpha WebM. Returns final size in bytes."""
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        for i, fr in enumerate(frames):
            fr.save(td_path / f"f_{i:03d}.png")

        # libvpx-vp9 with alpha. -auto-alt-ref 0 is required for yuva420p.
        # Two-pass kept off — single pass is small enough at this resolution.
        cmd = [
            "ffmpeg", "-y", "-loglevel", "error",
            "-framerate", str(FPS),
            "-i", str(td_path / "f_%03d.png"),
            "-c:v", "libvpx-vp9",
            "-pix_fmt", "yuva420p",
            "-b:v", "180k",
            "-minrate", "80k",
            "-maxrate", "350k",
            "-deadline", "good",
            "-cpu-used", "2",
            "-auto-alt-ref", "0",
            "-an",
            str(out_path),
        ]
        subprocess.run(cmd, check=True)
    return out_path.stat().st_size


def render_emoji(name: str, renderer) -> Path:
    frames = [renderer(i) for i in range(FRAMES)]
    out_path = OUT_DIR / f"{name}.webm"
    size = encode_webm(frames, out_path)
    kb = size / 1024
    status = "✅" if kb <= SIZE_LIMIT_KB else "❌"
    print(f"  {status} {name:<8} {kb:>6.1f} KB  → {out_path.relative_to(ROOT)}")
    if kb > SIZE_LIMIT_KB:
        print(f"     (over {SIZE_LIMIT_KB} KB limit — reduce bitrate or duration)")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--only",
        type=str,
        default="",
        help="Comma-separated emoji names to render (default: all)",
    )
    args = parser.parse_args()

    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found on PATH")

    selected = (
        [n.strip() for n in args.only.split(",") if n.strip()]
        if args.only else list(EMOJIS.keys())
    )
    unknown = [n for n in selected if n not in EMOJIS]
    if unknown:
        sys.exit(f"Unknown emoji name(s): {unknown}. Choices: {list(EMOJIS.keys())}")

    print(f"Rendering {len(selected)} emoji(s) at {W}×{H}, {FPS} fps, {DURATION_S}s loop")
    for name in selected:
        _emoji_char, renderer = EMOJIS[name]
        render_emoji(name, renderer)
    print()
    print("Next: python scripts/upload_emoji_pack.py")


if __name__ == "__main__":
    main()
