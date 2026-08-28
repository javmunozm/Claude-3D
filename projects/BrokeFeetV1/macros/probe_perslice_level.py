"""Per-slice, per-ring adaptive level -- the level at which THIS ring closes.

Measured at the calcaneus, the level at which the cortical outline becomes a
closed loop is not merely local to the bone, it is local to the SLICE:

  slice  T=115  T=112  T=108  T=104  T=100   (enclosed interior px, local window)
     81   6970   6538   5684   4725   3332
     83     24     28   7942   6560   4801
     87      0      0     62   8521   6728
     93     12      8   9638   8589   7076
     99      0  10557   9728   8433   6940

A fixed level therefore cannot work in either direction: 112 recovers the
interior on slices 81/93/99 and nothing on 85-91, while 104 recovers it
everywhere and (measured in probe_ringclose.py) also recruits 72.6 % of the
ankle mortise.

The rule tested here takes, for each ring, the HIGHEST level at which it
encloses an interior, and stops at the first one that does -- so a slice whose
cortex is intact is never dropped to a permissive level, and a slice whose
cortex has one break is dropped only as far as it must be.

The danger this creates is explicit: on a slice where a bone's cortex is broken
BEYOND repair, the descent continues until some outline closes -- which may be
an outline around two bones. That is what the ceiling, the area cap and the
per-level acceptance below are for, and what the mortise measurement tests.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy import ndimage

HERE = Path(__file__).resolve().parent
WORK = HERE.parent / "work"
sys.path.insert(0, str(HERE))

import frames  # noqa: E402
import stack_source  # noqa: E402
from probe_sites import SITES  # noqa: E402

SEED = 115
FIELD_MARGIN_PX = 12
MIN_RING_AREA_PX = 60


def first_close_fill(src, floor, max_px, seed_plane):
    """Descend from SEED to `floor`; take each hole the FIRST level it appears.

    A hole is attributed to the highest level that encloses it. Once a region
    has been filled it is not revisited, so a lower level cannot enlarge an
    interior that a higher one already closed -- which is what stops the
    descent from creeping outward into tissue.
    """
    taken = np.zeros(src.shape, dtype=bool)
    for level in range(SEED, floor - 1, -1):
        m = src >= level
        m[:FIELD_MARGIN_PX] = False
        m[-FIELD_MARGIN_PX:] = False
        m[:, :FIELD_MARGIN_PX] = False
        m[:, -FIELD_MARGIN_PX:] = False
        holes = ndimage.binary_fill_holes(m) & ~m
        holes &= ~taken
        if not holes.any():
            continue
        lab, n = ndimage.label(holes)
        if n == 0:
            continue
        sizes = ndimage.sum(holes, lab, range(1, n + 1))
        ok = [i + 1 for i, s in enumerate(sizes)
              if MIN_RING_AREA_PX <= s <= max_px]
        if ok:
            taken |= np.isin(lab, ok)
    return taken & ~seed_plane


def main() -> None:
    volume, geom = stack_source.load_volume(source="legacy")
    iso = np.load(WORK / "v0_iso.npy")
    fr = frames.IsoFrame(iso)
    vox = geom.voxel_mm3

    seed = volume >= SEED
    seed[:, :FIELD_MARGIN_PX, :] = False
    seed[:, -FIELD_MARGIN_PX:, :] = False
    seed[:, :, :FIELD_MARGIN_PX] = False
    seed[:, :, -FIELD_MARGIN_PX:] = False

    for floor in (108, 104, 100, 96):
        for max_px in (40000, 15000):
            gained = np.zeros(volume.shape, dtype=bool)
            for k in range(volume.shape[0]):
                gained[k] = first_close_fill(volume[k], floor, max_px, seed[k])
            print(f"\n=== descend 115 -> {floor}, ring cap {max_px} px "
                  f"({max_px*geom.mm_per_px**2:.0f} mm2) ===")
            print(f"  recovered {gained.sum()*vox/1000:6.2f} cm3")
            for name, centre, radius, verdict in SITES:
                lo, hi = fr.window(centre, radius)
                slo = np.maximum(np.floor(frames.iso_to_source(lo, geom)).astype(int), 0)
                shi = np.minimum(np.ceil(frames.iso_to_source(hi, geom)).astype(int),
                                 np.array(volume.shape))
                w = gained[slo[0]:shi[0], slo[1]:shi[1], slo[2]:shi[2]]
                ws = seed[slo[0]:shi[0], slo[1]:shi[1], slo[2]:shi[2]]
                void = (~ws).sum()
                flag = "FILL" if "FILL" in verdict else "OPEN"
                print(f"    {name:20s} [{flag}] {w.sum()*vox:8.1f} mm3 "
                      f"= {100*w.sum()/max(1,void):5.1f}% of void")


if __name__ == "__main__":
    main()
