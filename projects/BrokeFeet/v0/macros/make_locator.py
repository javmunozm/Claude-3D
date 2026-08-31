"""Make it possible to read a coordinate off the model by eye.

The operator can see defects but cannot name their position, so every report
becomes a cropped screenshot with no anchor. Two things fix that:

1. A GRID CAGE around the model, with a tick every 10 mm on each axis and a
   marker block at every 50 mm, exported alongside the bone. Load both in any
   viewer and a defect's position can be read off the cage.

2. LABELLED VIEW RENDERS with a coordinate grid drawn over them, so a defect
   can be located from a screenshot alone.
"""
import os

import numpy as np
import trimesh

PROJECT = r"D:\CAD\Claude-Projects\BrokeFeet"
SRC = os.path.join(PROJECT, "BrokeFeet_axial_raw.stl")
OUT = os.path.join(PROJECT, "locate")
os.makedirs(OUT, exist_ok=True)

mesh = trimesh.load(SRC)
lo, hi = mesh.bounds
print(f"model bounds  X {lo[0]:.1f}..{hi[0]:.1f}  Y {lo[1]:.1f}..{hi[1]:.1f}  "
      f"Z {lo[2]:.1f}..{hi[2]:.1f}")

# round outward to 10 mm
glo = np.floor(lo / 10.0) * 10.0
ghi = np.ceil(hi / 10.0) * 10.0
print(f"grid cage     X {glo[0]:.0f}..{ghi[0]:.0f}  Y {glo[1]:.0f}..{ghi[1]:.0f}  "
      f"Z {glo[2]:.0f}..{ghi[2]:.0f}")

BAR = 0.6        # strut thickness
TICK = 1.4       # tick block size
parts = []


def bar(p0, p1, r=BAR):
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    v = p1 - p0
    L = np.linalg.norm(v)
    if L < 1e-6:
        return None
    box = trimesh.creation.box(extents=[r, r, L])
    # orient +Z to v
    z = np.array([0, 0, 1.0])
    d = v / L
    axis = np.cross(z, d)
    if np.linalg.norm(axis) < 1e-9:
        R = np.eye(4) if d[2] > 0 else trimesh.transformations.rotation_matrix(
            np.pi, [1, 0, 0])
    else:
        ang = np.arccos(np.clip(np.dot(z, d), -1, 1))
        R = trimesh.transformations.rotation_matrix(ang, axis)
    box.apply_transform(R)
    box.apply_translation((p0 + p1) / 2.0)
    return box


# ---- twelve edges of the cage --------------------------------------------
corners = [(x, y, z) for x in (glo[0], ghi[0])
           for y in (glo[1], ghi[1]) for z in (glo[2], ghi[2])]
edges = []
for i, a in enumerate(corners):
    for bb in corners[i + 1:]:
        diff = [abs(a[k] - bb[k]) > 1e-6 for k in range(3)]
        if sum(diff) == 1:
            edges.append((a, bb))
for a, bb in edges:
    m = bar(a, bb)
    if m is not None:
        parts.append(m)
print(f"cage edges: {len(edges)}")

# ---- ticks every 10 mm, bigger block every 50 mm --------------------------
nt = 0
for axis in range(3):
    v0, v1 = glo[axis], ghi[axis]
    vals = np.arange(v0, v1 + 0.1, 10.0)
    for v in vals:
        big = abs(v % 50.0) < 1e-6
        s = TICK * (2.0 if big else 1.0)
        # place ticks on the four cage edges parallel to this axis
        others = [k for k in range(3) if k != axis]
        for o0 in (glo[others[0]], ghi[others[0]]):
            for o1 in (glo[others[1]], ghi[others[1]]):
                p = [0, 0, 0]
                p[axis] = v
                p[others[0]] = o0
                p[others[1]] = o1
                cube = trimesh.creation.box(extents=[s, s, s])
                cube.apply_translation(p)
                parts.append(cube)
                nt += 1
print(f"tick blocks: {nt}")

cage = trimesh.util.concatenate(parts)
cage_path = os.path.join(OUT, "BrokeFeet_grid_cage.stl")
cage.export(cage_path)
print(f"wrote {cage_path}  ({len(cage.faces)} faces)")

# ---- an origin marker: 3 axis arrows -------------------------------------
ax = []
L = 25.0
for i, col in enumerate("XYZ"):
    p0 = glo.copy()
    p1 = glo.copy()
    p1[i] += L
    m = bar(p0, p1, r=1.6)
    if m is not None:
        ax.append(m)
    # count blocks: 1 for X, 2 for Y, 3 for Z at the tip
    for j in range(i + 1):
        c = trimesh.creation.box(extents=[2.4, 2.4, 2.4])
        q = p1.copy()
        q[(i + 1) % 3] += 4.0 * (j + 1)
        c.apply_translation(q)
        ax.append(c)
axes = trimesh.util.concatenate(ax)
ax_path = os.path.join(OUT, "BrokeFeet_axes.stl")
axes.export(ax_path)
print(f"wrote {ax_path}   (1 block=+X, 2=+Y, 3=+Z, from the cage's low corner)")
