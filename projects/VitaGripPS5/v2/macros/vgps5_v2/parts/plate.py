"""Floor plate between the grip ends (right half, x >= 0) and its blend into the grip end's underside.
No window or camera hole yet (a later pass)."""
from ..shapes import box, blend_wire, loft_wires, one_solid


def build_plate_half(x_s, x2, z2, y0, y1, z0, z1):
    """Boxes only, so every face that meets the floor or the plate bottom is a plane: main slab x 0..x_s (touches
    the blend loft's trimmed end at x_s), an upper slab z2..z1 out to x2 (over the blend loft's top, into the grip).
    Both run from the plate front y0 to the rear face y1."""
    a = box(0.0, x_s, y0, y1, z0, z1)
    b = box(0.0, x2, y0, y1, z2, z1)
    return one_solid(a.fuse(b), "plate boxes")


def build_blend(profiles, x_s, y1, what="plate blend"):
    """profiles: [(y, blend_profile dict)], front to rear. Loft, then trim at x >= x_s and y <= y1 (exact planes)."""
    s = loft_wires([blend_wire(y, p) for y, p in profiles], what)
    return one_solid(s.intersect(box(x_s, 300.0, -100.0, y1, -100.0, 100.0)), what + " trimmed")
