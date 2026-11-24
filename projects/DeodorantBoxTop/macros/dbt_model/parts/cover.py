"""Stage 5: the cover. Plate z in [0, plate_t] (top face at z = plate_t, printed face down);
sockets hang below it, z in [-depth, 0]. Origin at a plate corner; X along the 200 side."""

from build123d import Box, Ellipse, Location, Polygon, Pos, Rot, extrude


def _corner_triangle(leg, inset, height):
    """Right-isosceles prism, right angle at (inset, inset), legs along +X and +Y, z in [-height, 0]."""
    tri = Polygon((inset, inset), (inset + leg, inset), (inset, inset + leg), align=None)
    return extrude(tri, amount=-height)


def build_cover(plate_x, plate_y, plate_t, hole_x, hole_y, cx, cy, cavity_leg, outer_leg, wall, depth, **_):
    plate = Box(plate_x, plate_y, plate_t).moved(Location((plate_x / 2, plate_y / 2, plate_t / 2)))
    for x in cx:
        for y in cy:
            hole = extrude(Ellipse(hole_x / 2, hole_y / 2), amount=plate_t + 2).moved(Location((x, y, -1)))
            plate = plate - hole

    # the cavity extrusion runs 1 mm past the socket bottom so the cut is open at the end; its top is the
    # plate underside (z = 0), which becomes the socket floor once the ring is fused to the plate
    socket = _corner_triangle(outer_leg, 0.0, depth) - _corner_triangle(cavity_leg, wall, depth + 1)
    # rotate the origin-corner socket into the four corners
    corners = [
        Location((0, 0, 0)),
        Pos(plate_x, 0, 0) * Rot(0, 0, 90),
        Pos(plate_x, plate_y, 0) * Rot(0, 0, 180),
        Pos(0, plate_y, 0) * Rot(0, 0, 270),
    ]
    part = plate
    for loc in corners:
        part = part + socket.moved(loc)
    return part
