"""
widen_hori_grip.py — adapt the Hori Remote Play Assist grip for the PS Vita PCH-1000.

The Hori grip (`sources/psvitaGrip/grip2000/`) is moulded for the PCH-2000
"slim". The PCH-1000 is 3.6 mm deeper. This script widens the console pocket of
each half-shell by exactly that, and changes nothing else.

    PCH-2000  183.60 x 85.10 x 15.00 mm
    PCH-1000  182.00 x 83.55 x 18.60 mm
              -1.60    -1.55    +3.60

Only the depth is corrected. X and Y are left alone: the PCH-1000 is *smaller*
in both, so the existing pocket ends up ~0.8 mm looser per side — take that up
with a liner rather than reshaping a moulded shell. This is also why a uniform
scale is wrong: scaling by the 1.24 depth ratio gives a 227.7 mm wide part,
45.7 mm too wide, and moves the in-plane axes the wrong way.

Method — split and widen
------------------------
1. Cut the shell on a plane just above the console-facing plate.
2. Translate everything above the cut by +3.6 mm along the depth axis.
3. Fill the gap with a spacer extruded from the *actual* cut cross-section.
4. Boolean-union the three pieces, then repair.

Step 3 matters. An earlier plan assumed the wall was prismatic near the cut and
could be bridged by triangulating one loop to another. It is not: measured on
the rear, loop count swings 19 -> 23 -> 29 -> 20 -> 11 and section area falls
2099 -> 1151 mm2 across z = 17-22. There is no straight-extrusion zone. Building
the spacer from the section polygon at the cut plane sidesteps the problem
entirely — the spacer's end face matches the cut face by construction.

Everything below the cut is preserved exactly: measured section areas at
z = 5/10/14/16 are identical to the original to the last decimal. That is the
point of adapting rather than redesigning — the handle, wing and plate geometry
are the Hori originals, untouched.

Cut planes were located by ray-probing each shell, not guessed:
  rear  — plate spans z 14.18-16.50 (2.32 mm); cut at 18.0
  front — plate spans z 19.05-21.27 (2.22 mm); cut at 22.0

Run
---
    python projects/VitaGrip/macros/widen_hori_grip.py

Takes a few minutes: the sources are 2.2-2.6M faces and the work is done at
full resolution. Decimating first preserves volume to 0.04% but breaks
watertightness, so decimate only for rendering.

Requires: trimesh, manifold3d (boolean engine), pymeshfix, numpy.
"""

import collections
import time
from pathlib import Path

import numpy as np
import trimesh

REPO = Path(__file__).resolve().parents[3]
SRC_DIR = REPO / "sources" / "psvitaGrip" / "grip2000"
OUT_DIR = Path(__file__).resolve().parent.parent

# PCH-1000 depth minus PCH-2000 depth.
GAP = 3.6

# (source file, cut plane in the shell's local frame, output name)
PARTS = [
    ("Rear Cleaned.stl", 18.0, "VitaGrip_rear.stl"),
    ("Front Cleaned.stl", 22.0, "VitaGrip_front.stl"),
]


def bad_edge_count(mesh):
    """Edges not shared by exactly two faces — holes (1) or pinch points (3+)."""
    counts = collections.Counter(map(tuple, mesh.edges_sorted))
    return sum(1 for _, c in counts.items() if c != 2)


def widen(src_path, z_cut, gap=GAP):
    """Split the shell at z_cut and insert a `gap` mm spacer. Returns a mesh."""
    mesh = trimesh.load(src_path)
    # Local frame: min corner at the origin. Each Hori part ships on its own
    # print bed (rear at Z 434-467, front at Z 56-93) with no shared frame.
    mesh.apply_translation(-mesh.bounds[0])

    lower = mesh.slice_plane([0, 0, z_cut], [0, 0, -1.0], cap=True)
    upper = mesh.slice_plane([0, 0, z_cut], [0, 0, 1.0], cap=True)

    section = mesh.section(plane_origin=[0, 0, z_cut], plane_normal=[0, 0, 1])
    profile, to_3d = section.to_2D()
    spacer = profile.extrude(gap)
    if isinstance(spacer, list):
        spacer = trimesh.util.concatenate(spacer)
    spacer.apply_transform(to_3d)

    upper.apply_translation([0, 0, gap])

    out = trimesh.boolean.union([lower, spacer, upper], engine="manifold")
    out.merge_vertices()
    return out, mesh.volume, spacer.volume


def repair(mesh):
    """Close the handful of pinch points the union leaves behind.

    The union introduces a few non-manifold edges (3 on the front, 2 on the
    rear, out of 3-4 million) even though both sources are clean. pymeshfix
    closes them without moving the surface — volume is unchanged to 3 decimals.
    trimesh's fill_holes does not help: these are non-manifold edges shared by
    4 faces, not boundary holes. pymeshlab's non-manifold repair made it worse
    (3 bad edges -> 12).
    """
    import pymeshfix

    fixer = pymeshfix.MeshFix(np.asarray(mesh.vertices), np.asarray(mesh.faces))
    fixer.repair(remove_smallest_components=True)
    out = trimesh.Trimesh(fixer.points, fixer.faces)
    out.merge_vertices()
    return out


def main():
    for src_name, z_cut, out_name in PARTS:
        src = SRC_DIR / src_name
        print(f"\n=== {src_name} (cut at z={z_cut}) ===")
        t0 = time.time()

        widened, orig_vol, spacer_vol = widen(src, z_cut)
        print(f"  union    faces {len(widened.faces):>9,}  "
              f"vol {widened.volume / 1000:7.3f} cm3 "
              f"(orig {orig_vol / 1000:.3f} + spacer {spacer_vol / 1000:.3f})")

        fixed = repair(widened)
        print(f"  repaired faces {len(fixed.faces):>9,}  "
              f"watertight {fixed.is_watertight}  bodies {fixed.body_count}  "
              f"bad edges {bad_edge_count(fixed)}")

        ext = fixed.bounds[1] - fixed.bounds[0]
        print(f"  extent   {ext[0]:.2f} x {ext[1]:.2f} x {ext[2]:.2f} mm "
              f"({time.time() - t0:.0f}s)")

        out_path = OUT_DIR / "stl" / out_name
        out_path.parent.mkdir(exist_ok=True)
        fixed.export(str(out_path))
        print(f"  -> {out_path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
