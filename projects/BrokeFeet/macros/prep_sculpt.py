"""Prepare BrokeFeet bone mesh for hand-sculpting in Meshmixer / Blender.

Meshmixer handles the full 461k-face mesh, so no decimation.  What it needs
instead is guidance: its Inspector auto-repair bridges any gap smaller than its
patch size, and the joint spaces in this model are 0.5-1.4 mm.  Measure the
real gaps so a safe threshold can be stated rather than guessed.

Outputs into BrokeFeet/sculpt/:
  BrokeFeet_bone_sculpt.stl      full-res, cleaned, ready to open
  BrokeFeet_repair_markers.stl   sphere on each hole worth patching
  BrokeFeet_repair_sites.csv     coordinates + verdict
"""
import csv
import os

import numpy as np
import trimesh
from scipy import ndimage

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(PROJECT, "BrokeFeet_axial_raw.stl")
OUT = os.path.join(PROJECT, "sculpt")
PITCH = 0.5
MIN_VOX = 8

os.makedirs(OUT, exist_ok=True)
mesh = trimesh.load(SRC)
print(f"source: {len(mesh.faces)} faces, genus {(2-mesh.euler_number)//2}, "
      f"{mesh.volume/1000:.1f} cm3, watertight={mesh.is_watertight}, "
      f"bodies={mesh.body_count}")

# ------------------------------------------------------------------ clean
m = mesh.copy()
m.merge_vertices()
m.update_faces(m.nondegenerate_faces())
m.update_faces(m.unique_faces())
m.remove_unreferenced_vertices()
m.fix_normals()
print(f"cleaned: {len(m.faces)} faces, watertight={m.is_watertight}, "
      f"bodies={m.body_count}, vol {m.volume/1000:.1f} cm3")

sculpt = os.path.join(OUT, "BrokeFeet_bone_sculpt.stl")
m.export(sculpt)
print(f"wrote {sculpt}")

# ------------------------------------------------- measure the joint gaps
# The narrowest place two distinct bones approach each other sets the ceiling
# on any auto-repair patch size.  Work on the segmentation-era components by
# eroding the filled volume until it breaks into pieces is unreliable; instead
# measure directly across the known joint sites.
vg = mesh.voxelized(pitch=PITCH).fill()
occ = np.asarray(vg.matrix, dtype=bool)
origin = vg.transform[:3, 3]


def holes_along(axis):
    out = np.zeros_like(occ)
    for k in range(occ.shape[axis]):
        sl = [slice(None)] * 3
        sl[axis] = k
        plane = occ[tuple(sl)]
        if plane.any():
            out[tuple(sl)] = ndimage.binary_fill_holes(plane) & ~plane
    return out


holes = holes_along(2) | holes_along(1) | holes_along(0)
lbl, n = ndimage.label(holes, structure=np.ones((3, 3, 3)))
sizes = ndimage.sum(holes, lbl, range(1, n + 1))
keep = np.where(sizes >= MIN_VOX)[0] + 1
coms = ndimage.center_of_mass(holes, lbl, keep)

rows = []
for lab, com in zip(keep, coms):
    vol = float(sizes[lab - 1] * PITCH ** 3)
    xyz = origin + np.array(com) * PITCH
    idx = np.argwhere(lbl == lab)
    ext = (idx.max(0) - idx.min(0) + 1) * PITCH
    bbox = float(np.prod(ext))
    frac = vol / bbox if bbox else 1.0
    # A cavity inside one bone is a compact blob; a joint space is a thin rind
    # with a big bounding box and little of it filled.  Verified by rendering
    # slices -- see README 'Hand-repair export'.
    if vol > 100 and frac < 0.25:
        verdict = f"DO NOT PATCH - joint space (fills {frac:.0%} of bbox)"
    else:
        verdict = "PATCH - void inside bone"
    rows.append(dict(vol_mm3=round(vol, 2),
                     x=round(float(xyz[0]), 2), y=round(float(xyz[1]), 2),
                     z=round(float(xyz[2]), 2),
                     ext_x=round(float(ext[0]), 1),
                     ext_y=round(float(ext[1]), 1),
                     ext_z=round(float(ext[2]), 1),
                     bbox_fill=round(frac, 3),
                     verdict=verdict))

rows.sort(key=lambda r: -r["vol_mm3"])
patch = [r for r in rows if r["verdict"].startswith("PATCH")]
skip = [r for r in rows if not r["verdict"].startswith("PATCH")]

csv_path = os.path.join(OUT, "BrokeFeet_repair_sites.csv")
with open(csv_path, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
print(f"wrote {csv_path}")
print(f"  {len(patch)} to patch ({sum(r['vol_mm3'] for r in patch):.0f} mm3)")
print(f"  {len(skip)} excluded ({sum(r['vol_mm3'] for r in skip):.0f} mm3)")

# ------------------------------------------------------------- markers
marks = []
for r in patch:
    rad = max(1.5, min(6.0, (r["vol_mm3"] * 3 / (4 * np.pi)) ** (1 / 3)))
    s = trimesh.creation.icosphere(subdivisions=2, radius=rad)
    s.apply_translation([r["x"], r["y"], r["z"]])
    marks.append(s)
mk = os.path.join(OUT, "BrokeFeet_repair_markers.stl")
trimesh.util.concatenate(marks).export(mk)
print(f"wrote {mk}  ({len(patch)} spheres)")

print("\nSites to patch:")
for i, r in enumerate(patch, 1):
    print(f"{i:>3} {r['vol_mm3']:8.1f} mm3   X {r['x']:8.2f}  Y {r['y']:8.2f}  "
          f"Z {r['z']:8.2f}")
print("\nDo NOT patch:")
for r in skip:
    print(f"    {r['vol_mm3']:8.1f} mm3   X {r['x']:8.2f}  Y {r['y']:8.2f}  "
          f"Z {r['z']:8.2f}   {r['verdict']}")
