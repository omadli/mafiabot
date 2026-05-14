"""Generate default atmosphere GIFs for the Mafia bot.

Outputs:
  backend/app/assets/atmosphere/night.gif   — city at night, twinkling
                                              stars + slow flickering windows
  backend/app/assets/atmosphere/day.gif     — sun rising over the city,
                                              sky gradient warms up

Run once and commit the outputs. Telegram's send_animation accepts GIFs
up to 10 MB; these stay well under 500 KB at 480x270 / 24 frames.

Pillow is the only dependency.
"""

from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw

OUT_DIR = Path(__file__).resolve().parents[1] / "backend" / "app" / "assets" / "atmosphere"
OUT_DIR.mkdir(parents=True, exist_ok=True)

W, H = 480, 270  # 16:9 — friendly for Telegram in-chat previews
FRAMES = 24
DURATION_MS = 80  # 24 frames * 80ms = ~1.9s per loop

# Shared city silhouette: (x_start, width, height, has_lit_windows)
CITY_BUILDINGS: list[tuple[int, int, int, bool]] = [
    (-5, 55, 105, True),
    (52, 32, 75, True),
    (88, 42, 130, True),
    (134, 35, 95, True),
    (172, 62, 150, True),
    (238, 28, 88, False),
    (270, 50, 118, True),
    (324, 30, 70, False),
    (358, 48, 142, True),
    (410, 40, 100, True),
    (452, 35, 80, True),
]


def _shade(rgb: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
    return tuple(max(0, min(255, int(c * factor))) for c in rgb)  # type: ignore[return-value]


def _draw_city(draw: ImageDraw.ImageDraw, body_color: tuple[int, int, int],
               window_color: tuple[int, int, int] | None, frame_idx: int) -> None:
    """Solid silhouette + optional window grid (frame_idx drives flicker)."""
    for x, width, height, lit in CITY_BUILDINGS:
        top_y = H - height
        draw.rectangle([x, top_y, x + width, H], fill=body_color)
        # Antenna on tall buildings
        if height > 120:
            cx = x + width // 2
            draw.line([(cx, top_y), (cx, top_y - 10)], fill=body_color, width=2)
        if not (lit and window_color):
            continue
        # Window grid — deterministic flicker pattern per (wx, wy, frame)
        for wy in range(top_y + 10, H - 6, 14):
            for wx in range(x + 5, x + width - 5, 9):
                seed = (wx * 13 + wy * 7 + frame_idx) % 14
                if seed < 9:
                    c = window_color if seed % 3 != 0 else _shade(window_color, 0.78)
                    draw.rectangle([wx, wy, wx + 4, wy + 6], fill=c)


def generate_night() -> Path:
    """Dark sky, moon with halo, twinkling stars, lit-up city silhouette."""
    random.seed(42)
    stars: list[tuple[int, int]] = [
        (random.randint(0, W - 1), random.randint(0, int(H * 0.55))) for _ in range(70)
    ]
    star_phases = [random.uniform(0, 1) for _ in stars]

    frames: list[Image.Image] = []
    for fi in range(FRAMES):
        t = fi / FRAMES
        img = Image.new("RGB", (W, H))
        draw = ImageDraw.Draw(img)

        # Sky gradient (top dark navy → softer near horizon)
        for y in range(H):
            ratio = y / H
            r = int(8 + ratio * 22)
            g = int(10 + ratio * 28)
            b = int(35 + ratio * 35)
            draw.line([(0, y), (W, y)], fill=(r, g, b))

        # Moon + halo (top-right)
        moon_x, moon_y, moon_r = W - 80, 55, 26
        for r_off in range(34, 0, -3):
            halo = max(0, 32 - r_off)
            draw.ellipse(
                [moon_x - moon_r - r_off, moon_y - moon_r - r_off,
                 moon_x + moon_r + r_off, moon_y + moon_r + r_off],
                fill=(40 + halo, 40 + halo, 70 + halo),
            )
        draw.ellipse(
            [moon_x - moon_r, moon_y - moon_r, moon_x + moon_r, moon_y + moon_r],
            fill=(245, 240, 220),
        )
        # Subtle moon "craters"
        draw.ellipse([moon_x - 12, moon_y - 7, moon_x + 2, moon_y + 5], fill=(225, 218, 195))
        draw.ellipse([moon_x + 6, moon_y + 4, moon_x + 14, moon_y + 12], fill=(225, 218, 195))

        # Stars (twinkle via sin phase)
        for i, (sx, sy) in enumerate(stars):
            phase = (t + star_phases[i]) % 1.0
            twinkle = (math.sin(phase * math.pi * 2) + 1) / 2
            b = int(150 + twinkle * 105)
            size = 1 if twinkle < 0.45 else 2
            draw.ellipse(
                [sx - size, sy - size, sx + size, sy + size],
                fill=(b, b, min(255, b + 25)),
            )
            # Occasional cross-glint on brighter stars
            if twinkle > 0.85 and size == 2:
                draw.line([(sx - 3, sy), (sx + 3, sy)], fill=(b, b, b))
                draw.line([(sx, sy - 3), (sx, sy + 3)], fill=(b, b, b))

        _draw_city(draw, body_color=(6, 6, 16), window_color=(255, 215, 95), frame_idx=fi)

        frames.append(img)

    out_path = OUT_DIR / "night.gif"
    frames[0].save(
        out_path,
        save_all=True,
        append_images=frames[1:],
        duration=DURATION_MS,
        loop=0,
        optimize=True,
        disposal=2,
    )
    return out_path


def generate_day() -> Path:
    """Pre-dawn → dawn: sun rises from horizon, sky warms, city brightens."""
    random.seed(7)
    frames: list[Image.Image] = []
    for fi in range(FRAMES):
        t = fi / FRAMES
        # Smoothstep easing for nicer motion
        progress = t * t * (3 - 2 * t)

        img = Image.new("RGB", (W, H))
        draw = ImageDraw.Draw(img)

        # Sky gradient: top zenith (cool blue) → horizon (warm orange/pink)
        # All channels interpolate from "pre-dawn" to "post-dawn".
        r_top = int(60 + progress * 80)    # 60 → 140
        g_top = int(85 + progress * 100)   # 85 → 185
        b_top = int(150 + progress * 75)   # 150 → 225
        r_bot = int(215 + progress * 25)   # 215 → 240
        g_bot = int(135 + progress * 75)   # 135 → 210
        b_bot = int(95 + progress * 80)    # 95 → 175
        for y in range(H):
            ratio = y / H
            r = int(r_top * (1 - ratio) + r_bot * ratio)
            g = int(g_top * (1 - ratio) + g_bot * ratio)
            b = int(b_top * (1 - ratio) + b_bot * ratio)
            draw.line([(0, y), (W, y)], fill=(r, g, b))

        # Soft horizon haze band
        for y in range(int(H * 0.65), int(H * 0.78)):
            ratio = (y - H * 0.65) / (H * 0.13)
            alpha = int(40 * (1 - abs(ratio - 0.5) * 2))
            if alpha > 0:
                draw.line([(0, y), (W, y)], fill=(255, 200, 130))

        # Sun: rises from below the city to above
        sun_x = W // 2 + 70
        sun_y_start = H - 60
        sun_y_end = 60
        sun_y = int(sun_y_start + (sun_y_end - sun_y_start) * progress)
        sun_r = 32

        # Layered halo
        for r_off in range(46, 0, -4):
            alpha = max(0, 50 - r_off)
            draw.ellipse(
                [sun_x - sun_r - r_off, sun_y - sun_r - r_off,
                 sun_x + sun_r + r_off, sun_y + sun_r + r_off],
                fill=(min(255, 245 + alpha // 6), min(255, 200 + alpha // 5), max(80, 130 - r_off)),
            )
        draw.ellipse(
            [sun_x - sun_r, sun_y - sun_r, sun_x + sun_r, sun_y + sun_r],
            fill=(255, 235, 110),
        )
        # Highlight rim
        draw.arc(
            [sun_x - sun_r, sun_y - sun_r, sun_x + sun_r, sun_y + sun_r],
            start=210, end=330, fill=(255, 250, 200), width=2,
        )

        # City silhouette — body brightens as sun rises
        body_shade = int(15 + progress * 50)
        _draw_city(
            draw,
            body_color=(body_shade, body_shade, body_shade + 6),
            window_color=None,  # daylight: windows not lit anymore
            frame_idx=fi,
        )

        # Birds — flock crosses the sky once dawn is well underway
        if progress > 0.35:
            base_offset = (fi - int(FRAMES * 0.35)) * 6
            for i in range(4):
                bx = (40 + i * 90 + base_offset) % (W + 40) - 20
                by = 42 + (i % 2) * 14 + int(math.sin((t + i) * math.pi * 2) * 3)
                draw.line([(bx - 7, by + 4), (bx, by), (bx + 7, by + 4)],
                          fill=(35, 28, 28), width=2)

        frames.append(img)

    out_path = OUT_DIR / "day.gif"
    frames[0].save(
        out_path,
        save_all=True,
        append_images=frames[1:],
        duration=DURATION_MS,
        loop=0,
        optimize=True,
        disposal=2,
    )
    return out_path


if __name__ == "__main__":
    n = generate_night()
    d = generate_day()
    print(f"Wrote {n.relative_to(Path.cwd())} ({n.stat().st_size:,} bytes)")
    print(f"Wrote {d.relative_to(Path.cwd())} ({d.stat().st_size:,} bytes)")
