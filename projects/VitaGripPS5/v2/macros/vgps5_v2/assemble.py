"""Assembly helpers: junction edges between the grip-end loft and the plate, fillet search, mirror."""
from build123d import GeomType, Plane

from .shapes import one_solid, try_fillet


def junction_edges(half, x_lo, x_hi, plate_levels, log=print):
    """Curved edges lying on a plate face (plate_levels: {"Z": (z...), "Y": (y...)}) with centre x in [x_lo, x_hi]."""
    out = []
    for e in half.edges():
        if e.geom_type in (GeomType.LINE, GeomType.ELLIPSE):
            continue
        c = e.center()
        if not x_lo <= c.X <= x_hi:
            continue
        bb = e.bounding_box()
        on = [k for k, lv in plate_levels.items() for v in lv
              if (k == "Z" and abs(bb.min.Z - v) < 0.02 and abs(bb.max.Z - v) < 0.02)
              or (k == "Y" and abs(bb.min.Y - v) < 0.02 and abs(bb.max.Y - v) < 0.02)]
        if on:
            out.append(e)
            log("    junction edge: %-8s len %6.2f centre (%.2f, %.2f, %.2f)"
                % (e.geom_type.name, e.length, c.X, c.Y, c.Z))
    return out


def fillet_search(half, edges, radii, log=print):
    """Largest radius valid on all edges at once, then the largest per edge."""
    r_all, _ = try_fillet(half, edges, radii, "junction (all %d edges)" % len(edges), log)
    per_edge = []
    for i, e in enumerate(edges):
        r_i, _ = try_fillet(half, [e], radii, "junction edge %d" % i, lambda *_: None)
        per_edge.append(r_i)
    log("  junction per-edge largest radius: %s" % per_edge)
    return r_all, per_edge


def mirror_union(half):
    other = half.mirror(Plane.YZ)
    return one_solid(half.fuse(other), "mirrored union"), other
