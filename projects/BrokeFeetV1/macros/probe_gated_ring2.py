"""Ring-close fill, gated on REAL bones only (speckle does not count).

probe_gated_ring.py kept 0.0 % of the calcaneal void and looked like a dead
end. It was not: the gate was counting trabecular speckle as bone. Measured, the
calcaneus window holds 102 distinct seed components, of which ONE has 81,391
voxels and every other is <= 206 -- surface trabeculae resolved at 0.179 mm.
Any interior blob touches a dozen of them, so "touches more than one component"
rejected everything.

This is the exact counting error the V0 README records against CRATER_MIN_BONE_MM3
("count components above a volume floor, never raw"), reproduced independently
here.

The gate therefore becomes: a proposed interior is accepted when it touches at
most ONE seed component ABOVE a bone-sized volume floor. Speckle is ignored for
the purposes of the count but is still real bone in the mask.
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
from probe_gated_ring import propose, clear_margin, HIGH  # noqa: E402


def real_bone_labels(seed, struct3, floor_voxels):
    """Label the seed, keep only components at or above the floor."""
    lab, n = ndimage.label(seed, structure=struct3)
    if n == 0:
        return lab, np.zeros(n + 1, bool)
    sizes = np.bincount(lab.ravel(), minlength=n + 1)
    big = sizes >= floor_voxels
    big[0] = False
    return lab, big


def gate(proposal, lab, big, struct3):
    """Keep blobs adjacent to at most one BIG seed component."""
    blobs, nblob = ndimage.label(proposal, structure=struct3)
    if nblob == 0:
        return proposal, 0

    big_lab = np.where(big[lab], lab, 0)
    neigh = ndimage.grey_dilation(big_lab, footprint=struct3)
    touch = np.where(proposal, neigh, 0)

    kept = np.zeros(nblob + 1, dtype=bool)
    rejected = 0
    for i, sl in enumerate(ndimage.find_objects(blobs), start=1):
        if sl is None:
            continue
        sub = blobs[sl] == i
        here = np.unique(touch[sl][sub])
        here = here[here > 0]
        if here.size <= 1:
            kept[i] = True
        else:
            rejected += 1
    return kept[blobs], rejected


def main() -> None:
    volume, geom = stack_source.load_volume()
    iso = np.load(WORK / "v0_iso.npy")
    fr = frames.IsoFrame(iso)
    vox = geom.voxel_mm3
    struct3 = ndimage.generate_binary_structure(3, 3)

    seed = clear_margin(volume >= HIGH)

    for floor_mm3 in (50.0, 200.0, 1000.0):
        floor_vox = int(floor_mm3 / vox)
        lab, big = real_bone_labels(seed, struct3, floor_vox)
        print(f"\n########## bone floor {floor_mm3} mm3 "
              f"({floor_vox} vox) -> {int(big.sum())} real bones ##########")

        for levels in ((112,), (112, 108), (112, 108, 104, 100)):
            prop = propose(volume, seed, levels)
            kept, rejected = gate(prop, lab, big, struct3)
            print(f"\n=== levels {levels} ===")
            print(f"  proposed {prop.sum()*vox/1000:6.2f} cm3 -> kept "
                  f"{kept.sum()*vox/1000:6.2f} cm3 ({rejected} blobs rejected)")
            for name, centre, radius, verdict in SITES:
                lo, hi = fr.window(centre, radius)
                slo = np.maximum(np.floor(frames.iso_to_source(lo, geom)).astype(int), 0)
                shi = np.minimum(np.ceil(frames.iso_to_source(hi, geom)).astype(int),
                                 np.array(volume.shape))
                w = kept[slo[0]:shi[0], slo[1]:shi[1], slo[2]:shi[2]]
                ws = seed[slo[0]:shi[0], slo[1]:shi[1], slo[2]:shi[2]]
                void = (~ws).sum()
                flag = "FILL" if "FILL" in verdict else "OPEN"
                print(f"    {name:20s} [{flag}] kept {w.sum()*vox:8.1f} mm3 "
                      f"= {100*w.sum()/max(1,void):5.1f}% of void")


if __name__ == "__main__":
    main()
