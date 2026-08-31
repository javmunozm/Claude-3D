"""Write marker spheres and a pillar/pin locator for hand editing.

The automated hole-finder does not flag the craters the operator sees: a
crater is open to the outside, so nothing that looks for enclosed voids finds
it. These are the regions located by hand in MeshLab (Get Point Info), plus
the support pillars and joint pins, so both can be found and dealt with in a
mesh editor.
"""
import os

import numpy as np
import trimesh

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(PROJECT, "sculpt")
os.makedirs(OUT, exist_ok=True)

# Craters located by the operator in MeshLab. (x, y, z, approx radius mm)
CRATERS = [
    (-116.25, -124.50, 66.25, 6.0, "visible in print; 463 mm3, traced"),
    (-106.50, -135.50, 73.50, 2.5, ""),
    (-98.40, -112.90, 70.00, 2.5, ""),
    (-126.25, -129.50, 73.50, 3.5, ""),
    (-130.00, -138.13, 56.38, 3.0, ""),
]

# Support pillars, as reported by segment_axial (scan frame) -> mesh frame.
# MIRROR_X negates X.
PILLARS_SCAN = [
    (128.8, -138.2, 56.2),
    (123.8, -129.2, 69.2),
    (126.8, -132.8, 76.2),
    (102.8, -156.8, 91.2),
]
PINS_SCAN = [
    (115.2, -159.0, 86.5, 4.0),
    (114.0, -67.0, 17.2, 2.0),
    (123.0, -74.0, 13.2, 2.0),
    (107.2, -65.5, 23.2, 2.0),
    (134.0, -82.8, 7.5, 2.0),
    (104.5, -149.5, 91.8, 4.0),
]


def sphere(c, r):
    s = trimesh.creation.icosphere(subdivisions=2, radius=r)
    s.apply_translation(c)
    return s


parts = [sphere((x, y, z), r) for x, y, z, r, _ in CRATERS]
trimesh.util.concatenate(parts).export(
    os.path.join(OUT, "BrokeFeet_crater_markers.stl"))
print(f"wrote BrokeFeet_crater_markers.stl ({len(CRATERS)} spheres)")

# pillars/pins: mirror X to reach the exported frame
marks = []
for x, y, z in PILLARS_SCAN:
    marks.append(sphere((-x, y, z), 3.0))
for x, y, z, d in PINS_SCAN:
    marks.append(sphere((-x, y, z), max(2.0, d / 2 + 1.0)))
trimesh.util.concatenate(marks).export(
    os.path.join(OUT, "BrokeFeet_pillar_pin_markers.stl"))
print(f"wrote BrokeFeet_pillar_pin_markers.stl "
      f"({len(PILLARS_SCAN)} pillars + {len(PINS_SCAN)} pins)")

print("\ncraters (mesh frame, as MeshLab reports):")
for x, y, z, r, note in CRATERS:
    print(f"  X {x:8.2f}  Y {y:8.2f}  Z {z:7.2f}   r~{r:.1f} mm  {note}")
print("\nsupport pillars (mesh frame):")
for x, y, z in PILLARS_SCAN:
    print(f"  X {-x:8.2f}  Y {y:8.2f}  Z {z:7.2f}   2 mm dia, vertical")
print("\njoint pins (mesh frame):")
for x, y, z, d in PINS_SCAN:
    print(f"  X {-x:8.2f}  Y {y:8.2f}  Z {z:7.2f}   {d:.0f} mm dia")
print("\nWARNING: deleting a pin can drop a bone as a loose body. The 5th toe "
      "phalanx\nis held ONLY by its 2 mm pin at X -134.0. Check body count "
      "after any deletion.")
