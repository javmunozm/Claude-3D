"""Acceptance measurement: V1 against V0, on the pipelines' own iso grids.

Everything here is measured on the isotropic grid each pipeline produced, never
on a re-voxelisation of an exported mesh. That substitution has fooled this
project twice (README: MAX_FILLED_HOLE_MM2 predicted genus 333->232 and
delivered 301->300; the local accretion fill measured genus 174->39 on the mesh
and <=4 % crater removal on the grid).

Reported per the acceptance list:
  * void volume in each named ball, before and after
  * tibiotalar gap at the ankle mortise
  * component count above the size filter (a DROP means bones fused)
  * volume, genus and cavity count
  * per-band area/volume, so no band can be traded for another
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
from probe_sites import SITES  # noqa: E402

ISO = 0.5
VOX = ISO ** 3
MIN_BONE_MM3 = 50.0


def ball_void(iso, fr, centre, radius):
    lo, hi = fr.window(centre, radius)
    lo = np.maximum(lo, 0)
    hi = np.minimum(hi, np.array(iso.shape))
    sub = iso[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]]
    gz, gy, gx = np.ogrid[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]]
    ci = fr.to_index(centre)
    d2 = ((gz - ci[0]) ** 2 + (gy - ci[1]) ** 2 + (gx - ci[2]) ** 2) * ISO ** 2
    ball = d2 <= radius * radius
    return float(((~sub) & ball).sum() * VOX), float((ball).sum() * VOX)


def enclosed_void(iso, fr, centre, radius):
    """Void inside the ball that does NOT reach the ball's surface.

    This is the number that matters for a hollow bone: an unroofed interior is
    empty space wrapped in bone, whereas a joint space runs out of the window.
    """
    lo, hi = fr.window(centre, radius + 2)
    lo = np.maximum(lo, 0)
    hi = np.minimum(hi, np.array(iso.shape))
    sub = iso[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]]
    lab, n = ndimage.label(~sub)
    if n == 0:
        return 0.0
    edge = set(lab[0].flat) | set(lab[-1].flat)
    edge |= set(lab[:, 0].flat) | set(lab[:, -1].flat)
    edge |= set(lab[:, :, 0].flat) | set(lab[:, :, -1].flat)
    edge.discard(0)
    return float((~np.isin(lab, list(edge)) & ~sub).sum() * VOX)


def topology(iso):
    """(components, cavities, tunnels) via b1 = b0 + b2 - chi."""
    from skimage import measure
    lab, n = ndimage.label(iso)
    sizes = ndimage.sum(iso, lab, range(1, n + 1)) * VOX
    real = int((sizes >= MIN_BONE_MM3).sum())
    chi = measure.euler_number(iso, connectivity=1)
    bg, nb = ndimage.label(~iso)
    edge = set(bg[0].flat) | set(bg[-1].flat)
    edge |= set(bg[:, 0].flat) | set(bg[:, -1].flat)
    edge |= set(bg[:, :, 0].flat) | set(bg[:, :, -1].flat)
    edge.discard(0)
    cavities = nb - len(edge)
    tunnels = n + cavities - chi
    return n, real, cavities, tunnels


def gap_between(iso, fr, centre, radius, min_mm3=200.0):
    """Distance between the two largest bone components inside a window.

    If they have fused the window holds ONE component and the gap is reported
    as 0.0 -- which is the failure this measurement exists to catch.
    """
    lo, hi = fr.window(centre, radius)
    lo = np.maximum(lo, 0)
    hi = np.minimum(hi, np.array(iso.shape))
    sub = iso[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]]
    lab, n = ndimage.label(sub)
    if n < 2:
        return 0.0, n
    sizes = ndimage.sum(sub, lab, range(1, n + 1)) * VOX
    order = np.argsort(sizes)[::-1]
    big = [i + 1 for i in order if sizes[i] >= min_mm3]
    if len(big) < 2:
        return 0.0, len(big)
    a = lab == big[0]
    b = lab == big[1]
    dist = ndimage.distance_transform_edt(~a, sampling=(ISO, ISO, ISO))
    return float(dist[b].min()), len(big)


def bands(iso, fr, n=7):
    """Per-band bone fraction and surface roughness, heel to leg."""
    z0, z1 = fr.mesh_lo[2], fr.mesh_hi[2]
    edges = np.linspace(z0, z1, n + 1)
    out = []
    for i in range(n):
        i0 = int(fr.to_index((fr.mesh_lo[0], fr.mesh_lo[1], edges[i]))[0])
        i1 = int(fr.to_index((fr.mesh_lo[0], fr.mesh_lo[1], edges[i + 1]))[0])
        i0, i1 = max(min(i0, i1), 0), min(max(i0, i1), iso.shape[0])
        if i1 <= i0:
            continue
        sub = iso[i0:i1]
        vol = sub.sum() * VOX
        if vol == 0:
            continue
        surf = (sub & ~ndimage.binary_erosion(
            sub, ndimage.generate_binary_structure(3, 1))).sum() * ISO ** 2
        out.append((edges[i], edges[i + 1], vol / 1000.0, surf / max(vol, 1e-9)))
    return out


def report(iso, tag):
    fr = frames.IsoFrame(iso)
    n, real, cav, tun = topology(iso)
    print(f"\n########## {tag} ##########")
    print(f"  volume    {iso.sum()*VOX/1000:8.2f} cm3")
    print(f"  components {n} raw, {real} >= {MIN_BONE_MM3} mm3")
    print(f"  cavities  {cav}   tunnels(genus) {tun}")

    print("  named sites (void inside ball / enclosed void):")
    for name, centre, radius, verdict in SITES:
        void, ball = ball_void(iso, fr, centre, radius)
        enc = enclosed_void(iso, fr, centre, radius)
        flag = "FILL" if "FILL" in verdict else "OPEN"
        print(f"    {name:20s} r={radius:4.1f} [{flag}] void {void:8.1f} mm3 "
              f"({100*void/ball:4.1f}% of ball), enclosed {enc:7.1f} mm3")

    g, nb = gap_between(iso, fr, (-114.53, -145.15, 74.43), 12.0)
    print(f"  tibiotalar gap  {g:.3f} mm  ({nb} bodies >=200 mm3 in window)")
    g2, nb2 = gap_between(iso, fr, (-120.71, -110.99, 49.72), 12.0)
    print(f"  tarsal rind gap {g2:.3f} mm  ({nb2} bodies >=200 mm3 in window)")

    print("  per-band  z_lo   z_hi     cm3   area/volume")
    for lo, hi, vol, av in bands(iso, fr):
        print(f"           {lo:6.1f} {hi:6.1f} {vol:7.2f}   {av:.3f}")
    return fr


def main() -> None:
    v0 = np.load(WORK / "v0_iso.npy")
    report(v0, "V0 (segment_axial.py, all four repair passes)")
    p = WORK / "v1_iso.npy"
    if p.exists():
        report(np.load(p), "V1 (segment_v1.py, adaptive threshold, no repair)")
    else:
        print("\nv1_iso.npy not present yet -- run segment_v1.py")


if __name__ == "__main__":
    main()
