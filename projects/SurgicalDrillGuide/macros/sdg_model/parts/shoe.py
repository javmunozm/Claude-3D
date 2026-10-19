"""shoe (r8 rigid pawl): toothed block with a through-Z slot for a DIN 557 nut and a teardrop screw hole; plus the
bought hardware as clearance volumes (screw + head, washer + jam-nut sweep, drive nut). All in the MIN locked pose."""

from ..constants import SHOE_HOLE_TOP_WALL, Z_MID
from ..shapes import box, cyl_y, extrude_z, one_solid, polygon_face, teardrop_bore_y


def build_shoe(S, apex_dir):
    """Body (face on the rack lands at S['face']) + PAWL_TEETH teeth, minus the nut slot (through Z) and the screw
    hole in the floor. Prints with the -Z face on the bed: every feature is a vertical wall except the Y hole,
    which is a teardrop with its apex +Z."""
    body = box(S["x0"], S["x1"], S["y_bot"], S["face"], S["z0"], S["z1"])
    for p in S["teeth"]:
        body = body + extrude_z(polygon_face(p), S["z0"], S["z1"])
    shoe = one_solid(body, "shoe + teeth")
    sl = S["slot"]
    shoe = one_solid(shoe - box(sl["x0"], sl["x1"], sl["y0"], sl["y1"], S["z0"] - 1.0, S["z1"] + 1.0), "shoe - nut slot")
    sc = S["screw"]
    # The point is cut flat SHOE_HOLE_TOP_WALL under the apex-side face; the flat must not enter the Ø hole_d circle.
    flat = (S["z1"] - SHOE_HOLE_TOP_WALL - sc["z"]) if apex_dir > 0 else (sc["z"] - S["z0"] - SHOE_HOLE_TOP_WALL)
    if flat < sc["hole_d"] / 2.0 - 1e-9:
        raise RuntimeError(f"shoe hole flat {flat:.3f} from the axis cuts into the Ø{sc['hole_d']} clearance circle")
    shoe = one_solid(shoe - teardrop_bore_y(sc["x"], S["y_bot"] - 1.0, sl["y0"] + 0.5, sc["z"], sc["hole_d"], apex_dir,
                                            flat=flat), "shoe - screw hole")
    return shoe


def _cyl_y(x, y0, y1, z, d):
    return cyl_y(x, y0, y1, d / 2.0, z)


def build_hardware(S):
    """Clearance volumes of the bought parts (not printed), MIN pose, locked. One solid each."""
    sc, jm = S["screw"], S["jam"]
    x, z = sc["x"], sc["z"]
    screw = one_solid(_cyl_y(x, sc["head_top"] - sc["head_h"], sc["head_top"], z, sc["head_d"])
                      + _cyl_y(x, sc["head_top"] - 0.5, sc["tip"], z, sc["d"]), "hardware screw")
    jam = one_solid(_cyl_y(x, jm["washer_bot"], jm["nut_bot"] + 0.2, z, S["washer_d"])
                    + _cyl_y(x, jm["nut_bot"], jm["top"], z, S["nut_e"]), "hardware washer + jam nut sweep")
    y0, y1 = S["nut_lock"]
    h = S["nut_s"] / 2.0
    drive = box(x - h, x + h, y0, y1, Z_MID - h, Z_MID + h)
    return {"hw_screw": screw, "hw_jam": jam, "hw_drive_nut": drive}
