"""SurgicalDrillGuide stage 4: parameter bundles derived from the constants and the rings, plus the build-time
arithmetic checks (MAX tip gap, collar seating, boss-pad clearance) that stop the build before any geometry."""

import math

from shapely.geometry import LineString, Polygon
from shapely.geometry import box as sbox

from .constants import *  # noqa: F401,F403  (this stage turns every constant into a bundle)
from .mechanisms import pawl_tooth_pts
from .rings import derive, derive_channel, horizontal_chord, rack_bottom_y, ring_points, vertical_chord


def derive_pin(D):
    """End-stop pin position (DERIVED from the rings) and the travel at which the collar meets it."""
    fr = D["frame_poly"]
    r_hole = (PIN_D + PIN_FIT_CLEAR) / 2.0
    x = 3.0 - RACK_EXT
    for _ in range(5):
        y_top = vertical_chord(fr, x)[1]
        y_apex = rack_bottom_y(D, x) + TOOTH_DEPTH           # notch apex line (the teeth band's upper limit)
        y = 0.5 * (y_top + y_apex)
        x_tip = horizontal_chord(fr, y)[0]
        x = x_tip + PIN_TIP_WALL + r_hole
    col = Polygon(ring_points("collar"))
    collar_face = min(horizontal_chord(col, y + dy)[0] for dy in [PIN_D / 2.0 * k / 10.0 for k in range(-10, 11)])
    # Round 3: the pin may sit c/2 towards the collar in its hole (slip fit), so the worst-case contact travel
    # is to the HOLE's +X edge, not the centred pin's.
    travel_stop_centred = collar_face - (x + PIN_D / 2.0)
    travel_stop = collar_face - (x + r_hole)
    n_max = int(math.floor((travel_stop - PIN_STOP_MIN_GAP) / TOOTH_PITCH))
    return {"x": x, "y": y, "d": PIN_D, "hole_d": PIN_D + PIN_FIT_CLEAR, "x_tip": x_tip, "y_top": y_top,
            "travel_stop_centred": travel_stop_centred,
            "y_apex": y_apex, "collar_face": collar_face, "travel_stop": travel_stop, "n_max": n_max,
            "z0": -PIN_PROTRUDE, "z1": T_Z + PIN_PROTRUDE}


def parameters():
    D = derive()
    pin = derive_pin(D)
    D["pin"] = pin
    pose_teeth = {"min": 0, "mid": int(round(pin["n_max"] / 2.0)), "max": pin["n_max"]}
    D["pose_teeth"] = pose_teeth
    travel = {k: n * TOOTH_PITCH for k, n in pose_teeth.items()}
    ch_y0, ch_y1, ch_env = derive_channel(D, travel["max"])
    chan = {"y0": ch_y0, "y1": ch_y1, "envelope": ch_env}
    # Round 4: squared carriage end = the traced end face at the channel mid-height (DERIVED).
    D["carriage_end_x"] = horizontal_chord(D["carriage_poly"], 0.5 * (ch_y0 + ch_y1))[1]
    bx0 = D["rack_bottom_line"][0]
    # Teeth: the traced-rack phase (first wall bx0 + margin) continued -X, in whole pitches, into the extension.
    x0_traced = bx0 + TEETH_START_MARGIN
    m_ext = int(math.floor((x0_traced - (bx0 - RACK_EXT + TEETH_START_MARGIN)) / TOOTH_PITCH + 1e-9))
    teeth = {"x0": x0_traced - m_ext * TOOTH_PITCH, "x1": TEETH_X_END, "x0_traced": x0_traced, "n_ext": m_ext, "pitch": TOOTH_PITCH, "depth": TOOTH_DEPTH,
             "land": TOOTH_LAND, "eps": TOOTH_CUT_EPS, "hook": TOOTH_HOOK_DEG}
    # C-tip bore cutter: X range of the C-tip chord at the wire height, plus overrun.
    c = D["frame_poly"].intersection(LineString([(140.0, D["wire_y"]), (200.0, D["wire_y"])]))
    cx = [q[0] for g in getattr(c, "geoms", [c]) for q in g.coords]
    # C-tip pad: sleeve from the jaw face at the wire height to just past where the bore's lower edge leaves
    # the traced arm on the outer (45°) edge.
    lo = horizontal_chord(D["frame_poly"].intersection(sbox(140, 40, 200, 70)), D["wire_y"] - BORE_D / 2.0)
    ctip = {"x_entry": min(cx), "x_exit": lo[1] + CTIP_PAD_EXIT_MARGIN,
            "half_h": BORE_D / 2.0 + CTIP_WALL_MIN + CTIP_PAD_MARGIN, "blend_r": CTIP_PAD_BLEND_R}
    D["ctip"] = ctip
    # Tip gap at wire height = jaw face (x_entry) - crown face on the wire line; must reach TARGET_MAX_GAP at MAX.
    crown_x = horizontal_chord(Polygon(ring_points("l_arm")), D["wire_y"])[1]
    D["gap_min"] = min(cx) - crown_x
    D["gap_max"] = D["gap_min"] + travel["max"]
    if D["gap_max"] < TARGET_MAX_GAP:
        raise RuntimeError(f"MAX tip gap {D['gap_max']:.3f} < {TARGET_MAX_GAP}: increase RACK_EXT")
    bore = {"d": BORE_D, "apex_dir": TEARDROP_APEX_DIR, "overrun": BORE_OVERRUN,
            "ctip_x0": min(cx) - BORE_OVERRUN, "ctip_x1": max(max(cx), ctip["x_exit"]) + BORE_OVERRUN,
            "ctip_chord": (min(cx), max(cx))}
    r_crest = THREAD_MAJOR_D / 2.0
    thread = {"pitch": THREAD_PITCH, "r_crest": r_crest, "r_root": r_crest - THREAD_H, "crest_w": THREAD_CREST_W,
              "flank": THREAD_FLANK_DEG, "rclear": THREAD_RADIAL_CLEAR, "aclear": THREAD_AXIAL_CLEAR,
              "engage": THREAD_ENGAGE, "chamfer": THREAD_TIP_CHAMFER, "n": THREAD_CAM_N}
    hx = D["handle_axis_x"]
    half = BOSS_OD / 2.0                     # flat band = the boss width (boss flush with the pad faces)
    boss = {"od": BOSS_OD, "floor": BOSS_HOLE_FLOOR, "pad_blend": BOSS_PAD_BLEND, "half_len": half,
            "mouth_r_face": r_crest + THREAD_RADIAL_CLEAR + BOSS_MOUTH_FACE_CLEAR, "mouth_depth": BOSS_MOUTH_DEPTH,
            "pad_x0": hx - half - BOSS_PAD_BLEND, "pad_x1": hx + half + BOSS_PAD_BLEND,
            "taper_deg": math.degrees(math.atan2((BOSS_OD - T_Z) / 2.0, BOSS_PAD_BLEND))}
    # Seating arithmetic (round 4). The model is the seated pose: collar face = boss face = ferrule shoulder Y.
    # Screwing in, the collar reaches the boss face first iff the male tip is still short of the hole floor and
    # nothing of the handle wider than the male crest lies above the collar face (the Ø16 core ends inside it).
    y_face = D["ferrule_top_y"]
    seat = {"face_y": y_face, "collar_r": HANDLE_COLLAR_OD / 2.0, "collar_t": HANDLE_COLLAR_T,
            "taper_r": HANDLE_COLLAR_TAPER_R,
            "tip_to_floor": (D["bar_bottom_at_axis"] - BOSS_HOLE_FLOOR) - (y_face + THREAD_ENGAGE),
            "annulus": (boss["mouth_r_face"], min(HANDLE_COLLAR_OD, BOSS_OD) / 2.0)}
    seat["annulus_w"] = seat["annulus"][1] - seat["annulus"][0]
    if seat["tip_to_floor"] <= 0.0 or seat["annulus_w"] <= 0.0 or HANDLE_COLLAR_OD > BOSS_OD:
        raise RuntimeError(f"collar cannot seat first: tip->floor {seat['tip_to_floor']:.3f}, annulus "
                           f"{seat['annulus_w']:.3f}, collar Ø{HANDLE_COLLAR_OD} vs boss Ø{BOSS_OD}")
    thread["seat"] = seat
    if boss["pad_x0"] < D["carriage_x1"] + BOSS_PAD_CARRIAGE_CLEAR:
        raise RuntimeError(f"boss pad starts at X {boss['pad_x0']:.3f}, inside the carriage clearance at MIN "
                           f"({D['carriage_x1']:.3f} + {BOSS_PAD_CARRIAGE_CLEAR})")
    pawl = {"anchor_x": PAWL_ANCHOR_X, "free_x": PAWL_FREE_X, "slot_w": PAWL_SLOT_W,
            "window_top_y": PAWL_WINDOW_TOP_Y, "seat_clear": PAWL_SEAT_CLEAR, "tab_w": TAB_W,
            "tab_bottom_y": TAB_BOTTOM_Y, "pad_len": PAD_LEN, "pad_t": PAD_T, "hook": TOOTH_HOOK_DEG,
            "stop": {"drop": TAB_STOP_DROP, "leg_w": STOP_LEG_W, "beam_t": STOP_BEAM_T, "relief": STOP_RELIEF}}
    return D, travel, chan, teeth, bore, thread, boss, pawl


def seat_notch(a_list, pawl, D):
    """The notch the pawl tooth sits in at MIN opening: the right-most one whose tooth fits in the tongue."""
    best = None
    for a in a_list:
        _, (xl, xr, _) = pawl_tooth_pts(a, rack_bottom_y(D, a), TOOTH_PITCH, TOOTH_DEPTH, TOOTH_LAND,
                                        pawl["seat_clear"], 0.0, pawl["hook"])
        if xl > pawl["anchor_x"] + 2.0 and xr <= pawl["free_x"] - PAWL_TOOTH_MARGIN:
            best = a
    if best is None:
        raise RuntimeError("no rack notch lies under the pawl tongue")
    k = a_list.index(best)
    if k - max(D["pose_teeth"].values()) < 0:
        raise RuntimeError("pawl would run off the toothed length at MAX opening")
    return best, k
