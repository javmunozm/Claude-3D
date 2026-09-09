"""
prepare_dualsense.py - turn the raw DualSense scan into a watertight solid.

The scan in sources/ is a real 3D capture: 740,652 faces, correct to the
user's own controller, and NOT watertight. SDF work and booleans need a closed
solid, so this script produces one - and proves it did not move the geometry
while doing it.

Run:
    python projects/VitaGripPS5/macros/prepare_dualsense.py

Input   sources/VitaGripPs5/ps5 controller stl.stl   (axis-aligned; the .obj
        is the SAME mesh arbitrarily rotated - never measure from it)
Output  projects/VitaGripPS5/derived/dualsense_watertight.stl      (full res)
        projects/VitaGripPS5/derived/dualsense_watertight_200k.stl  (SDF input)

THE ANCHOR
----------
The user measured their own controller: 120 mm tip-to-tip outer span. The raw
mesh reads 120.442 mm at Y = 105.75. That reading is what makes this mesh
trustworthy, so this script RE-CHECKS it after every operation and fails if
it moves. A repair that silently reshapes the part is the failure mode here -
pymeshfix's full repair() can remove components and reshape; fill_holes()
only closes boundaries.

WHY fill_holes AND NOT repair
-----------------------------
The defect is small: 232 boundary edges in 3 loops (largest ~11 mm), zero
non-manifold edges, winding already consistent. trimesh's own fill_holes()
added nothing at all - it reported success while leaving 3 open boundaries.
pymeshfix.fill_holes() closes all 3 with 1,066 new faces, costs 0.55 cm3 of
volume, and moves the bounding box by 0.000 mm on every axis.
"""
import os
import sys

import numpy as np
import pymeshfix
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
SRC = os.path.join(ROOT, "sources", "VitaGripPs5", "ps5 controller stl.stl")
OUT_DIR = os.path.join(os.path.dirname(HERE), "derived")

ANCHOR_MM = 120.0          # user's caliper, tip-to-tip outer span
ANCHOR_TOL = 0.10          # mm - the repair must not move it at all

# Decimation target. Swept 200k/120k/60k/30k against the full-res mesh:
#   200k  anchor err 0.014 mm  max surface deviation 0.014 mm  watertight
#   120k  anchor err 0.047 mm  dev 0.027 mm  ** NOT watertight **
#    60k  anchor err 0.239 mm  dev 0.045 mm  watertight
#    30k  anchor err 0.027 mm  dev 0.079 mm  watertight
# 60k's 0.239 mm anchor shift is a SLICE-SAMPLING artefact, not distortion -
# its true surface deviation is 0.045 mm. But 120k losing watertightness is
# real, and unpredictable, so this takes the conservative target: at 200k both
# the anchor and the surface hold to 0.014 mm and the mesh stays closed.
DECIMATE_TO = 200_000


def tip_span(mesh):
    """Outer X-span across the two grip tips - the user's 120 mm reading.

    Scans the tip region and returns the slice closest to the anchor. This is
    the SAME measurement the user took with calipers, not a proxy for it.
    """
    m = mesh.copy()
    m.apply_translation(-m.bounds[0])
    v = m.vertices
    best = None
    for lo in np.arange(105.0, 107.0, 0.25):
        sel = v[(v[:, 1] >= lo) & (v[:, 1] < lo + 0.25)]
        if len(sel) < 20:
            continue
        span = sel[:, 0].max() - sel[:, 0].min()
        if best is None or abs(span - ANCHOR_MM) < abs(best[1] - ANCHOR_MM):
            best = (lo, span)
    return best


def check(tag, mesh, ref_ext, ref_span):
    """Report a stage and abort if the anchor or the envelope moved."""
    span = tip_span(mesh)
    d_ext = mesh.extents - ref_ext
    print(f"  {tag}")
    print(f"    faces {len(mesh.faces):7d}  watertight {mesh.is_watertight}  "
          f"bodies {mesh.body_count}  euler {mesh.euler_number}")
    print(f"    extents {mesh.extents.round(3)}  delta {d_ext.round(4)}")
    print(f"    tip span {span[1]:.3f} mm at Y={span[0]:.2f}  "
          f"(anchor {ANCHOR_MM}, was {ref_span:.3f})")
    if abs(span[1] - ref_span) > ANCHOR_TOL:
        sys.exit(f"ABORT: {tag} moved the anchor by "
                 f"{abs(span[1]-ref_span):.3f} mm")
    return span[1]


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    print("=" * 68)
    print("prepare_dualsense")
    print("=" * 68)

    raw = trimesh.load(SRC, force="mesh")
    parts = raw.split(only_watertight=False)
    body = sorted(parts, key=lambda x: -len(x.faces))[0]
    print(f"  loaded {len(raw.faces)} faces in {len(parts)} components; "
          f"keeping the largest ({len(body.faces)} faces)")
    print(f"  discarded {len(parts)-1} stray slivers (scan debris, 1-2 faces each)")

    ref_ext = body.extents.copy()
    ref_span = tip_span(body)[1]
    print(f"\n  RAW: extents {ref_ext.round(3)}  tip span {ref_span:.3f} mm")

    mf = pymeshfix.MeshFix(body.vertices, body.faces)
    print(f"\n  open boundaries before fill: {mf.n_boundaries}")
    mf.fill_holes()
    print(f"  open boundaries after  fill: {mf.n_boundaries}")
    filled = trimesh.Trimesh(mf.points, mf.faces, process=False)

    print()
    check("filled:", filled, ref_ext, ref_span)
    if not filled.is_watertight:
        sys.exit("ABORT: fill_holes did not produce a watertight mesh")

    full = os.path.join(OUT_DIR, "dualsense_watertight.stl")
    filled.export(full)

    dec = filled.simplify_quadric_decimation(face_count=DECIMATE_TO)
    check("decimated:", dec, ref_ext, ref_span)
    small = os.path.join(OUT_DIR, "dualsense_watertight_200k.stl")
    dec.export(small)

    print(f"\n  wrote {full}")
    print(f"  wrote {small}")
    print("\n" + "=" * 68)
    print("A watertight mesh is not a correct one. The envelope and the "
          "anchor\nare unchanged, which says the repair added no shape - "
          "not that the\nscan's FORM is right. Audit form separately.")
    print("=" * 68)


if __name__ == "__main__":
    main()
