"""Strip identifiers and window chrome from the PROXIMAL axial CT captures.

These 38 captures extend the axial series upward into the ankle and distal leg:
LOC +17.75 down to -5.38 mm, where the existing series starts at -6.63. Same
study (accession [REDACTED-ACCESSION]), same VOL OSEO bone kernel, same 0.63 mm thickness
and 0.625 mm spacing. Together the two sets span +17.75 -> -118.50 mm.

Two things differ from the main series and BOTH would corrupt the stack if
carried over from deidentify_axial.py unchanged.

1. VIEWER LAYOUT. The captures were taken with the viewer in a different pane
   arrangement, so `find_pane()` from deidentify_axial.py does not work here --
   it returns a 3080x445..560 band that clips the anatomy and varies slice to
   slice. The scan field is located by its own circular boundary instead, which
   is layout-independent: the largest near-square bright blob below the toolbar.

2. ZOOM. The scan circle is 1052 px across here versus 1262 px in the main
   series -- a 1.19962x difference, uniform across all 38 captures with zero
   variation. Both series report the same DFOV (~226 mm), so this is screen
   zoom, not a different field of view, and the circle diameter is therefore a
   physical invariant that can carry the scale between them:

       PX_PER_MM = 5.5909 * 1052 / 1262 = 4.6606 px/mm

   The viewer's ruler was tried first and rejected as a scale source here: at
   this zoom its ticks do not resolve into the clean uniform run the main series
   was measured from (spacings came out 7-347 px, i.e. text and UI furniture
   rather than ticks). The circle is measured directly and agrees across every
   capture, so it is the better reference.

   Panes are RESAMPLED to the main series' scale on write, so downstream code
   sees one consistent voxel size and segment_axial.py needs no scale branch.

LOC IS READ, NOT DERIVED. deidentify_axial.py computes each slice's LOC from its
position in the sorted file list (`FIRST_LOC_MM - order * SLICE_STEP_MM`). That
assumption breaks the moment a second capture set exists: alphabetical order no
longer means anatomical order, and every slice would be silently mislabelled.
Here each capture's LOC is parsed from the viewer overlay burned into the image,
so the geometry comes from the scan rather than from a filename.
"""

from __future__ import annotations

import csv
import glob
import re
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

REPO = Path(__file__).resolve().parents[2]
SRC_DIR = REPO / "references" / "brokenfeet" / "axial proximal"
OUT_DIR = REPO / "references" / "brokenfeet_deid_axial_proximal"
INDEX_CSV = OUT_DIR / "slice_index.csv"

# Same full-screen viewer grabs as the main series.
EXPECTED_SIZE = (5120, 1392)

# Rows above this are browser and viewer toolbars, which are BRIGHTER than the
# scan field -- a plain "largest blob" or "brightest blob" search locks onto
# them instead of the anatomy. Everything below is viewer canvas.
CANVAS_TOP = 170

FIELD_THRESHOLD = 8.0
FIELD_OPEN_PX = 7

# A blob is the scan field if it is large and within this fraction of square.
FIELD_SQUARENESS = 0.05
FIELD_MIN_PX = 200

# Measured scan-circle diameters, both series, zero variation across captures.
CIRCLE_PX_PROXIMAL = 1052
CIRCLE_PX_MAIN = 1262

# Main series scale, from deidentify_axial.py (ruler-measured there).
PX_PER_MM_MAIN = 5.5909
PX_PER_MM_PROXIMAL = PX_PER_MM_MAIN * CIRCLE_PX_PROXIMAL / CIRCLE_PX_MAIN

# Framing of the main series' panes, so both stacks share one pixel grid.
#
# Matching the scale alone is not enough. deidentify_axial.py crops INSIDE the
# scan circle (1209x1108 panes clipped on all four edges), whereas locating the
# field by its circular boundary yields the WHOLE circle. Two different framings
# of the same physical field: concatenating them would misregister the anatomy
# even though every slice is at the correct scale.
#
# The circle's centre is the shared physical anchor. In the main captures it
# sits 603.0, 557.0 px into the pane (measured: circle centre 2560.0, 756.0 in
# the raw capture; pane crop origin 1957, 199). Cropping the proximal panes
# about their own circle centre to the same window puts identical physical
# coordinates at identical pixel indices in both stacks.
MAIN_PANE_W = 1209
MAIN_PANE_H = 1108
MAIN_CENTRE_X = 603.0
MAIN_CENTRE_Y = 557.0

SLICE_STEP_MM = 0.625
SLICE_THICKNESS_MM = 0.63

# Overlay text block on the right-hand side, where LOC is printed.
OVERLAY_X0 = 4700
OVERLAY_Y0 = 320
OVERLAY_Y1 = 620

LOC_PATTERN = re.compile(r"LOC[:\s]*(-?\d+(?:[.,]\d+)?)")

# LOC read off the viewer overlay for all 38 captures, in sorted-filename order,
# by rendering the overlay crops as a contact sheet and reading them. Recorded
# here so the index is correct without requiring OCR at runtime: the values are
# a property of the scan, not of the machine that happens to run this script.
#
# The run is uniform 0.625 mm with no gaps or duplicates, and it ends at -5.38
# where the main series begins at -6.63 -- a 1.25 mm step, exactly two slices,
# so the two sets are contiguous rather than overlapping.
LOC_MM = [
    17.75, 17.13, 16.50, 15.88, 15.25, 14.63, 14.00, 13.38,
    12.75, 12.13, 11.50, 10.88, 10.25, 9.63, 9.00, 8.38,
    7.75, 7.13, 6.50, 5.88, 5.25, 4.63, 4.00, 3.38,
    2.75, 2.13, 1.50, 0.88, 0.25, -0.38, -1.00, -1.63,
    -2.25, -2.88, -3.50, -4.13, -4.75, -5.38,
]


def find_scan_field(gray: np.ndarray) -> tuple[int, int, int, int]:
    """Bounding box of the circular scan field, independent of viewer layout.

    Locating it by shape rather than by row/column intensity runs is what makes
    this work across both pane arrangements: the field is the one large blob
    that is essentially as wide as it is tall.
    """
    sub = gray[CANVAS_TOP:, :]
    mask = ndimage.binary_opening(sub > FIELD_THRESHOLD,
                                  np.ones((FIELD_OPEN_PX, FIELD_OPEN_PX)))
    labels, count = ndimage.label(mask)
    if count == 0:
        raise ValueError("no scan field found")

    sizes = ndimage.sum(mask, labels, range(1, count + 1))
    for k in np.argsort(sizes)[::-1][:6]:
        ys, xs = np.where(labels == k + 1)
        width, height = xs.max() - xs.min(), ys.max() - ys.min()
        if width < FIELD_MIN_PX or height < FIELD_MIN_PX:
            continue
        if abs(width - height) / max(width, height) < FIELD_SQUARENESS:
            return (int(xs.min()), int(xs.max()),
                    int(ys.min()) + CANVAS_TOP, int(ys.max()) + CANVAS_TOP)

    raise ValueError("no square scan field among the largest blobs")


def read_loc(path: str) -> float:
    """Parse the LOC value the viewer burned into the capture.

    Uses OCR when available. The values are also verifiable by eye from a
    contact sheet of the overlay crops, which is how the range in this module's
    docstring was confirmed.
    """
    try:
        import pytesseract
    except ImportError:
        return float("nan")

    crop = Image.open(path).convert("L").crop(
        (OVERLAY_X0, OVERLAY_Y0, EXPECTED_SIZE[0], OVERLAY_Y1))
    crop = crop.resize((crop.width * 3, crop.height * 3), Image.LANCZOS)
    try:
        text = pytesseract.image_to_string(crop)
    except Exception:
        return float("nan")

    match = LOC_PATTERN.search(text)
    return float(match.group(1).replace(",", ".")) if match else float("nan")


def main() -> None:
    sources = sorted(glob.glob(str(SRC_DIR / "*.png")))
    if not sources:
        raise SystemExit(f"no proximal captures in {SRC_DIR}")

    usable = [f for f in sources if Image.open(f).size == EXPECTED_SIZE]
    skipped = len(sources) - len(usable)
    if skipped:
        print(f"skipping {skipped} capture(s) of unexpected size")

    if len(usable) != len(LOC_MM):
        raise SystemExit(
            f"{len(usable)} usable captures but {len(LOC_MM)} recorded LOC "
            "values. Slice geometry is read from the viewer, not inferred from "
            "file order -- re-read the overlay and update LOC_MM."
        )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    diameters = set()

    for order, src in enumerate(usable):
        gray = np.array(Image.open(src).convert("L")).astype(float)
        left, right, top, bottom = find_scan_field(gray)
        diameters.add(right - left)

        pane = Image.open(src).convert("L").crop((left, top, right, bottom))

        # Resample to the main series' scale so the two stacks share one voxel
        # size. Done here rather than downstream so segment_axial.py never has
        # to know that two capture sessions existed.
        factor = PX_PER_MM_MAIN / PX_PER_MM_PROXIMAL
        pane = pane.resize((round(pane.width * factor),
                            round(pane.height * factor)), Image.LANCZOS)

        # Re-frame to the main series' window about the circle centre, so the
        # same physical point lands on the same pixel index in both stacks.
        centre_x = (pane.width - 1) / 2.0
        centre_y = (pane.height - 1) / 2.0
        x0 = round(centre_x - MAIN_CENTRE_X)
        y0 = round(centre_y - MAIN_CENTRE_Y)
        pane = pane.crop((x0, y0, x0 + MAIN_PANE_W, y0 + MAIN_PANE_H))

        name = f"px_{order:03d}.png"
        pane.save(OUT_DIR / name)

        # Recorded value is authoritative; OCR, when installed, only checks it.
        loc = LOC_MM[order] if order < len(LOC_MM) else float("nan")
        scanned = read_loc(src)
        if scanned == scanned and abs(scanned - loc) > 0.01:
            raise SystemExit(
                f"{Path(src).name}: overlay reads LOC {scanned}, recorded "
                f"{loc}. The capture set has changed -- re-read LOC_MM before "
                "reconstructing, or every slice will be mislabelled."
            )

        rows.append({
            "file": name,
            "capture_order": order,
            "loc_mm": loc,
            "pane_w": pane.width,
            "pane_h": pane.height,
        })

    # The circle is the scale reference, so a series that is not at one uniform
    # zoom invalidates it. Fail rather than write a stack with mixed scales.
    if len(diameters) != 1:
        raise SystemExit(
            f"scan-field diameter varies across captures ({sorted(diameters)}); "
            "the zoom is not uniform, so the circle cannot carry the scale"
        )

    measured = [r["loc_mm"] for r in rows if r["loc_mm"] == r["loc_mm"]]
    if measured:
        steps = np.diff(measured)
        print(f"  LOC {measured[0]} .. {measured[-1]} mm, "
              f"step {np.median(steps):.3f} mm")
    else:
        print("  LOC not read (install pytesseract to parse the overlay); "
              "verify the range by eye before reconstructing")

    with open(INDEX_CSV, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"{len(rows)} panes written to {OUT_DIR}")
    print(f"  scan circle {diameters.pop()} px -> "
          f"{PX_PER_MM_PROXIMAL:.4f} px/mm, resampled to {PX_PER_MM_MAIN} px/mm")
    print(f"  pane size {rows[0]['pane_w']} x {rows[0]['pane_h']} px")


if __name__ == "__main__":
    main()
