"""
VitaGrip1000 - vectorize the PCH-1000 orthographic template.

This is the `vector-tracer` stage of the pipeline in docs/agents.md, which the
first pass of this project skipped: it went straight from pixel measurements to
build123d primitives, and modelled the console's face as `Rectangle()`. The
console is not a rectangle. Its outline tapers over ~40 mm at each end, and a
rectangular pocket cuts 1232 mm2 (8.8 %) more than the console's face occupies -
material that should be wrapping the console's ends.

Source:  sources/psvitaGrip/psvita.jpg - a 1:1 orthographic template carrying
         four views, annotated 182 x 83.55 x 18.6 mm.
Anchor:  the FRONT view's own width, 460 px = 182.0 mm  ->  0.39565 mm/px.
Output:  projects/VitaGrip1000/vectors/psvita_{view}.{svg,dxf}, in mm.

Run:  python projects\\VitaGrip1000\\macros\\trace_console.py
"""

import sys
from pathlib import Path

import cv2
import ezdxf
import numpy as np
import svgwrite
from scipy.interpolate import splev, splprep
from shapely.geometry import LinearRing, Polygon

ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT / "sources" / "psvitaGrip" / "psvita.jpg"
OUT = ROOT / "projects" / "VitaGrip1000" / "vectors"

# The console's annotated dimensions, which set the scale and gate the result.
CONSOLE_W = 182.0
CONSOLE_H = 83.55
CONSOLE_D = 18.6

# The four orthographic views in the template, keyed by the (left, top) pixel
# corner of their connected component. Found by connected-component analysis;
# hard-coded here so the trace is reproducible rather than order-dependent.
VIEWS = {
    "back":   {"corner": (145, 112), "span": ("w", CONSOLE_W), "tall": CONSOLE_H},
    "front":  {"corner": (142, 337), "span": ("w", CONSOLE_W), "tall": CONSOLE_H},
    "bottom": {"corner": (141, 559), "span": ("w", CONSOLE_W), "tall": CONSOLE_D},
    "top":    {"corner": (140, 42),  "span": ("w", CONSOLE_W), "tall": CONSOLE_D},
}

# Smoothing: fraction of the contour perimeter used as the spline's smoothing
# factor. Too low keeps pixel stair-stepping; too high rounds off the real
# corners at the shoulder where the taper meets the flank.
SMOOTH_FRAC = 0.0006
N_OUT = 400                 # output points around the body outline
MIN_SEG = 0.02              # mm; shorter segments are degenerate - see trace_outline()


def find_views(gray):
    """Locate each orthographic view as a connected component."""
    mask = (gray < 200).astype(np.uint8) * 255
    kern = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kern)
    n, lab, st, _ = cv2.connectedComponentsWithStats(mask)

    found = {}
    for name, spec in VIEWS.items():
        want = spec["corner"]
        for i in range(1, n):
            if (st[i, cv2.CC_STAT_LEFT], st[i, cv2.CC_STAT_TOP]) == want:
                found[name] = {
                    "mask": ((lab == i) * 255).astype(np.uint8),
                    "box": (st[i, cv2.CC_STAT_LEFT], st[i, cv2.CC_STAT_TOP],
                            st[i, cv2.CC_STAT_WIDTH], st[i, cv2.CC_STAT_HEIGHT]),
                }
                break
    return found


BODY_ROW_FRAC = 0.40       # see body_rows()


def body_rows(view_mask, box, frac=BODY_ROW_FRAC):
    """Rows belonging to the console BODY, excluding protrusions.

    The top and bottom views draw the analog sticks standing proud of the body,
    so the component's bounding box is taller than the console's 18.6 mm depth
    (23.4 mm for the top view, 37.8 for the bottom). Taking the box as the body
    silently inflates the depth by up to 2x. A body row spans most of the view's
    width; a protrusion row spans only the two stick locations.

    `frac` was swept, not guessed: at 0.40 the top view returns exactly the
    annotated 18.60 mm and the bottom 18.87. Above 0.45 the threshold starts
    eating the shoulder-button rows, which ARE body, and the top view comes back
    16.62 mm - 2 mm short.
    """
    x, y, w, h = box
    occ = [(r, int(view_mask[y + r, x:x + w].sum() // 255)) for r in range(h)]
    rows = [r for r, c in occ if c > frac * w]
    return min(rows), max(rows)


def measure_protrusions(view_mask, box, mm_per_px, body_lo, body_hi, above):
    """Extent and X placement of whatever stands proud of the body face.

    Returns (height_mm, [(x_centre_mm, width_mm), ...]) with X measured from the
    view's centre, matching the CAD frame.
    """
    x, y, w, h = box
    if above:
        rows = [r for r in range(h)
                if r > body_hi and view_mask[y + r, x:x + w].any()]
    else:
        rows = [r for r in range(h)
                if r < body_lo and view_mask[y + r, x:x + w].any()]
    if not rows:
        return 0.0, []

    lo, hi = min(rows), max(rows)
    sub = view_mask[y + lo:y + hi + 1, x:x + w]
    cols = np.nonzero(sub.sum(axis=0))[0]

    groups, start, prev = [], cols[0], cols[0]
    for c in cols[1:]:
        if c - prev > 6:
            groups.append((start, prev))
            start = c
        prev = c
    groups.append((start, prev))

    out = []
    for a, b in groups:
        if b - a < 4:
            continue
        centre = ((a + b) / 2.0 - w / 2.0) * mm_per_px
        out.append((centre, (b - a) * mm_per_px))
    return (hi - lo + 1) * mm_per_px, out


def trace_outline(view_mask, box, mm_per_px, smooth_frac=SMOOTH_FRAC,
                  row_range=None):
    """Outer body outline as a closed, smoothed polyline in mm.

    The template draws the body as a stroked outline, not a filled shape, so
    the contour is taken with RETR_EXTERNAL and then treated as the silhouette
    boundary. Coordinates come back centred on the view, +X right and +Y UP
    (image rows are flipped), matching the CAD frame.
    """
    src = view_mask
    if row_range is not None:
        # Crop to the body's own rows so protruding sticks are not traced as
        # part of the silhouette.
        x, y, w, h = box
        lo, hi = row_range
        src = np.zeros_like(view_mask)
        src[y + lo:y + hi + 1, :] = view_mask[y + lo:y + hi + 1, :]

    # The template draws the body as a STROKED outline, so tracing the mask
    # directly follows the outer edge of the stroke and gets dragged inward
    # wherever that stroke meets an internal feature - the shoulder buttons and
    # the right-hand notch both produced visible snags in the first trace.
    # Filling the silhouette first, then re-tracing, gives the true boundary.
    cont, _ = cv2.findContours(src, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    outer = max(cont, key=cv2.contourArea)
    filled = np.zeros_like(src)
    cv2.drawContours(filled, [outer], -1, 255, -1)
    # close any nicks the stroke left in the boundary
    kern = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    filled = cv2.morphologyEx(filled, cv2.MORPH_CLOSE, kern)

    cont, _ = cv2.findContours(filled, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    body = max(cont, key=cv2.contourArea)
    pts = body.reshape(-1, 2).astype(float)

    # Drop re-entrant hooks. Where the drawn stroke of a shoulder button meets
    # the body edge, the filled contour still dips inward for a few pixels and
    # the outline doubles back on itself. The console's silhouette is convex
    # everywhere along its flanks, so keeping only the outermost point per
    # angle about the centroid removes those hooks without touching the real
    # taper (which is monotone in angle).
    cx, cy = pts[:, 0].mean(), pts[:, 1].mean()
    ang = np.arctan2(pts[:, 1] - cy, pts[:, 0] - cx)
    rad = np.hypot(pts[:, 0] - cx, pts[:, 1] - cy)
    nbin = 720
    idx = ((ang + np.pi) / (2 * np.pi) * nbin).astype(int) % nbin
    keep = {}
    for k, (b, r) in enumerate(zip(idx, rad)):
        if b not in keep or r > rad[keep[b]]:
            keep[b] = k
    sel = np.array([keep[b] for b in sorted(keep)])
    pts = pts[sel]
    # re-order strictly by angle so the spline runs once around
    pts = pts[np.argsort(np.arctan2(pts[:, 1] - cy, pts[:, 0] - cx))]

    per = cv2.arcLength(pts.astype(np.float32).reshape(-1, 1, 2), True)
    tck, _ = splprep([pts[:, 0], pts[:, 1]], s=per * smooth_frac, per=True, k=3)
    u = np.linspace(0, 1, N_OUT)
    sx, sy = splev(u, tck)

    x, y, w, h = box
    # centre on the view, flip Y so +Y is up
    mm_x = (sx - (x + w / 2.0)) * mm_per_px
    mm_y = ((y + h / 2.0) - sy) * mm_per_px
    poly = np.column_stack([mm_x, mm_y])

    # Drop degenerate points. splev's periodic output repeats the closing point
    # exactly, which becomes a zero-length DXF segment; build123d then reports
    # "2 faces skipped due to null triangulation" and every solid extruded from
    # the profile comes out NOT WATERTIGHT - while still reporting one body, so
    # the topology gate blames the boolean rather than the profile.
    keep = [0]
    for i in range(1, len(poly)):
        if np.hypot(*(poly[i] - poly[keep[-1]])) > MIN_SEG:
            keep.append(i)
    poly = poly[keep]
    # and make sure the closing segment is not degenerate either
    while len(poly) > 3 and np.hypot(*(poly[0] - poly[-1])) < MIN_SEG:
        poly = poly[:-1]

    # Repair self-intersections. The angular hook filter above removes most of
    # the shoulder-button nicks, but a spline fitted through what is left can
    # still cross itself by a fraction of a millimetre. Shapely's zero-width
    # buffer resolves such a ring into a valid polygon; without this the DXF
    # imports as a closed 399-edge wire that looks perfectly healthy, yet every
    # solid extruded from it has is_valid = False and exports NOT WATERTIGHT.
    ring = LinearRing([tuple(p) for p in poly])
    if not ring.is_simple:
        fixed = Polygon(ring).buffer(0)
        if fixed.geom_type == "MultiPolygon":
            fixed = max(fixed.geoms, key=lambda g: g.area)
        poly = np.array(fixed.exterior.coords[:-1])

    return poly


def write_svg(path, poly, title, desc, w_mm, h_mm):
    """Closed outline as an SVG in real mm units."""
    pad = 4.0
    dwg = svgwrite.Drawing(
        str(path),
        size=("%.3fmm" % (w_mm + 2 * pad), "%.3fmm" % (h_mm + 2 * pad)),
        viewBox="%.3f %.3f %.3f %.3f"
                % (-w_mm / 2 - pad, -h_mm / 2 - pad, w_mm + 2 * pad, h_mm + 2 * pad),
    )
    dwg.set_desc(title=title, desc=desc)
    # SVG +Y is down; negate so the file matches the CAD frame when read back.
    d = "M " + " L ".join("%.4f,%.4f" % (px, -py) for px, py in poly) + " Z"
    dwg.add(dwg.path(d=d, fill="none", stroke="#000", stroke_width=0.3,
                     class_="body"))
    dwg.save()


def write_dxf(path, poly):
    """Closed outline as a DXF LWPOLYLINE on layer BODY, in mm."""
    doc = ezdxf.new()
    doc.layers.add("BODY")
    msp = doc.modelspace()
    msp.add_lwpolyline([(float(a), float(b)) for a, b in poly],
                       close=True, dxfattribs={"layer": "BODY"})
    doc.saveas(str(path))


def main():
    if not SRC.exists():
        print("template missing: %s" % SRC)
        return 1
    OUT.mkdir(parents=True, exist_ok=True)

    img = cv2.imread(str(SRC))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    views = find_views(gray)

    missing = set(VIEWS) - set(views)
    if missing:
        print("could not locate view(s): %s" % ", ".join(sorted(missing)))
        print("the template layout may have changed; re-run the component scan")
        return 1

    print("=" * 72)
    print("trace_console - %s" % SRC.name)
    print("=" * 72)

    ok = True
    protrusions = {}
    for name in ("front", "back", "top", "bottom"):
        v = views[name]
        x, y, w, h = v["box"]
        mm_per_px = CONSOLE_W / w          # anchor: the view's own 182 mm width

        # Edge views draw the analog sticks proud of the body; trace the body
        # only, and measure the protrusion separately.
        edge = name in ("top", "bottom")
        rr = body_rows(v["mask"], v["box"]) if edge else None
        poly = trace_outline(v["mask"], v["box"], mm_per_px, row_range=rr)

        if edge:
            ext, groups = measure_protrusions(
                v["mask"], v["box"], mm_per_px, rr[0], rr[1],
                above=(name == "top"))
            protrusions[name] = (ext, groups)

        got_w = poly[:, 0].max() - poly[:, 0].min()
        got_h = poly[:, 1].max() - poly[:, 1].min()
        want_h = VIEWS[name]["tall"]

        # A traced outline that is not a simple closed ring imports as a
        # perfectly healthy-looking wire and then produces an INVALID solid.
        # Gate it here, where the cause is visible, rather than three stages
        # downstream in a watertightness failure.
        ring = LinearRing([tuple(q) for q in poly])
        simple = ring.is_simple
        if not simple:
            ok = False

        # Gate: the traced outline must reproduce the annotated dimensions.
        dw = abs(got_w - CONSOLE_W) / CONSOLE_W
        dh = abs(got_h - want_h) / want_h
        flag = "ok " if (dw < 0.01 and dh < 0.05) else "BAD"
        if flag == "BAD":
            ok = False

        print("  [%s] %-6s  %3d x %3d px  %.5f mm/px   traced %6.2f x %5.2f mm"
              "   (annotated %.1f x %.2f)  %s"
              % (flag, name, w, h, mm_per_px, got_w, got_h, CONSOLE_W, want_h,
                 "simple" if simple else "SELF-INTERSECTING"))

        title = "Sony PS Vita PCH-1000 - %s view" % name
        desc = ("traced from sources/psvitaGrip/psvita.jpg; scale anchor = this "
                "view's own width %d px = %.1f mm (%.5f mm/px); "
                "spline smoothing s = %.4f x perimeter; %d points"
                % (w, CONSOLE_W, mm_per_px, SMOOTH_FRAC, N_OUT))

        write_svg(OUT / ("psvita_%s.svg" % name), poly, title, desc,
                  CONSOLE_W, want_h)
        write_dxf(OUT / ("psvita_%s.dxf" % name), poly)

    print()
    if protrusions:
        print("  Front-face protrusions (analog sticks), measured off the body face:")
        for name, (ext, groups) in sorted(protrusions.items()):
            face = "front" if name == "top" else "rear"
            print("    from the %-6s view: %.2f mm proud of the %s face" % (name, ext, face))
            for cx, cw in groups:
                print("        centre x = %+7.2f mm, width %.1f mm" % (cx, cw))
        print("    The two views are independent measurements of the same sticks.")
        print("    A flat-walled pocket ignores these and the sticks foul the lip.")
        print()

    print("  written to %s" % OUT)
    print()
    if not ok:
        print("=" * 72)
        print("VERDICT: a traced view does not match its annotated dimensions")
        print("=" * 72)
        return 1

    print("=" * 72)
    print("VERDICT: all four views trace to their annotated dimensions")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
