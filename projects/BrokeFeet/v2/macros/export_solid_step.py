"""Export the bone mesh as a genuine STEP solid, for FreeCAD and other CAD.

WHY THIS EXISTS, AND WHAT IT CORRECTS
-------------------------------------
BrokeFeet's README states that a CT reconstruction cannot become an editable
solid and that no export format fixes it. The second half of that claim was
never actually tested -- BrokeFeet/macros/export_step.py existed but
BrokeFeet/cad/ was empty. Run, it reveals the real obstacle, which is NOT the
file format:

    trimesh decimation ->  124 broken faces at 25k
                       ->  OCC sews 12 SHELLS (3 closed, 9 open)
                       ->  BRepBuilderAPI_MakeSolid raises Standard_TypeMismatch
                       ->  STEP written as SHELL_BASED_SURFACE_MODEL

Twelve disjoint shells is why CAD tools show an uneditable blob. OCC never had
a closed shell to make a solid from, because the decimation punched holes in a
mesh that was watertight to begin with. `trimesh.repair.fill_holes` does not
close them -- they are not simple boundary loops (euler stays at -52).

The fix is to decimate with manifold3d, which is topology-preserving:

    manifold3d.simplify(0.15) -> 122,416 tris, genus 79 and volume 120.6 cm3
                                 BOTH PRESERVED EXACTLY, watertight, 0.15 mm
                              -> OCC sews 1 CLOSED SHELL
                              -> MANIFOLD_SOLID_BREP

TOLERANCE IS A CLIFF, NOT A KNOB
--------------------------------
Face count plateaus at ~122k regardless of tolerance; asking for looser does
not buy a smaller file, it only breaks the mesh. Measured:

    tol 0.15   122,416 tris  genus 79  120.6 cm3  watertight   max dev 0.15 mm
    tol 0.18   122,262       genus 47  120.6      BROKEN       0.18 mm
    tol 0.20   122,268       genus 47  120.6      BROKEN       0.18 mm
    tol 0.22   122,290       genus 47  120.6      BROKEN       0.18 mm
    tol 0.30    59,556       genus 50  111.2      BROKEN       4.72 mm  (-9 cm3)

So ~300 MB is the FLOOR for a topologically correct solid at full genus, not a
tuning oversight. Do not raise SIMPLIFY_TOL to shrink the file.

WHAT THE RESULT IS, AND IS NOT
------------------------------
One freeform solid body with no feature tree. Booleans, sectioning, cutting and
measurement work in FreeCAD. Sketch-driven parametric editing does not, and does
not exist for scan-derived geometry in ANY tool -- the geometry never had
sketches, extrusions or features to recover. Expect a slow first open.

Usage:
    python macros/export_solid_step.py                      # corrected mesh -> cad/
    python macros/export_solid_step.py <in.stl> <out.step>
"""
from __future__ import annotations

import os
import sys
import time

import numpy as np
import trimesh

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SRC = os.path.join(PROJECT, "BrokeFeetV1_craters_final.stl")
DEFAULT_OUT = os.path.join(PROJECT, "cad", "BrokeFeetV1_bone_solid.step")

# The only value that keeps the mesh watertight. See the module docstring --
# this is a cliff. Raising it does not shrink the file, it breaks the solid.
SIMPLIFY_TOL = 0.15

# Sewing tolerance. The mesh is in mm and vertices are shared exactly after
# manifold3d, so this only needs to absorb float32 round-trip error.
SEW_TOL = 1e-6


def simplify_manifold(mesh: trimesh.Trimesh, tol: float = SIMPLIFY_TOL):
    """Topology-preserving decimation. Returns (vertices, faces, genus, volume).

    trimesh's quadric decimation is NOT usable here: it breaks watertightness,
    which costs the solid downstream. manifold3d guarantees the result stays a
    manifold, so genus and volume come through unchanged.
    """
    import manifold3d as m3

    man = m3.Manifold(
        m3.Mesh(
            vert_properties=np.asarray(mesh.vertices, dtype=np.float32),
            tri_verts=np.asarray(mesh.faces, dtype=np.uint32),
        )
    )
    if man.status() != m3.Error.NoError:
        raise SystemExit(f"input is not a manifold: {man.status()}")

    simplified = man.simplify(tol)
    out = simplified.to_mesh()
    verts = np.asarray(out.vert_properties)[:, :3].astype(float)
    faces = np.asarray(out.tri_verts)
    return verts, faces, simplified.genus(), simplified.volume() / 1000.0


def to_step(verts: np.ndarray, faces: np.ndarray, path: str) -> tuple[bool, bool]:
    """Sew triangles into a shell and write STEP. Returns (is_solid, wrote_ok).

    Every triangle becomes one ADVANCED_FACE. Nothing recovers a feature tree,
    because the geometry never had one -- what this buys is a body CAD tools
    will boolean and section rather than a surface model they can only display.
    """
    from OCP.BRepBuilderAPI import (
        BRepBuilderAPI_MakeFace,
        BRepBuilderAPI_MakePolygon,
        BRepBuilderAPI_MakeSolid,
        BRepBuilderAPI_Sewing,
    )
    from OCP.gp import gp_Pnt
    from OCP.IFSelect import IFSelect_RetDone
    from OCP.STEPControl import STEPControl_AsIs, STEPControl_Writer
    from OCP.TopoDS import TopoDS

    sew = BRepBuilderAPI_Sewing(SEW_TOL)
    t0 = time.time()
    for i, f in enumerate(faces):
        p = [gp_Pnt(*verts[k]) for k in f]
        poly = BRepBuilderAPI_MakePolygon(p[0], p[1], p[2], True)
        if not poly.IsDone():
            continue
        face = BRepBuilderAPI_MakeFace(poly.Wire())
        if face.IsDone():
            sew.Add(face.Face())
        if i and i % 25000 == 0:
            print(f"      {i:,}/{len(faces):,} ({time.time() - t0:.0f}s)",
                  flush=True)
    sew.Perform()
    shape = sew.SewedShape()
    print(f"      sewed in {time.time() - t0:.0f}s", flush=True)

    # A single CLOSED shell is the precondition for a solid. If the mesh was
    # not watertight this raises Standard_TypeMismatch and the file degrades to
    # SHELL_BASED_SURFACE_MODEL -- the documented failure this script exists to
    # avoid, so it is reported rather than swallowed.
    is_solid = False
    try:
        shell = TopoDS.Shell_s(shape)
        mk = BRepBuilderAPI_MakeSolid(shell)
        if mk.IsDone():
            shape = mk.Solid()
            is_solid = True
    except Exception as exc:
        print(f"      NOT A SOLID ({type(exc).__name__}) -- writing surface "
              f"model; check the input is watertight")

    os.makedirs(os.path.dirname(path), exist_ok=True)
    writer = STEPControl_Writer()
    writer.Transfer(shape, STEPControl_AsIs)
    return is_solid, writer.Write(path) == IFSelect_RetDone


def main() -> None:
    src = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SRC
    out = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT

    mesh = trimesh.load(src)
    print(f"source: {os.path.basename(src)}")
    print(f"  {len(mesh.faces):,} faces, {mesh.volume / 1000:.2f} cm3, "
          f"watertight={mesh.is_watertight}, bodies={mesh.body_count}")
    if not mesh.is_watertight:
        print("  WARNING: input is not watertight; the result cannot be a solid")

    verts, faces, genus, volume = simplify_manifold(mesh)
    print(f"  simplified to {len(faces):,} faces, genus {genus}, "
          f"{volume:.2f} cm3 (tol {SIMPLIFY_TOL} mm)")

    is_solid, ok = to_step(verts, faces, out)
    size = os.path.getsize(out) / 1e6 if os.path.exists(out) else 0
    print(f"  {'SOLID' if is_solid else 'SHELL ONLY'} -- "
          f"{'written' if ok else 'WRITE FAILED'}: {size:.0f} MB")
    print(f"\n{out}")


if __name__ == "__main__":
    main()
