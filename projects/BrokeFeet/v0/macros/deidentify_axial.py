"""Strip identifiers and window chrome from the BrokeFeet axial CT captures.

The axial series is the better of the two: 0.63 mm slices from a VOL OSEO
(bone-kernel) reconstruction at 0.625 mm spacing, versus 2.21/2.0 mm for the
sagittal set. It is the primary source for the 3D reconstruction; the sagittal
series becomes an independent check on it.

These captures are full-desktop screenshots rather than viewer-only grabs, so
they carry three things that must not reach the repo or the segmentation:

  1. Patient name, ID and date of birth, burned into the top-left overlay.
  2. The Chrome window: title bar showing the PACS URL, toolbar, tab strip.
  3. A Windows screenshot notification popup in the lower-right corner, which
     is bright enough to threshold as bone and sits inside the frame.

Cropping to the scan pane removes all three at once. The pane was located by
column-intensity profiling and is stable to within 2 px across the series, so a
per-image detection (rather than a fixed box) keeps it exact.
"""

from __future__ import annotations

import csv
import glob
from pathlib import Path

import numpy as np
from PIL import Image

REPO = Path(__file__).resolve().parents[4]
SRC_DIR = REPO / "references" / "brokenfeet" / "axiales"
OUT_DIR = REPO / "references" / "brokenfeet_deid_axial"
INDEX_CSV = OUT_DIR / "slice_index.csv"

# Captures at this size are the full-screen viewer grabs. One stray capture in
# the folder is a different size (a partial grab) and is skipped -- mixing
# geometries into one stack would corrupt the reconstruction.
EXPECTED_SIZE = (5120, 1392)

PANE_THRESHOLD = 6.0

# Inset past the pane border and the viewer's own orientation letters (A/P/H/L)
# and ruler, which are drawn just inside it. The circular scan field never
# reaches the pane edge, so nothing anatomical is lost.
INSET_X = 20
INSET_TOP = 40
INSET_BOTTOM = 60

# --- slice geometry, read from the viewer overlay --------------------------

# LOC runs -6.63 -> -118.50 mm in uniform 0.625 mm steps (confirmed against
# `SP: 0,63` in the header and by sampling the series at 12 points).
FIRST_LOC_MM = -6.63
SLICE_STEP_MM = 0.625
SLICE_THICKNESS_MM = 0.63

# Ruler measured at 12 ticks spanning 615 px over 11 cm, spacing 56 px
# (one 55 px step), so the scale is uniform.
PX_PER_MM = 5.5909
MM_PER_PX = 1.0 / PX_PER_MM


def _longest_run(mask: np.ndarray) -> tuple[int, int]:
    best_len, best = 0, (0, len(mask))
    start = None
    for i, flag in enumerate(mask):
        if flag:
            if start is None:
                start = i
        elif start is not None:
            if i - start > best_len:
                best_len, best = i - start, (start, i)
            start = None
    if start is not None and len(mask) - start > best_len:
        best = (start, len(mask))
    return best


def find_pane(gray: np.ndarray) -> tuple[int, int, int, int]:
    """Locate the scan pane, excluding chrome and the notification popup.

    The popup is bright and forms its own column run on the right of the frame;
    taking the LONGEST run rather than the brightest keeps the scan pane, which
    is far wider.
    """
    col_mean = gray.mean(axis=0)
    left, right = _longest_run(col_mean > PANE_THRESHOLD)

    row_mean = gray[:, left:right].mean(axis=1)
    top, bottom = _longest_run(row_mean > PANE_THRESHOLD)

    return (
        left + INSET_X,
        right - INSET_X,
        top + INSET_TOP,
        bottom - INSET_BOTTOM,
    )


def main() -> None:
    sources = sorted(glob.glob(str(SRC_DIR / "*.png")))
    if not sources:
        raise SystemExit(f"no axial captures in {SRC_DIR}")

    usable = [f for f in sources if Image.open(f).size == EXPECTED_SIZE]
    skipped = len(sources) - len(usable)
    if skipped:
        print(f"skipping {skipped} capture(s) of unexpected size")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []

    for order, src in enumerate(usable):
        gray = np.array(Image.open(src).convert("L")).astype(float)
        left, right, top, bottom = find_pane(gray)

        pane = Image.open(src).convert("L").crop((left, top, right, bottom))
        name = f"ax_{order:03d}.png"
        pane.save(OUT_DIR / name)

        rows.append({
            "file": name,
            "capture_order": order,
            "loc_mm": round(FIRST_LOC_MM - order * SLICE_STEP_MM, 3),
            "pane_w": right - left,
            "pane_h": bottom - top,
        })

    widths = {r["pane_w"] for r in rows}
    heights = {r["pane_h"] for r in rows}

    with open(INDEX_CSV, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"{len(rows)} panes written to {OUT_DIR}")
    print(f"  pane widths  {sorted(widths)}")
    print(f"  pane heights {sorted(heights)}")
    print(f"  LOC {rows[0]['loc_mm']} .. {rows[-1]['loc_mm']} mm "
          f"at {SLICE_STEP_MM} mm/slice")
    print(f"  in-plane {PX_PER_MM:.4f} px/mm -> voxel "
          f"{MM_PER_PX:.3f} x {MM_PER_PX:.3f} x {SLICE_STEP_MM} mm")


if __name__ == "__main__":
    main()
