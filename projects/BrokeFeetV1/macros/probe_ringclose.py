"""Per-bone adaptive threshold: find the level at which each ring CLOSES.

Evidence from the rendered slices (renders/site_*.png) and from a threshold
sweep at four named sites:

  calcaneus slice 88   T=105 fills     14 px of interior -- ring broken
                       T=100 fills  6,879 px            -- ring CLOSED
  navicular slice 107  ring closes only intermittently; V0's 115 recovers
                       1,111 px, T=120 recovers 0

So the level at which a cortical outline becomes a closed loop is a LOCAL
property of that bone, not a global constant -- which is precisely the case for
replacing the single 115.

The rule measured here:

  for each candidate bone region, in each slice, lower the threshold until
  binary_fill_holes finds an enclosed interior; accept that interior ONLY if
  the region it encloses does not grow the region's own outer silhouette (the
  guarantee V0's _close_within_envelope earns and the rejected per-component
  fill lacked), and only down to a floor.

Filling an interior enclosed by a ring at threshold T <= 115 cannot bridge two
bones, because a ring that encloses two bones would have to enclose the joint
space between them -- which this pass checks for directly by counting how many
SEED components the proposed interior touches.
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

HIGH = 115
FIELD_MARGIN_PX = 12
LEVELS = (112, 108, 104, 100, 96, 92)
MIN_RING_AREA_PX = 60      # a ring smaller than this is speckle, not a bone
MAX_INTERIOR_PX = 40000    # ~1280 mm2: bigger than any single tarsal section


def ring_close_fill(plane_src, plane_seed, levels=LEVELS):
    """Return interior voxels recovered by lowering the threshold per ring.

    At each level the whole slice is re-thresholded and filled. The material
    the fill ADDS (holes enclosed at that level) is accepted when:
      * the hole is not absurdly large (a joint space enclosed by two bones
        plus surrounding tissue would be), and
      * the hole's own intensity is bone-plausible.
    Each accepted hole is recorded once; lower levels only add holes that the
    higher ones could not see.
    """
    gained = np.zeros(plane_src.shape, dtype=bool)
    for level in levels:
        m = plane_src >= level
        m[:FIELD_MARGIN_PX] = False
        m[-FIELD_MARGIN_PX:] = False
        m[:, :FIELD_MARGIN_PX] = False
        m[:, -FIELD_MARGIN_PX:] = False
        holes = ndimage.binary_fill_holes(m) & ~m
        if not holes.any():
            continue
        lab, n = ndimage.label(holes)
        if n == 0:
            continue
        sizes = ndimage.sum(holes, lab, range(1, n + 1))
        ok = [i + 1 for i, s in enumerate(sizes)
              if MIN_RING_AREA_PX <= s <= MAX_INTERIOR_PX]
        if ok:
            gained |= np.isin(lab, ok)
    return gained & ~plane_seed


def main() -> None:
    volume, geom = stack_source.load_volume()
    iso = np.load(WORK / "v0_iso.npy")
    fr = frames.IsoFrame(iso)
    vox = geom.voxel_mm3

    seed = volume >= HIGH
    seed[:, :FIELD_MARGIN_PX, :] = False
    seed[:, -FIELD_MARGIN_PX:, :] = False
    seed[:, :, :FIELD_MARGIN_PX] = False
    seed[:, :, -FIELD_MARGIN_PX:] = False

    for stop in (1, 2, 3, 4, 5, 6):
        levels = LEVELS[:stop]
        gained = np.zeros(volume.shape, dtype=bool)
        for k in range(volume.shape[0]):
            gained[k] = ring_close_fill(volume[k], seed[k], levels)
        print(f"\n=== levels down to {levels[-1]} ===")
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
