"""Triangle mesh -> OCC shape, built from the mesh's own topology instead of sewing.

WHY NOT SEWING
--------------
The old path made one free face per triangle and let BRepBuilderAPI_Sewing
rediscover, geometrically and within a tolerance, which triangles share an
edge. The mesh already says so. Here every mesh vertex becomes one
TopoDS_Vertex, every undirected edge one TopoDS_Edge held in a dict keyed by
its (lo, hi) vertex indices, and each triangle's wire reuses those edges --
reversed where the triangle walks them backwards. Measured 2026-09-24 on
icospheres, both paths giving a valid single-shell solid of identical volume:

      1,280 faces   direct 0.1 s    sewing   0.2 s
     81,920 faces   direct 6.6 s    sewing 180.2 s    (27x)

WHEN IT FALLS BACK
------------------
Shared edges are only correct when the mesh is a closed, consistently wound
2-manifold: every undirected edge used by exactly two triangles, in opposite
directions. manifold_edges() checks exactly that. A mesh that fails it (e.g.
trimesh quadric decimation, which leaves broken faces) goes through the old
sewing path unchanged, and the returned method says which one ran.
"""
from __future__ import annotations

import time

import numpy as np


def manifold_edges(faces: np.ndarray) -> tuple[bool, int]:
    """(ok, n_bad): every edge in exactly 2 faces, walked in opposite directions."""
    faces = np.asarray(faces)
    directed = faces[:, [0, 1, 1, 2, 2, 0]].reshape(-1, 2)
    und = np.sort(directed, axis=1)
    _, und_count = np.unique(und, axis=0, return_counts=True)
    _, dir_count = np.unique(directed, axis=0, return_counts=True)
    bad = int((und_count != 2).sum() + (dir_count != 1).sum())
    return bad == 0, bad


def _direct(verts, faces, progress):
    from OCP.BRep import BRep_Builder
    from OCP.BRepBuilderAPI import (BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeFace,
                                    BRepBuilderAPI_MakeVertex, BRepBuilderAPI_MakeWire)
    from OCP.gp import gp_Pnt
    from OCP.TopoDS import TopoDS, TopoDS_Shell

    vtx = [BRepBuilderAPI_MakeVertex(gp_Pnt(*v)).Vertex() for v in verts]
    edges = {}                                   # (lo, hi) vertex index -> TopoDS_Edge
    bb = BRep_Builder()
    shell = TopoDS_Shell()
    bb.MakeShell(shell)
    t0 = time.time()
    for i, f in enumerate(faces):
        wire = BRepBuilderAPI_MakeWire()
        for a, b in ((f[0], f[1]), (f[1], f[2]), (f[2], f[0])):
            key = (a, b) if a < b else (b, a)
            e = edges.get(key)
            if e is None:
                e = edges[key] = BRepBuilderAPI_MakeEdge(vtx[key[0]], vtx[key[1]]).Edge()
            wire.Add(e if a < b else TopoDS.Edge_s(e.Reversed()))
        face = BRepBuilderAPI_MakeFace(wire.Wire(), True)
        if not face.IsDone():
            return None                          # degenerate triangle: shell would be open
        bb.Add(shell, face.Face())
        if progress and i and i % progress == 0:
            print(f"      {i:,}/{len(faces):,} ({time.time() - t0:.0f}s)", flush=True)
    shell.Closed(True)
    return shell


def _sew(verts, faces, sew_tol, progress):
    from OCP.BRepBuilderAPI import (BRepBuilderAPI_MakeFace, BRepBuilderAPI_MakePolygon,
                                    BRepBuilderAPI_Sewing)
    from OCP.gp import gp_Pnt

    sew = BRepBuilderAPI_Sewing(sew_tol)
    t0 = time.time()
    for i, f in enumerate(faces):
        p = [gp_Pnt(*verts[k]) for k in f]
        poly = BRepBuilderAPI_MakePolygon(p[0], p[1], p[2], True)
        if not poly.IsDone():
            continue
        face = BRepBuilderAPI_MakeFace(poly.Wire())
        if face.IsDone():
            sew.Add(face.Face())
        if progress and i and i % progress == 0:
            print(f"      {i:,}/{len(faces):,} ({time.time() - t0:.0f}s)", flush=True)
    sew.Perform()
    return sew.SewedShape()


def triangles_to_shape(verts, faces, sew_tol: float = 1e-6, progress: int = 25000):
    """Returns (shape, is_solid, method). method is 'direct' or 'sewing (<reason>)'."""
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeSolid
    from OCP.TopoDS import TopoDS

    verts = np.asarray(verts, dtype=float).tolist()
    faces = np.asarray(faces, dtype=np.int64)
    ok, n_bad = manifold_edges(faces)
    shape = _direct(verts, faces.tolist(), progress) if ok else None
    if shape is not None:
        method = "direct"
    else:
        reason = f"{n_bad} non-manifold edges" if not ok else "degenerate triangle"
        method = f"sewing ({reason})"
        shape = _sew(verts, faces.tolist(), sew_tol, progress)

    # A single CLOSED shell is the precondition for a solid. If it is not one,
    # Shell_s raises Standard_TypeMismatch and the caller gets the bare shape.
    try:
        mk = BRepBuilderAPI_MakeSolid(TopoDS.Shell_s(shape))
        if mk.IsDone():
            return mk.Solid(), True, method
    except Exception as exc:
        print(f"      NOT A SOLID ({type(exc).__name__}) -- check the input is watertight")
    return shape, False, method


def write_step(shape, path: str) -> bool:
    from OCP.IFSelect import IFSelect_RetDone
    from OCP.STEPControl import STEPControl_AsIs, STEPControl_Writer

    writer = STEPControl_Writer()
    writer.Transfer(shape, STEPControl_AsIs)
    return writer.Write(path) == IFSelect_RetDone
