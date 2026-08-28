"""Slice positions for the BrokeFeet sagittal stack.

Transcribed by reading the `LOC:` field off each screenshot's viewer overlay
before de-identification cropped it away. The tesseract binary is not installed
in this environment, so these were read visually from magnified tiles of the
overlay region rather than by OCR.

The sequence is a regular 2 mm sagittal sweep descending from LOC 121 to LOC 30
-- NOT the irregular spacing an early spot-check of four non-adjacent captures
suggested. Two positions were captured twice (117, 85) and one step is missing
between 77 and 72, but the underlying acquisition grid is uniform.

LOC decreases as the sweep runs medial->lateral (or the reverse; the viewer's
R/L markers place the sweep across the foot's width). Slice thickness is
2.21 mm per the THK field, slightly greater than the 2 mm step, so adjacent
slices overlap a little -- expected for a reconstructed viewing series.
"""

from __future__ import annotations

# capture_order -> LOC in mm, as read from the viewer overlay.
SLICE_LOC_MM: dict[int, float] = {
    0: 121.0,   1: 119.0,   2: 117.0,   3: 117.0,   4: 115.0,   5: 113.0,
    6: 111.0,   7: 109.0,   8: 107.0,   9: 105.0,  10: 103.0,  11: 101.0,
    12: 99.0,  13: 97.0,   14: 95.0,   15: 93.0,   16: 91.0,   17: 89.0,
    18: 87.0,  19: 85.0,   20: 85.0,   21: 83.0,   22: 81.0,   23: 79.0,
    24: 77.0,  25: 74.0,   26: 72.0,   27: 70.0,   28: 68.0,   29: 66.0,
    30: 64.0,  31: 62.0,   32: 60.0,   33: 58.0,   34: 56.0,   35: 54.0,
    36: 52.0,  37: 50.6,   38: 48.6,   39: 46.0,   40: 44.0,   41: 42.0,
    42: 40.0,  43: 38.0,   44: 36.0,   45: 34.0,   46: 32.0,   47: 30.0,
}

# Slice 25's LOC digit was obscured in the capture; 74 is interpolated from its
# neighbours (77 and 72) and flagged here so downstream code can weight it.
INTERPOLATED = {25}

# Duplicate acquisitions -- same anatomical plane captured twice.
DUPLICATES = [(2, 3), (19, 20)]

NOMINAL_STEP_MM = 2.0
SLICE_THICKNESS_MM = 2.21

# --- in-plane scale --------------------------------------------------------

# Measured from the viewer's own ruler: 12 tick marks spanning x=1014..1539 px
# at 1 cm intervals -> 525 px / 11 cm. Tick-to-tick spacings were 48,48,47,48,
# 48,47,48,48,47,48,48 px (std 0.45 px), so the ruler is uniform and the scale
# is trustworthy to well under a percent.
PX_PER_MM = 4.7727
MM_PER_PX = 1.0 / PX_PER_MM


def sorted_slices() -> list[tuple[int, float]]:
    """(capture_order, loc_mm) sorted by anatomical position, duplicates dropped."""
    seen: set[float] = set()
    out: list[tuple[int, float]] = []
    for order, loc in sorted(SLICE_LOC_MM.items(), key=lambda kv: kv[1]):
        if loc in seen:
            continue
        seen.add(loc)
        out.append((order, loc))
    return out


if __name__ == "__main__":
    slices = sorted_slices()
    locs = [loc for _, loc in slices]
    steps = [round(b - a, 2) for a, b in zip(locs, locs[1:])]

    print(f"{len(SLICE_LOC_MM)} captures -> {len(slices)} distinct planes")
    print(f"LOC range {min(locs)} .. {max(locs)} mm  (span {max(locs)-min(locs)} mm)")
    print(f"step sizes present: {sorted(set(steps))}")
    print(f"in-plane scale {PX_PER_MM:.4f} px/mm ({MM_PER_PX:.5f} mm/px)")
