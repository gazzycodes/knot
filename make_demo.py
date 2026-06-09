#!/usr/bin/env python3
"""Generate docs/demo.gif: an animated terminal demo of knot.

Runs knot for real, captures its output, and renders a typing animation as an
animated GIF. Usage (from the repo root):

    py -m pip install pillow
    py make_demo.py
"""

import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(ROOT, "docs")
OUT = os.path.join(OUT_DIR, "demo.gif")

# Dracula-ish palette
BG = (40, 42, 54)
FG = (248, 248, 242)
GREEN = (80, 250, 123)
CYAN = (139, 233, 253)
ORANGE = (255, 184, 108)

W, H = 940, 430
PAD = 26
LINE_H = 27
FONT_SIZE = 19
CURSOR_W = 11


def load_font():
    candidates = [
        r"C:\Windows\Fonts\consola.ttf",
        r"C:\Windows\Fonts\CascadiaCode.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            return ImageFont.truetype(p, FONT_SIZE)
    return ImageFont.load_default()


FONT = load_font()


def run_knot(args):
    proc = subprocess.run(
        [sys.executable, "-m", "knot", *args],
        cwd=ROOT, capture_output=True, text=True,
    )
    return proc.stdout.replace("\r\n", "\n").rstrip("\n").split("\n")


def color_for(line):
    if "->" in line or "cycle" in line.lower():
        return ORANGE
    if line.strip().startswith(("graph", "class", "m_")):
        return CYAN
    return FG


def render(seglines, cursor=False):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    y = PAD
    end_x = end_y = PAD
    for segs in seglines:
        x = PAD
        for text, color in segs:
            d.text((x, y), text, font=FONT, fill=color)
            x += d.textlength(text, font=FONT)
        end_x, end_y = x, y
        y += LINE_H
    if cursor:
        d.rectangle(
            [end_x + 2, end_y + 4, end_x + 2 + CURSOR_W, end_y + LINE_H - 6], fill=FG
        )
    return img


frames, durations = [], []


def push(img, ms):
    frames.append(img)
    durations.append(ms)


PROMPT = ("$ ", GREEN)


def scene(display_cmd, run_args):
    out = run_knot(run_args)
    for i in range(len(display_cmd) + 1):
        push(render([[PROMPT, (display_cmd[:i], FG)]], cursor=True), 45)
    push(render([[PROMPT, (display_cmd, FG)]], cursor=True), 350)
    shown = []
    base = [[PROMPT, (display_cmd, FG)]]
    for line in out:
        shown.append([(line, color_for(line))])
        push(render(base + shown), 120)
    push(render(base + shown), 1900)


scene("knot examples/shop", ["examples/shop"])
push(Image.new("RGB", (W, H), BG), 250)
scene("knot examples/shop --format mermaid", ["examples/shop", "--format", "mermaid"])

os.makedirs(OUT_DIR, exist_ok=True)
frames[0].save(
    OUT, save_all=True, append_images=frames[1:],
    duration=durations, loop=0, optimize=True,
)
print(f"Wrote {OUT} ({len(frames)} frames)")
