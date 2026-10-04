"""Right grip end: handle + end wall as one loft of r16 y-sections, clipped at the rear corner, trimmed flat at the
top and the tip; the tip edge rolled here, the top edge rolled after the pocket cut (roll_top)."""
from build123d import GeomType, Plane

from ..shapes import loft, one_solid, box, face_at, try_fillet, prism_in_frame


def rear_clip_cutter(y0, z0, slope, x0=0.0, x1=250.0):
    """Wedge above the plane z = z0 - slope * (y - y0), extruded along X."""
    zt = z0 + 20.0
    y_far = y0 + 40.0
    pts = [(y0 - 20.0 / slope, zt), (y_far, zt), (y_far, z0 - slope * (y_far - y0))]
    return prism_in_frame(pts, x0, x1, Plane(origin=(0, 0, 0), x_dir=(0, 1, 0), z_dir=(1, 0, 0)))


def build_grip_end(main_stations, rear_stations, top_z, tip_y, tip_roll, clip, log=print):
    """main_stations / rear_stations: [(y, Nx2 (x, z) loop)], rear to tip. clip: (y0, slope).
    Returns (solid, results dict)."""
    res = {}
    main = loft(main_stations, "main loft")
    rear = loft(rear_stations, "rear loft")
    log("  lofts valid: main vol %.0f, rear vol %.0f" % (main.volume, rear.volume))
    main = one_solid(main.cut(rear_clip_cutter(clip[0], top_z, clip[1])), "rear clip")
    end = one_solid(main.fuse(rear), "grip end lofts")
    end = one_solid(end.intersect(box(0.0, 250.0, tip_y, 150.0, -80.0, top_z)), "grip end trimmed")
    tip_edges = [e for f in face_at(end, "y", tip_y) for e in f.edges()]
    log("  tip face edges: %d" % len(tip_edges))
    r, end = try_fillet(end, tip_edges, [tip_roll, 2.0, 1.0], "tip edge", log)
    res["tip_roll"] = r
    return end, res


def roll_top(solid, top_z, r, x_keep, pocket_ys, log=print):
    """Roll the outer edges of the flat top: skip pocket edges (ellipse caps, straight lines at the pocket's
    y limits) and the inner edges (centre x < x_keep)."""
    edges = []
    for f in face_at(solid, "z", top_z):
        for e in f.edges():
            c = e.center()
            if e.geom_type == GeomType.ELLIPSE or c.X < x_keep:
                continue
            if e.geom_type == GeomType.LINE and any(abs(c.Y - py) < 0.02 for py in pocket_ys):
                continue
            edges.append(e)
            log("    top edge: %-8s len %6.2f centre (%.2f, %.2f)" % (e.geom_type.name, e.length, c.X, c.Y))
    rr, out = try_fillet(solid, edges, [r, 2.0, 1.0], "top edge", log)
    return rr, out
