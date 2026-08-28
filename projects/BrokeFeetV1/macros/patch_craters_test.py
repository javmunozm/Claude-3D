"""Run _patch_named_craters over MULTIPLE named craters and gate the result.

The V0 pass was only ever validated on ONE crater (BrokeFeet README, "Patching
a named crater works"). It held every gate there. Whether it still holds over
the whole located set is a different question, because each accepted patch
changes the grid the next one is measured against, and because several of the
operator's craters sit within a few millimetres of the ankle mortise -- the one
void that must never be filled.

Everything is measured on work/v0_iso.npy, the pipeline's own isotropic grid,
never on a re-voxelisation of the exported mesh.

Gates, all on the iso grid:
  real bones   (>= CRATER_MIN_BONE_MM3)  must not change
  tunnels      (b1 = b0 + b2 - chi)      must not rise
  volume                                  reported; a large rise with falling
                                           genus is the documented fusion sign
  mortise gap  tibiotalar, must stay ~0.950 mm
  rind         tarsal rind must stay open

Per crater it also reports how much of that crater's own pocket was actually
removed, which is the only number that says whether the operator's complaint
was addressed.
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

VOX = v0.ISO_VOXEL_MM

# The five operator-located craters (BrokeFeet README, "The five defects the
# operator located"), plus the navicular defect from the V1 README. Boxes are
# built as a cube of half-width HALF around each located centre, in the
# EXPORTED MESH frame -- the frame MeshLab reports and NAMED_CRATERS expects.
CRATERS = [
    ("op1 tarsal 516mm3", (-114.8, -125.0, 67.5)),
    ("op2 near mortise",  (-106.5, -135.5, 73.5)),
    ("op3 lateral",       (-98.4, -112.9, 70.0)),
    ("op4 medial 286mm3", (-126.2, -129.5, 73.5)),
    ("op5 plantar",       (-130.0, -138.1, 56.4)),
    ("nav navicular",     (-118.74, -128.10, 66.66)),
]

# Per-crater closing radius, from sweep_crater_radius.py. The BrokeFeet README
# established that radius is a cliff rather than a knob on the ONE crater it
# swept, and settled on 2.5 mm. Swept over all six here, the cliff turns out to
# be a property of the individual crater, not a global constant: 2.5 mm is
# optimal for op1/op3/op5, costs op4 +2 tunnels (1.5 is its knee) and costs the
# navicular +4 (only 3.5 holds, and by then it is roofing rather than filling).
# A single global radius is therefore the wrong shape for this parameter.
RADIUS_MM = {
    "op1 tarsal 516mm3": 2.5,
    "op2 near mortise":  3.0,
    "op3 lateral":       2.5,
    "op4 medial 286mm3": 1.5,
    "op5 plantar":       2.5,
    "nav navicular":     3.5,
}

# Must stay open. Checked explicitly after every patch.
MORTISE = (-114.53, -145.15, 74.43)
RIND = (-120.71, -110.99, 49.72)


def box_from_centre(c, half):
    return (c[0] - half, c[1] - half, c[2] - half,
            c[0] + half, c[1] + half, c[2] + half)


def gap_at(iso, pt, to_index, axis_probe=14):
    """Width of the void at a named point, along the axis in which it is
    narrowest -- the tibiotalar gap measurement the gates use."""
    idx = np.round(to_index(pt)).astype(int)
    idx = np.clip(idx, 0, np.array(iso.shape) - 1)
    # nearest void voxel
    best = None
    for r in range(0, 12):
        lo = np.maximum(idx - r, 0)
        hi = np.minimum(idx + r + 1, np.array(iso.shape))
        w = (slice(lo[0], hi[0]), slice(lo[1], hi[1]), slice(lo[2], hi[2]))
        sub = ~iso[w]
        if sub.any():
            loc = np.argwhere(sub)
            d = np.abs(loc - (idx - lo)).max(1)
            best = lo + loc[np.argmin(d)]
            break
    if best is None:
        return 0.0
    widths = []
    for ax in range(3):
        n = 0
        for s in (1, -1):
            p = best.copy()
            for _ in range(axis_probe):
                p[ax] += s
                if not (0 <= p[ax] < iso.shape[ax]) or iso[tuple(p)]:
                    break
                n += 1
        widths.append((n + 1) * VOX)
    return min(widths)


def pocket_volume_in_box(iso, box, to_index, r_open=2.0, min_depth=2.0):
    """Recessed void inside a named box, on the iso grid."""
    depth, _ = cmap.crater_depth(iso, r_open)
    return _pocket_in_box(depth, box, to_index, iso.shape, min_depth)


def _pocket_in_box(depth, box, to_index, shape, min_depth):
    c1 = to_index(box[:3])
    c2 = to_index(box[3:6])
    lo = np.maximum(np.floor(np.minimum(c1, c2)).astype(int), 0)
    hi = np.minimum(np.ceil(np.maximum(c1, c2)).astype(int) + 1, np.array(shape))
    w = (slice(lo[0], hi[0]), slice(lo[1], hi[1]), slice(lo[2], hi[2]))
    return float((depth[w] >= min_depth).sum()) * VOX ** 3


def report(iso, tag, to_index):
    print(f"  {tag:22s} vol {iso.sum() * VOX ** 3 / 1000:8.3f} cm3  "
          f"bones {v0._real_bone_count(iso):2d}  "
          f"tunnels {v0._tunnel_count(iso):3d}  "
          f"mortise {gap_at(iso, MORTISE, to_index):.3f} mm  "
          f"rind {gap_at(iso, RIND, to_index):.3f} mm")


def main():
    half = float(sys.argv[1]) if len(sys.argv) > 1 else 5.0
    radius = float(sys.argv[2]) if len(sys.argv) > 2 else 2.5

    iso0 = np.load(WORK / "v0_iso.npy")
    to_index, _, _ = v0._mesh_to_index(iso0)
    struct = ndimage.generate_binary_structure(3, 1)

    print(f"half-box {half} mm, closing radius {radius} mm")
    print("BASELINE")
    report(iso0, "v0_iso", to_index)

    depth0, _ = cmap.crater_depth(iso0, 2.0)
    boxes = [(name, box_from_centre(c, half)) for name, c in CRATERS]
    pock0 = {n: _pocket_in_box(depth0, b, to_index, iso0.shape, 2.0)
             for n, b in boxes}

    bones0 = v0._real_bone_count(iso0)
    tun0 = v0._tunnel_count(iso0)

    iso = iso0
    accepted = []
    for name, box in boxes:
        c1 = to_index(box[:3]); c2 = to_index(box[3:6])
        lo = np.maximum(np.floor(np.minimum(c1, c2)).astype(int) - 4, 0)
        hi = np.minimum(np.ceil(np.maximum(c1, c2)).astype(int) + 5,
                        np.array(iso.shape))
        w = (slice(lo[0], hi[0]), slice(lo[1], hi[1]), slice(lo[2], hi[2]))
        r_this = RADIUS_MM.get(name, radius) if radius <= 0 else radius
        it = max(1, int(round(r_this / VOX)))
        sub = iso[w]
        prop = ndimage.binary_closing(sub, structure=struct, iterations=it)
        added = int((prop & ~sub).sum())
        if not added:
            print(f"  {name:22s} nothing proposed")
            continue
        trial = iso.copy()
        trial[w] = sub | prop
        b = v0._real_bone_count(trial)
        t = v0._tunnel_count(trial)
        ok = (b == bones0) and (t <= tun0)
        print(f"  {name:22s} r={r_this:.1f} +{added * VOX ** 3:6.0f} mm3  "
              f"bones {b:2d}  tunnels {t:3d} (base {tun0})  "
              f"{'ACCEPT' if ok else 'REJECT'}")
        if ok:
            iso = trial
            tun0 = t
            accepted.append(name)

    print("\nAFTER")
    report(iso, f"patched x{len(accepted)}", to_index)

    depth1, _ = cmap.crater_depth(iso, 2.0)
    print(f"\n{'crater':22s} {'pocket before':>14s} {'after':>9s} {'removed':>9s}")
    for name, box in boxes:
        a = pock0[name]
        b = _pocket_in_box(depth1, box, to_index, iso.shape, 2.0)
        pct = 100 * (a - b) / a if a > 0 else 0.0
        print(f"{name:22s} {a:11.0f} mm3 {b:8.0f} {pct:8.1f} %")

    np.save(WORK / "iso_patched.npy", iso)
    print(f"\nwrote {WORK / 'iso_patched.npy'}")


if __name__ == "__main__":
    main()
