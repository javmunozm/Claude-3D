"""Stage 2/4: derived values and build-time arithmetic checks (run before any geometry)."""

from . import constants as C


def derive(rod_d=C.ROD_D, clearance=C.BORE_CLEARANCE, wall=C.WALL, overall=C.OVERALL,
           gusset_t=C.GUSSET_T, gusset_tip_proud=C.GUSSET_TIP_PROUD, end_chamfer=C.END_CHAMFER,
           bore_chamfer=C.BORE_CHAMFER):
    bore_d = rod_d + clearance
    od = bore_d + 2 * wall
    r_out = od / 2
    reach = overall - r_out              # axis intersection -> arm tip
    socket = reach - r_out               # bore stops at the other arms' skin: the core stays solid
    gusset_tip = reach - end_chamfer     # plate ends where the tip chamfer starts
    gusset_w = r_out + gusset_tip_proud  # plate height above the arm axis at the tip
    p = dict(bore_d=bore_d, od=od, r_out=r_out, reach=reach, socket=socket, wall=wall,
             gusset_t=gusset_t, gusset_tip=gusset_tip, gusset_w=gusset_w, end_chamfer=end_chamfer,
             bore_chamfer=bore_chamfer, overall=overall)
    check(p)
    return p


def check(p):
    """Raise before any geometry if the numbers are inconsistent."""
    if abs((p["od"] - p["bore_d"]) / 2 - C.WALL) > 1e-9:
        raise ValueError(f"wall {(p['od'] - p['bore_d']) / 2} != {C.WALL}")
    if p["gusset_t"] < C.GUSSET_T_MIN:
        raise ValueError(f"gusset {p['gusset_t']} < user minimum {C.GUSSET_T_MIN}")
    if p["gusset_t"] >= p["od"]:
        raise ValueError(f"gusset {p['gusset_t']} not thinner than the arm {p['od']}")
    if p["socket"] <= 0:
        raise ValueError(f"socket depth {p['socket']} <= 0")
    if not (p["r_out"] < p["gusset_w"] < p["gusset_tip"]):
        raise ValueError(f"gusset tip height {p['gusset_w']} outside ({p['r_out']}, {p['gusset_tip']})")
    if p["bore_chamfer"] >= p["wall"]:
        raise ValueError("bore chamfer eats the wall")
