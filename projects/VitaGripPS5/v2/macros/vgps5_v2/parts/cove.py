"""Pass "cove" (2026-10-27): a rounded strip in the console seat corner, built as its own solid.

The strip has a square r x r section in the corner where the pocket wall meets the floor, with its free edge rounded
to the full radius r: the arc is tangent to the wall and to the floor, so the joined part has a concave round there.
It is built alone and joined to the half before the pit cuts (the pit cutters trim it). The section reaches `embed`
into the wall and the floor so the union overlaps a real volume.

The path is the pocket cutter's own ellipse (shapes.oval_cutter), its outer half, theta -90 -> +90 degrees.
"""
import math

from build123d import Edge, Face, Plane, Vector, Wire, sweep

from ..shapes import one_solid


def cove_profile(r, embed, plane):
    """The section in `plane`: local x = into the pocket (u), local y = up (h); {-embed..r} x {-embed..r} minus the
    disk at (r, r), radius r."""
    s = r * (1.0 - math.sqrt(0.5))
    pts = [(-embed, -embed), (r, -embed), (r, 0.0)]
    P = [plane.from_local_coords(p) for p in pts]
    a0 = plane.from_local_coords((r, 0.0))
    am = plane.from_local_coords((s, s))
    a1 = plane.from_local_coords((0.0, r))
    q0 = plane.from_local_coords((-embed, r))
    edges = [Edge.make_line(P[0], P[1]), Edge.make_line(P[1], P[2]),
             Edge.make_three_point_arc(a0, am, a1),
             Edge.make_line(a1, q0), Edge.make_line(q0, P[0])]
    return Face(Wire(edges))


def corner_cove(xc, a, b, yc, floor_z, r, embed, theta_end=90.0, pits=()):
    """The strip along the +x cap of the pocket ellipse (centre (xc, yc), semi-axes a in x, b in y) at floor_z,
    from theta -90 deg to theta_end. Amendment A1 (2026-10-27, user report): it stops at theta_end (the upper pit:
    behind the rear corner there is no wall, and the strip stood alone as a 0.5-1.8 mm fin), and it is removed over
    each pit's full length and section, `pits` = [(p, n, half_length)], so no 0.40 mm sliver is left in front of a
    slot. Returns the remaining pieces, each a valid solid."""
    from .lip import build_pit
    path = Edge.make_ellipse(a, b, Plane(origin=(xc, yc, floor_z)), start_angle=-90.0, end_angle=theta_end)
    p0 = path.position_at(0.0)
    t0 = path.tangent_at(0.0)
    if abs(p0.X - xc) > 1e-6 or abs(p0.Y - (yc - b)) > 1e-6 or t0.X < 0.999:
        raise RuntimeError("cove path does not start at (%.3f, %.3f) heading +x: %s, %s" % (xc, yc - b, p0, t0))
    # profile plane at the start: local x = inward (+y here), local y = up, normal = the path tangent (+x)
    plane = Plane(origin=p0, x_dir=(0.0, 1.0, 0.0), z_dir=(1.0, 0.0, 0.0))
    if abs(plane.y_dir.Z - 1.0) > 1e-9:
        raise RuntimeError("cove profile plane: local y is not up (%s)" % plane.y_dir)
    face = cove_profile(r, embed, plane)
    strip = one_solid(sweep(face, path=Wire([path]), is_frenet=True), "corner cove")
    for p, n, hl in pits:
        # in the pit frame: u outward from the wall (the strip lies at u -r .. +embed), t along the wall
        clear = build_pit(p, n, [(-(r + 1.0), -hl), (embed + 1.0, -hl), (embed + 1.0, hl), (-(r + 1.0), hl)],
                          floor_z - embed - 1.0, floor_z + r + 1.0)
        strip = strip.cut(clear)
    pieces = strip.solids() if hasattr(strip, "solids") else [strip]
    for i, s in enumerate(pieces):
        one_solid(s, "corner cove piece %d" % i)
    return list(pieces)
