"""Map surface craters as SEPARATED pockets, on the pipeline's own iso grid.

find_craters.py showed that a plain closing merges every tarsal concavity into
one 12 cm3 blob touching 6 bones, because the whole interosseous air space is
one connected region (probe_blob_identity.py: all nine named sites share ONE
background component of 5824 cm3). Enumerating "the craters" therefore needs a
pocket definition that does not rely on the concavity being disconnected.

DEFINITION USED HERE
--------------------
For each empty voxel, compute the distance to the nearest exterior "open air"
-- meaning background that survives an opening by a ball of radius R_open,
i.e. genuinely outside the foot rather than in a crevice between bones. A
pocket is then empty space that is FAR from open air but still connected to it:
a dent whose mouth is narrower than its depth.

  depth_mm  = distance from the voxel to genuine open air
  A crater voxel has depth_mm >= MIN_DEPTH, and is not enclosed (open_frac 1).

This ranks by how RECESSED a void is rather than by how much a closing spans,
so a joint space -- which is a thin slot open along its whole length -- scores
LOW, while a blind pocket eaten into a cortical wall scores HIGH. That is the
opposite ranking to the closing-based measure, and is the point.

Reported in exported-mesh coordinates, ready for NAMED_CRATERS.
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


def open_air(iso, r_open_mm=4.0):
    """Background that a ball of radius r_open can occupy without touching
    bone, dilated back -- i.e. space genuinely outside the foot, excluding
    every crevice narrower than the ball."""
    r = int(round(r_open_mm / VOX))
    free = ~iso
    # distance from every empty voxel to the nearest bone voxel
    dist = ndimage.distance_transform_edt(free) * VOX
    core = dist >= r_open_mm
    # keep only the core that reaches the grid boundary (outside, not a cavity)
    lab, n = ndimage.label(core)
    if n == 0:
        return np.zeros_like(iso)
    edge = set(lab[0].flat) | set(lab[-1].flat)
    edge |= set(lab[:, 0].flat) | set(lab[:, -1].flat)
    edge |= set(lab[:, :, 0].flat) | set(lab[:, :, -1].flat)
    edge.discard(0)
    outside_core = np.isin(lab, list(edge))
    return outside_core


def crater_depth(iso, r_open_mm=4.0):
    """Geodesic-ish depth: distance through free space to genuine open air."""
    outside = open_air(iso, r_open_mm)
    free = ~iso
    # distance from open air, measured only through free space.
    # EDT of "not outside" gives euclidean distance to the nearest outside
    # voxel; that is an underestimate of geodesic depth but monotone in it and
    # far cheaper. Bone is excluded afterwards.
    depth = ndimage.distance_transform_edt(~outside) * VOX
    depth[~free] = 0.0
    return depth, outside


def main():
    iso = np.load(WORK / "v0_iso.npy")
    r_open = float(sys.argv[1]) if len(sys.argv) > 1 else 4.0
    min_depth = float(sys.argv[2]) if len(sys.argv) > 2 else 3.0

    print(f"iso {iso.shape} {iso.sum() * VOX ** 3 / 1000:.2f} cm3")
    depth, outside = crater_depth(iso, r_open)
    print(f"open-air ball r={r_open} mm -> "
          f"{outside.sum() * VOX ** 3 / 1000:.0f} cm3 of genuine exterior")

    pocket = depth >= min_depth
    print(f"pockets deeper than {min_depth} mm: "
          f"{pocket.sum() * VOX ** 3 / 1000:.2f} cm3")

    to_mesh = fc.index_to_mesh(iso)
    lab_b, nb = ndimage.label(iso)
    sizes_b = ndimage.sum(iso, lab_b, range(1, nb + 1)) * VOX ** 3
    real = np.zeros(nb + 1, bool)
    real[1:] = sizes_b >= v0.CRATER_MIN_BONE_MM3
    dil = ndimage.generate_binary_structure(3, 3)

    lab, n = ndimage.label(pocket)
    sizes = ndimage.sum(pocket, lab, range(1, n + 1)) * VOX ** 3
    order = np.argsort(sizes)[::-1]

    print(f"\n{'vol mm3':>8} {'X':>8} {'Y':>8} {'Z':>7} {'bones':>5} "
          f"{'maxdep':>7} {'bbfill':>7}  extent mm")
    rows = []
    for j in order[:30]:
        if sizes[j] < 20:
            break
        blob = lab == (j + 1)
        idx = np.argwhere(blob)
        cm = to_mesh(idx.mean(0))
        lo = np.maximum(idx.min(0) - 2, 0)
        hi = np.minimum(idx.max(0) + 3, np.array(iso.shape))
        w = (slice(lo[0], hi[0]), slice(lo[1], hi[1]), slice(lo[2], hi[2]))
        sub = blob[w]
        touch = ndimage.binary_dilation(sub, dil) & ~sub
        labs = np.unique(lab_b[w][touch]); labs = labs[labs > 0]
        nbones = int(real[labs].sum())
        ext = (idx.max(0) - idx.min(0) + 1) * VOX
        bbfill = sub.sum() / float(np.prod(idx.max(0) - idx.min(0) + 1))
        md = depth[blob].max()
        lo_m = to_mesh(idx.min(0)); hi_m = to_mesh(idx.max(0))
        blo = np.minimum(lo_m, hi_m); bhi = np.maximum(lo_m, hi_m)
        rows.append((sizes[j], cm, nbones, md, bbfill, ext, blo, bhi))
        print(f"{sizes[j]:8.0f} {cm[0]:8.2f} {cm[1]:8.2f} {cm[2]:7.2f} "
              f"{nbones:5d} {md:7.2f} {bbfill:7.2f}  "
              f"{ext[0]:.0f}x{ext[1]:.0f}x{ext[2]:.0f}")

    print("\nNAMED_CRATERS-style boxes (x_lo,y_lo,z_lo,x_hi,y_hi,z_hi):")
    for s, cm, nbones, md, bbfill, ext, blo, bhi in rows[:12]:
        print(f"  ({blo[0]:.2f}, {blo[1]:.2f}, {blo[2]:.2f}, "
              f"{bhi[0]:.2f}, {bhi[1]:.2f}, {bhi[2]:.2f}, 2.5),"
              f"   # {s:.0f} mm3 depth {md:.1f} bones {nbones}")


if __name__ == "__main__":
    main()
