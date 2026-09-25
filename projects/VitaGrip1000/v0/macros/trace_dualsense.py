"""
trace_dualsense.py - the vector-tracer stage for the GRIP itself.

This is the stage VitaGrip1000's first pass skipped. That pass traced the
CONSOLE (trace_console.py) and then built the grip's handles from eyeballed
photo pixels straight into a build123d loft: a hand-typed HANDLE_RAKE = 5.9 deg
that the built solid delivered as 1.6 deg, against a sketch asking for a
pronounced DualSense hook. Importing a vector of a MATING part does not satisfy
the vector stage for the part being designed.

Source:  sources/psvitaGrip/dualsenseDiagram.svg - an Illustrator export of a
         dimensioned orthographic three-view of the PS5 DualSense, annotated
         160 mm wide / 106 mm tall / 66 mm deep.
Anchor:  the front view's own 160 mm width.
Gate:    every view is checked against its annotated dimension, and the two
         independent anchors (width, height) must agree.
Output:  projects/VitaGrip1000/vectors/dualsense_{front,side,top}.{svg,dxf}, mm.
"""

import re
import sys
from pathlib import Path

import ezdxf
import numpy as np
import svgwrite
from shapely.geometry import LinearRing

ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT / "sources" / "psvitaGrip" / "dualsenseDiagram.svg"
OUT = Path(__file__).resolve().parents[1] / "vectors"

# Annotated on the drawing itself.
DS_WIDTH = 160.0
DS_HEIGHT = 106.0
DS_DEPTH = 66.0

ANCHOR_TOL = 0.01      # the two scale anchors must agree to 1 %
VIEW_TOL = 1.5         # a view must reproduce its annotated dim to 1.5 mm

TOKEN = re.compile(r"([MmLlHhVvCcSsQqTtAaZz])|(-?\d*\.?\d+(?:[eE][-+]?\d+)?)")
BEZ_STEPS = 24


def _bezier(p0, p1, p2, p3, n=BEZ_STEPS):
    t = np.linspace(0, 1, n)[:, None]
    return ((1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1
            + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3)


def parse_path(d):
    """Flatten one SVG path's `d` attribute into polylines.

    Relative commands are the trap here: reading the coordinate stream without
    tracking the current point produces a plausible-looking tangle, which is
    what a first attempt at this file did.
    """
    toks = []
    for m in TOKEN.finditer(d):
        toks.append(m.group(1) if m.group(1) else float(m.group(2)))

    subs, cur = [], []
    x = y = sx = sy = 0.0
    i, cmd = 0, None
    while i < len(toks):
        if isinstance(toks[i], str):
            cmd = toks[i]
            i += 1
            continue
        if cmd in "Mm":
            nx, ny = toks[i], toks[i + 1]
            i += 2
            if cmd == "m":
                nx, ny = nx + x, ny + y
            if cur:
                subs.append(np.array(cur))
            x, y = nx, ny
            sx, sy = x, y
            cur = [(x, y)]
            cmd = "L" if cmd == "M" else "l"
        elif cmd in "Ll":
            nx, ny = toks[i], toks[i + 1]
            i += 2
            if cmd == "l":
                nx, ny = nx + x, ny + y
            x, y = nx, ny
            cur.append((x, y))
        elif cmd in "Hh":
            nx = toks[i]
            i += 1
            x = nx + x if cmd == "h" else nx
            cur.append((x, y))
        elif cmd in "Vv":
            ny = toks[i]
            i += 1
            y = ny + y if cmd == "v" else ny
            cur.append((x, y))
        elif cmd in "Cc":
            c = list(toks[i:i + 6])
            i += 6
            if cmd == "c":
                c = [c[0] + x, c[1] + y, c[2] + x, c[3] + y, c[4] + x, c[5] + y]
            pts = _bezier(np.array([x, y]), np.array(c[0:2]),
                          np.array(c[2:4]), np.array(c[4:6]))
            cur.extend(map(tuple, pts[1:]))
            x, y = c[4], c[5]
        elif cmd in "Ss":
            c = list(toks[i:i + 4])
            i += 4
            if cmd == "s":
                c = [c[0] + x, c[1] + y, c[2] + x, c[3] + y]
            pts = _bezier(np.array([x, y]), np.array([x, y]),
                          np.array(c[0:2]), np.array(c[2:4]))
            cur.extend(map(tuple, pts[1:]))
            x, y = c[2], c[3]
        elif cmd in "Zz":
            cur.append((sx, sy))
            subs.append(np.array(cur))
            cur = [(sx, sy)]
            x, y = sx, sy
            cmd = None
        else:
            i += 1
    if cur:
        subs.append(np.array(cur))
    return [s for s in subs if len(s) > 1]


def load_subpaths(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    out = []
    for d in re.findall(r'\sd="([^"]+)"', text):
        out.extend(parse_path(d))
    return out


def pick_views(subs):
    """The three view outlines are the largest closed subpaths.

    Front and top share the drawing's left column; the side view sits right of
    them. Classify by bounding box rather than by index, so an edit to the
    source file that reorders paths does not silently pick the wrong curve.
    """
    big = [(s, s[:, 0].max() - s[:, 0].min(), s[:, 1].max() - s[:, 1].min())
           for s in subs]
    big = [b for b in big if b[1] > 150 and b[2] > 100]
    if not big:
        return {}

    widest = max(big, key=lambda b: b[1])
    left_x = widest[0][:, 0].min()

    front = max((b for b in big if b[0][:, 0].min() < left_x + 50
                 and b[0][:, 1].min() < 300),
                key=lambda b: b[1] * b[2], default=None)
    top = max((b for b in big if b[0][:, 0].min() < left_x + 50
               and b[0][:, 1].min() >= 300),
              key=lambda b: b[1] * b[2], default=None)
    side = max((b for b in big if b[0][:, 0].min() > left_x + 300),
               key=lambda b: b[1] * b[2], default=None)

    views = {}
    for name, b in (("front", front), ("top", top), ("side", side)):
        if b is not None:
            views[name] = b[0]
    return views


def write_svg(pts, path):
    w = pts[:, 0].max() - pts[:, 0].min()
    h = pts[:, 1].max() - pts[:, 1].min()
    dwg = svgwrite.Drawing(str(path), size=("%.3fmm" % w, "%.3fmm" % h),
                           viewBox="%.3f %.3f %.3f %.3f"
                                   % (pts[:, 0].min(), pts[:, 1].min(), w, h))
    dwg.add(dwg.polygon([(float(a), float(b)) for a, b in pts],
                        fill="none", stroke="black", stroke_width=0.3))
    dwg.save()


def write_dxf(pts, path):
    doc = ezdxf.new("R2010")
    doc.units = ezdxf.units.MM
    msp = doc.modelspace()
    msp.add_lwpolyline([(float(a), float(b)) for a, b in pts], close=True)
    doc.saveas(str(path))


def main():
    if not SRC.exists():
        print("source missing: %s" % SRC)
        return 1

    subs = load_subpaths(SRC)
    views = pick_views(subs)
    missing = {"front", "side", "top"} - set(views)
    if missing:
        print("could not locate view(s): %s" % ", ".join(sorted(missing)))
        return 1

    print("trace_dualsense - %s" % SRC.name)
    print("  %d subpaths, 3 views located" % len(subs))

    fr = views["front"]
    fw = fr[:, 0].max() - fr[:, 0].min()
    fh = fr[:, 1].max() - fr[:, 1].min()
    s_w = DS_WIDTH / fw
    s_h = DS_HEIGHT / fh
    drift = abs(s_w - s_h) / s_w
    print("  scale from width  %.5f mm/px" % s_w)
    print("  scale from height %.5f mm/px" % s_h)
    print("  anchors agree to %.2f %%" % (drift * 100))
    if drift > ANCHOR_TOL:
        print("  FAIL: the two scale anchors disagree; the drawing is not "
              "orthographic or a view was mis-picked")
        return 1
    scale = s_w

    OUT.mkdir(parents=True, exist_ok=True)
    expected = {"front": (DS_WIDTH, DS_HEIGHT),
                "side": (DS_DEPTH, DS_HEIGHT),
                "top": (DS_WIDTH, None)}

    ok = True
    for name in ("front", "side", "top"):
        pts = views[name].astype(float).copy()
        pts[:, 0] = (pts[:, 0] - pts[:, 0].min()) * scale
        pts[:, 1] = (pts[:, 1].max() - pts[:, 1]) * scale   # +Y up
        w = pts[:, 0].max()
        h = pts[:, 1].max()

        exp_w, exp_h = expected[name]
        flags = []
        if exp_w is not None and abs(w - exp_w) > VIEW_TOL:
            flags.append("width %.1f != %.1f" % (w, exp_w))
        if exp_h is not None and abs(h - exp_h) > VIEW_TOL:
            flags.append("height %.1f != %.1f" % (h, exp_h))

        ring = LinearRing(pts)
        if not ring.is_simple:
            flags.append("self-intersecting ring")

        status = "ok" if not flags else "FAIL: " + "; ".join(flags)
        print("  %-6s %7.2f x %7.2f mm   %s" % (name, w, h, status))
        if flags:
            ok = False
            continue

        write_svg(pts, OUT / ("dualsense_%s.svg" % name))
        write_dxf(pts, OUT / ("dualsense_%s.dxf" % name))

    if not ok:
        print("  gates failed; vectors for failing views were not written")
        return 1

    print("  wrote dualsense_{front,side,top}.{svg,dxf} to %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
