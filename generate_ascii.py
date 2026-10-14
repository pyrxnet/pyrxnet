#!/usr/bin/env python3
"""
PYRX ASCII generator.

Builds an animated, loopable ASCII-noise SVG (pure SMIL, no JavaScript, so it
plays inside a GitHub README via <img>).

Usage:
    python generate_ascii.py                  # seed rotates every 6 hours
    python generate_ascii.py --seed 1337      # fixed seed
    python generate_ascii.py --out assets/pyrx-ascii.svg
"""
import argparse
import hashlib
import math
import os
import random
from datetime import datetime, timezone

COLS, ROWS = 96, 30          # grid size
FRAMES = 24                  # frames per loop
FRAME_DUR = 0.14             # seconds per frame
CHAR_W, LINE_H = 6, 11       # px per cell
FONT_SIZE = 10
LABEL = "0x50595258"         # "PYRX" in hex
BG = "#0d1117"
FG = "#8b949e"
LABEL_FG = "#ffffff"


def default_seed() -> int:
    now = datetime.now(timezone.utc)
    key = f"{now:%Y-%m-%d}-{now.hour // 6}"
    return int(hashlib.sha256(key.encode()).hexdigest()[:8], 16)


def build_waves(rng):
    """Random sine components. Integer time multiples keep the loop seamless."""
    waves = []
    for k in range(1, 5):
        waves.append(
            (
                rng.uniform(0.05, 0.28),          # x frequency
                rng.uniform(0.08, 0.40),          # y frequency
                rng.uniform(0, math.tau),         # phase
                k,                                # time multiple (integer)
                rng.choice((-1, 1)),              # direction
            )
        )
    return waves


def density(x, y, f, waves):
    u, v = x / COLS, y / ROWS
    base = 1.05 - 1.15 * u - 0.30 * v             # dense top-left, fades right/down
    n = 0.0
    for fx, fy, ph, k, d in waves:
        n += math.sin(x * fx + y * fy + ph + d * math.tau * k * f / FRAMES)
    return base + (n / len(waves)) * 0.38


def glyph(val, rng):
    if val < 0.10:
        return "." if rng.random() < 0.025 else " "
    if val < 0.28:
        return "." if rng.random() < 0.7 else " "
    if val < 0.44:
        return ":"
    if val < 0.60:
        return rng.choice("0:x")
    if val < 0.80:
        return rng.choice("x05")
    return rng.choice("50x5")


def make_frame(f, waves, rng, clear):
    rows = []
    for y in range(ROWS):
        line = []
        for x in range(COLS):
            if (y, x) in clear:
                line.append(" ")
                continue
            val = density(x, y, f, waves) + rng.uniform(-0.12, 0.12)
            line.append(glyph(val, rng))
        rows.append("".join(line))
    return rows


def render(seed: int) -> str:
    rng = random.Random(seed)
    waves = build_waves(rng)

    width, height = COLS * CHAR_W, ROWS * LINE_H + 8
    label_row = int(ROWS * 0.55)
    label_cols = range(COLS - 23, COLS - 2)
    clear = {(r, c) for r in (label_row - 1, label_row, label_row + 1) for c in label_cols}

    total = FRAMES * FRAME_DUR
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" role="img" aria-label="PYRX ASCII animation">',
        f'<rect width="100%" height="100%" fill="{BG}"/>',
        f'<g font-family="SFMono-Regular,Consolas,\'Liberation Mono\',Menlo,monospace" '
        f'font-size="{FONT_SIZE}" fill="{FG}" xml:space="preserve" style="white-space:pre">',
    ]

    for f in range(FRAMES):
        rows = make_frame(f, waves, rng, clear)
        vals = ";".join("1" if i == f else "0" for i in range(FRAMES))
        out.append(f'<g opacity="{1 if f == 0 else 0}">')
        out.append(
            f'<animate attributeName="opacity" calcMode="discrete" '
            f'dur="{total:.2f}s" repeatCount="indefinite" values="{vals}"/>'
        )
        for y, line in enumerate(rows):
            out.append(
                f'<text x="0" y="{(y + 1) * LINE_H}" '
                f'textLength="{COLS * CHAR_W}" lengthAdjust="spacing">{line}</text>'
            )
        out.append("</g>")
    out.append("</g>")

    # Static label, with a slow pulse
    lx = (COLS - 21) * CHAR_W
    ly = (label_row + 1) * LINE_H
    out.append(
        f'<text x="{lx}" y="{ly}" font-family="SFMono-Regular,Consolas,monospace" '
        f'font-size="12" letter-spacing="4" fill="{LABEL_FG}">{LABEL}'
        f'<animate attributeName="opacity" values="1;0.55;1" dur="3s" repeatCount="indefinite"/>'
        f"</text>"
    )
    out.append("</svg>")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--out", default="assets/pyrx-ascii.svg")
    args = ap.parse_args()

    seed = args.seed if args.seed is not None else default_seed()
    svg = render(seed)

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(svg)
    print(f"wrote {args.out} (seed={seed}, {len(svg) / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
