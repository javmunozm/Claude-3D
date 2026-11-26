"""Stage 5: the platform. Disc z in [0, h_disc] (the bottom face is printed on the bed), socket ring on top,
z in [h_disc, h_disc + h_socket]. Axis on Z; slot 0 centred on +X."""

from build123d import Align, Box, Cone, Cylinder, Pos, Rot

_MIN = (Align.CENTER, Align.CENTER, Align.MIN)


def build_platform(r_out, r_stop, r_sock, r_sock_od, h_disc, h_socket, chamfer,
                   n_slots, slot_w, slot_r0, slot_r1, **_):
    top = h_disc + h_socket
    disc = Cylinder(r_out, h_disc, align=_MIN) - Pos(0, 0, -1) * Cylinder(r_stop, h_disc + 2, align=_MIN)
    # the ring overlaps the disc by 0.5 mm so the fuse is a volume overlap, not a shared face
    ring = (Pos(0, 0, h_disc - 0.5) * Cylinder(r_sock_od, h_socket + 0.5, align=_MIN)
            - Pos(0, 0, h_disc - 1) * Cylinder(r_sock, h_socket + 2, align=_MIN))
    part = disc + ring

    # 45 deg lead-in: a cone that crosses the hole wall at z = top - chamfer and leaves the top face at r_sock + chamfer.
    # It starts 0.5 mm lower and 0.5 mm inside the (already empty) hole so it cuts the wall transversally.
    lead = 0.5
    part = part - Pos(0, 0, top - chamfer - lead) * Cone(r_sock - lead, r_sock + chamfer + 1, chamfer + lead + 1, align=_MIN)

    slot_len = slot_r1 - slot_r0
    slot = Pos((slot_r0 + slot_r1) / 2, 0, -1) * Box(slot_len, slot_w, h_disc + 2, align=_MIN)
    for i in range(n_slots):
        part = part - Rot(0, 0, i * 360 / n_slots) * slot
    return part
