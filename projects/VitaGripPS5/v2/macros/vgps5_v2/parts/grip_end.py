"""Right grip end as two lofts of r16 y-sections sharing one station (pass 1c): the body/corner loft (rear face to
the shared station; its top corner cut by one cutter with the rounds built in) and the handle loft (shared station
to the tip). Each loft also takes the other's first neighbour station and is trimmed at the shared plane, so both
have the same tangent there; a change on one side cannot move the other."""
from ..shapes import loft, one_solid, box, face_at, try_fillet


def build_body(stations, shared_y, top_z, rear_y, cutter, rim_radii, rim_args, log=print, loft_opts=None):
    """stations: [(y, Nx2 loop)], rear to tip, ending one station past shared_y. Returns (solid, rim radius)."""
    body = loft(stations, "body/corner loft", uniform=True, **(loft_opts or {}))
    body = one_solid(body.intersect(box(0.0, 250.0, shared_y, rear_y, -80.0, top_z)), "body trimmed")
    body = one_solid(body.cut(cutter), "rear corner cut")
    log("  body/corner loft: valid, volume %.0f" % body.volume)
    r, body = try_fillet(body, rim_edges(body, *rim_args, log=log), rim_radii, "rim crest", log)
    return body, r


def build_single(stations, tip_y, top_z, rear_y, cutter, rim_radii, rim_args, tip_roll, log=print):
    """Body/corner and handle as one loft through all stations (no seam). Returns (solid, rim r, tip r)."""
    end, r_rim = build_body(stations, tip_y, top_z, rear_y, cutter, rim_radii, rim_args, log)
    tip_edges = [e for f in face_at(end, "y", tip_y) for e in f.edges()]
    r_tip, end = try_fillet(end, tip_edges, [tip_roll, 2.0, 1.0], "tip edge", log)
    return end, r_rim, r_tip


def build_handle(stations, shared_y, top_z, tip_y, tip_roll, log=print, loft_opts=None):
    """stations: [(y, Nx2 loop)], rear to tip, starting one station before shared_y. Returns (solid, tip radius)."""
    hand = loft(stations, "handle loft", uniform=True, **(loft_opts or {}))
    hand = one_solid(hand.intersect(box(0.0, 250.0, tip_y, shared_y, -80.0, top_z)), "handle trimmed")
    log("  handle loft: valid, volume %.0f" % hand.volume)
    tip_edges = [e for f in face_at(hand, "y", tip_y) for e in f.edges()]
    r, hand = try_fillet(hand, tip_edges, [tip_roll, 2.0, 1.0], "tip edge", log)
    return hand, r


def tangent_guide(body, y0, loop, g):
    """Guide section for the handle loft: each point of the shared section moved g mm past y0 (toward -y) along
    the body loft surface's own v-derivative there, so the handle leaves the shared section on the body's end
    tangent (G1 seam; the body loft is not changed)."""
    import numpy as np
    from OCP.BRep import BRep_Tool
    from OCP.GeomAPI import GeomAPI_ProjectPointOnSurf
    from OCP.gp import gp_Pnt, gp_Vec
    from build123d import GeomType
    surfs = [BRep_Tool.Surface_s(f.wrapped) for f in body.faces() if f.geom_type == GeomType.BSPLINE]
    out = []
    for x, z in loop:
        p = gp_Pnt(float(x), float(y0), float(z))
        best = None
        for s in surfs:
            pr = GeomAPI_ProjectPointOnSurf(p, s)
            if pr.NbPoints() and (best is None or pr.LowerDistance() < best[0]):
                best = (pr.LowerDistance(), s, pr.LowerDistanceParameters())
        d, s, (u, v) = best
        if d > 1e-3:
            raise RuntimeError("shared-section point (%.2f, %.2f) is %.4f off the body loft" % (x, z, d))
        q, du, dv = gp_Pnt(), gp_Vec(), gp_Vec()
        s.D1(u, v, q, du, dv)
        if abs(dv.Y()) < 1e-6:
            raise RuntimeError("body loft tangent at (%.2f, %.2f) has no y component" % (x, z))
        k = -g / dv.Y()
        out.append((q.X() + k * dv.X(), q.Z() + k * dv.Z()))
    return y0 - g, np.array(out)


def sew_at_seam(body, hand, shared_y, tol):
    """One solid from the faces of both pieces minus their trim faces on the shared plane, sewn at tol."""
    from build123d import Solid
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing, BRepBuilderAPI_MakeSolid
    from OCP.ShapeFix import ShapeFix_Solid
    from OCP.TopAbs import TopAbs_SHELL
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopoDS import TopoDS
    cap = [f for s in (body, hand) for f in face_at(s, "y", shared_y)]
    sew = BRepBuilderAPI_Sewing(tol)
    for s in (body, hand):
        for f in s.faces():
            if not any(f.is_same(c) for c in cap):
                sew.Add(f.wrapped)
    sew.Perform()
    exp = TopExp_Explorer(sew.SewedShape(), TopAbs_SHELL)
    shells = []
    while exp.More():
        shells.append(TopoDS.Shell_s(exp.Current()))
        exp.Next()
    if len(shells) != 1:
        raise RuntimeError("sewing gave %d shells" % len(shells))
    fix = ShapeFix_Solid(BRepBuilderAPI_MakeSolid(shells[0]).Solid())
    fix.Perform()
    return one_solid(Solid(fix.Solid()), "sewn body + handle")


def fuse_at_seam(body, hand, shared_y, log=print):
    """Union of the two pieces, which meet on the shared plane (coincident trim faces): exact fuse, then fuzzy,
    then sewing (build 1 fused exactly; without the fillets the same pieces fused into 2 solids)."""
    for how, tol in (("fuse", None), ("fuse", 1e-4), ("fuse", 1e-3), ("sew", 1e-3), ("sew", 1e-2)):
        try:
            if how == "sew":
                s = sew_at_seam(body, hand, shared_y, tol)
            else:
                s = one_solid(body.fuse(hand) if tol is None else body.fuse(hand, tol=tol), "body + handle")
            if abs(s.volume - body.volume - hand.volume) > 1e-3 * s.volume:
                raise RuntimeError("volume %.0f, pieces %.0f + %.0f" % (s.volume, body.volume, hand.volume))
            log("  seam %s (tol %s): valid, volume %.0f" % (how, tol, s.volume))
            return s, "%s %s" % (how, tol)
        except Exception as ex:
            log("  seam %s (tol %s): failed (%s)" % (how, tol, str(ex).splitlines()[0][:100]))
    raise RuntimeError("body + handle: no valid union")


def rim_edges(solid, zf, x_min, y_min, log=print):
    """Edges of the corner's flat (the cutter's floor at zf) on the outer side (x > x_min, y > y_min) and the
    cutter-to-flank edges running up from it: the rim crest to be rolled."""
    out = []
    for f in face_at(solid, "z", zf):
        for e in f.edges():
            c = e.center()
            if c.X > x_min and c.Y > y_min and e.geom_type.name != "LINE":
                out.append(e)
                log("    rim edge: %-8s len %6.2f centre (%.2f, %.2f, %.2f)" % (e.geom_type.name, e.length, c.X, c.Y,
                                                                              c.Z))
    return out
