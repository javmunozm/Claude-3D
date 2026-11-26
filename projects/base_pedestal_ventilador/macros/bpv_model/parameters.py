"""Stages 2 and 4: derived values and the build-time arithmetic checks. Nothing runs at import."""

import math

from . import constants as C


def _pt_seg(pt, seg):
    """Distance from point pt to segment seg = (a, b)."""
    (ax, ay), (bx, by) = seg
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((pt[0] - ax) * dx + (pt[1] - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(pt[0] - ax - t * dx, pt[1] - ay - t * dy)


def derive(**over):
    """Return the parameter dict for build_platform(). Keyword overrides replace a constant (lower-case name),
    which the gates use for their control cases. Raises ValueError when the arithmetic is out of order."""
    v = {k.lower(): getattr(C, k) for k in dir(C) if k.isupper()}
    v.update(over)

    r_out, r_stop, r_sock = v["d_out"] / 2, v["d_stop"] / 2, v["d_socket"] / 2
    r_sock_od = r_sock + v["wall"]
    w2 = v["slot_w"] / 2
    a = 2 * math.pi / v["n_slots"]

    slot_r0 = r_sock_od + v["rim_in"]
    corner_r = r_out - v["rim_out"]
    if corner_r <= w2:
        raise ValueError(f"slot half-width {w2} does not fit inside r={corner_r}")
    slot_r1 = math.sqrt(corner_r ** 2 - w2 ** 2)            # outer corners of the slot land on r = corner_r
    # spoke between slot 0 (its +Y edge) and slot 1 (its -Y edge, rotated by a): distances between edge segments,
    # not lines. The perpendicular from slot 0's inner corner lands before slot 1's inner end, so the inner
    # spoke is corner to corner (13.034 for the user's values, not the line distance 12.590).
    edge0 = ((slot_r0, w2), (slot_r1, w2))
    edge1 = tuple((x * math.cos(a) + w2 * math.sin(a), x * math.sin(a) - w2 * math.cos(a)) for x in (slot_r0, slot_r1))
    spoke_in = min(_pt_seg(edge0[0], edge1), _pt_seg(edge1[0], edge0))
    spoke_out = min(_pt_seg(edge0[1], edge1), _pt_seg(edge1[1], edge0))

    errs = []
    if not r_stop < r_sock:
        errs.append(f"stop hole D{v['d_stop']} must be smaller than the socket D{v['d_socket']}")
    if not r_sock_od < slot_r0 < slot_r1 < r_out:
        errs.append(f"slots r {slot_r0:.3f}..{slot_r1:.3f} not between socket OD r {r_sock_od} and edge r {r_out}")
    if spoke_in <= 0:
        errs.append(f"slots overlap at their inner ends (spoke {spoke_in:.3f})")
    if not 0 < v["chamfer"] < v["h_socket"]:
        errs.append(f"chamfer {v['chamfer']} must be inside the socket height {v['h_socket']}")
    if errs:
        raise ValueError("; ".join(errs))

    slot_len = slot_r1 - slot_r0
    vol = (math.pi * (r_out ** 2 - r_stop ** 2) * v["h_disc"]
           + math.pi * (r_sock_od ** 2 - r_sock ** 2) * v["h_socket"]
           - v["n_slots"] * v["slot_w"] * slot_len * v["h_disc"]
           - math.pi * v["chamfer"] ** 2 * (r_sock + v["chamfer"] / 3))   # ring of a 45 deg triangle, by Pappus

    return {
        "r_out": r_out, "r_stop": r_stop, "r_sock": r_sock, "r_sock_od": r_sock_od,
        "h_disc": v["h_disc"], "h_socket": v["h_socket"], "chamfer": v["chamfer"],
        "n_slots": v["n_slots"], "slot_w": v["slot_w"], "slot_r0": slot_r0, "slot_r1": slot_r1,
        "slot_len": slot_len, "spoke_in": spoke_in, "spoke_out": spoke_out, "volume": vol,
    }
