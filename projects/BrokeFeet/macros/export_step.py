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
SRC = os.path.join(PROJECT, "BrokeFeet_axial_raw.stl")
OUT = os.path.join(PROJECT, "cad")
os.makedirs(OUT, exist_ok=True)

# Face budgets. The low ones exist because a 461k-face STEP is unusable in most
# CAD tools; the high one is there if the tool can take it.
LEVELS = [10_000, 25_000, 60_000, 150_000]
if len(sys.argv) > 1:
    LEVELS = [int(a) for a in sys.argv[1:]]

mesh = trimesh.load(SRC)
print(f"source: {len(mesh.faces):,} faces, {mesh.volume/1000:.2f} cm3, "
      f"watertight={mesh.is_watertight}, bodies={mesh.body_count}")


def to_step(tri: trimesh.Trimesh, path: str) -> bool:
    """Build an OCC shell from triangles and write STEP."""
    from OCP.BRep import BRep_Builder
    from OCP.BRepBuilderAPI import (BRepBuilderAPI_MakeFace,
                                    BRepBuilderAPI_MakePolygon,
                                    BRepBuilderAPI_Sewing)
    from OCP.gp import gp_Pnt
    from OCP.TopoDS import TopoDS_Compound, TopoDS_Shell, TopoDS
    from OCP.STEPControl import STEPControl_Writer, STEPControl_AsIs
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeSolid
    from OCP.IFSelect import IFSelect_RetDone

    verts = tri.vertices
    sew = BRepBuilderAPI_Sewing(1e-6)
    t0 = time.time()
    for i, f in enumerate(tri.faces):
        p = [gp_Pnt(*verts[k]) for k in f]
        poly = BRepBuilderAPI_MakePolygon(p[0], p[1], p[2], True)
        if not poly.IsDone():
            continue
        face = BRepBuilderAPI_MakeFace(poly.Wire())
        if face.IsDone():
            sew.Add(face.Face())
        if i and i % 20000 == 0:
            print(f"      {i:,}/{len(tri.faces):,} faces "
                  f"({time.time()-t0:.0f}s)")
    sew.Perform()
    shape = sew.SewedShape()

    # try to make it a solid so CAD tools treat it as a body
    try:
        shell = TopoDS.Shell_s(shape)
        mk = BRepBuilderAPI_MakeSolid(shell)
        if mk.IsDone():
            shape = mk.Solid()
    except Exception:
        pass  # stays a shell; still importable

    w = STEPControl_Writer()
    w.Transfer(shape, STEPControl_AsIs)
    status = w.Write(path)
    return status == IFSelect_RetDone


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

    stl_path = os.path.join(OUT, f"BrokeFeet_bone_{tag}.stl")
    m.export(stl_path)

    # 3MF too -- a real solid-model container most CAD tools read, and far
    # smaller than STEP for the same geometry
    try:
        m.export(os.path.join(OUT, f"BrokeFeet_bone_{tag}.3mf"))
    except Exception as exc:
        print(f"      3mf failed: {exc}")

    step_path = os.path.join(OUT, f"BrokeFeet_bone_{tag}.step")
    t0 = time.time()
    try:
        ok = to_step(m, step_path)
        size = os.path.getsize(step_path) / 1e6 if os.path.exists(step_path) else 0
        print(f"      STEP {'written' if ok else 'FAILED'}: {size:.1f} MB "
              f"in {time.time()-t0:.0f}s")
    except Exception as exc:
        print(f"      STEP failed: {type(exc).__name__}: {exc}")

print(f"\nfiles in {OUT}")
