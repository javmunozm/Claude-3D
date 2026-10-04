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


def section_wire(y, loop):
    pts = [Vector(float(x), float(y), float(z)) for x, z in loop]
    return Wire([Edge.make_spline(pts, periodic=True)])


def loft(stations, what):
    wires = [section_wire(y, loop) for y, loop in stations]
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
