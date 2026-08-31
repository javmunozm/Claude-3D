"""Detect surface craters on the PIPELINE'S OWN ISO GRID, not on a
re-voxelisation of the exported mesh.

This project has twice been fooled by measuring a proposed fix against a
re-voxelisation of its own output ("A failed fix", and the local accretion
fill). Both reported large fillable concavities that do not exist in the grid
that generated the mesh. Everything here therefore reads work/v0_iso.npy, which
is exactly what to_isotropic() hands to marching cubes.

METHOD
------
A crater is material missing from a locally convex surface. Measure it as the
difference between the grid and its own morphological closing at a ball radius
R: closing(iso, R) & ~iso is every concavity narrower than 2R, whether it is a
dent in the outer wall (crater), a channel through bone (tunnel) or a joint
space (must never be filled).

Discriminating them is the whole difficulty and is NOT attempted here. This
pass only ENUMERATES and MEASURES; each blob is reported with the properties
that let a human decide:

  vol_mm3       size of the concavity
  n_bones       real bone components (>= CRATER_MIN_BONE_MM3) touching the blob
                -- 2 or more means filling it would bridge bones. Veto.
  open_frac     fraction of the blob's own volume that reaches the exterior
                background; 1.0 = a crater (open dent), 0.0 = an enclosed cavity
  depth_mm      max distance from the blob into the closing, i.e. how deep
  bbox_fill     fraction of its bounding box occupied -- a compact blob is a
                pocket, a thin rind wrapping a bone is a joint space

Reported in EXPORTED MESH coordinates via segment_axial._mesh_to_index's
inverse, so the numbers can be typed straight into NAMED_CRATERS.
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

VOX = v0.ISO_VOXEL_MM


def ball(radius_vox: int) -> np.ndarray:
    r = int(radius_vox)
    z, y, x = np.ogrid[-r:r + 1, -r:r + 1, -r:r + 1]
    return (z * z + y * y + x * x) <= r * r + 1e-9


def index_to_mesh(iso):
    """Inverse of segment_axial._mesh_to_index. Index -> exported mesh mm."""
    occupied = np.argwhere(iso)
    lo_idx = occupied.min(0)
    hi_idx = occupied.max(0)
    mesh_lo, _ = v0._exported_bounds(lo_idx, hi_idx)

    def to_mesh(idx):
        i0, i1, i2 = idx
        z = mesh_lo[2] + (i0 - lo_idx[0]) * VOX
        y = mesh_lo[1] + (hi_idx[1] - i1) * VOX
        x = mesh_lo[0] + (hi_idx[2] - i2) * VOX
        return np.array([x, y, z])

    return to_mesh


def analyse(iso, radius_vox=6, min_vol_mm3=60.0, zlo=None, zhi=None,
            ylo=None, yhi=None, verbose=True):
    to_mesh = index_to_mesh(iso)

    elem = ball(radius_vox)
    closed = ndimage.binary_closing(iso, structure=elem)
    concav = closed & ~iso

    if verbose:
        print(f"closing r={radius_vox * VOX:.1f} mm -> "
              f"{concav.sum() * VOX ** 3 / 1000:.2f} cm3 of concavity")

    # real bones, for the bridging veto
    lab_b, nb = ndimage.label(iso)
    sizes_b = ndimage.sum(iso, lab_b, range(1, nb + 1)) * VOX ** 3
    real = np.zeros(nb + 1, bool)
    real[1:] = sizes_b >= v0.CRATER_MIN_BONE_MM3

    # exterior background: the background component touching the grid boundary
    bg_lab, nbg = ndimage.label(~iso)
    boundary = set(bg_lab[0].flat) | set(bg_lab[-1].flat)
    boundary |= set(bg_lab[:, 0].flat) | set(bg_lab[:, -1].flat)
    boundary |= set(bg_lab[:, :, 0].flat) | set(bg_lab[:, :, -1].flat)
    boundary.discard(0)
    exterior = np.isin(bg_lab, list(boundary))

    lab, n = ndimage.label(concav)
    sizes = ndimage.sum(concav, lab, range(1, n + 1)) * VOX ** 3
    order = np.argsort(sizes)[::-1]

    dil = ndimage.generate_binary_structure(3, 3)
    out = []
    for j in order:
        vol = sizes[j]
        if vol < min_vol_mm3:
            break
        blob = lab == (j + 1)
        idx = np.argwhere(blob)
        c = idx.mean(0)
        cm = to_mesh(c)
        if zlo is not None and not (zlo <= cm[2] <= zhi):
            continue
        if ylo is not None and not (ylo <= cm[1] <= yhi):
            continue

        lo = np.maximum(idx.min(0) - 3, 0)
        hi = np.minimum(idx.max(0) + 4, np.array(iso.shape))
        w = (slice(lo[0], hi[0]), slice(lo[1], hi[1]), slice(lo[2], hi[2]))
        sub = blob[w]
        touch = ndimage.binary_dilation(sub, dil) & ~sub
        labs = np.unique(lab_b[w][touch])
        labs = labs[labs > 0]
        n_bones = int(real[labs].sum())

        open_frac = float((blob[w] & exterior[w]).sum()) / max(sub.sum(), 1)
        ext = idx.max(0) - idx.min(0) + 1
        bbox_fill = sub.sum() / float(np.prod(ext))
        # depth: distance transform inside the blob
        depth = ndimage.distance_transform_edt(sub).max() * VOX * 2

        lo_m = to_mesh(idx.min(0))
        hi_m = to_mesh(idx.max(0))
        box_lo = np.minimum(lo_m, hi_m)
        box_hi = np.maximum(lo_m, hi_m)

        out.append(dict(vol=vol, centre=cm, n_bones=n_bones,
                        open_frac=open_frac, bbox_fill=bbox_fill,
                        depth=depth, box_lo=box_lo, box_hi=box_hi,
                        ext_mm=ext * VOX, label=j + 1))
    return out, concav, lab


def main():
    iso = np.load(WORK / "v0_iso.npy")
    print(f"iso {iso.shape}  {iso.sum() * VOX ** 3 / 1000:.2f} cm3  "
          f"tunnels {v0._tunnel_count(iso)}  bones {v0._real_bone_count(iso)}")

    radius = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    res, _, _ = analyse(iso, radius_vox=radius, min_vol_mm3=60.0)

    print(f"\n{'vol mm3':>9} {'X':>8} {'Y':>8} {'Z':>7} {'bones':>5} "
          f"{'open%':>6} {'bbfill':>7} {'depth':>6}  extent mm")
    for r in res[:45]:
        c = r["centre"]
        print(f"{r['vol']:9.0f} {c[0]:8.2f} {c[1]:8.2f} {c[2]:7.2f} "
              f"{r['n_bones']:5d} {100 * r['open_frac']:6.1f} "
              f"{r['bbox_fill']:7.2f} {r['depth']:6.2f}  "
              f"{r['ext_mm'][0]:.0f}x{r['ext_mm'][1]:.0f}x{r['ext_mm'][2]:.0f}")


if __name__ == "__main__":
    main()
