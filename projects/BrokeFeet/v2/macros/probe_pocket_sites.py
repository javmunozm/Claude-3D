"""Which recessed pocket does each named acceptance site fall in?

crater_map.py ranks pockets by how recessed they are. This checks the ranking
against the four gate sites and the five operator craters, because the ranking
is only useful if it puts the must-fill sites ABOVE the must-not-fill ones --
which is the test every previous discriminator in this project has failed.
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
import crater_map as cmap  # noqa: E402
import find_craters as fc  # noqa: E402
from probe_gate_sites import SITES  # noqa: E402

VOX = v0.ISO_VOXEL_MM


def main():
    iso = np.load(WORK / "v0_iso.npy")
    r_open = float(sys.argv[1]) if len(sys.argv) > 1 else 2.0
    min_depth = float(sys.argv[2]) if len(sys.argv) > 2 else 4.0

    depth, outside = cmap.crater_depth(iso, r_open)
    pocket = depth >= min_depth
    lab, n = ndimage.label(pocket)
    sizes = ndimage.sum(pocket, lab, range(1, n + 1)) * VOX ** 3
    rank = {int(l + 1): r for r, l in enumerate(np.argsort(sizes)[::-1])}

    to_index, _, _ = v0._mesh_to_index(iso)
    to_mesh = fc.index_to_mesh(iso)

    print(f"r_open={r_open} mm  min_depth={min_depth} mm  "
          f"{n} pockets, {pocket.sum() * VOX ** 3 / 1000:.2f} cm3\n")
    print(f"{'site':20s} {'want':5s} {'rank':>4s} {'pktvol':>8s} "
          f"{'depth@site':>10s}  pocket centre")
    for name, pt, verdict in SITES:
        idx = np.round(to_index(pt)).astype(int)
        idx = np.clip(idx, 0, np.array(iso.shape) - 1)
        # nearest pocket voxel within 6 mm
        r = int(6.0 / VOX)
        lo = np.maximum(idx - r, 0)
        hi = np.minimum(idx + r + 1, np.array(iso.shape))
        w = (slice(lo[0], hi[0]), slice(lo[1], hi[1]), slice(lo[2], hi[2]))
        sub = lab[w]
        d_at = depth[tuple(idx)]
        if not (sub > 0).any():
            print(f"{name:20s} {verdict:5s} {'-':>4s} {'-':>8s} "
                  f"{d_at:10.2f}  (no pocket within 6 mm)")
            continue
        loc = np.argwhere(sub > 0)
        dd = np.abs(loc - (idx - lo)).max(1)
        best = int(sub[tuple(loc[np.argmin(dd)])])
        c = to_mesh(np.argwhere(lab == best).mean(0))
        print(f"{name:20s} {verdict:5s} {rank[best]:4d} {sizes[best - 1]:8.0f} "
              f"{d_at:10.2f}  ({c[0]:.1f},{c[1]:.1f},{c[2]:.1f})")


if __name__ == "__main__":
    main()
