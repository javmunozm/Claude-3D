"""Sample SOURCE intensities at the operator-named sites.

The whole V1 premise -- replace the global 115 with something locally adaptive
-- stands or falls on whether the trabecular interior of a named void is
separable from the soft tissue of a named joint by anything OTHER than
brightness. This prints the numbers rather than assuming them.

Sites are MESH coordinates (post-mirror), as reported by MeshLab.
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

# (name, mesh xyz, radius mm, verdict)
SITES = (
    ("hollow calcaneus",  (-109.92, -160.54,  54.72), 8.0, "MUST FILL"),
    ("navicular/talar r6", (-118.74, -128.10,  66.66), 6.0, "MUST FILL"),
    ("navicular/talar r12", (-118.74, -128.10, 66.66), 12.0, "MUST FILL"),
    ("ankle mortise",     (-114.53, -145.15,  74.43), 6.0, "MUST STAY OPEN"),
    ("tarsal rind",       (-120.71, -110.99,  49.72), 6.0, "MUST STAY OPEN"),
)


def describe(values, label):
    if values.size == 0:
        print(f"    {label}: EMPTY")
        return
    q = np.percentile(values, [5, 25, 50, 75, 95])
    print(f"    {label:22s} n={values.size:8,d} mean={values.mean():6.1f} "
          f"p5={q[0]:5.1f} p25={q[1]:5.1f} p50={q[2]:5.1f} "
          f"p75={q[3]:5.1f} p95={q[4]:5.1f}")


def main() -> None:
    volume, geom = stack_source.load_volume()
    iso = np.load(WORK / "v0_iso.npy")
    fr = frames.IsoFrame(iso)
    print(f"iso grid {iso.shape}, mesh bounds "
          f"{np.round(fr.mesh_lo,1)} .. {np.round(fr.mesh_hi,1)}")

    mask = np.load(WORK / "v0_mask.npy")

    for name, centre, radius, verdict in SITES:
        lo, hi = fr.window(centre, radius)
        lo = np.maximum(lo, 0)
        hi = np.minimum(hi, np.array(iso.shape))
        sub_iso = iso[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]]

        # same window in SOURCE indices
        slo = np.floor(frames.iso_to_source(lo, geom)).astype(int)
        shi = np.ceil(frames.iso_to_source(hi, geom)).astype(int)
        slo = np.maximum(slo, 0)
        shi = np.minimum(shi, np.array(volume.shape))
        sub_vol = volume[slo[0]:shi[0], slo[1]:shi[1], slo[2]:shi[2]]
        sub_mask = mask[slo[0]:shi[0], slo[1]:shi[1], slo[2]:shi[2]]

        vox = geom.voxel_mm3
        print(f"\n{name}  r={radius} mm  [{verdict}]")
        print(f"  iso window {sub_iso.shape} bone {sub_iso.mean()*100:5.1f}% "
              f"void {(~sub_iso).sum()*0.125:7.1f} mm3")
        print(f"  src window {sub_vol.shape} mask {sub_mask.mean()*100:5.1f}% "
              f"empty {(~sub_mask).sum()*vox:7.1f} mm3")
        describe(sub_vol[sub_mask], "IN mask (bone)")
        describe(sub_vol[~sub_mask], "OUT of mask (void)")

        # the empty voxels that a lowered threshold would recruit
        for t in (78, 85, 95, 105, 115):
            recruit = (~sub_mask) & (sub_vol >= t)
            print(f"      threshold>={t:3d} would add "
                  f"{recruit.sum()*vox:8.1f} mm3 "
                  f"({100*recruit.sum()/max(1,(~sub_mask).sum()):5.1f}% of void)")


if __name__ == "__main__":
    main()
