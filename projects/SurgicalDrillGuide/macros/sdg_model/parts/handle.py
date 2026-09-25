"""handle: revolved grip + ferrule, Ø16 core, seating collar, male Tr16x4 thread."""

from shapely.geometry import Polygon

from build123d import Axis, Face, Pos, Solid, Wire, revolve

from ..constants import BUTT_FLAT, HANDLE_CORE_GRIP_DEPTH
from ..mechanisms import cam_thread
from ..rings import horizontal_chord, ring_face, ring_points
from ..shapes import along_y, box, cone_y, cyl_y, one_solid


def build_handle(D, t_z, thread):
    """Revolved grip + ferrule (traced half-profiles) + male thread on the ferrule top."""
    hx, zc = D["handle_axis_x"], t_z / 2.0
    ax = Axis((hx, 0, 0), (0, 1, 0))
    grip = revolve(ring_face("grip_half"), ax, 360)
    ferrule = revolve(ring_face("ferrule_half"), ax, 360)
    # Handle core (round 3, user decision): the male thread is Ø16 major, and no section between it and the grip
    # may be narrower. The traced ferrule is r 7.19-7.49 and the traced halves leave a 0.25 mm gap at the grip
    # top (grip top Y -52.315, ferrule bottom Y -52.066; round 2 bridged it with a Ø8 neck). One Ø(major)
    # cylinder from HANDLE_CORE_GRIP_DEPTH inside the grip up to the shoulder replaces the bridge: DEVIATION.
    y_core0 = D["grip_top_y"] - HANDLE_CORE_GRIP_DEPTH
    r_core = thread["r_crest"]
    r_grip = horizontal_chord(Polygon(ring_points("grip_half")), y_core0)[1] - hx
    if r_grip < r_core + 1.0:
        raise RuntimeError(f"handle core bottom Y {y_core0:.3f}: grip radius {r_grip:.3f} does not embed r {r_core}")
    # Round 4 collar (user decision): one revolved profile = Ø22 cylinder (flat seating face at the shoulder Y,
    # square to the axis) + a 45° cone under it down to r taper_r. One revolve, so no internal coincident faces.
    y_sh = D["ferrule_top_y"]
    st = thread["seat"]
    rc, rt = st["collar_r"], st["taper_r"]
    y_c0 = y_sh - st["collar_t"]
    y_c1 = y_c0 - (rc - rt)
    collar = revolve(Face(Wire.make_polygon([(hx, y_sh, 0), (hx + rc, y_sh, 0), (hx + rc, y_c0, 0),
                                             (hx + rt, y_c1, 0), (hx, y_c1, 0)], close=True)), ax, 360)
    # The core now ends INSIDE the collar, 0.5 below the male's start (which is one pitch below the face, inside
    # the collar): the core surface r 8.0 would otherwise coincide with the male crest r 8.0 (the round-3 hang).
    y_core1 = y_sh - thread["pitch"] - 0.5
    r_at = rc - max(0.0, y_c0 - y_core1)
    if not (y_c1 < y_core1 < y_sh and r_at > r_core + 0.5):
        raise RuntimeError(f"core top Y {y_core1:.3f} is not inside the collar")
    core = along_y(Solid.make_cylinder(r_core, y_core1 - y_core0), hx, y_core0, 0.0)
    # Traced ferrule (r <= 7.49) clipped 1.0 below the face so its top face is buried in the collar.
    ferrule = ferrule & box(hx - 20, hx + 20, y_core0 - 5, y_sh - 1.0, -20, 20)
    handle = one_solid(grip + ferrule + core + collar, "handle revolve fuse").moved(Pos(0, 0, zc))
    y_butt = handle.bounding_box().min.Y
    handle = one_solid(handle - box(hx - 30, hx + 30, y_butt - 5, y_butt + BUTT_FLAT, zc - 30, zc + 30),
                       "handle butt flat")

    th = thread
    y_sh = D["ferrule_top_y"]
    # Phase origin: whole pitches (2P) from the female's origin at y_sh - 2P. Round 3 fix: the male starts AT the
    # shoulder, not one pitch below it. Below the shoulder it lay inside the Ø16 core whose surface coincides with
    # the male crest (r_crest), and that coincident fuse made the handle is_valid False; its STL export then hung
    # (> 81 min at 0.03/0.2). Starting at y_sh, the male's bottom face lands flat on the core's top face: the fuse
    # is valid, one solid, and the STL exports in 0.7 s (probe cad3/probe.py, 2026-09-23).
    # Round 4: the male starts ONE PITCH below the face (phase kept: still whole pitches from the female origin),
    # inside the Ø22 collar where nothing sits at r 8.0, so the male/collar fuse is a real overlap (no flat landing).
    y_start = y_sh - th["pitch"]
    length = th["engage"] + th["pitch"]
    male = along_y(cam_thread(th["r_root"], th["r_crest"], th["crest_w"], th["pitch"], th["flank"], length,
                              th["n"]), hx, y_start, zc)
    y_tip = y_sh + th["engage"]
    clip = cyl_y(hx, y_start - 0.1, y_tip - th["chamfer"] + 0.01, th["r_crest"] + 1.0, zc) + cone_y(
        hx, y_tip - th["chamfer"], y_tip, th["r_crest"], th["r_crest"] - th["chamfer"], zc)
    male = male & clip
    handle = one_solid(handle + male, "handle + male thread")
    return handle
