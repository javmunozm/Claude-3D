"""One snap finger with its lip, and the clearance pit cut around it (profiles of r16's finger_solid / pit_solid)."""
import numpy as np
from build123d import Plane
from shapely.geometry import Point, Polygon, box as sbox
from shapely.ops import unary_union

from ..shapes import prism_in_frame


def finger_profile(lip_u, lip_top_z, root_z, t_root, t_tip, overhang, lead_deg, ret_deg, flat, land,
                   inner_slot, gap, root_r):
    """(u, z) polygon: u outward from the pocket wall, z world height. Same construction as r16."""
    L = lip_u - root_z
    slope = (t_root - t_tip) / L

    def beam_u(z):
        return t_root - slope * (z - root_z)

    t_below = beam_u(root_z - 1.0)
    z_tip = lip_u + (overhang - flat) / np.tan(np.radians(ret_deg))
    t_top = -overhang + (lip_top_z - z_tip) * np.tan(np.radians(lead_deg))
    u_head = max(t_tip, t_top + land)
    z_ch = (lip_u - u_head + t_root + slope * root_z) / (1.0 + slope)
    pp = [(0.0, root_z - 1.0), (t_below, root_z - 1.0), (beam_u(z_ch), z_ch),
          (u_head, lip_u), (u_head, lip_top_z), (t_top, lip_top_z),
          (-overhang, z_tip), (-flat, lip_u), (0.0, lip_u)]
    pp = [q for i, q in enumerate(pp) if i == 0 or np.hypot(q[0] - pp[i - 1][0], q[1] - pp[i - 1][1]) > 1e-6]
    prof = Polygon(pp)
    strip = sbox(-inner_slot + 0.05, root_z - 1.0, t_root + gap - 0.05, root_z)
    low = unary_union([prof, strip]).intersection(sbox(-5.0, root_z - 1.0, 10.0, root_z + 3.0))
    low = low.buffer(root_r, resolution=16).buffer(-root_r, resolution=16)
    prof = unary_union([prof, low])
    if prof.geom_type != "Polygon":
        raise RuntimeError("finger profile is not one polygon")
    info = dict(z_tip=z_tip, t_top=t_top, u_head=u_head, land=u_head - t_top)
    return np.asarray(prof.exterior.coords)[:-1], info


def pit_profile(width, slot, inner_slot, t_root, gap, corner_r):
    """(u, t) polygon of the pit: u outward, t along the outline."""
    hw = width / 2.0 + slot
    a0, a1, R = -inner_slot, t_root + gap, corner_r
    prof = sbox(a0, -hw, a1 - R, hw).union(sbox(a0, -hw + R, a1, hw - R))
    prof = prof.union(Point(a1 - R, hw - R).buffer(R, resolution=16)).union(Point(a1 - R, -hw + R).buffer(R, resolution=16))
    return np.asarray(prof.simplify(1e-4).exterior.coords)[:-1]


def build_finger(p, n, width, prof_uz):
    """Finger solid: the (u, z) profile extruded +-width/2 along the outline tangent at p."""
    plane = Plane(origin=(p[0], p[1], 0.0), x_dir=(n[0], n[1], 0.0), z_dir=(n[1], -n[0], 0.0))
    return prism_in_frame(prof_uz, -width / 2.0, width / 2.0, plane)


def build_pit(p, n, prof_ut, z0, z1):
    """Pit cutter: the (u, t) profile extruded in Z from z0 to z1."""
    plane = Plane(origin=(p[0], p[1], 0.0), x_dir=(n[0], n[1], 0.0), z_dir=(0.0, 0.0, 1.0))
    return prism_in_frame(prof_ut, z0, z1, plane)
