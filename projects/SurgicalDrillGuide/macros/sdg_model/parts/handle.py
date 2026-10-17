"""handle: revolved traced grip, Ø16 core, round 6 square head with a blind socket for the frame lug and a snap
notch for the frame finger. Prints standing, butt down (+Y up)."""

import math

from shapely.geometry import Polygon

from build123d import Axis, Face, Pos, Solid, Wire, revolve

from ..constants import BUTT_FLAT, HANDLE_CORE_GRIP_DEPTH
from ..rings import horizontal_chord, ring_face, ring_points
from ..shapes import along_y, box, extrude_z, keep_below, one_solid, polygon_face, yz_prism_x


def head_solid(coup, zc):
    """Square head (prism) trimmed underneath by a cone at cone_deg from the axis down into the Ø16 core, so the
    head has no flat down-facing face when the handle stands. Then the socket (with mouth chamfers), the 45° top
    +X edge chamfer and the snap notch are cut."""
    hx, hd, so, nt = coup["hx"], coup["head"], coup["socket"], coup["notch"]
    x0, x1, z0, z1, yt, yh = hd["x0"], hd["x1"], hd["z0"], hd["z1"], hd["y_top"], hd["y_bot"]
    R = math.hypot((x1 - x0) / 2, (z1 - z0) / 2) + 0.05               # circumscribes the square at the head bottom
    r_low = hd["core_r"] - 1.0                                         # cone ends inside the core (no coincidence)
    tn = math.tan(math.radians(hd["cone_deg"]))
    y_low = yh - (R - r_low) / tn
    ax = Axis((hx, 0, 0), (0, 1, 0))
    env = revolve(Face(Wire.make_polygon([(hx, y_low, 0), (hx + r_low, y_low, 0), (hx + R, yh, 0),
                                          (hx + R, yt + 1.0, 0), (hx, yt + 1.0, 0)], close=True)), ax, 360)
    head = one_solid(box(x0, x1, y_low - 1.0, yt, z0, z1) & env.moved(Pos(0, 0, zc)), "head prism & cone")

    # Socket: box + two 45° mouth-chamfer prisms (mouth_x on the X edges over the full socket Z, mouth_z on the
    # Z edges over the full socket X). A union, not a half-space intersection: the intersection clipped the X
    # relief near Z 0 / 10, where the lug's r 3 fillets reach into the mouth (0.063 mm3 interference, build 1).
    cx, cz = so["mouth_x"], so["mouth_z"]
    xp = extrude_z(polygon_face([(so["x0"] - cx - 1.0, yt + 1.0), (so["x0"], yt - cx), (so["x1"], yt - cx),
                                 (so["x1"] + cx + 1.0, yt + 1.0)]), so["z0"], so["z1"])
    zp = yz_prism_x([(yt + 1.0, so["z0"] - cz - 1.0), (yt - cz, so["z0"]), (yt - cz, so["z1"]),
                     (yt + 1.0, so["z1"] + cz + 1.0)], so["x0"], so["x1"])
    socket = one_solid(box(so["x0"], so["x1"], so["y_floor"], yt + 1.0, so["z0"], so["z1"]) + xp + zp, "socket cutter")
    head = one_solid(head - socket, "head - socket")

    # Top +X outer edge chamfer (hook lead-in).
    c = hd["top_chamfer"]
    edge = keep_below(box(x1 - c - 1.0, x1 + 1.0, yt - c - 1.0, yt + 1.0, z0 - 1.0, z1 + 1.0),
                      (x1 - c, yt, zc), (-1, -1, 0), "head top chamfer cutter")
    head = one_solid(head - edge, "head - top chamfer")

    # Snap notch in the +X face: flat floor, vertical sides, 45° gable roof rising k toward -X.
    k, za = nt["k"], 0.5 * (nt["z0"] + nt["z1"])
    n = box(nt["x0"], x1 + 1.0, nt["y_floor"], nt["apex_y"] + 1.5, nt["z0"], nt["z1"])
    n = keep_below(n, (x1, nt["apex_y"], za), (k, 1, -1), "notch roof -Z")
    n = keep_below(n, (x1, nt["apex_y"], za), (k, 1, 1), "notch roof +Z")
    head = one_solid(head - n, "head - notch")
    return head, y_low


def build_handle(D, t_z, coup):
    """Revolved grip (traced half-profile) + Ø16 core + square head with the lug socket and the snap notch.
    The traced ferrule (r <= 7.49) lies wholly inside the Ø16 core, so it is not built."""
    hx, zc = D["handle_axis_x"], t_z / 2.0
    ax = Axis((hx, 0, 0), (0, 1, 0))
    grip = revolve(ring_face("grip_half"), ax, 360)
    y_core0 = D["grip_top_y"] - HANDLE_CORE_GRIP_DEPTH
    r_core = coup["head"]["core_r"]
    r_grip = horizontal_chord(Polygon(ring_points("grip_half")), y_core0)[1] - hx
    if r_grip < r_core + 1.0:
        raise RuntimeError(f"handle core bottom Y {y_core0:.3f}: grip radius {r_grip:.3f} does not embed r {r_core}")
    fh = Polygon(ring_points("ferrule_half"))
    r_fer = fh.bounds[2] - hx
    if r_fer >= r_core - 0.1:
        raise RuntimeError(f"traced ferrule r {r_fer:.3f} is not inside the core r {r_core}")
    head, y_low = head_solid(coup, zc)
    y_core1 = coup["head"]["y_bot"] + 1.0                              # core top inside the head floor
    core = along_y(Solid.make_cylinder(r_core, y_core1 - y_core0), hx, y_core0, zc)
    handle = one_solid(grip.moved(Pos(0, 0, zc)) + core, "handle grip + core")
    handle = one_solid(handle + head, "handle + head")
    y_butt = handle.bounding_box().min.Y
    handle = one_solid(handle - box(hx - 30, hx + 30, y_butt - 5, y_butt + BUTT_FLAT, zc - 30, zc + 30),
                       "handle butt flat")
    return handle
