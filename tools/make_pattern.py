"""Generate the seamless embossed-swirl background tiles (light and dark).

Mimics the textured wallpaper behind the portrait: short tapered strokes that
follow a swirling flow field, drawn as a highlight (top-left) and a shadow
(bottom-right) so they read as raised ridges. The flow field uses whole-number
frequencies, so the tile wraps seamlessly.

Run from the repo root:  python3 tools/make_pattern.py
"""
import math
import random

T = 360           # tile size in px
SEED = 3
STEP = 2.0        # streamline step length
CELL = 5          # spacing grid; keeps strokes from piling up
MIN_LEN, MAX_LEN = 16, 64   # stroke length in steps
WIDTH = 3.0       # max stroke width

rng = random.Random(SEED)
waves = []
for _ in range(6):
    fx, fy = rng.randint(-2, 2), rng.randint(-2, 2)
    if fx == 0 and fy == 0:
        fx = 1
    waves.append((fx, fy, rng.uniform(0, 2 * math.pi), rng.uniform(0.6, 1.0)))


def angle(x, y):
    """Direction along the contour lines of a periodic 'height' function.

    Following contours (rather than a free angle field) means strokes never
    converge into sinks: they run in parallel bundles and curl round centres.
    """
    gx = gy = 0.0
    for fx, fy, ph, amp in waves:
        c = amp * math.cos(2 * math.pi * (fx * x + fy * y) / T + ph)
        gx += c * fx
        gy += c * fy
    return math.atan2(-gx, gy)


G = T // CELL
occupied = {}


def cell(x, y):
    return (int(x % T // CELL) % G, int(y % T // CELL) % G)


def trace(x, y, sid, curl):
    pts = [(x, y)]
    for direction in (1, -1):
        cx, cy = x, y
        seg = []
        prev = None
        for k in range(MAX_LEN // 2):
            a = angle(cx % T, cy % T) + direction * curl * k
            if prev is not None:
                turn = (a - prev + math.pi) % (2 * math.pi) - math.pi
                if abs(turn) > 0.45:  # too sharp: would fold the ribbon
                    break
            prev = a
            nx, ny = cx + direction * STEP * math.cos(a), cy + direction * STEP * math.sin(a)
            owner = occupied.get(cell(nx, ny))
            if owner is not None and owner != sid:
                break
            seg.append((nx, ny))
            cx, cy = nx, ny
        if direction == 1:
            pts = pts + seg
        else:
            pts = list(reversed(seg)) + pts
    return pts


def ribbon(pts):
    """Tapered closed outline around a polyline."""
    n = len(pts)
    left, right = [], []
    for i, (x, y) in enumerate(pts):
        x0, y0 = pts[max(i - 1, 0)]
        x1, y1 = pts[min(i + 1, n - 1)]
        dx, dy = x1 - x0, y1 - y0
        d = math.hypot(dx, dy) or 1
        nx, ny = -dy / d, dx / d
        w = WIDTH / 2 * max(0.0, math.sin(math.pi * i / (n - 1))) ** 0.7
        left.append((x + nx * w, y + ny * w))
        right.append((x - nx * w, y - ny * w))
    outline = left + list(reversed(right))
    return "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in outline) + "Z"


strokes = []
seeds = [(rng.uniform(0, T), rng.uniform(0, T)) for _ in range(12000)]
for sid, (sx, sy) in enumerate(seeds):
    if cell(sx, sy) in occupied:
        continue
    pts = trace(sx, sy, sid, rng.uniform(-0.025, 0.025))
    if len(pts) < MIN_LEN:
        continue
    for px, py in pts:
        occupied.setdefault(cell(px, py), sid)
    strokes.append(pts[::2] if len(pts) % 2 else pts[::2] + [pts[-1]])

paths = []
for pts in strokes:
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    for ox in (-T, 0, T):
        for oy in (-T, 0, T):
            if max(xs) + ox < -WIDTH or min(xs) + ox > T + WIDTH:
                continue
            if max(ys) + oy < -WIDTH or min(ys) + oy > T + WIDTH:
                continue
            paths.append(ribbon([(x + ox, y + oy) for x, y in pts]))

d = "".join(paths)


def svg(highlight, shadow):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{T}" height="{T}" viewBox="0 0 {T} {T}">'
        f'<defs><path id="s" d="{d}"/></defs>'
        f'<use href="#s" x="1.1" y="1.1" fill="{shadow}"/>'
        f'<use href="#s" x="-0.9" y="-0.9" fill="{highlight}"/>'
        "</svg>"
    )


with open("assets/img/pattern-light.svg", "w") as f:
    f.write(svg("rgba(255,255,255,0.6)", "rgba(15,58,51,0.05)"))
with open("assets/img/pattern-dark.svg", "w") as f:
    f.write(svg("rgba(255,255,255,0.03)", "rgba(0,0,0,0.26)"))
print(len(strokes), "strokes,", len(paths), "paths")
