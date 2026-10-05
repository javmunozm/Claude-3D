"""Right grip end: handle, end wall and rear corner as ONE loft of r16 y-sections (tip to the rear face), trimmed
flat at the top, the tip and the rear face; the rear corner's top is one cutter with its rounds built in."""
from ..shapes import loft, one_solid, box, face_at, try_fillet


def build_grip_end(stations, top_z, tip_y, rear_y, tip_roll, cutter, log=print):
    """stations: [(y, Nx2 (x, z) loop)], rear to tip. cutter: shapes.clip_cutter solid. Returns (solid, results)."""
    res = {}
    end = loft(stations, "grip-end loft", uniform=True)
    log("  loft valid: volume %.0f" % end.volume)
    end = one_solid(end.intersect(box(0.0, 250.0, tip_y, rear_y, -80.0, top_z)), "grip end trimmed")
    end = one_solid(end.cut(cutter), "rear corner cut")
    log("  rear corner cut: valid, volume %.0f" % end.volume)
    tip_edges = [e for f in face_at(end, "y", tip_y) for e in f.edges()]
    log("  tip face edges: %d" % len(tip_edges))
    r, end = try_fillet(end, tip_edges, [tip_roll, 2.0, 1.0], "tip edge", log)
    res["tip_roll"] = r
    return end, res


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
