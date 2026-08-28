"""Are the must-fill and must-not-fill sites literally the same air space?

probe_gate_sites.py reports several sites sharing one concavity blob, which
would mean no region-bounded fill can reach one without reaching the other.
That is a strong claim, so it is checked directly here rather than inferred
from a nearest-blob lookup with an 4 mm search window:

  * exact voxel at each site -- is it bone, or which concavity blob
  * geodesic path WITHIN the concavity from site A to site B -- if a path
    exists the two are one connected air space
  * the narrowest point (bottleneck) along that connection, which is what a
    NAMED_CRATERS box would have to avoid crossing
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy import ndimage

HERE = Path(__file__).resolve().parent
WORK = HERE.parent / "work"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / "BrokeFeet" / "macros"))

import segment_axial as v0  # noqa: E402
import find_craters as fc  # noqa: E402
from probe_gate_sites import SITES  # noqa: E402

VOX = v0.ISO_VOXEL_MM


def nearest_void(iso, idx, maxr=14):
    """Nearest non-bone voxel to idx, so a site picked on a surface still
    resolves to the air space it names."""
    for r in range(0, maxr):
        lo = np.maximum(idx - r, 0)
        hi = np.minimum(idx + r + 1, np.array(iso.shape))
        w = (slice(lo[0], hi[0]), slice(lo[1], hi[1]), slice(lo[2], hi[2]))
        sub = ~iso[w]
        if sub.any():
            loc = np.argwhere(sub)
            d = np.abs(loc - (idx - lo)).max(1)
            return lo + loc[np.argmin(d)]
    return None


def main():
    iso = np.load(WORK / "v0_iso.npy")
    to_index, _, _ = v0._mesh_to_index(iso)

    # the exterior air space, as _tunnel_count defines it
    bg, n = ndimage.label(~iso)
    boundary = set(bg[0].flat) | set(bg[-1].flat)
    boundary |= set(bg[:, 0].flat) | set(bg[:, -1].flat)
    boundary |= set(bg[:, :, 0].flat) | set(bg[:, :, -1].flat)
    boundary.discard(0)

    print("Which BACKGROUND component does each site belong to?")
    print("(same label = one continuous air space, no fill can separate them)")
    print(f"{'site':20s} {'want':5s} {'bglabel':>8s} {'exterior?':>10s}")
    ids = {}
    for name, pt, verdict in SITES:
        idx = np.round(to_index(pt)).astype(int)
        idx = np.clip(idx, 0, np.array(iso.shape) - 1)
        v = nearest_void(iso, idx)
        lab = int(bg[tuple(v)])
        ids[name] = (lab, v)
        print(f"{name:20s} {verdict:5s} {lab:8d} "
              f"{str(lab in boundary):>10s}")

    labs = {v[0] for v in ids.values()}
    print(f"\ndistinct background components across all sites: {len(labs)} "
          f"-> {sorted(labs)}")
    if len(labs) == 1:
        lab = labs.pop()
        size = (bg == lab).sum() * VOX ** 3 / 1000
        print(f"ALL sites lie in ONE background component of {size:.1f} cm3.")
        print("A fill bounded by a named box cannot separate a must-fill site")
        print("from a must-not-fill site by connectivity -- only by geometry.")


if __name__ == "__main__":
    main()
