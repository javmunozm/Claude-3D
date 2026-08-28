"""Per-crater radius sweep, each measured against the SAME baseline grid.

The BrokeFeet README records that radius is a cliff and not a knob: on the one
crater it was swept, 1.0 -> +5 tunnels, 1.5 -> +1, 2.0 -> +2, 2.5 -> +0,
3.0 -> +3, and only 2.5 leaves the topology untouched. That sweep was done on
one crater. If radius is genuinely a cliff then its position is a property of
the individual crater, not a global constant, and a single value cannot be
assumed to transfer.

Each (crater, radius) pair is applied to the UNPATCHED baseline so the
measurements are independent -- applying them cumulatively makes each result
depend on the acceptance order.
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
import crater_map as cmap  # noqa: E402
from patch_craters_test import (CRATERS, box_from_centre, _pocket_in_box,
                                MORTISE, RIND, gap_at)  # noqa: E402

VOX = v0.ISO_VOXEL_MM
RADII = (1.0, 1.5, 2.0, 2.5, 3.0, 3.5)


def main():
    half = float(sys.argv[1]) if len(sys.argv) > 1 else 5.0
    iso0 = np.load(WORK / "v0_iso.npy")
    to_index, _, _ = v0._mesh_to_index(iso0)
    struct = ndimage.generate_binary_structure(3, 1)

    bones0 = v0._real_bone_count(iso0)
    tun0 = v0._tunnel_count(iso0)
    depth0, _ = cmap.crater_depth(iso0, 2.0)
    print(f"baseline: bones {bones0}  tunnels {tun0}  "
          f"vol {iso0.sum() * VOX ** 3 / 1000:.3f} cm3  half-box {half} mm\n")

    for name, centre in CRATERS:
        box = box_from_centre(centre, half)
        p0 = _pocket_in_box(depth0, box, to_index, iso0.shape, 2.0)
        c1 = to_index(box[:3]); c2 = to_index(box[3:6])
        lo = np.maximum(np.floor(np.minimum(c1, c2)).astype(int) - 4, 0)
        hi = np.minimum(np.ceil(np.maximum(c1, c2)).astype(int) + 5,
                        np.array(iso0.shape))
        w = (slice(lo[0], hi[0]), slice(lo[1], hi[1]), slice(lo[2], hi[2]))
        print(f"{name}  ({centre[0]:.1f},{centre[1]:.1f},{centre[2]:.1f})  "
              f"pocket {p0:.0f} mm3")
        print(f"  {'r mm':>5} {'added':>8} {'bones':>5} {'tunnels':>8} "
              f"{'d':>4} {'removed':>8} {'mortise':>8} {'rind':>6}")
        for r in RADII:
            it = max(1, int(round(r / VOX)))
            sub = iso0[w]
            prop = ndimage.binary_closing(sub, structure=struct, iterations=it)
            added = int((prop & ~sub).sum())
            trial = iso0.copy()
            trial[w] = sub | prop
            b = v0._real_bone_count(trial)
            t = v0._tunnel_count(trial)
            d1, _ = cmap.crater_depth(trial, 2.0)
            p1 = _pocket_in_box(d1, box, to_index, trial.shape, 2.0)
            rem = 100 * (p0 - p1) / p0 if p0 > 0 else 0.0
            mg = gap_at(trial, MORTISE, to_index)
            rg = gap_at(trial, RIND, to_index)
            flag = "" if (b == bones0 and t <= tun0) else "  <-- fails gate"
            print(f"  {r:5.1f} {added * VOX ** 3:8.0f} {b:5d} {t:8d} "
                  f"{t - tun0:+4d} {rem:7.1f}% {mg:8.3f} {rg:6.3f}{flag}")
        print()


if __name__ == "__main__":
    main()
