"""SurgicalDrillGuide stage 4: parameter bundles derived from the constants and the rings, plus the build-time
arithmetic checks (MAX tip gap; round 6 coupling: carriage clearance, head-to-bar gap, fillet-in-mouth clearance,
seating, snap engagement and slack) that stop the build before any geometry."""

import math

from shapely.geometry import LineString, Polygon
from shapely.geometry import box as sbox

from .constants import *  # noqa: F401,F403  (this stage turns every constant into a bundle)
from .mechanisms import pawl_tooth_pts, sawtooth_cutter_face
from .rings import derive, derive_channel, horizontal_chord, rack_bottom_y, rack_line_y, ring_points, vertical_chord


def derive_pin(D):
    """End-stop pin position (DERIVED from the rings) and the travel at which the collar meets it."""
    fr = D["frame_poly"]
    r_hole = (PIN_D + PIN_FIT_CLEAR) / 2.0
    x = 3.0 - RACK_EXT
    for _ in range(5):
        y_top = vertical_chord(fr, x)[1]
        # notch apex line over the TRACED bottom line (the pin lies left of the first notch; r7 keeps the
        # placement rule the ratchet sizing reconciled, so MAX = 23 teeth is the sizing's number)
        y_apex = rack_line_y(D, x) + TOOTH_DEPTH
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


def parameters(wire=WIRE_D):
    """`wire` selects a WIRE_VARIANTS entry (bore drawn / reamed / output suffix); only the bores follow it."""
    if wire not in WIRE_VARIANTS:
        raise RuntimeError(f"wire Ø {wire} not in WIRE_VARIANTS {sorted(WIRE_VARIANTS)}")
    bore_d, ream_d, suffix = WIRE_VARIANTS[wire]
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
    # Teeth: the traced-rack phase (first wall bx0 + margin) continued -X, in whole pitches, into the extension, but
    # never under the pin hole (r8 fix R8-12: the first notch wall stays at or +X of the hole's +X edge).
    x0_traced = bx0 + TEETH_START_MARGIN
    x_lim = max(bx0 - RACK_EXT + TEETH_START_MARGIN, pin["x"] + pin["hole_d"] / 2.0)
    m_ext = int(math.floor((x0_traced - x_lim) / TOOTH_PITCH + 1e-9))
    teeth = {"x0": x0_traced - m_ext * TOOTH_PITCH, "x1": TEETH_X_END, "x0_traced": x0_traced, "n_ext": m_ext, "pitch": TOOTH_PITCH, "depth": TOOTH_DEPTH,
             "land": TOOTH_LAND, "eps": TOOTH_CUT_EPS, "hook": TOOTH_HOOK_DEG}
    # C-tip bore cutter: X range of the C-tip chord at the wire height, plus overrun.
    c = D["frame_poly"].intersection(LineString([(140.0, D["wire_y"]), (200.0, D["wire_y"])]))
    cx = [q[0] for g in getattr(c, "geoms", [c]) for q in g.coords]
    # C-tip pad: sleeve from the jaw face at the wire height to just past where the bore's lower edge leaves
    # the traced arm on the outer (45°) edge. Sized from the Ø WIRE_D bore for every variant (user 2026-10-18), so a
    # variant frame differs from the Ø WIRE_D frame only in its bore.
    pad_d = WIRE_VARIANTS[WIRE_D][0]
    lo = horizontal_chord(D["frame_poly"].intersection(sbox(140, 40, 200, 70)), D["wire_y"] - pad_d / 2.0)
    ctip = {"x_entry": min(cx), "x_exit": lo[1] + CTIP_PAD_EXIT_MARGIN,
            "half_h": pad_d / 2.0 + CTIP_WALL_MIN + CTIP_PAD_MARGIN, "blend_r": CTIP_PAD_BLEND_R}
    D["ctip"] = ctip
    # Tip gap at wire height = jaw face (x_entry) - crown face on the wire line; must reach TARGET_MAX_GAP at MAX.
    crown_x = horizontal_chord(Polygon(ring_points("l_arm")), D["wire_y"])[1]
    D["gap_min"] = min(cx) - crown_x
    D["gap_max"] = D["gap_min"] + travel["max"]
    if D["gap_max"] < TARGET_MAX_GAP:
        raise RuntimeError(f"MAX tip gap {D['gap_max']:.3f} < {TARGET_MAX_GAP}: increase RACK_EXT")
    bore = {"d": bore_d, "wire_d": wire, "ream_d": ream_d, "suffix": suffix,
            "apex_dir": TEARDROP_APEX_DIR, "overrun": BORE_OVERRUN,
            "ctip_x0": min(cx) - BORE_OVERRUN, "ctip_x1": max(max(cx), ctip["x_exit"]) + BORE_OVERRUN,
            "ctip_chord": (min(cx), max(cx))}
    coup = derive_coupling(D)
    D["hook_outer"] = derive_hook_outer(D, ctip)
    shoe = derive_shoe(D, chan, teeth)
    return D, travel, chan, teeth, bore, coup, shoe


def derive_shoe(D, chan, teeth):
    """r8 rigid pawl (concept B): shoe, pocket, window, lower block, screw and nut stack, all in the MIN pose, and
    the build-time arithmetic (flat lands, toothed length at MAX, travel, insertion, carriage end, jam stack)."""
    _, a_list = sawtooth_cutter_face(lambda x: rack_bottom_y(D, x), teeth["x0"], teeth["x1"], teeth["pitch"],
                                     teeth["depth"], teeth["land"], teeth["eps"], teeth["hook"])
    n = PAWL_TEETH
    k_seat = list(range(len(a_list) - n, len(a_list)))
    a_seat = [a_list[k] for k in k_seat]
    if k_seat[0] - D["pose_teeth"]["max"] < 0:
        raise RuntimeError("inner shoe tooth would run off the toothed length at MAX opening")
    ys = {round(rack_bottom_y(D, a + dx), 9) for a in a_seat for dx in (-0.5, 0.0, teeth["pitch"])}
    if len(ys) != 1:
        raise RuntimeError(f"rack lands under the shoe are not flat: {sorted(ys)}")
    face = ys.pop()                                   # locked: shoe face on the rack lands, gap 0
    p, dp, ld, cl = teeth["pitch"], teeth["depth"], teeth["land"], PAWL_SEAT_CLEAR
    tooth = [pawl_tooth_pts(a, face, p, dp, ld, cl, face - 0.5, teeth["hook"]) for a in a_seat]
    tooth_h = tooth[0][1][2] - face
    x0, x1 = a_seat[0] - SHOE_END_MARGIN, a_seat[-1] + (p - ld) + SHOE_END_MARGIN
    z0, z1 = -SLIDE_CLEAR + SHOE_CLEAR_Z, T_Z + SLIDE_CLEAR - SHOE_CLEAR_Z
    y_bot = face - (SHOE_ROOF + SHOE_SLOT_Y + SHOE_FLOOR)
    sx, sz = 0.5 * (x0 + x1), Z_MID
    slot = {"x0": sx - SHOE_SLOT_X / 2, "x1": sx + SHOE_SLOT_X / 2, "y1": face - SHOE_ROOF,
            "y0": face - SHOE_ROOF - SHOE_SLOT_Y}
    travel = face + tooth_h - (chan["y0"] - SHOE_RELEASE_GAP)          # lock -> release, shoe moves -Y
    pocket = {"x0": x0 - SHOE_CLEAR_X, "x1": x1 + SHOE_CLEAR_X, "z0": -SLIDE_CLEAR, "z1": T_Z + SLIDE_CLEAR,
              "y0": y_bot - travel - POCKET_INSERT_MARGIN}
    window = {"x0": pocket["x0"], "x1": pocket["x1"], "y0": pocket["y0"], "y1": chan["y0"] - WINDOW_TOP_BELOW_CHANNEL}
    jam_top = y_bot - travel - JAM_GAP
    floor_top = jam_top - NUT_M - WASHER_T
    floor_bot = floor_top - BLOCK_FLOOR_T
    head_top = floor_bot - SCREW_AXIAL_PLAY
    block = {"x0": pocket["x0"] - BLOCK_WALL_X, "x1": pocket["x1"] + BLOCK_WALL_X, "y0": floor_bot}
    screw = {"x": sx, "z": sz, "d": SCREW_D, "hole_d": SCREW_HOLE_D, "head_top": head_top, "tip": head_top + SCREW_L,
             "head_d": SCREW_HEAD_D, "head_h": SCREW_HEAD_H}
    jam = {"top": jam_top, "nut_bot": jam_top - NUT_M, "washer_bot": floor_top, "bore_d": JAM_BORE_D,
           "bore_y0": floor_top, "bore_y1": max(pocket["y0"], jam_top + JAM_BORE_TOP_CLEAR)}
    nut_lock = (slot["y1"] - NUT_M, slot["y1"])                       # drive nut on the slot roof (lock)
    nut_rel = (slot["y0"] - travel, slot["y0"] - travel + NUT_M)       # on the slot floor (release)
    S = {"a_seat": a_seat, "k_seat": k_seat, "a_list": a_list, "face": face, "teeth": [t[0] for t in tooth],
         "tooth_h": tooth_h, "x0": x0, "x1": x1, "z0": z0, "z1": z1, "y_bot": y_bot, "slot": slot, "travel": travel,
         "pocket": pocket, "window": window, "block": block, "screw": screw, "jam": jam, "nut_lock": nut_lock,
         "nut_rel": nut_rel, "nut_s": NUT_S, "nut_e": NUT_E, "washer_d": WASHER_D, "seat_clear": cl,
         "engage_lock": screw["tip"] - nut_lock[0], "engage_rel": screw["tip"] - nut_rel[0]}
    # Arithmetic gates before any geometry.
    h = (face + tooth_h) - y_bot
    if h > window["y1"] - window["y0"]:
        raise RuntimeError(f"shoe height {h:.3f} does not pass the window {window['y1'] - window['y0']:.3f}")
    if block["x1"] >= D["carriage_end_x"]:
        raise RuntimeError(f"lower block +X {block['x1']:.3f} passes the carriage end {D['carriage_end_x']:.4f}")
    if not (0.0 < S["engage_lock"] <= NUT_M and S["engage_rel"] > S["engage_lock"]):
        raise RuntimeError(f"screw engagement lock {S['engage_lock']:.3f} / release {S['engage_rel']:.3f}")
    if screw["tip"] >= slot["y1"] - travel:
        raise RuntimeError(f"screw tip {screw['tip']:.3f} reaches the released slot roof {slot['y1'] - travel:.3f}")
    if NUT_E >= JAM_BORE_D or not (slot["x1"] - slot["x0"] > NUT_S):
        raise RuntimeError("nut does not fit the jam bore / the shoe slot")
    return S


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

