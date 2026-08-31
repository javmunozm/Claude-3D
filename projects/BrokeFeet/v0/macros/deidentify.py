"""Strip burned-in patient identifiers from the BrokeFeet CT screenshots.

The reference captures are screenshots of a Synapse PACS viewer. Every one of
them carries protected health information rendered directly into the pixels in
the surrounding chrome: patient name, patient ID, date of birth, accession
number, institution and acquisition timestamp. The scan pane in the middle of
the window carries none of that -- it is only image data plus the scale bar.

This script finds that pane per image (its position shifts a few pixels between
captures because each screenshot was taken separately) and writes out the pane
alone. The `LOC:` slice position is read off the right-hand overlay BEFORE the
crop and recorded in a sidecar index, because slice position is geometry we
need and is not recoverable once the chrome is gone.

Run once; the de-identified output is what every downstream step reads.
"""

from __future__ import annotations

import csv
import glob
import os
import re
from pathlib import Path

import numpy as np
from PIL import Image

# --- paths -----------------------------------------------------------------

REPO = Path(__file__).resolve().parents[4]
SRC_DIR = REPO / "references" / "brokenfeet"
OUT_DIR = REPO / "references" / "brokenfeet_deid"
INDEX_CSV = OUT_DIR / "slice_index.csv"

# --- pane detection --------------------------------------------------------

# The viewer renders the scan pane as a dark-grey block against the pure-black
# window background. A low mean-intensity threshold separates the two; the pane
# is then the longest contiguous run of columns above it.
PANE_THRESHOLD = 6.0

# The pane is drawn with a 1-2 px border and the viewer overlays a scale bar and
# orientation letters (H/F/R/P) just inside its edges. Insetting past them costs
# nothing -- the foot never reaches the pane border.
INSET = 12


def find_pane(gray: np.ndarray) -> tuple[int, int, int, int]:
    """Return (left, right, top, bottom) of the scan pane within a screenshot."""
    height, width = gray.shape

    col_mean = gray.mean(axis=0)
    left, right = _longest_run(col_mean > PANE_THRESHOLD, width)

    row_mean = gray[:, left:right].mean(axis=1)
    top, bottom = _longest_run(row_mean > PANE_THRESHOLD, height)

    return (
        left + INSET,
        right - INSET,
        top + INSET,
        bottom - INSET,
    )


def _longest_run(mask: np.ndarray, length: int) -> tuple[int, int]:
    """Start and end index of the longest contiguous True run in `mask`."""
    best_len, best_start, best_end = 0, 0, length
    run_start = None

    for i in range(length):
        if mask[i]:
            if run_start is None:
                run_start = i
        elif run_start is not None:
            if i - run_start > best_len:
                best_len, best_start, best_end = i - run_start, run_start, i
            run_start = None

    if run_start is not None and length - run_start > best_len:
        best_len, best_start, best_end = length - run_start, run_start, length

    return best_start, best_end


# --- slice position --------------------------------------------------------

# `LOC: 121,68` and `Page: 46 of 46` are rendered in the right-hand and
# bottom-left overlay respectively. Both use a comma decimal separator.
LOC_RE = re.compile(r"LOC[:\s]*([0-9]+[,.][0-9]+)")
PAGE_RE = re.compile(r"Page[:\s]*([0-9]+)\s*of\s*([0-9]+)")


def read_overlay(path: Path) -> dict[str, float | int | None]:
    """Read slice position and page number from the viewer chrome via OCR.

    OCR is optional -- if pytesseract is not installed the caller falls back to
    filename ordering, which preserves acquisition order but not true spacing.
    """
    empty: dict[str, float | int | None] = {"loc": None, "page": None, "pages": None}

    try:
        import pytesseract
    except ImportError:
        return empty

    image = Image.open(path).convert("L")
    width, height = image.size

    # Right-hand overlay strip carries LOC; bottom-left carries Page.
    right = image.crop((int(width * 0.72), 0, width, int(height * 0.35)))
    lower_left = image.crop((0, int(height * 0.6), int(width * 0.30), height))

    loc = page = pages = None

    try:
        match = LOC_RE.search(pytesseract.image_to_string(right))
        if match:
            loc = float(match.group(1).replace(",", "."))

        match = PAGE_RE.search(pytesseract.image_to_string(lower_left))
        if match:
            page, pages = int(match.group(1)), int(match.group(2))
    except pytesseract.TesseractNotFoundError:
        # Binary not installed. Slice positions are transcribed by hand into
        # slice_positions.py instead; ordering still comes from the filenames.
        return empty

    return {"loc": loc, "page": page, "pages": pages}


# --- main ------------------------------------------------------------------


def main() -> None:
    sources = sorted(glob.glob(str(SRC_DIR / "*.png")))
    if not sources:
        raise SystemExit(f"no screenshots found in {SRC_DIR}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []

    for order, src in enumerate(sources):
        src_path = Path(src)
        gray = np.array(Image.open(src_path).convert("L")).astype(float)
        left, right, top, bottom = find_pane(gray)

        pane = Image.open(src_path).convert("L").crop((left, top, right, bottom))
        out_name = f"slice_{order:03d}.png"
        pane.save(OUT_DIR / out_name)

        overlay = read_overlay(src_path)
        rows.append(
            {
                "file": out_name,
                "capture_order": order,
                "page": overlay["page"],
                "loc_mm": overlay["loc"],
                "pane_w": right - left,
                "pane_h": bottom - top,
            }
        )
        print(f"{out_name}  pane {right-left}x{bottom-top}  LOC={overlay['loc']}")

    with open(INDEX_CSV, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    located = sum(1 for r in rows if r["loc_mm"] is not None)
    print(f"\n{len(rows)} panes written to {OUT_DIR}")
    print(f"slice position recovered for {located}/{len(rows)} (index: {INDEX_CSV})")
    if located == 0:
        print("NOTE: no LOC values read (pytesseract missing?) -- spacing unknown")


if __name__ == "__main__":
    main()
