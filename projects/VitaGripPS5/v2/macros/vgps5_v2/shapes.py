"""Shape helpers shared by the part builders."""
import numpy as np
from build123d import (Axis, Edge, Face, Location, Plane, Solid, Vector, Wire, GeomType)


def valid(shape):
    v = shape.is_valid
    return bool(v() if callable(v) else v)


def one_solid(shape, what):
    """Return the single valid solid in shape, or raise with the pieces listed."""
    solids = shape.solids() if hasattr(shape, "solids") else [shape]
    if len(solids) != 1:
        info = ["%d: vol %.2f bbox %s" % (i, s.volume, s.bounding_box()) for i, s in enumerate(solids)]
        raise RuntimeError("%s: %d solids\n%s" % (what, len(solids), "\n".join(info)))
    s = solids[0]
    if not valid(s):
        raise RuntimeError("%s: solid is not valid" % what)
    return s


def section_wire(y, loop, uniform=False):
    """Periodic spline through the loop. uniform: parameter i at point i, so every station gets the same knots
    and the loft pairs points by index (for index-aligned loops)."""
    pts = [Vector(float(x), float(y), float(z)) for x, z in loop]
    par = [float(i) for i in range(len(pts) + 1)] if uniform else None
    return Wire([Edge.make_spline(pts, periodic=True, parameters=par)])


def loft(stations, what, uniform=False):
    wires = [section_wire(y, loop, uniform) for y, loop in stations]
    return one_solid(Solid.make_loft(wires, ruled=False), what)


def blend_wire(y, prof):
    """Bezier bottom + straight corners, in the plane y (same edge count on every station)."""
    v = lambda p: Vector(float(p[0]), float(y), float(p[1]))
    edges = [Edge.make_bezier(*[v(p) for p in prof["bezier"]])]
    c = prof["corners"]
    edges += [Edge.make_line(v(a), v(b)) for a, b in zip(c[:-1], c[1:])]
    return Wire(edges)


def loft_wires(wires, what):
    return one_solid(Solid.make_loft(wires, ruled=False), what)


def box(x0, x1, y0, y1, z0, z1):
    return Solid.make_box(x1 - x0, y1 - y0, z1 - z0, Plane(origin=(x0, y0, z0)))


def polygon_face(pts2d):
    return Face(Wire.make_polygon([Vector(float(a), float(b), 0.0) for a, b in pts2d], close=True))


def prism_in_frame(pts2d, h0, h1, plane):
    """Extrude a 2D polygon (local x, y) from local z h0 to h1, then place it in plane's frame."""
    f = polygon_face(pts2d).moved(Location((0, 0, h0)))
    s = Solid.extrude(f, Vector(0, 0, h1 - h0))
    return s.moved(Location(plane))


def clip_cutter(w, phi_deg, k, rt, rf, zh, zf, u_far=60.0, z_hi=40.0, half_len=150.0):
    """Rear-corner cutter: the solid above the corner's top surface. In the (u, z) plane (u along the plan normal
    n = (-sin phi, cos phi), toward the rear) the surface is: flat at zh, a convex rt round, a wall falling k mm per
    mm u, a concave rf foot, flat at zf. u = 0 at the round's end on the wall line through w = (x, y).
    Extruded along the plan direction t = (cos phi, sin phi). Rounds are true arcs (no facets)."""
    th = np.arctan(1.0 / k)
    c1 = np.array([-rt * np.cos(th), zh - rt])
    z_end = c1[1] + rt * np.sin(th)
    uf = (z_end - zf - rf + rf * np.sqrt(k * k + 1.0)) / k
    c2 = np.array([uf, zf + rf])
    nw = np.array([np.cos(th), np.sin(th)])
    pt = c2 - rf * nw

    def V(p):
        return Vector(float(p[0]), float(p[1]), 0.0)

    def on(c, r, a):
        return c + r * np.array([np.cos(a), np.sin(a)])

    a_top = 0.5 * (np.pi / 2 + th)
    a_ft = 0.5 * (np.pi + th + 1.5 * np.pi)
    p0 = np.array([c1[0], zh])
    p1 = np.array([0.0, z_end])
    p3 = np.array([uf, zf])
    edges = [Edge.make_three_point_arc(V(p0), V(on(c1, rt, a_top)), V(p1)),
             Edge.make_line(V(p1), V(pt)),
             Edge.make_three_point_arc(V(pt), V(on(c2, rf, a_ft)), V(p3)),
             Edge.make_line(V(p3), V((u_far, zf))),
             Edge.make_line(V((u_far, zf)), V((u_far, z_hi))),
             Edge.make_line(V((u_far, z_hi)), V((c1[0], z_hi))),
             Edge.make_line(V((c1[0], z_hi)), V(p0))]
    f = Face(Wire(edges)).moved(Location((0, 0, -half_len)))
    s = Solid.extrude(f, Vector(0, 0, 2.0 * half_len))
    ph = np.radians(phi_deg)
    plane = Plane(origin=(w[0], w[1], 0.0), x_dir=(-np.sin(ph), np.cos(ph), 0.0), z_dir=(np.cos(ph), np.sin(ph), 0.0))
    return one_solid(s.moved(Location(plane)), "clip cutter")


def oval_cutter(xc, a, b, yc, y_lo, y_hi, z0, z1):
    """Pocket prism: straight top/bottom, elliptical end caps centred at x = +-xc."""
    h = z1 - z0
    caps = []
    for sx in (1.0, -1.0):
        e = Edge.make_ellipse(a, b, Plane(origin=(sx * xc, yc, z0)))
        caps.append(Solid.extrude(Face(Wire([e])), Vector(0, 0, h)))
    mid = box(-xc, xc, y_lo, y_hi, z0, z1)
    return one_solid(mid.fuse(*caps), "pocket cutter")


def face_at(solid, axis, value, tol=0.02):
    """Planar faces whose normal is along axis and that lie at the given coordinate."""
    out = []
    for f in solid.faces():
        if f.geom_type != GeomType.PLANE:
            continue
        n = f.normal_at()
        c = f.center()
        k = {"x": 0, "y": 1, "z": 2}[axis]
        if abs(abs(n.to_tuple()[k]) - 1.0) < 1e-6 and abs(c.to_tuple()[k] - value) < tol:
            out.append(f)
    return out


def try_fillet(solid, edges, radii, what, log=print):
    """Largest radius (in the order given) that gives one valid solid. Returns (radius, solid) or (None, solid)."""
    for r in radii:
        try:
            res = solid.fillet(r, edges)
            s = one_solid(res, what)
            log("  fillet %s r %.2f: valid" % (what, r))
            return r, s
        except Exception as ex:
            log("  fillet %s r %.2f: failed (%s)" % (what, r, str(ex).splitlines()[0][:80]))
    return None, solid
