"""Does connectivity separate a trabecular void from a joint space?

Intensity provably does not (probe_sites.py: the two joints that must stay open
are BRIGHTER than the two voids that must be filled, and every lowered
threshold recruits more joint than void). The V1 premise is that CONNECTIVITY
does: a trabecular interior is contiguous with its own cortex, a joint space is
a slab of tissue between two cortices.

This probe runs a 3D hysteresis on the real stack and reports, per site, how
much of the void the flood recruits and -- the number that decides everything --
whether the flood joins two distinct seed components.

Nothing here writes a mesh. It is a measurement of the mask only.
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

HIGH = 115   # the V0 global threshold, reused as the SEED level
FIELD_MARGIN_PX = 12


def hysteresis(volume, high, low, connectivity=1):
    """Classic dual-threshold: keep every `low` component containing a `high`."""
    seed = volume >= high
    seed[:, :FIELD_MARGIN_PX, :] = False
    seed[:, -FIELD_MARGIN_PX:, :] = False
    seed[:, :, :FIELD_MARGIN_PX] = False
    seed[:, :, -FIELD_MARGIN_PX:] = False

    weak = volume >= low
    weak[:, :FIELD_MARGIN_PX, :] = False
    weak[:, -FIELD_MARGIN_PX:, :] = False
    weak[:, :, :FIELD_MARGIN_PX] = False
    weak[:, :, -FIELD_MARGIN_PX:] = False

    struct = ndimage.generate_binary_structure(3, connectivity)
    labels, n = ndimage.label(weak, structure=struct)
    if n == 0:
        return seed, seed
    keep = np.unique(labels[seed])
    keep = keep[keep > 0]
    grown = np.isin(labels, keep)
    return seed, grown


def main() -> None:
    volume, geom = stack_source.load_volume()
    iso = np.load(WORK / "v0_iso.npy")
    fr = frames.IsoFrame(iso)
    vox = geom.voxel_mm3

    for low in (105, 100, 95, 90, 85):
        seed, grown = hysteresis(volume, HIGH, low)
        added = grown & ~seed
        print(f"\n=== hysteresis  seed>={HIGH}  grow>={low} ===")
        print(f"  seed {seed.sum()*vox/1000:7.1f} cm3   "
              f"grown {grown.sum()*vox/1000:7.1f} cm3   "
              f"added {added.sum()*vox/1000:7.1f} cm3 "
              f"(+{100*added.sum()/max(1,seed.sum()):.0f}%)")

        lab, n = ndimage.label(grown)
        sizes = ndimage.sum(grown, lab, range(1, n + 1)) * vox / 1000.0
        big = np.sort(sizes)[::-1][:6]
        print(f"  components {n}, largest cm3: "
              + ", ".join(f"{s:.1f}" for s in big))

        for name, centre, radius, verdict in SITES:
            lo, hi = fr.window(centre, radius)
            slo = np.maximum(np.floor(frames.iso_to_source(lo, geom)).astype(int), 0)
            shi = np.minimum(np.ceil(frames.iso_to_source(hi, geom)).astype(int),
                             np.array(volume.shape))
            w_add = added[slo[0]:shi[0], slo[1]:shi[1], slo[2]:shi[2]]
            w_seed = seed[slo[0]:shi[0], slo[1]:shi[1], slo[2]:shi[2]]
            void = (~w_seed).sum()
            print(f"    {name:20s} [{verdict:14s}] recruited "
                  f"{w_add.sum()*vox:8.1f} mm3 = {100*w_add.sum()/max(1,void):5.1f}% of void")


if __name__ == "__main__":
    main()
