"""
extract_profile.py — measure a grip's lobe profile from a rear-view photo
=========================================================================
Produces the LOBE_PROFILE table in projects/VitaGripPS5/macros/build_grip.py.

WHY ROWS ARE ACCEPTED, NOT JUST MEASURED
----------------------------------------
The obvious method - "widest blue run in each row" - silently returns a number
for rows where the mask is not two clean lobes at all. On 054-1.webp:

    row  54   10 runs   -> 59.0   (bar + shadow specks)
    row  70    3 runs   -> 70.6   (a 140 mm centre run that is still the bar)
    rows 100-110  3-4 runs -> 7.4, 23.4, 22.4, 25.8   (tip + shadow)

Swept through a bevel object, that noise becomes GEOMETRY: a terraced lobe
with a ridge at every control point and a cone-shaped pinch across the data
gap. The width RMS was a respectable 5.7 mm the whole time, because a width
table cannot see surface smoothness.

So a row counts only if it passes THREE tests:
  1. exactly TWO runs - the two lobes, nothing else
  2. neither run wider than MAX_LOBE_MM - rejects rows the bar spans
  3. left and right widths agree within SYMMETRY_TOL - the part is symmetric,
     so a row where they disagree is measuring something else

A cubic smoothing spline through the survivors then gives a profile that is
smooth by construction and interpolates the bar gap instead of coning across
it. `--smooth` trades residual against curvature: s=100 gives max residual
3.58 mm with max |curvature| 0.65, against 1.71 at s=50.

Usage
-----
    python tools/extract_profile.py sources/VitaGripPs5/054-1.webp --width 237.9
    python tools/extract_profile.py <img> --width 237.9 --smooth 100 --step 3
"""

import argparse
import sys

import numpy as np
from PIL import Image

MAX_LOBE_MM = 100.0      # a run wider than this is the bar, not a lobe
SYMMETRY_TOL = 3.0       # mm; left and right lobe widths must agree
RUN_GAP_PX = 3           # pixels of background that separate two runs


def blue_mask(img):
    """Saturated-blue mask.

    The S floor matters: at S>110 the product's soft blue-grey drop shadow is
    included and the part measures 343.5 mm instead of 237.9. 150 drops it.
    """
    a = np.asarray(img.convert("RGB")).astype(int)
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    mx, mn = a.max(2), a.min(2)
    s = np.where(mx > 0, (mx - mn) * 255 // np.maximum(mx, 1), 0)
    return (b > r + 40) & (b > g + 30) & (s > 150) & (mx > 60)


def runs_in_row(row):
    """Contiguous True runs as (start, end) index pairs."""
    idx = np.where(row)[0]
    if len(idx) == 0:
        return []
    out, st, pv = [], idx[0], idx[0]
    for i in idx[1:]:
        if i > pv + RUN_GAP_PX:
            out.append((st, pv))
            st = i
        pv = i
    out.append((st, pv))
    return out


def extract(path, known_width_mm, smooth, step):
    mask = blue_mask(Image.open(path))
    ys, xs = np.where(mask)
    if len(xs) == 0:
        sys.exit("no blue pixels found - is this the right image?")
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    mm = known_width_mm / (x1 - x0 + 1)
    height = (y1 - y0 + 1) * mm

    accepted, rejected = [], []
    for d in np.arange(1, height, 1.0):
        y = int(y0 + d / mm)
        if y > y1:
            break
        rr = runs_in_row(mask[y])
        if len(rr) != 2:
            rejected.append((d, "%d runs" % len(rr)))
            continue
        lw = (rr[0][1] - rr[0][0] + 1) * mm
        rw = (rr[1][1] - rr[1][0] + 1) * mm
        if lw > MAX_LOBE_MM or rw > MAX_LOBE_MM:
            rejected.append((d, "run > %.0f mm (bar)" % MAX_LOBE_MM))
            continue
        if abs(lw - rw) > SYMMETRY_TOL:
            rejected.append((d, "asymmetric %.1f vs %.1f" % (lw, rw)))
            continue
        accepted.append((d, (lw + rw) / 2.0))

    print("scale %.4f mm/px   grip height %.1f mm" % (mm, height))
    print("accepted %d rows, rejected %d"
          % (len(accepted), len(rejected)))
    if not accepted:
        sys.exit("no row passed the acceptance tests")

    g = np.array(accepted)
    from scipy.interpolate import UnivariateSpline
    sp = UnivariateSpline(g[:, 0], g[:, 1], s=smooth, k=3)
    resid = g[:, 1] - sp(g[:, 0])
    dd = np.linspace(g[:, 0].min(), g[:, 0].max(), 400)
    curv = np.abs(sp.derivative(2)(dd)).max()
    peak_i = int(np.argmax(sp(dd)))
    print("spline s=%g: max residual %.2f mm, RMS %.2f, max |curvature| %.3f"
          % (smooth, np.abs(resid).max(), np.sqrt((resid ** 2).mean()), curv))
    print("peak %.1f mm at depth %.1f mm"
          % (float(sp(dd[peak_i])), dd[peak_i]))
    print()
    print("LOBE_PROFILE = [")
    lo, hi = g[:, 0].min(), g[:, 0].max()
    line = "    "
    for d in range(int(np.ceil(lo)), int(hi) + 1, step):
        item = "(%d, %.1f), " % (d, float(sp(d)))
        if len(line) + len(item) > 76:
            print(line.rstrip())
            line = "    "
        line += item
    if line.strip():
        print(line.rstrip().rstrip(","))
    print("]")


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("image")
    ap.add_argument("--width", type=float, required=True,
                    help="known overall width of the blue part, mm")
    ap.add_argument("--smooth", type=float, default=100.0,
                    help="spline smoothing factor (default 100)")
    ap.add_argument("--step", type=int, default=3,
                    help="table row spacing in mm (default 3)")
    args = ap.parse_args()
    extract(args.image, args.width, args.smooth, args.step)


if __name__ == "__main__":
    main()
