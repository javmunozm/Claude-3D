"""Stage 2/4: derived values and build-time arithmetic checks (run before any geometry)."""

import math

from . import constants as C

K_OFFSET = 2 + math.sqrt(2)   # leg growth of a right-isosceles triangle per unit of outward offset


def derive(plate_x=C.PLATE_X, plate_y=C.PLATE_Y, plate_t=C.PLATE_T, hole_x=C.HOLE_X, hole_y=C.HOLE_Y,
           n_x=C.N_X, n_y=C.N_Y, margin_x=C.MARGIN_X, margin_y=C.MARGIN_Y, pillar_leg=C.PILLAR_LEG,
           clear=C.SOCKET_CLEAR, wall=C.SOCKET_WALL, depth=C.SOCKET_DEPTH):
    gap_x = (plate_x - 2 * margin_x - n_x * hole_x) / (n_x - 1)
    gap_y = (plate_y - 2 * margin_y - n_y * hole_y) / (n_y - 1)
    pitch_x, pitch_y = hole_x + gap_x, hole_y + gap_y
    cx = [margin_x + hole_x / 2 + i * pitch_x for i in range(n_x)]
    cy = [margin_y + hole_y / 2 + j * pitch_y for j in range(n_y)]
    cavity_leg = pillar_leg + clear * K_OFFSET
    outer_leg = cavity_leg + wall * K_OFFSET
    # plan-view clearance: corner hole (nearest the origin corner) vs the socket hypotenuse x + y = outer_leg
    a, b = hole_x / 2, hole_y / 2
    min_sum = cx[0] + cy[0] - math.hypot(a, b)
    corner_clear = (min_sum - outer_leg) / math.sqrt(2)
    p = dict(plate_x=plate_x, plate_y=plate_y, plate_t=plate_t, hole_x=hole_x, hole_y=hole_y,
             margin_x=margin_x, margin_y=margin_y, gap_x=gap_x, gap_y=gap_y, pitch_x=pitch_x, pitch_y=pitch_y,
             cx=cx, cy=cy, pillar_leg=pillar_leg, clear=clear, wall=wall, depth=depth,
             cavity_leg=cavity_leg, outer_leg=outer_leg, corner_clear=corner_clear)
    check(p)
    return p


def check(p):
    """Raise before any geometry if the numbers are inconsistent."""
    if p["gap_x"] <= 0 or p["gap_y"] <= 0:
        raise ValueError(f"holes overlap: gap_x={p['gap_x']:.3f}, gap_y={p['gap_y']:.3f}")
    if p["margin_y"] <= 0 or p["margin_x"] <= 0:
        raise ValueError("hole touches the plate edge")
    if p["corner_clear"] <= 0:
        raise ValueError(f"socket runs into the corner hole: clearance {p['corner_clear']:.3f}")
    if p["depth"] <= 0 or p["wall"] <= 0 or p["clear"] < 0:
        raise ValueError("socket depth/wall/clearance out of range")
