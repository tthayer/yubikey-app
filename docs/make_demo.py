# Regenerate docs/demo.gif:  python3 make_demo.py
# Needs Pillow + macOS system fonts (Arial, Menlo). Renders the LP3 YubiKey flow.

#!/usr/bin/env python3
"""Render an animated GIF of the Light Phone III YubiKey tool in use.

Draws at 2x and downsamples with LANCZOS for crisp monochrome text, then
quantizes every frame against one shared palette so there's no inter-frame
flicker. Faithful to the app's real copy, layout, and flow.
"""
from PIL import Image, ImageDraw, ImageFont

# ---- palette (warm minimal monochrome, LightOS-ish) -----------------------
PAPER  = (233, 231, 226)   # canvas behind the device
BODY   = (13, 13, 13)      # phone body
SCREEN = (0, 0, 0)         # display
WHITE  = (244, 244, 241)   # primary text
GRAY   = (139, 139, 136)   # secondary / "lighten" text
FAINT  = (58, 58, 58)      # dividers, ring tails

# ---- draw-space geometry (2x; downsampled at the end) ---------------------
SCREEN_W, SCREEN_H = 900, 1040
BZ_X, BZ_TOP, BZ_BOT = 46, 74, 96
DEV_W = SCREEN_W + 2 * BZ_X
DEV_H = SCREEN_H + BZ_TOP + BZ_BOT
MARGIN = 66
CW = DEV_W + 2 * MARGIN
CH = DEV_H + 2 * MARGIN
SX = MARGIN + BZ_X          # screen origin x
SY = MARGIN + BZ_TOP        # screen origin y

def font(path, size):
    return ImageFont.truetype(path, size)

SANS = "/System/Library/Fonts/Supplemental/Arial.ttf"
MONO = "/System/Library/Fonts/Menlo.ttc"
F_TITLE = font(SANS, 44)
F_BODY  = font(SANS, 40)
F_BTN   = font(SANS, 40)
F_READ  = font(SANS, 46)
F_LABEL = font(SANS, 30)
F_SUB   = font(SANS, 28)
F_CODE  = font(MONO, 74)

ACCOUNTS = [
    ("GitHub · octocat",        "738 291"),
    ("Google · you@gmail.com",  "105 664"),
    ("AWS · root",              "042 913"),
]

def sc(x, y):
    return (SX + x, SY + y)

def center_text(d, cx, y, text, fnt, fill, spacing=0):
    if spacing:
        # manual letter-spacing
        widths = [d.textlength(ch, font=fnt) for ch in text]
        total = sum(widths) + spacing * (len(text) - 1)
        x = cx - total / 2
        for ch, w in zip(text, widths):
            d.text((x, y), ch, font=fnt, fill=fill)
            x += w + spacing
    else:
        w = d.textlength(text, font=fnt)
        d.text((cx - w / 2, y), text, font=fnt, fill=fill)

def wrap(d, text, fnt, max_w):
    words, lines, cur = text.split(), [], ""
    for wd in words:
        t = (cur + " " + wd).strip()
        if d.textlength(t, font=fnt) <= max_w:
            cur = t
        else:
            lines.append(cur); cur = wd
    if cur:
        lines.append(cur)
    return lines

def base():
    img = Image.new("RGB", (CW, CH), PAPER)
    d = ImageDraw.Draw(img)
    # device body
    d.rounded_rectangle([MARGIN, MARGIN, MARGIN + DEV_W, MARGIN + DEV_H],
                        radius=64, fill=BODY)
    # screen
    d.rounded_rectangle([SX, SY, SX + SCREEN_W, SY + SCREEN_H],
                        radius=20, fill=SCREEN)
    return img, d

def chrome(d, bottom="READ"):
    # top bar
    center_text(d, SX + SCREEN_W / 2, SY + 46, "YubiKey", F_TITLE, WHITE)
    d.line([sc(60, 132), sc(SCREEN_W - 60, 132)], fill=FAINT, width=2)
    # bottom bar
    by = SCREEN_H - 150
    d.line([sc(60, by), sc(SCREEN_W - 60, by)], fill=FAINT, width=2)
    center_text(d, SX + SCREEN_W / 2, SY + by + 44,
                bottom, F_READ if bottom == "READ" else F_BTN, WHITE, spacing=6)

def frame_idle():
    img, d = base(); chrome(d, "READ")
    msg = "Hold your YubiKey flat to the back of the phone to show your codes."
    lines = wrap(d, msg, F_BODY, SCREEN_W - 150)
    lh = 56
    y0 = SY + SCREEN_H / 2 - len(lines) * lh / 2 - 20
    for i, ln in enumerate(lines):
        center_text(d, SX + SCREEN_W / 2, y0 + i * lh, ln, F_BODY, GRAY)
    return img

def frame_tap(t):
    # t in 0..1 across one wave; concentric rings expanding + fading upward
    img, d = base(); chrome(d, "READ")
    msg = "Hold your YubiKey flat to the back of the phone to show your codes."
    lines = wrap(d, msg, F_BODY, SCREEN_W - 150)
    lh = 56
    y0 = SY + SCREEN_H / 2 - len(lines) * lh / 2 - 150
    for i, ln in enumerate(lines):
        center_text(d, SX + SCREEN_W / 2, y0 + i * lh, ln, F_BODY, GRAY)
    cx, cy = SX + SCREEN_W / 2, SY + SCREEN_H / 2 + 170
    for k in range(3):
        phase = (t + k / 3.0) % 1.0
        r = 30 + phase * 150
        # fade white -> screen as it expands
        f = 1.0 - phase
        col = tuple(int(SCREEN[j] + (WHITE[j] - SCREEN[j]) * f) for j in range(3))
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col, width=5)
    d.ellipse([cx - 12, cy - 12, cx + 12, cy + 12], fill=WHITE)
    return img

def frame_reading(dots):
    img, d = base(); chrome(d, "CANCEL")
    center_text(d, SX + SCREEN_W / 2, SY + SCREEN_H / 2 - 40,
                "Reading" + "." * dots, F_READ, WHITE)
    return img

def frame_loaded(secs):
    img, d = base(); chrome(d, "READ")
    top = SY + 190
    row_h = (SCREEN_H - 150 - 190) / 3
    for i, (label, code) in enumerate(ACCOUNTS):
        ry = top + i * row_h
        cx = SX + SCREEN_W / 2
        center_text(d, cx, ry, label, F_LABEL, GRAY)
        center_text(d, cx, ry + 40, code, F_CODE, WHITE, spacing=4)
        center_text(d, cx, ry + 128, f"resets in {secs}s", F_SUB, GRAY)
    return img

# ---- assemble frames + per-frame durations --------------------------------
frames, durs = [], []

def add(img, ms):
    frames.append(img); durs.append(ms)

add(frame_idle(), 2200)
for i in range(12):                      # ~2 expanding waves
    add(frame_tap(i / 6.0), 75)
for rep in range(2):
    for dots in (1, 2, 3):
        add(frame_reading(dots), 260)
for s in range(27, 21, -1):              # live countdown 27 -> 22
    add(frame_loaded(s), 1000)
add(frame_loaded(21), 1200)              # brief hold before loop

# downsample 2x -> 1x, then quantize all to one shared palette
small = [f.resize((CW // 2, CH // 2), Image.LANCZOS) for f in frames]
pal = small[0].quantize(colors=64, method=Image.MEDIANCUT)
qframes = [f.quantize(palette=pal, dither=Image.FLOYDSTEINBERG) for f in small]

import os
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo.gif")
qframes[0].save(out, save_all=True, append_images=qframes[1:],
                duration=durs, loop=0, disposal=2, optimize=True)
print("wrote", out, "frames:", len(qframes), "size:", small[0].size)
