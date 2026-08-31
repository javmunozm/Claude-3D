"""Render the model from the six orthogonal views with a labelled coordinate
grid drawn over each, so a defect's position can be read off a screenshot.

Depth-shaded orthographic projection -- no renderer dependency, and depth
shading makes craters and rods visible rather than flattening them.
"""
import os

import numpy as np
import trimesh
from PIL import Image, ImageDraw

PROJECT = r"D:\CAD\Claude-Projects\BrokeFeet"
OUT = os.path.join(PROJECT, "locate")
os.makedirs(OUT, exist_ok=True)
SRC = os.path.join(PROJECT, "BrokeFeet_axial_raw.stl")

mesh = trimesh.load(SRC)
V = mesh.vertices
lo, hi = mesh.bounds
print(f"bounds X {lo[0]:.1f}..{hi[0]:.1f} Y {lo[1]:.1f}..{hi[1]:.1f} "
      f"Z {lo[2]:.1f}..{hi[2]:.1f}")

AX = "XYZ"
# (name, horizontal axis, vertical axis, depth axis, flip_h, flip_v, near=)
VIEWS = [
    ("top",    0, 1, 2, False, True,  +1),   # looking down -Z
    ("bottom", 0, 1, 2, False, False, -1),
    ("front",  0, 2, 1, False, True,  -1),   # looking along +Y
    ("back",   0, 2, 1, True,  True,  +1),
    ("right",  1, 2, 0, False, True,  +1),   # looking along -X
    ("left",   1, 2, 0, True,  True,  -1),
]

W, H = 1500, 1150
MARGIN = 95
GRID = 10.0


def render(name, ha, va, da, flip_h, flip_v, near):
    h = V[:, ha].copy()
    v = V[:, va].copy()
    d = V[:, da].copy() * near     # larger = nearer the camera

    hlo, hhi = np.floor(lo[ha] / GRID) * GRID, np.ceil(hi[ha] / GRID) * GRID
    vlo, vhi = np.floor(lo[va] / GRID) * GRID, np.ceil(hi[va] / GRID) * GRID

    pw, ph = W - 2 * MARGIN, H - 2 * MARGIN
    sc = min(pw / (hhi - hlo), ph / (vhi - vlo))

    def to_px(hv, vv):
        x = (hv - hlo) * sc
        y = (vv - vlo) * sc
        if flip_h:
            x = (hhi - hlo) * sc - x
        if flip_v:
            y = (vhi - vlo) * sc - y
        return MARGIN + x, MARGIN + y

    img = Image.new("RGB", (W, H), (250, 250, 250))
    dr = ImageDraw.Draw(img)

    # painter's algorithm on vertices, shaded by depth
    order = np.argsort(d)
    dmin, dmax = d.min(), d.max()
    step = max(1, len(order) // 260000)
    for i in order[::step]:
        x, y = to_px(h[i], v[i])
        if MARGIN - 2 <= x < W - MARGIN + 2 and MARGIN - 2 <= y < H - MARGIN + 2:
            t = (d[i] - dmin) / (dmax - dmin + 1e-9)
            c = int(55 + 165 * t)
            dr.point((x, y), fill=(int(c * 0.42), int(c * 0.86), int(c * 0.80)))

    # grid
    for hv in np.arange(hlo, hhi + 0.1, GRID):
        x, _ = to_px(hv, vlo)
        major = abs(hv % 50.0) < 1e-6
        dr.line([(x, MARGIN), (x, H - MARGIN)],
                fill=(150, 150, 160) if major else (222, 222, 228),
                width=2 if major else 1)
        if major:
            dr.text((x - 16, H - MARGIN + 10), f"{hv:.0f}", fill=(20, 20, 20))
    for vv in np.arange(vlo, vhi + 0.1, GRID):
        _, y = to_px(hlo, vv)
        major = abs(vv % 50.0) < 1e-6
        dr.line([(MARGIN, y), (W - MARGIN, y)],
                fill=(150, 150, 160) if major else (222, 222, 228),
                width=2 if major else 1)
        if major:
            dr.text((MARGIN - 46, y - 7), f"{vv:.0f}", fill=(20, 20, 20))

    dr.rectangle([MARGIN, MARGIN, W - MARGIN, H - MARGIN],
                 outline=(90, 90, 90), width=2)

    dr.text((MARGIN, 22), f"{name.upper()}", fill=(0, 0, 0))
    dr.text((MARGIN, 44),
            f"horizontal = {AX[ha]}   vertical = {AX[va]}   "
            f"(depth = {AX[da]}, brighter is nearer)", fill=(40, 40, 40))
    dr.text((MARGIN, 62), "grid 10 mm, labelled every 50 mm",
            fill=(90, 90, 90))
    dr.text((W - MARGIN - 300, 44),
            f"{AX[ha]} {hlo:.0f}..{hhi:.0f}   {AX[va]} {vlo:.0f}..{vhi:.0f}",
            fill=(40, 40, 40))

    p = os.path.join(OUT, f"locate_{name}.png")
    img.save(p)
    print(f"wrote {p}")


for args in VIEWS:
    render(*args)
