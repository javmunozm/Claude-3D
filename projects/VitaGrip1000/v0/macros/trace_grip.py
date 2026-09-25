"""
trace_grip.py - the grip's own geometry, measured from the product photograph.

WHY THIS FILE WAS REWRITTEN (2026-09-02)
----------------------------------------
The previous version traced `BackView.png`, a 200 x 121 px line drawing, and
its own docstring listed five different tracing failures on it. It settled on
a grid-square method that produced `vitagrip_front.dxf`: 223.3 x 104.6 mm
bounding box - correct - enclosing only **6,211 mm2** of area. The console
alone is 13,984 mm2. The "grip" was 44 % of the area of the object it wraps
around: the trace had captured the drawing's lit RIM, not its filled body.

Every gate passed, because every gate checked the bounding box, and the
bounding box of a rim is the bounding box of the part.

This version traces `054-1.webp` (960 x 960, straight-on rear view, saturated
blue against white) by HSV colour segmentation. A colour mask cannot return a
rim: it returns the filled region or nothing. Result: 10,434 mm2, one
connected component, fill ratio 0.409 - the signature of a U.

  resolution   200x121  ->  960x960   (4.8x linear)
  method       grey threshold + grid  ->  HSV colour segmentation
  area         6,211 mm2  ->  10,434 mm2

Scale: the console's own 182 mm width, unoccluded at image row y=275 (31 blue
pixels in that row). 737 px -> 0.24695 mm/px.

  The console's HEIGHT is NOT a usable anchor in this view and is not used:
  the grip's cross-bar occludes the console's lower 21.5 mm, so the dark blob
  measures 63.22 mm against the true 83.55. Measuring it and dividing would
  have given a scale 32 % wrong. This is recorded because the number is
  reachable and looks plausible.

Outputs (mm, console-centred: X across, Y up, +Y toward the console's top):
  vitagrip_front.{svg,dxf}     the grip's filled plan outline
  vitagrip_section.{svg,dxf}   the C-section that wraps the console's edge

and, for the builder, two measured profiles returned as arrays:
  handle_plan_profile()        half-width against height, from 054-1.webp
  handle_depth_profile()       depth against height, from lateralHAndleview.jpg

DEPTH SOURCE CHANGED 2026-09-02: was dualsense_side.dxf, now the grip's own
orthographic lateral. The DualSense drawing is verified but is the wrong
OBJECT - it carries the controller body, so its depth grows monotonically to
45 mm where the real handle necks down to 17 mm. See handle_depth_profile().
"""

import sys
from pathlib import Path

import cv2
import ezdxf
import numpy as np
import svgwrite
from shapely.geometry import LinearRing, LineString, Polygon

ROOT = Path(__file__).resolve().parents[4]
OUT_DIR = Path(__file__).resolve().parents[1]
VEC = OUT_DIR / "vectors"
SRC = ROOT / "sources" / "psvitaGrip" / "054-1.webp"
DS_FRONT = VEC / "dualsense_front.dxf"
DS_SIDE = VEC / "dualsense_side.dxf"

CONSOLE_W, CONSOLE_H, CONSOLE_D = 182.0, 83.55, 18.6
HALF_W, HALF_H, HALF_D = CONSOLE_W / 2, CONSOLE_H / 2, CONSOLE_D / 2

# Expected, from handle-back.jpg with an independent anchor. Used as a GATE,
# not as an input - the trace must arrive here on its own.
EXPECT_W, EXPECT_H = 223.3, 112.4
ENVELOPE_TOL = 0.03          # 3 %

# The blue grip against white. Wide enough to hold the shaded flank, tight
# enough to exclude the console's blue-grey highlights.
HSV_LO = (95, 110, 60)
HSV_HI = (130, 255, 255)

# A U-shaped part fills far less of its bounding box than a blob does. The old
# rim trace scored 0.19; a filled-in solid block scores > 0.75.
FILL_LO, FILL_HI = 0.30, 0.60


# ---------------------------------------------------------------- the mask ---
def grip_mask():
    """The grip as a filled binary mask, plus its stats. One component."""
    im = cv2.imread(str(SRC))
    if im is None:
        raise SystemExit("cannot read %s" % SRC)
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    m = cv2.inRange(hsv, np.array(HSV_LO), np.array(HSV_HI))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))

    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    if n < 2:
        raise SystemExit("colour segmentation found no grip")
    g = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    mask = (lab == g).astype(np.uint8)
    x, y, w, h = (int(st[g, i]) for i in range(4))
    fill = st[g, cv2.CC_STAT_AREA] / float(w * h)

    # A rim would come back as several components or as a very low fill; a
    # flood-filled block as a very high one. Gate both.
    big = int((st[1:, cv2.CC_STAT_AREA] > 500).sum())
    if big != 1:
        raise SystemExit("expected 1 grip component, found %d" % big)
    if not (FILL_LO <= fill <= FILL_HI):
        raise SystemExit(
            "fill ratio %.3f outside [%.2f,%.2f] - a rim or a filled block, "
            "not a U" % (fill, FILL_LO, FILL_HI))
    return mask, (x, y, w, h), fill


def console_scale(mask_bbox):
    """mm/px, from the console's 182 mm width where the bar does not cover it.

    Returns (scale, diagnostics). The console is the dark low-saturation blob;
    its widest row is the unoccluded one.
    """
    _, _, w_px, h_px, _ = _console_blob()
    scale = CONSOLE_W / w_px
    return scale, (w_px, h_px, h_px * scale)


# --------------------------------------------------------------- profiles ---
def _console_blob():
    """Stats of the console's dark blob: (x, y, w, h, cx)."""
    im = cv2.imread(str(SRC))
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    dark = (((hsv[:, :, 2] < 110) & (hsv[:, :, 1] < 160)).astype(np.uint8) * 255)
    dark = cv2.morphologyEx(dark, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(dark, 8)
    i = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    return (int(st[i, 0]), int(st[i, 1]), int(st[i, 2]), int(st[i, 3]),
            st[i, 0] + st[i, 2] / 2.0)


def _console_top_px():
    return _console_blob()[1]


def _row_runs(mask, yy, gap=3):
    xs = np.where(mask[yy])[0]
    if len(xs) == 0:
        return []
    brk = np.where(np.diff(xs) > gap)[0]
    out = []
    for r in np.split(xs, brk + 1):
        if r[-1] - r[0] > 3:
            out.append((int(r[0]), int(r[-1])))
    return out


def handle_plan_profile(n=28, with_y=False):
    """Left handle half-width and centreline against height.

    Returns (N,3): f in 0..1 from tip to top, half-width mm, centre-x mm.
    With `with_y`, also returns (y_tip, y_top) in console-centred mm, so the
    builder can place the sweep instead of guessing its extent.

    Rows where the two handles merge into the cross-bar are excluded - there
    the run is the bar, not a handle, and including it was how the old build
    ended up with a 222 mm wide "handle".
    """
    mask, (x0, y0, w, h), _ = grip_mask()
    scale, _ = console_scale((x0, y0, w, h))
    cx = x0 + w / 2.0
    con_top_px = _console_top_px()

    rows = []
    for yy in range(y0, y0 + h):
        r = _row_runs(mask, yy)
        if len(r) < 2:            # bar, or off the end
            continue
        l = r[0]
        if (l[1] - l[0]) * scale > 90.0:
            continue              # a run this wide is not one handle
        rows.append((yy, (l[1] - l[0]) * scale / 2.0,
                     ((l[0] + l[1]) / 2.0 - cx) * scale))
    if len(rows) < 20:
        raise SystemExit("only %d handle rows found" % len(rows))

    rows = np.array(rows, float)
    # y grows DOWNWARD in the image, so the smallest row index is the handle's
    # TOP and the largest is its TIP. f runs 0 at the tip to 1 at the top, so
    # it decreases as the row index grows. Sort by f before interpolating -
    # np.interp requires an increasing x and returns silent garbage without it
    # (this returned a 1.5 mm handle when the rows were left in image order).
    ytop, ybot = rows[:, 0].min(), rows[:, 0].max()
    f = (ybot - rows[:, 0]) / (ybot - ytop)      # 0 at tip, 1 at top
    prof = np.column_stack([f, rows[:, 1], rows[:, 2]])
    prof = prof[np.argsort(prof[:, 0])]
    assert np.all(np.diff(prof[:, 0]) >= 0)

    # The extreme rows are the anti-aliased first/last scanline of the blob,
    # where the handle measures ~1.5 mm. Sampling f=0 and f=1 there gives a
    # handle that tapers to a POINT at both ends; the real one has a rounded
    # cap, and a sweep through a zero-radius section produces a degenerate
    # face. Trim to where the section is structurally real, and let the
    # builder close the ends with a dome.
    keep = prof[prof[:, 1] >= 3.0]
    if len(keep) < 20:
        raise SystemExit("handle profile collapsed: %d usable rows" % len(keep))
    lo, hi = keep[0, 0], keep[-1, 0]
    ff = np.linspace(lo, hi, n)
    out = np.column_stack([np.linspace(0, 1, n),
                           np.interp(ff, prof[:, 0], prof[:, 1]),
                           np.interp(ff, prof[:, 0], prof[:, 2])])
    if not with_y:
        return out
    # f -> image row -> console-centred Y
    row_lo = ybot - lo * (ybot - ytop)
    row_hi = ybot - hi * (ybot - ytop)
    y_tip = HALF_H - (row_lo - con_top_px) * scale
    y_top = HALF_H - (row_hi - con_top_px) * scale
    return out, (y_tip, y_top)


def _dxf(path):
    pl = list(ezdxf.readfile(str(path)).modelspace().query("LWPOLYLINE"))[0]
    return np.array([(x, y) for x, y, *_ in pl.get_points()])


SRC_LAT = ROOT / "sources" / "psvitaGrip" / "lateralHAndleview.jpg"


def handle_depth_profile(n=28, source="drawing"):
    """Handle DEPTH and spine against height.

    SOURCE: `lateralHAndleview.jpg`, an orthographic lateral of the grip's own
    handle. This replaced `dualsense_side.dxf` on 2026-09-02.

    The DualSense side view is a verified orthographic drawing, but it is the
    wrong OBJECT: it carries the controller's body, so its depth grows
    monotonically 10 -> 45 mm to the top. The real grip's handle NECKS DOWN -
    48 mm at the palm swell (f 0.38), then 17 mm through the neck (f 0.73-0.85)
    before it meets the bridge. Diff at the top: 41 mm.

    That missing neck is why the built handle had no waist, why its top had to
    be faked with a taper (the "gnome hat" cone), and why its side read as a
    wedge instead of the drawing's rounded swell.

    The drawing's own cotes are NOT used - they are internally inconsistent
    (it calls the grip 173 mm wide when the console alone is 182, and its
    "install void" of 160 x 56 mm cannot hold an 182 x 83.55 mm console). Only
    its SHAPE is taken, scaled by the handle length measured independently
    from 054-1.webp.

      CROSS-CHECK: scaling the traced silhouette by that 106.68 mm length
      gives a max depth of 49.24 mm. The drawing annotates [50] mm. Two
      independent routes, 1.5 % apart - so the shape and the scale agree even
      though the cotes as a set do not.

    Returns (N,3): f in 0..1 tip->top, depth mm, spine offset mm.
    """
    if source == "drawing":
        return _depth_from_lateral(n)
    return _depth_from_dualsense(n)


def _depth_from_lateral(n=28):
    """Trace the handle's lateral silhouette from lateralHAndleview.jpg.

    Row-wise outer envelope of the largest ink structure. The ROI excludes the
    bridge stub at top-right and the annotation gutter at left; a filled
    flood-fill is NOT used because the drawing is a line rendering whose
    outline is not closed - filling it returned the whole ROI (fill 1.000) and
    contour-finding returned the wall strokes (fill 0.046), the same class of
    failure as the old BackView.png trace.
    """
    im = cv2.imread(str(SRC_LAT))
    if im is None:
        raise SystemExit("cannot read %s" % SRC_LAT)
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    roi = g[118:540, 415:610]
    ink = (roi < 130).astype(np.uint8)
    ink = cv2.morphologyEx(ink, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    nc, lab, st, _ = cv2.connectedComponentsWithStats(ink, 8)
    i = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    m = (lab == i)

    rows = []
    for y in range(m.shape[0]):
        xs = np.where(m[y])[0]
        if len(xs) < 2:
            continue
        rows.append((y, xs.min(), xs.max()))
    if len(rows) < 50:
        raise SystemExit("lateral trace found only %d rows" % len(rows))
    rows = np.array(rows, float)

    y0, y1 = rows[0, 0], rows[-1, 0]
    span = y1 - y0
    f = 1.0 - (rows[:, 0] - y0) / span          # 0 at the tip, 1 at the top
    depth = rows[:, 2] - rows[:, 1]
    spine = (rows[:, 2] + rows[:, 1]) / 2.0

    k = 15                                       # smooth the raster stair
    ker = np.ones(k) / k
    ds = np.convolve(depth, ker, mode="same")
    cs = np.convolve(spine, ker, mode="same")
    ds[:k], ds[-k:] = depth[:k], depth[-k:]
    cs[:k], cs[-k:] = spine[:k], spine[-k:]

    o = np.argsort(f)
    f, ds, cs = f[o], ds[o], cs[o]

    # Scale by the handle length measured on 054-1.webp, not by the drawing's
    # own cotes.
    _, (y_tip, y_top) = handle_plan_profile(n, with_y=True)
    scale = abs(y_top - y_tip) / span
    ff = np.linspace(0, 1, n)
    out = np.column_stack([ff,
                           np.interp(ff, f, ds) * scale,
                           np.interp(ff, f, cs) * scale])
    out[:, 2] -= out[0, 2]
    return out


def _depth_from_dualsense(n=28):
    """Handle DEPTH against height, from the DualSense's side view.

    The depth source is `dualsense_side.dxf`, not `lateral.jpg`. lateral.jpg is
    a three-quarter perspective shot - the previous version measured a 50.8 mm
    "belly" off it, which no orthographic view supports. The DualSense drawing
    is verified orthographic (annotated width and height anchors agree to
    0.04 %), and the sketch's brief is that the handles match a DualSense.

    Below y = 37.75 mm the front view shows two separate runs: that is the
    isolated handle. Above it the views carry the controller's body, which
    this grip does not have. Only the handle region is sampled.

    Returns (N,3): f in 0..1 tip->top, depth mm, depth-centre offset mm.
    """
    side = Polygon([tuple(map(float, q)) for q in _dxf(DS_SIDE)]).buffer(0)
    y_hi = 36.5                       # handle/body split, measured
    rows = []
    for f in np.linspace(0.02, 1.0, 60):
        y = f * y_hi
        row = side.intersection(LineString([(-20, y), (120, y)]))
        if row.is_empty:
            continue
        gs = [row] if row.geom_type in ("LineString", "Point") else list(row.geoms)
        b = [g.bounds for g in gs if g.bounds[2] - g.bounds[0] > 0.05]
        if not b:
            continue
        lo = min(v[0] for v in b)
        hi = max(v[2] for v in b)
        rows.append((f, hi - lo, (lo + hi) / 2.0))
    prof = np.array(rows, float)
    # centre the spine on its own tip so the offset is a travel, not a position
    prof[:, 2] -= prof[0, 2]
    ff = np.linspace(0, 1, n)
    return np.column_stack([ff,
                            np.interp(ff, prof[:, 0], prof[:, 1]),
                            np.interp(ff, prof[:, 0], prof[:, 2])])


def bar_extent():
    """The cross-bar's top and bottom edge, in console-centred mm.

    Measured directly: the rows where the mask is a single wide run.
    """
    mask, (x0, y0, w, h), _ = grip_mask()
    scale, _ = console_scale((x0, y0, w, h))

    con_top_px = _console_top_px()

    bar_rows = [yy for yy in range(y0, y0 + h)
                if len(_row_runs(mask, yy)) == 1
                and (lambda r: (r[0][1] - r[0][0]) * scale > 150.0)(_row_runs(mask, yy))]
    if not bar_rows:
        raise SystemExit("no cross-bar rows found")
    top_px, bot_px = min(bar_rows), max(bar_rows)
    # console top is +HALF_H in model coords
    y_top = HALF_H - (top_px - con_top_px) * scale
    y_bot = HALF_H - (bot_px - con_top_px) * scale
    return y_top, y_bot


def grip_outline():
    """The grip's filled plan outline as a closed (N,2) array in mm."""
    mask, (x0, y0, w, h), _ = grip_mask()
    scale, _ = console_scale((x0, y0, w, h))

    _, con_top_px, _, _, con_cx = _console_blob()

    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    c = max(cnts, key=cv2.contourArea)
    c = cv2.approxPolyDP(c, 1.2, True).reshape(-1, 2).astype(float)

    pts = np.column_stack([(c[:, 0] - con_cx) * scale,
                           HALF_H - (c[:, 1] - con_top_px) * scale])
    # symmetrise about X = 0: the product is symmetric and the photo is not
    # perfectly square-on. Mirror, then average by nearest-y matching.
    return pts


# ------------------------------------------------------------------ output ---
def c_section():
    """The C that wraps the console's edge: front lip, web, rear lip."""
    fit, wall, lipf, lipr = 0.35, 3.0, 4.5, 7.0
    zf = HALF_D + fit + wall
    zi = HALF_D + fit
    y0 = -HALF_H
    return np.array([
        (y0 - wall, -zf), (y0 - wall, zf), (y0 - wall + lipf, zf),
        (y0 - wall + lipf, zi), (y0, zi), (y0, -zi),
        (y0 - wall + lipr, -zi), (y0 - wall + lipr, -zf),
    ])


def write_svg(pts, path):
    mn, mx = pts.min(axis=0), pts.max(axis=0)
    d = svgwrite.Drawing(str(path), profile="tiny",
                         size=("%.2fmm" % (mx[0] - mn[0]),
                               "%.2fmm" % (mx[1] - mn[1])))
    d.viewbox(mn[0], -mx[1], mx[0] - mn[0], mx[1] - mn[1])
    d.add(d.polygon([(float(a), float(-b)) for a, b in pts],
                    fill="none", stroke="black", stroke_width=0.3))
    d.save()


def write_dxf(pts, path):
    doc = ezdxf.new("R2010")
    doc.modelspace().add_lwpolyline(
        [(float(a), float(b)) for a, b in pts], close=True)
    doc.saveas(str(path))


def emit(name, pts, expect=None):
    ring = LinearRing([(float(a), float(b)) for a, b in pts])
    if not ring.is_simple:
        raise SystemExit("%s self-intersects" % name)
    poly = Polygon(ring).buffer(0)
    w, h = np.ptp(pts[:, 0]), np.ptp(pts[:, 1])
    print("  %-20s %4d pts  %7.2f x %7.2f mm  area %8.0f mm2"
          % (name, len(pts), w, h, poly.area))
    if expect:
        for got, exp, lab in ((w, expect[0], "width"), (h, expect[1], "height")):
            if abs(got - exp) / exp > ENVELOPE_TOL:
                raise SystemExit("  FAIL %s %s %.2f vs expected %.2f"
                                 % (name, lab, got, exp))
        print("       envelope agrees with handle-back.jpg to %.1f %% / %.1f %%"
              % (abs(w - expect[0]) / expect[0] * 100,
                 abs(h - expect[1]) / expect[1] * 100))
    VEC.mkdir(parents=True, exist_ok=True)
    write_svg(pts, VEC / ("%s.svg" % name))
    write_dxf(pts, VEC / ("%s.dxf" % name))
    return poly


def main():
    print("trace_grip - the grip, from %s" % SRC.name)
    mask, bbox, fill = grip_mask()
    scale, (cw, ch, ch_mm) = console_scale(bbox)
    print("  mask       %d x %d px, fill %.3f, 1 component"
          % (bbox[2], bbox[3], fill))
    print("  scale      console %d px = %.1f mm -> %.5f mm/px"
          % (cw, CONSOLE_W, scale))
    print("  (console height reads %.2f mm, not %.2f - the bar occludes it; "
          "not used as an anchor)" % (ch_mm, CONSOLE_H))

    out = grip_outline()
    emit("vitagrip_front", out, expect=(EXPECT_W, EXPECT_H))
    emit("vitagrip_section", c_section())

    plan = handle_plan_profile()
    dep = handle_depth_profile()
    yt, yb = bar_extent()
    print("  handle     half-width %.2f (tip) -> %.2f mm (top)"
          % (plan[0, 1], plan[-1, 1]))
    print("             depth      %.2f (tip) -> %.2f mm (top)"
          % (dep[0, 1], dep[-1, 1]))
    # Reported, not consumed: the builder pins the front face and lets each
    # section's own depth run backward from it, so the rearward migration
    # falls out of the depth profile. Applying this travel ON TOP of that
    # double-counts the same curve - it took the built depth to 57.51 mm on a
    # 45.14 mm handle.
    print("             (side-view spine travel %.2f mm - already inside the "
          "depth, not applied again)" % (dep[-1, 2] - dep[0, 2]))
    print("  bar        Y %.2f .. %.2f mm (%.2f tall)" % (yb, yt, yt - yb))
    return 0


if __name__ == "__main__":
    sys.exit(main())
