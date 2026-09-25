"""SurgicalDrillGuide stage 3a: generic shape helpers (dimensions in, shape out; no project constants)."""

import math

from build123d import Box, Edge, Face, Pos, Rot, Solid, Vector, Wire


def one_solid(shape, what):
    """Hard gate at construction: a boolean result must be exactly one solid."""
    sols = shape.solids()
    if len(sols) != 1:
        info = "; ".join(f"#{i} vol {s.volume:.2f} bbox {s.bounding_box()}" for i, s in enumerate(sols))
        raise RuntimeError(f"{what}: {len(sols)} solids ({info})")
    return sols[0]


def extrude_z(face, z0, z1):
    return Solid.extrude(face.moved(Pos(0, 0, z0)), Vector(0, 0, z1 - z0))


def box(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


def polygon_face(pts_xy):
    return Face(Wire.make_polygon([(x, y, 0) for x, y in pts_xy], close=True))


def teardrop_bore_x(x0, x1, y, z, d, apex_dir=+1):
    """Bore along X: circle Ø d plus a 45° point towards apex_dir*Z (support-free when Z is the build axis)."""
    r = d / 2.0
    s = r / math.sqrt(2.0)
    zc = z
    apex = Vector(x0, y, zc + apex_dir * r * math.sqrt(2.0))
    t1 = Vector(x0, y + s, zc + apex_dir * s)
    t2 = Vector(x0, y - s, zc + apex_dir * s)
    bottom = Vector(x0, y, zc - apex_dir * r)
    w = Wire([Edge.make_line(apex, t1), Edge.make_three_point_arc(t1, bottom, t2), Edge.make_line(t2, apex)])
    return Solid.extrude(Face(w), Vector(x1 - x0, 0, 0))


def along_y(shape, x, y0, z):
    """Map a shape built along +Z (axis at the origin) onto an axis parallel to +Y through (x, y0, z)."""
    return Pos(x, y0, z) * Rot(-90, 0, 0) * shape


def cone_y(x, y0, y1, r0, r1, z):
    """Frustum along +Y from y0 (radius r0) to y1 (radius r1)."""
    return along_y(Solid.make_cone(r0, r1, y1 - y0), x, y0, z)


def cyl_y(x, y0, y1, r, z):
    return along_y(Solid.make_cylinder(r, y1 - y0), x, y0, z)


def shapely_faces(geom):
    """shapely (Multi)Polygon without holes -> list of build123d Faces."""
    out = []
    for g in getattr(geom, "geoms", [geom]):
        if g.is_empty or g.area < 1e-6:
            continue
        if len(g.interiors):
            raise RuntimeError("pad region has holes; not expected")
        out.append(polygon_face(list(g.exterior.coords)[:-1]))
    return out
