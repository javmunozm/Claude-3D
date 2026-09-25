"""Convert the bone mesh to STEP (and 3MF) for CAD tools.

Honest framing: a CT reconstruction is a triangle mesh. STEP has no way to
represent that except as a shell of triangular faces -- one face per triangle.
Nothing recovers sketches, extrusions or a feature tree, because the geometry
never had them. What STEP does buy is a solid body that CAD tools will accept,
boolean against, and section.

Face count is what decides whether the file opens in practice, so this writes
several decimation levels rather than guessing which one a given tool tolerates.

Usage:
    python macros/export_step.py            # all levels
    python macros/export_step.py 25000      # one specific face budget
"""
import os
import sys
import time

import numpy as np
import trimesh

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(PROJECT))))  # -> tools
SRC = os.path.join(PROJECT, "stl", "BrokeFeet_axial_raw.stl")
OUT_STL = os.path.join(PROJECT, "stl")     # .stl and .3mf (meshes)
OUT_STEP = os.path.join(PROJECT, "step")
os.makedirs(OUT_STL, exist_ok=True)
os.makedirs(OUT_STEP, exist_ok=True)

# Face budgets. The low ones exist because a 461k-face STEP is unusable in most
# CAD tools; the high one is there if the tool can take it.
LEVELS = [10_000, 25_000, 60_000, 150_000]
if len(sys.argv) > 1:
    LEVELS = [int(a) for a in sys.argv[1:]]

mesh = trimesh.load(SRC)
print(f"source: {len(mesh.faces):,} faces, {mesh.volume/1000:.2f} cm3, "
      f"watertight={mesh.is_watertight}, bodies={mesh.body_count}")


def to_step(tri: trimesh.Trimesh, path: str) -> bool:
    """Build an OCC shell from triangles and write STEP.

    tools/mesh_to_step.py shares edges from the mesh topology when the mesh is
    a closed 2-manifold, and sews otherwise -- which the decimated levels here
    are not (broken faces, see below), so they still sew. A shape that is not
    a closed shell stays a shell; still importable.
    """
    from tools.mesh_to_step import triangles_to_shape, write_step

    shape, _, method = triangles_to_shape(tri.vertices, tri.faces, 1e-6,
                                          progress=20000)
    print(f"      built by {method}")
    return write_step(shape, path)


for target in LEVELS:
    if target >= len(mesh.faces):
        m = mesh.copy()
    else:
        m = mesh.simplify_quadric_decimation(face_count=target)
        m.process(validate=True)
        # Decimation leaves a small number of broken faces (116-198 at these
        # levels, out of 10k-60k). Two repairs were tried and both were worse:
        #
        #   trimesh.repair.fill_holes  -- does not close them; they are not
        #       simple boundary loops.
        #   voxel remesh               -- vg.marching_cubes returns vertices in
        #       VOXEL INDEX space, not mm, so the result came out at 634 cm3
        #       instead of 120 and 205 mm from the original. Any use of it must
        #       apply the grid transform.
        #
        # Left unrepaired deliberately. These holes are irrelevant to a CAD
        # import -- STEP carries a face shell either way -- and this file is
        # for CAD, not for slicing. Print from BrokeFeet_axial_raw.stl, which
        # is watertight.
        if not m.is_watertight:
            print(f"      {len(trimesh.repair.broken_faces(m))} broken faces "
                  f"(fine for CAD; print from the raw STL instead)")
    # measure how far the surface moved
    pts, _ = trimesh.sample.sample_surface(mesh, 4000)
    dev = trimesh.proximity.closest_point(m, pts)[1]
    tag = f"{len(m.faces)//1000}k"
    print(f"\n[{tag}] {len(m.faces):,} faces, {m.volume/1000:.2f} cm3, "
          f"bodies {m.body_count}, watertight {m.is_watertight}")
    print(f"      deviation from original: mean {dev.mean():.3f} mm, "
          f"p95 {np.percentile(dev,95):.3f} mm, max {dev.max():.3f} mm")

    stl_path = os.path.join(OUT_STL, f"BrokeFeet_bone_{tag}.stl")
    m.export(stl_path)

    # 3MF too -- a real solid-model container most CAD tools read, and far
    # smaller than STEP for the same geometry
    try:
        m.export(os.path.join(OUT_STL, f"BrokeFeet_bone_{tag}.3mf"))
    except Exception as exc:
        print(f"      3mf failed: {exc}")

    step_path = os.path.join(OUT_STEP, f"BrokeFeet_bone_{tag}.step")
    t0 = time.time()
    try:
        ok = to_step(m, step_path)
        size = os.path.getsize(step_path) / 1e6 if os.path.exists(step_path) else 0
        print(f"      STEP {'written' if ok else 'FAILED'}: {size:.1f} MB "
              f"in {time.time()-t0:.0f}s")
    except Exception as exc:
        print(f"      STEP failed: {type(exc).__name__}: {exc}")

print(f"\nfiles in {OUT_STL} and {OUT_STEP}")
