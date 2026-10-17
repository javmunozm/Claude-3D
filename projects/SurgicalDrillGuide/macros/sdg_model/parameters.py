"""SurgicalDrillGuide stage 4: parameter bundles derived from the constants and the rings, plus the build-time
arithmetic checks (MAX tip gap; round 6 coupling: carriage clearance, head-to-bar gap, fillet-in-mouth clearance,
seating, snap engagement and slack) that stop the build before any geometry."""

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
    coup = derive_coupling(D)
    D["hook_outer"] = derive_hook_outer(D, ctip)
    pawl ={"anchor_x": PAWL_ANCHOR_X, "free_x": PAWL_FREE_X, "slot_w": PAWL_SLOT_W,
            "window_top_y": PAWL_WINDOW_TOP_Y, "seat_clear": PAWL_SEAT_CLEAR, "tab_w": TAB_W,
            "tab_bottom_y": TAB_BOTTOM_Y, "pad_len": PAD_LEN, "pad_t": PAD_T, "hook": TOOTH_HOOK_DEG,
            "stop": {"drop": TAB_STOP_DROP, "leg_w": STOP_LEG_W, "beam_t": STOP_BEAM_T, "relief": STOP_RELIEF}}
    return D, travel, chan, teeth, bore, coup, pawl


def hook_wire_clear(D, region, x_exit):
    """In-plane = 3D distance from the wire axis (Y wire_y, Z mid; the region spans Z 0..T_Z) to the added
    region beyond the bore exit. None if the region has no material past x_exit."""
    from shapely.geometry import LineString
    part = region.intersection(sbox(x_exit, -100.0, 400.0, 200.0))
    if part.is_empty:
        return None
    return part.distance(LineString([(x_exit, D["wire_y"]), (400.0, D["wire_y"])]))


def derive_hook_outer(D, ctip):
    """Round 6 pass 2 outer-offset bundle. The end taper always reaches 0 at the last station (s 66); the hold
    end is the LARGEST s (0.5 steps, taper >= HOOK_OUT_END_MIN) at which the added region keeps
    HOOK_OUT_WIRE_CLEAR from the wire axis beyond the bore exit; the build stops if none passes."""
    from .parts.main_frame import hook_outer_region
    ho = {"stations": HOOK_STATIONS, "d_full": HOOK_OUT_D, "d_hold": HOOK_OUT_HOLD, "s_blend": HOOK_OUT_S_BLEND,
          "s_taper": HOOK_OUT_S_TAPER, "step": HOOK_OUT_STEP, "fillet_r": HOOK_OUT_FILLET_R,
          "wire_min": HOOK_OUT_WIRE_CLEAR}
    s_last = HOOK_STATIONS[-1][0]
    s = s_last - HOOK_OUT_END_MIN
    while s >= HOOK_OUT_S_TAPER[1]:
        ho["s_hold_end"], ho["end_len"] = s, s_last - s
        c = hook_wire_clear(D, hook_outer_region(D, ho), ctip["x_exit"])
        if c is None or c >= HOOK_OUT_WIRE_CLEAR:
            ho["wire_clear"] = c
            return ho
        s -= 0.5
    raise RuntimeError("hook outer offset: no hold end keeps the wire clearance")


def derive_coupling(D):
    """Round 6 coupling bundle (lug, head + socket, snap finger + hook, notch, raised bar) and its build-time
    arithmetic: carriage clearance, head-to-bar gap, fillet-in-mouth clearance, seating, hook engagement/slack."""
    hx, zc = D["handle_axis_x"], Z_MID
    fr = D["frame_poly"]
    yb = lambda x: vertical_chord(fr, x)[0]                       # bar bottom (traced)
    x_min = D["carriage_end_x"] + COUPLING_CARRIAGE_CLEAR         # nothing new at bar level left of this
    k = math.tan(math.radians(HOOK_BACKCUT_DEG))
    lug = {"x0": hx - LUG_W / 2, "x1": hx + LUG_W / 2, "y_end": LUG_END_Y, "r": LUG_ROOT_R, "foot": LUG_FOOT_CHAMFER}
    head = {"x0": hx - HEAD_W_X / 2, "x1": hx + HEAD_W_X / 2, "z0": zc - HEAD_W_Z / 2, "z1": zc + HEAD_W_Z / 2,
            "y_top": HEAD_TOP_Y, "y_bot": HEAD_TOP_Y - HEAD_H, "top_chamfer": HEAD_TOP_CHAMFER,
            "cone_deg": HEAD_TRANSITION_DEG, "core_r": HANDLE_CORE_D / 2}
    sock = {"x0": lug["x0"] - SOCKET_CLEAR, "x1": lug["x1"] + SOCKET_CLEAR, "z0": -SOCKET_CLEAR,
            "z1": T_Z + SOCKET_CLEAR, "y_floor": HEAD_TOP_Y - SOCKET_DEPTH, "mouth_x": SOCKET_MOUTH_X,
            "mouth_z": SOCKET_MOUTH_Z}
    fx0 = head["x1"] + FINGER_GAP
    fin = {"x0": fx0, "x1": fx0 + FINGER_T, "y_tip": FINGER_TIP_Y, "r": FINGER_ROOT_R, "tip_ch": FINGER_TIP_CHAMFER}
    hook = {"z0": HOOK_Z[0], "z1": HOOK_Z[1], "depth": HOOK_DEPTH, "ramp_y": HOOK_RAMP_Y, "ridge_y": HOOK_RIDGE_Y,
            "k": k, "under_z": HOOK_UNDER_CHAMFER_Z, "x_tip": fx0 - HOOK_DEPTH}
    notch = {"x0": head["x1"] - NOTCH_DEPTH, "z0": NOTCH_Z[0], "z1": NOTCH_Z[1], "y_floor": NOTCH_FLOOR_Y,
             "apex_y": NOTCH_APEX_Y, "k": k}
    # Raised bar: the flat top meets the hook's inner contour where the traced ring crosses Y BAR_TOP_Y (X > 140).
    hook_in = horizontal_chord(fr.intersection(sbox(140, -20, 200, 30)), BAR_TOP_Y)[0]
    bar = {"x0": x_min, "x1": BAR_RAISE_X1, "y_top": BAR_TOP_Y, "y0": vertical_chord(fr, x_min)[1],
           "ramp_deg": BAR_RAMP_DEG, "blend_r": BAR_BLEND_R, "x_hook": hook_in}
    if hook_in < BAR_RAISE_X1:
        raise RuntimeError(f"hook inner contour reaches Y {BAR_TOP_Y} at X {hook_in:.3f} < {BAR_RAISE_X1}")
    # Carriage clearance: lug fillets, finger root fillets and the bar ramp all start at or right of x_min.
    starts = {"lug fillet": lug["x0"] - lug["r"], "finger fillet": fin["x0"] - fin["r"], "bar ramp": bar["x0"]}
    for what, x in starts.items():
        if x < x_min - 1e-9:
            raise RuntimeError(f"{what} starts at X {x:.3f}, inside the carriage clearance ({x_min:.3f})")
    # Head top below the bar bottom over the whole head width (axial seating is the lug end on the floor).
    hx_s = [head["x0"] + i * (head["x1"] - head["x0"]) / 40 for i in range(41)]
    gaps = [yb(x) - head["y_top"] for x in hx_s]
    if min(gaps) <= 0.0:
        raise RuntimeError(f"head top Y {head['y_top']} touches the bar bottom (gap {min(gaps):.3f})")
    # The r LUG_ROOT_R fillets reach below the head top: clearance to the socket mouth chamfer, per side.
    mouth = {}
    for side, xs, sgn in (("-X", lug["x0"], -1), ("+X", lug["x1"], +1)):
        y_root = yb(xs)
        worst = 1e9
        for i in range(401):
            dp = i * (lug["r"] + 1.0) / 400                           # depth below the head top
            d = dp + (y_root - head["y_top"])                          # depth below the bar bottom
            ext = lug["r"] - math.sqrt(max(0.0, lug["r"] ** 2 - (lug["r"] - d) ** 2)) if d < lug["r"] else 0.0
            clear = SOCKET_CLEAR + max(0.0, sock["mouth_x"] - dp)
            worst = min(worst, clear - ext)
        mouth[side] = worst
    if min(mouth.values()) < 0.05:
        raise RuntimeError(f"lug root fillet clears the socket mouth by only {mouth}")
    # Seating: lug end on the socket floor (push stop, D8); floor thickness; hook engagement and pull slack.
    seat = {"lug_end_to_floor": lug["y_end"] - sock["y_floor"], "floor_t": sock["y_floor"] - head["y_bot"],
            "head_bar_gap": (min(gaps), max(gaps)), "mouth_margin": mouth,
            "hook_engage_x": head["x1"] - hook["x_tip"], "hook_to_notch_back": hook["x_tip"] - notch["x0"],
            "pull_slack_tip": (notch["apex_y"] + k * (head["x1"] - hook["x_tip"]))
                              - (hook["ridge_y"] + k * (fx0 - hook["x_tip"])),
            "finger_L": yb(0.5 * (fin["x0"] + fin["x1"])) - 0.5 * (hook["ridge_y"] + hook["ramp_y"][1] + 0.3)}
    if seat["lug_end_to_floor"] < -1e-9 or seat["hook_engage_x"] <= 0 or seat["hook_to_notch_back"] <= 0 \
            or seat["pull_slack_tip"] <= 0:
        raise RuntimeError(f"coupling arithmetic fails: {seat}")
    return {"hx": hx, "x_min": x_min, "lug": lug, "head": head, "socket": sock, "finger": fin, "hook": hook,
            "notch": notch, "bar": bar, "seat": seat}


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
