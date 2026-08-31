"""Where the acceptance-gate sites sit in the concavity map.

The V1 README names four sites: two that MUST be filled and two that MUST stay
open. find_craters.py enumerates concavities without deciding. This joins the
two, so it is visible whether a proposed fill lands on a must-fill or a
must-not-fill site -- which is the failure this project keeps repeating.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy import ndimage

HERE = Path(__file__).resolve().parent
WORK = HERE.parent / "work"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / "v0" / "macros"))

import segment_axial as v0  # noqa: E402
import find_craters as fc  # noqa: E402

VOX = v0.ISO_VOXEL_MM

# (name, mesh xyz, verdict)
SITES = [
    ("hollow calcaneus", (-109.92, -160.54, 54.72), "FILL"),
    ("navicular/talar", (-118.74, -128.10, 66.66), "FILL"),
    ("ankle mortise", (-114.53, -145.15, 74.43), "OPEN"),
    ("tarsal rind", (-120.71, -110.99, 49.72), "OPEN"),
    # the five operator-located craters, BrokeFeet README
    ("op crater 1", (-114.8, -125.0, 67.5), "FILL"),
    ("op crater 2", (-106.5, -135.5, 73.5), "FILL"),
    ("op crater 3", (-98.4, -112.9, 70.0), "FILL"),
    ("op crater 4", (-126.2, -129.5, 73.5), "FILL"),
    ("op crater 5", (-130.0, -138.1, 56.4), "FILL"),
]


def main():
    iso = np.load(WORK / "v0_iso.npy")
    to_index, _, _ = v0._mesh_to_index(iso)

    radius = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    res, concav, lab = fc.analyse(iso, radius_vox=radius, min_vol_mm3=1.0,
                                  verbose=True)
    by_label = {r["label"]: r for r in res}

    print(f"\nconcavity blob each named site falls in "
          f"(closing r={radius * VOX:.1f} mm):")
    print(f"{'site':20s} {'want':5s} {'blobvol':>8s} {'bones':>5s} "
          f"{'open%':>6s} {'bbfill':>7s}  note")
    for name, pt, verdict in SITES:
        idx = np.round(to_index(pt)).astype(int)
        idx = np.clip(idx, 0, np.array(iso.shape) - 1)
        # search a small neighbourhood for the nearest concavity voxel
        r = 8
        lo = np.maximum(idx - r, 0)
        hi = np.minimum(idx + r + 1, np.array(iso.shape))
        w = (slice(lo[0], hi[0]), slice(lo[1], hi[1]), slice(lo[2], hi[2]))
        sub = lab[w]
        hits = sub[sub > 0]
        if hits.size == 0:
            print(f"{name:20s} {verdict:5s} {'-':>8s} {'-':>5s} {'-':>6s} "
                  f"{'-':>7s}  no concavity within 4 mm "
                  f"(iso={bool(iso[tuple(idx)])})")
            continue
        vals, counts = np.unique(hits, return_counts=True)
        best = vals[np.argmax(counts)]
        r_ = by_label.get(int(best))
        if r_ is None:
            print(f"{name:20s} {verdict:5s} tiny blob {best}")
            continue
        c = r_["centre"]
        print(f"{name:20s} {verdict:5s} {r_['vol']:8.0f} {r_['n_bones']:5d} "
              f"{100 * r_['open_frac']:6.1f} {r_['bbox_fill']:7.2f}  "
              f"blob centre ({c[0]:.1f},{c[1]:.1f},{c[2]:.1f}) "
              f"ext {r_['ext_mm'][0]:.0f}x{r_['ext_mm'][1]:.0f}x"
              f"{r_['ext_mm'][2]:.0f}")


if __name__ == "__main__":
    main()
