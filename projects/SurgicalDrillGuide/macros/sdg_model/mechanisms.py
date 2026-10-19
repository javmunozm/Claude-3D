"""SurgicalDrillGuide stage 3b: mechanism profiles - ratchet notch cutter, shoe (rigid pawl) tooth."""

import math

from .shapes import polygon_face


def sawtooth_cutter_face(yb, x_start, x_end, pitch, depth, land, eps, hook_deg=0.0, below=2.0):
    """In-plane cutter for ratchet notches in the rack BOTTOM face.

    Notch k: locking wall from the apex (a_k, yb+depth) down to the mouth (a_k + depth*tan(hook), yb) (rack
    material on its -X side; hook_deg > 0 undercuts it so the apex leans -X), ramp from the apex down to
    (a_k + pitch - land, yb). The slider may move +X (jaws close) over the ramps; -X (open) is blocked.
    The ramp and the apex are unchanged by the hook; the land at the mouth grows by depth*tan(hook).
    """
    tb = math.tan(math.radians(hook_deg))
    pts = []
    n = int((x_end - x_start - (pitch - land)) // pitch) + 1
    a_list = [x_start + k * pitch for k in range(n)]
    y_lo = min(yb(x_start), yb(x_end)) - below
    pts.append((x_start - 0.5, y_lo))
    for a in a_list:
        y = yb(a)
        # The ramp keeps the tooth's slope depth/(pitch-land) and is merely EXTENDED below the envelope by eps
        # (it meets the envelope at a + pitch - land). Before the fix-round the ramp ended at y - eps at
        # a + pitch - land, i.e. slope (depth+eps)/(pitch-land) = 0.603 vs the tooth's 0.567 (form-auditor),
        # which narrowed the seat gap along the ramp.
        pts += [(a + (depth + eps) * tb, y - eps), (a, y + depth), (a + (pitch - land) * (1.0 + eps / depth), y - eps)]
    pts.append((a_list[-1] + pitch, y_lo))
    return polygon_face(pts), a_list


def _line_x(p, u, y):
    """x where the line through p with direction u crosses height y."""
    return p[0] + u[0] * (y - p[1]) / u[1]


def pawl_tooth_pts(a, yb_a, pitch, depth, land, clear, y_root, hook_deg=0.0):
    """Pawl tooth = the notch triangle offset inward by `clear` (normal offset of the wall and the ramp),
    extended down to y_root (into the tongue). With hook_deg the locking face is parallel to the undercut wall."""
    be = math.radians(hook_deg)
    ax_, ay_ = a, yb_a + depth                                   # notch apex
    uw = (math.sin(be), -math.cos(be))                           # wall direction, apex -> mouth
    nw = (math.cos(be), math.sin(be))                            # wall normal into the notch
    L = math.hypot(pitch - land, depth)
    ur = ((pitch - land) / L, -depth / L)                        # ramp direction, apex -> land
    nr = (-depth / L, -(pitch - land) / L)                       # ramp normal into the notch
    pw = (ax_ + clear * nw[0], ay_ + clear * nw[1])
    pr = (ax_ + clear * nr[0], ay_ + clear * nr[1])
    # apex = offset wall ∩ offset ramp: pw + s*uw = pr + t*ur
    det = uw[0] * (-ur[1]) - uw[1] * (-ur[0])
    s = ((pr[0] - pw[0]) * (-ur[1]) - (pr[1] - pw[1]) * (-ur[0])) / det
    apex = (pw[0] + s * uw[0], pw[1] + s * uw[1])
    x_right = _line_x(pr, ur, yb_a - clear)                      # offset ramp meets y = yb - clear
    x_bot = _line_x(pw, uw, y_root)                              # locking face continued into the tongue
    pts = [(x_bot, y_root), apex, (x_right, yb_a - clear), (x_right, y_root)]
    return pts, (apex[0], x_right, apex[1])
