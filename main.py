"""ai-happy-01 entry: a handwritten note to the judge, taped to a warm wall.

Pure stdlib procedural render: warm beige surface, a sheet of lined notebook
paper held by two strips of masking tape, and a child's handwritten note in
blue ballpoint, drawn stroke by stroke from a small hand-made stroke font
with a gentle per-letter wobble. Deterministic: all variation comes from an
integer hash, so two runs write byte-identical PNGs.
"""

import os
import zlib
import struct

W = H = 960

# ---------------------------------------------------------------- noise util

def h2(x, y):
    """Deterministic 2D integer hash -> [0, 1)."""
    n = (x * 374761393 + y * 668265263) & 0xFFFFFFFF
    n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFFFF) / 16777216.0


def h1(n):
    n = (n * 2654435761) & 0xFFFFFFFF
    n ^= n >> 15
    return (n & 0xFFFFFF) / 16777216.0


# ------------------------------------------------------------------- canvas

# float RGB buffer
PX = [0.0] * (W * H * 3)


def set_px(x, y, r, g, b, a=1.0):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        if a >= 1.0:
            PX[i], PX[i + 1], PX[i + 2] = r, g, b
        else:
            PX[i] += (r - PX[i]) * a
            PX[i + 1] += (g - PX[i + 1]) * a
            PX[i + 2] += (b - PX[i + 2]) * a


def stamp(cx, cy, rad, r, g, b, a=1.0):
    """Filled disc with a soft rim, stamped into the buffer."""
    x0, x1 = int(cx - rad - 1), int(cx + rad + 1)
    y0, y1 = int(cy - rad - 1), int(cy + rad + 1)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            d2 = (x - cx) ** 2 + (y - cy) ** 2
            if d2 < (rad + 1) ** 2:
                d = d2 ** 0.5
                cov = 1.0 if d <= rad - 0.7 else max(0.0, (rad + 0.7 - d) / 1.4)
                set_px(x, y, r, g, b, a * cov)


def stroke(pts, width, r, g, b, a=1.0):
    """Polyline drawn as overlapping discs; width wobbles like a real pen."""
    rad = width / 2.0
    for k in range(len(pts) - 1):
        x0, y0 = pts[k]
        x1, y1 = pts[k + 1]
        steps = max(2, int(((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5 / 1.6))
        for s in range(steps + 1):
            t = s / steps
            wob = 0.82 + 0.36 * h1(int(x0 * 7 + y0 * 13 + s * 31 + k * 101))
            stamp(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, rad * wob, r, g, b, a)


# -------------------------------------------------------------- stroke font
# Glyph box: x 0..20, baseline y=17, x-height top y=6, ascender top y=1,
# descender bottom y=24. Each glyph: (advance, [stroke, ...]); a stroke is a
# polyline of (x, y) points. Single-story a and g, all lowercase: childlike.

GLYPHS = {
    'a': (14, [[(13, 9), (10.5, 6.4), (6.8, 6.4), (4.2, 9), (4.2, 13.2), (6.8, 15.8), (10.5, 15.8), (13.2, 13.4)],
               [(13, 6.6), (13, 16.6)]]),
    'b': (14, [[(5, 1), (5, 17)],
               [(5, 11), (8, 9.3), (11.8, 9.3), (13.8, 11.8), (13.2, 14.8), (10.8, 16.7), (7.4, 16.7), (5, 15)]]),
    'c': (13, [[(13.8, 8.2), (11, 6.3), (7, 6.3), (4.6, 9.4), (4.6, 13.4), (7, 16.2), (11, 16.2), (13.8, 14.6)]]),
    'd': (14, [[(13, 9), (10.4, 6.4), (6.8, 6.4), (4.4, 9.4), (4.4, 13), (6.8, 15.7), (10.4, 15.7), (13, 13.8)],
               [(13, 1), (13, 17)]]),
    'e': (13, [[(4.4, 11), (13.8, 11)],
               [(13.8, 11), (13.2, 8), (10.6, 6.3), (6.8, 6.5), (4.4, 9.4), (4.4, 13.4), (7, 16.2), (11, 16.2), (13.8, 14.8)]]),
    'f': (11, [[(13, 3.6), (10.6, 1.6), (7.6, 2), (6.6, 5), (6.6, 17)],
               [(3.4, 8.6), (11.4, 8.6)]]),
    'g': (14, [[(13, 9), (10.4, 6.4), (6.8, 6.4), (4.4, 9.4), (4.4, 13), (6.8, 15.7), (10.4, 15.7), (13, 13.8)],
               [(13, 6.6), (13, 15.2), (12, 19.2), (9.4, 21.6), (6.2, 20.6), (4.8, 18.4)]]),
    'h': (14, [[(5, 1), (5, 17)],
               [(5, 11), (7.4, 8), (10.8, 7.8), (13.4, 9.6), (13.4, 17)]]),
    'i': (8, [[(8.6, 6.6), (8.6, 17)],
              [(8.6, 2.2), (8.7, 3.2)]]),
    'j': (9, [[(11.6, 6.6), (11.6, 15.8), (10.6, 19.8), (8.2, 21.6), (5.8, 20.4)],
              [(11.6, 2.2), (11.7, 3.2)]]),
    'k': (14, [[(5, 1), (5, 17)],
               [(13, 7.4), (6.4, 12.6)],
               [(8.6, 11.4), (13.4, 17)]]),
    'l': (8, [[(9.4, 1.6), (8, 6), (8, 16.4), (9.2, 17.2)]]),
    'm': (21, [[(3.6, 6.6), (3.6, 17)],
               [(3.6, 10.2), (5.8, 7.6), (8.8, 7.4), (10.4, 9.6), (10.4, 17)],
               [(10.4, 10.2), (12.6, 7.6), (15.6, 7.4), (17.2, 9.6), (17.2, 17)]]),
    'n': (14, [[(4.4, 6.6), (4.4, 17)],
               [(4.4, 10.2), (6.8, 7.6), (10, 7.4), (12.2, 9.6), (12.2, 17)]]),
    'o': (14, [[(10, 6.3), (6.2, 6.5), (4.2, 9.4), (4.4, 13.4), (7, 16.2), (10.6, 16.2), (13.4, 13.4), (13.6, 9.4), (11, 6.5), (10, 6.3)]]),
    'p': (14, [[(5, 6.6), (5, 23.6)],
               [(5, 9.6), (8, 7.6), (11.8, 7.6), (13.8, 10.4), (13, 13.8), (10.6, 15.7), (7.2, 15.7), (5, 14)]]),
    'r': (12, [[(5, 6.6), (5, 17)],
               [(5, 10.2), (7.4, 7.4), (10.8, 7.1), (13, 8.6)]]),
    's': (12, [[(13.2, 8.2), (10.4, 6.3), (6.8, 7), (5.4, 9.6), (7.4, 11.9), (11.8, 13.9), (13, 15.6), (10.8, 16.9), (6.4, 16.6), (4.8, 15.2)]]),
    't': (11, [[(9, 3), (9, 14.8), (10.4, 16.7), (13, 16.4)],
               [(4.4, 8.2), (13.4, 8.2)]]),
    'u': (14, [[(5, 6.6), (5, 13.4), (7, 15.9), (10.4, 16.2), (13, 13.9), (13, 6.6)],
               [(13, 12.8), (13, 17)]]),
    'v': (14, [[(4.4, 6.6), (9.4, 17), (14.2, 6.6)]]),
    'w': (19, [[(3.4, 6.6), (6, 17), (9, 9.2), (11.6, 17), (14.4, 6.6)]]),
    'y': (14, [[(4.4, 6.6), (9.4, 14.4)],
               [(13.8, 6.6), (9.8, 14.4), (8.4, 19.4), (5.8, 21.4), (4.4, 19.8)]]),
    ',': (8, [[(8.6, 15.4), (7.8, 19.4), (6.2, 21)]]),
    '.': (8, [[(8.4, 16.2), (8.8, 16.9)]]),
    ' ': (9, []),
}

LINES = [
    "dear judge,",
    "you looked at so many",
    "pictures today.",
    "you did a really",
    "good job.",
    "now close your eyes",
    "and rest a little.",
    "love, your friend",
]

# ------------------------------------------------------------------- scene
# Paper in its own coordinate frame, then rotated onto the wall.
PAPER_W, PAPER_H = 720, 760
PAPER_CX, PAPER_CY = 480, 492
ROT = -0.038  # radians, a slight carefree tilt

import math
COS, SIN = math.cos(ROT), math.sin(ROT)


def to_screen(u, v):
    """Paper coords (origin top-left of the sheet) -> screen coords."""
    x = u - PAPER_W / 2
    y = v - PAPER_H / 2
    return (PAPER_CX + x * COS - y * SIN, PAPER_CY + x * SIN + y * COS)


def to_paper(px, py):
    x = px - PAPER_CX
    y = py - PAPER_CY
    return (x * COS + y * SIN + PAPER_W / 2, -x * SIN + y * COS + PAPER_H / 2)


def draw_background():
    for y in range(H):
        for x in range(W):
            # warm beige wall, soft light from upper left, gentle vignette
            dx = (x - 400) / 700.0
            dy = (y - 330) / 700.0
            light = max(0.0, 1.0 - 0.16 * (dx * dx + dy * dy))
            grain = (h2(x // 2, y // 2) - 0.5) * 0.028
            r = 0.905 * light + grain
            g = 0.835 * light + grain
            b = 0.700 * light + grain * 0.8
            set_px(x, y, r, g, b)


def draw_paper():
    # soft shadow: sample the sheet shape offset down-right, feathered
    for y in range(H):
        for x in range(W):
            u, v = to_paper(x - 13, y - 18)
            if 0 <= u < PAPER_W and 0 <= v < PAPER_H:
                edge = min(u, PAPER_W - u, v, PAPER_H - v)
                a = 0.34 if edge > 14 else 0.34 * (edge / 14.0)
                set_px(x, y, 0.36, 0.30, 0.22, a)
    for y in range(H):
        for x in range(W):
            u, v = to_paper(x, y)
            if 0 <= u < PAPER_W and 0 <= v < PAPER_H:
                grain = (h2(int(u) // 2, int(v) // 2) - 0.5) * 0.016
                r, g, b = 0.995 + grain, 0.985 + grain, 0.945 + grain
                # ruled lines
                lv = (v - 96) % 66
                if 0 <= lv < 2.4 and v > 90:
                    r, g, b = 0.62, 0.74, 0.90
                # red margin line
                if 56 <= u < 58.4:
                    r, g, b = 0.93, 0.55, 0.52
                # faint top holes shadow? no: a soft inner shade at edges
                edge = min(u, PAPER_W - u, v, PAPER_H - v)
                if edge < 10:
                    sh = 0.97 + 0.03 * (edge / 10.0)
                    r, g, b = r * sh, g * sh, b * sh
                set_px(x, y, r, g, b)


def draw_tape():
    def tape(cx_u, cy_v, ang, ln=128, wd=44, seed=0):
        ca, sa = math.cos(ang), math.sin(ang)
        # jagged rectangle (torn ends) in paper space
        pts = []
        for i in range(7):
            t = i / 6.0
            pts.append((-ln / 2 + ln * t, -wd / 2 + (h1(seed + i) - 0.5) * 7))
        for i in range(6, -1, -1):
            t = i / 6.0
            pts.append((-ln / 2 + ln * t, wd / 2 + (h1(seed + 40 + i) - 0.5) * 7))
        scr = []
        for (lx, ly) in pts:
            u = cx_u + lx * ca - ly * sa
            v = cy_v + lx * sa + ly * ca
            scr.append(to_screen(u, v))
        # fill by scanline over bbox with point-in-polygon
        xs = [p[0] for p in scr]
        ys = [p[1] for p in scr]
        for y in range(int(min(ys)) - 1, int(max(ys)) + 2):
            for x in range(int(min(xs)) - 1, int(max(xs)) + 2):
                inside = False
                j = len(scr) - 1
                for i in range(len(scr)):
                    xi, yi = scr[i]
                    xj, yj = scr[j]
                    if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                        inside = not inside
                    j = i
                if inside:
                    pu, pv = to_paper(x, y)
                    lx = (pu - cx_u) * ca + (pv - cy_v) * sa
                    fib = 0.03 * math.sin(lx * 1.7 + seed)
                    grain = (h2(x // 2, y // 2) - 0.5) * 0.03
                    a = 0.62
                    set_px(x, y, 0.93 + fib + grain, 0.845 + fib + grain, 0.60 + grain * 0.7, a)
    tape(66, 26, -0.62, seed=7)
    tape(PAPER_W - 66, 26, 0.62, seed=23)


def draw_heart(u, v, s, r, g, b, width=4.6):
    pts = []
    for i in range(41):
        t = i / 40.0 * 2 * math.pi
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append(to_screen(u + x * s, v - y * s))
    stroke(pts, width, r, g, b, 0.92)


def draw_cat():
    """A tiny crayon cat face doodled under the signature, same orange as the sun."""
    cu, cv = PAPER_W - 108, 672
    cx, cy = to_screen(cu, cv)
    orr, og, ob = 0.96, 0.62, 0.16
    R = 31
    # ears (behind the head circle)
    for sgn in (-1, 1):
        ex = cx + sgn * R * 0.62
        ey = cy - R * 0.78
        ear = [(ex - sgn * 13, ey + 12), (ex + sgn * 2, ey - 13), (ex + sgn * 14, ey + 9)]
        stroke(ear, 4.4, orr, og, ob, 0.9)
    # head
    ring = [(cx + R * math.cos(t), cy + R * math.sin(t)) for t in [i / 36 * 2 * math.pi for i in range(37)]]
    stroke(ring, 4.4, orr, og, ob, 0.92)
    # happy closed eyes: two shallow arcs
    for sgn in (-1, 1):
        ex = cx + sgn * R * 0.42
        ey = cy - R * 0.12
        arc = [(ex + dx, ey + 3.4 * (1 - (dx / 9.0) ** 2)) for dx in range(-9, 10, 3)]
        stroke(arc, 4.0, orr, og, ob, 0.95)
    # nose + mouth
    nose = [(cx - 4.5, cy + R * 0.18), (cx + 4.5, cy + R * 0.18), (cx, cy + R * 0.34), (cx - 4.5, cy + R * 0.18)]
    stroke(nose, 3.4, 0.90, 0.42, 0.40, 0.95)
    mouth = [(cx, cy + R * 0.34), (cx - 3, cy + R * 0.46), (cx - 7, cy + R * 0.42)]
    stroke(mouth, 3.2, orr, og, ob, 0.95)
    mouth2 = [(cx, cy + R * 0.34), (cx + 3, cy + R * 0.46), (cx + 7, cy + R * 0.42)]
    stroke(mouth2, 3.2, orr, og, ob, 0.95)
    # whiskers
    for sgn in (-1, 1):
        for k, dy in enumerate((-6, 0, 6)):
            stroke([(cx + sgn * R * 0.72, cy + R * 0.16 + dy * 0.7),
                    (cx + sgn * (R + 13), cy + R * 0.10 + dy)], 2.6, orr, og, ob, 0.75)
    # pink cheeks
    for sgn in (-1, 1):
        stamp(cx + sgn * R * 0.58, cy + R * 0.34, 6.5, 0.96, 0.55, 0.55, 0.35)


def draw_note():
    ink = (0.16, 0.22, 0.58)  # ballpoint blue
    scale = 2.18
    x0 = 86          # first baseline column, paper coords
    line_h = 66
    first_base = 96 + 47
    for li, line in enumerate(LINES):
        base_v = first_base + li * line_h
        cx = x0
        for ci, ch in enumerate(line):
            adv, strokes = GLYPHS[ch]
            seed = li * 131 + ci * 17
            wob_y = (h1(seed + 1) - 0.5) * 3.4
            wob_r = (h1(seed + 2) - 0.5) * 0.055
            wob_s = 0.96 + h1(seed + 3) * 0.09
            cr, sr = math.cos(wob_r), math.sin(wob_r)
            for st in strokes:
                pts = []
                for (gx, gy) in st:
                    lx = (gx - 10) * scale * wob_s
                    ly = (gy - 17) * scale * wob_s
                    rx = lx * cr - ly * sr
                    ry = lx * sr + ly * cr
                    pts.append(to_screen(cx + 10 * scale + rx, base_v + wob_y + ry))
                stroke(pts, 5.9, ink[0], ink[1], ink[2], 0.94)
            cx += adv * scale * wob_s
        if li == len(LINES) - 1:
            draw_heart(cx + 26, base_v - 16, 0.85, 0.88, 0.30, 0.34)
    # a tiny crayon sun in the top-right corner of the note
    su, sv = PAPER_W - 92, 92
    cx, cy = to_screen(su, sv)
    orr, og, ob = 0.96, 0.62, 0.16
    ring = [(cx + 21 * math.cos(t), cy + 21 * math.sin(t)) for t in [i / 24 * 2 * math.pi for i in range(25)]]
    stroke(ring, 4.2, orr, og, ob, 0.9)
    for k in range(8):
        a = k / 8 * 2 * math.pi + 0.2
        stroke([(cx + 27 * math.cos(a), cy + 27 * math.sin(a)),
                (cx + 36 * math.cos(a), cy + 36 * math.sin(a))], 4.2, orr, og, ob, 0.9)


# --------------------------------------------------------------------- png

def write_png(path):
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        for x in range(W):
            i = (y * W + x) * 3
            for c in range(3):
                v = PX[i + c]
                raw.append(0 if v < 0 else 255 if v > 1 else int(v * 255 + 0.5))
    comp = zlib.compress(bytes(raw), 6)

    def chunk(typ, data):
        c = struct.pack(">I", len(data)) + typ + data
        return c + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


def main():
    draw_background()
    draw_paper()
    draw_note()
    draw_cat()
    draw_tape()
    out = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out, exist_ok=True)
    write_png(os.path.join(out, "entry.png"))


if __name__ == "__main__":
    main()
