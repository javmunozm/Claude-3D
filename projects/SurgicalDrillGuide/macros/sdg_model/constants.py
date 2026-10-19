"""SurgicalDrillGuide stage 1: constants (millimetres unless named otherwise).

The only file that changes when the physical object changes. Status words: MEASURED / DERIVED / ASSUMED /
DESIGNED / PLACEHOLDER (see the main module's docstring). Nothing here runs at import beyond arithmetic.
"""

from pathlib import Path


PROJECT = Path(__file__).resolve().parents[2]  # sdg_model -> macros -> project
IMPORT_DIR = PROJECT / "vectors" / "import"
OUT_DIR = PROJECT
PREFIX = "SurgicalDrillGuide"

RING_FILES = {
    "frame": "main_frame_body.dxf",
    "l_arm": "l_arm_body.dxf",               # RECTIFIED L (top bar parallel to X); riser rebuilt at 7.50 mm
    "collar": "l_arm_collar.dxf",
    "carriage": "l_arm_carriage.dxf",
    "wire_axis": "l_arm_wire_axis.dxf",       # LINE, Y 51.80, parallel to X
    "grip_half": "handle_grip_revolve_half.dxf",
    "ferrule_half": "handle_ferrule_revolve_half.dxf",
}

# ── Z (breadth). No photo measures Z (MEASUREMENTS §8). ─────────────────────────
T_Z = 10.0               # ASSUMED (user decision 2026-09-23): frame, rack and hook thickness
Z_MID = T_Z / 2.0        # DERIVED: mid-plane; wire bores and handle axis lie on it
WRAP_WALL_Z = 4.0        # PROPOSED r8 sizing part 3 (the +Z window frees one top-wall edge; 3.995 needed at the
                         # bound, SF 3.01): collar/carriage side-wall thickness beside the rack (each side);
                         # slab -4.3 .. 14.3
SLIDE_CLEAR = 0.30       # PLACEHOLDER (print-tolerance-expert, keep 0.30): rack-channel clearance per side in Z
SLIDE_CLEAR_Y = 0.20     # PLACEHOLDER (print-tolerance-expert, round 3): channel clearance per side in Y (only
                         # derive_channel uses it; less Y play = less pawl-overlap loss when the slider cocks)
CARRIAGE_TOP_WALL = 4.4  # PROPOSED r8 sizing part 3 (user-approved 2026-10-18; needs 4.333 at the bound): top wall
                         # over the channel ceiling; the traced top (1.675-1.740) is raised
CARRIAGE_FLOOR = 2.5     # DESIGNED (user decision, round 4): carriage floor under the channel; r8: removed over the
                         # shoe pocket
# The carriage +X end is squared over its full height at the traced end face at channel mid-height (DERIVED,
# X 106.475); this removes the 0.048 mm sliver the round-3 top box left at X 106.438-106.486 (form-auditor).
# User decision (fix round 2026-09-23): the L-arm (riser, top bar, crown) takes the collar/carriage Z, so the
# slider is one 16.6 mm slab: Z = -SLIDE_CLEAR - WRAP_WALL_Z .. T_Z + SLIDE_CLEAR + WRAP_WALL_Z (-3.3 .. 13.3),
# still centred on Z_MID. Overrides the 10 mm decision for the L-arm only.
L_ARM_FULL_WRAP_Z = True  # ASSUMED (user decision)

# ── C-tip pad (user decision: thicken, never cut; >= 1.5 mm wall PERPENDICULAR to the faces round the bore) ──
CTIP_WALL_MIN = 1.5      # user requirement
CTIP_PAD_MARGIN = 0.3    # DESIGNED: extra wall above the requirement (sleeve half-height = r_bore + 1.5 + 0.3)
CTIP_PAD_EXIT_MARGIN = 0.3  # DESIGNED: sleeve exit face this far past where the bore's lower edge leaves the ring
CTIP_PAD_BLEND_R = 1.5   # DESIGNED: morphological-closing radius that fillets the pad into the traced hook

# ── Round 6 (user decision 2026-10-17): frame uniform Z 0..T_Z; no boss, pad or thread ───────────────────
COUPLING_CARRIAGE_CLEAR = 2.0  # DESIGNED: min X gap, squared carriage end at MIN -> any new frame material at bar
                               # level (lug fillets, finger, bar raise); the build raises an error below it

# ── Raised bar (print-tolerance-expert, bar_and_snap.md 1c: interlaminar torsion SF 3.01 at X 153) ─────────
BAR_TOP_Y = 7.5          # DESIGNED: flat bar top over BAR_RAISE_X1 back to the carriage clearance line
BAR_RAISE_X1 = 153.0     # DESIGNED: full depth must exist up to here (hook start, MEASURED form audit)
BAR_RAMP_DEG = 45.0      # DESIGNED: -X end ramps up from the traced bar top at this angle to X
BAR_BLEND_R = 3.0        # DESIGNED: closing radius where the flat top meets the hook's inner contour (adds only)

# ── Hook outer offset, round 6 pass 2 (user decision 2026-10-17; neck_sizing.md §4 proposal 2: X mid-grip, 100 %
#    to the hook). Outer contour only, in-plane, Z 0..T_Z; the inner contour, throat and jaw face do not move. ──
# Hook centreline stations (s, centroid X, Y, tangent ° from +X): MEASURED, neck_audit.md (r5 mesh; the outer
# contour of the traced ring is unchanged since). The outer edge is found on the live ring along each normal.
HOOK_STATIONS = ((8, 157.69, -3.58, 14), (10, 159.60, -3.00, 20), (12, 161.44, -2.20, 27),
                 (14, 163.17, -1.20, 33), (16, 164.78, -0.02, 39), (18, 166.29, 1.29, 44),
                 (20, 167.67, 2.73, 49), (22, 168.91, 4.30, 54), (24, 169.99, 5.98, 60),
                 (26.5, 171.15, 8.20, 68), (28, 171.62, 9.62, 74), (30, 172.00, 11.58, 81),
                 (32, 172.22, 13.57, 85), (34, 172.32, 15.57, 89), (36, 172.30, 17.57, 93),
                 (38, 172.15, 19.56, 96), (40, 171.88, 21.54, 99), (42, 171.55, 23.51, 100),
                 (44, 171.16, 25.48, 102), (46, 170.69, 27.42, 105), (48, 170.13, 29.34, 108),
                 (50, 169.47, 31.22, 111), (52, 168.71, 33.07, 114), (54, 167.88, 34.89, 116),
                 (56, 166.98, 36.68, 118), (58, 166.02, 38.43, 120), (60, 164.97, 40.14, 123),
                 (62, 163.85, 41.79, 126), (64, 162.64, 43.39, 129), (66, 161.38, 44.93, 140))
HOOK_OUT_D = 5.6         # PROPOSED (PTE): offset over HOOK_OUT_S_FULL
HOOK_OUT_HOLD = 3.6      # PROPOSED (PTE): offset held from HOOK_OUT_S_TAPER[1] to the hold end
HOOK_OUT_S_BLEND = (12.0, 18.0)   # DESIGNED (brief): smoothstep 0 -> HOOK_OUT_D into the bar bottom
HOOK_OUT_S_TAPER = (32.0, 36.0)   # PROPOSED (PTE): smoothstep HOOK_OUT_D -> HOOK_OUT_HOLD
HOOK_OUT_END_MIN = 3.0   # DESIGNED: shortest end taper; smoothstep HOOK_OUT_HOLD -> 0 from the hold end to the
                         # last station (s 66, the C-tip pad end), G1, no step
HOOK_OUT_WIRE_CLEAR = 2.0  # user/brief limit: new material >= this from the wire axis beyond the bore exit
HOOK_OUT_STEP = 0.2      # DESIGNED: sampling step along the outer contour (variable-radius disc sweep)
HOOK_OUT_FILLET_R = 4.0  # DESIGNED (pass 3; brief r >= 3): concave fillet where the band meets the bar bottom

# ── Rack extension (user decision: extend the rack so the ~74 mm maximum opening is restored) ─────────────
# The traced free end (end face + bottom chamfer) is moved RACK_EXT towards -X; the gap is filled with the rack
# section (top edge Y 0, bottom = the traced bottom line extended); teeth continue in phase at TOOTH_PITCH.
RACK_EXT = 11.1          # USER DECISION r8 fix (2026-10-18, R8-12): length added to the traced rack at its free
                         # end (was 9.8; +1.3 with the pin kept in place, so the pin's -X wall is 3.0). With pitch
                         # 3.5: MAX 18 teeth = 63.0, tip gap 77.472. Notches never run under the pin hole.
TARGET_MAX_GAP = 74.0    # user requirement: tip gap at wire height at the last pawl-seated pose (build asserts)

# ── End-stop pin (user decision: removable printed pin through a Z hole near the rack tip) ─────────────────
PIN_D = 3.0              # DESIGNED: pin diameter
PIN_FIT_CLEAR = 0.20     # PLACEHOLDER (print-tolerance-expert, round 3): hole Ø = PIN_D + this = 3.20, snug
                         # slip fit for a removable pin (coupon 3.15 / 3.20 / 3.25)
PIN_TIP_WALL = 3.0       # DESIGNED r8 fix (R8-12; was 1.7): rack material between the hole and the rack's free
                         # end. Raised by the same 1.3 as RACK_EXT, so the derived pin stays at X -6.482, Y -3.796
PIN_PROTRUDE = WRAP_WALL_Z + SLIDE_CLEAR  # DESIGNED: pin ends flush with the slider's outer Z faces
PIN_STOP_MIN_GAP = 0.10  # DESIGNED: the seated MAX pose must leave at least this gap to the pin, AFTER the pin's
                         # slop c/2 (round 3; see RACK_EXT)

# ── Wire and bores ──────────────────────────────────────────────────────────────
WIRE_D = 3.0             # ASSUMED (user decision): Ø3 mm K-wire
BORE_D = 3.4             # ASSUMED (user decision): bore drawn Ø3.4, reamed to 3.2 after printing
REAM_D = 3.2             # ASSUMED (user decision): final bore after reaming
# Wire variants (user request 2026-10-18): wire Ø -> (bore drawn, reamed, output suffix). Same rule for each: drawn
# = wire + 0.4, reamed = wire + 0.2. Only the bored parts (main_frame C-tip, l_arm_slider) differ; the default 3.0
# keeps the unsuffixed file names, the others write <name><suffix>.
WIRE_VARIANTS = {3.0: (BORE_D, REAM_D, ""), 1.5: (1.9, 1.7, "_wire1p5")}
BORE_PARTS = ("main_frame", "l_arm_slider")
TEARDROP_APEX_DIR = +1   # DESIGNED: teardrop point towards +Z (print with the -Z face on the bed)
BORE_OVERRUN = 3.0       # DESIGNED: bore cutters run this far past each traced face (through-hole)

# ── Rack teeth (bottom face, MEASUREMENTS §3b) ──────────────────────────────────
# r8 (user decision 2026-10-18, r8 sizing part 2): sawtooth, 0° locking wall, 60° ramp from vertical, no hook.
TOOTH_PITCH = 3.5        # PROPOSED r8: opening step 3.5 mm (MAX 18 teeth, tip gap 77.472)
TOOTH_DEPTH = 1.5        # PROPOSED r8 (rack net section 5a SF 3.06; 1.6 fails at 2.99)
TOOTH_LAND = 0.902       # PROPOSED r8: = pitch - depth*tan 60°; rack land at the mouth (hook 0)
TOOTH_CUT_EPS = 0.05     # DESIGNED: cutter lands sit this far below the envelope (no coincident faces)
TEETH_START_MARGIN = 2.45  # PROPOSED r7b (unchanged r8; first notch -2.016): first notch offset from the
                           # tip-chamfer end of the traced rack
TEETH_X_END = 100.7      # DERIVED in MEASUREMENTS §3b (teeth end at the "30" graduation), ±1.5 mm
TOOTH_HOOK_DEG = 0.0     # PROPOSED r8: vertical locking wall (a hook would block the shoe's straight retraction)
RACK_FLAT_X1 = TEETH_X_END  # PROPOSED r7: rack underside flat at its traced Y at this X, for every X <= it (adds a
                            # wedge <= 0.24 under the traced line; the overlap is then equal at every pose)

# ── Rigid pawl = screw-driven shoe (user decision r8, 2026-10-18, concept B; r8 sizing part 2). A separate printed
#    shoe with PAWL_TEETH teeth sits in a pocket of the carriage's lower block. A DIN 464 M6 knurled screw from below,
#    axially captured in the block floor (head below, washer + DIN 557 jam nut above), drives a DIN 557 square nut held
#    in the shoe's slot: turning it raises the shoe onto the rack lands (lock) or lowers it out of the teeth (release).
#    The shoe and the jam nut go in through a window in the carriage's +Z side wall. All values in the MIN pose. ──
PAWL_TEETH = 6           # USER DECISION r8: shoe teeth, in the 6 right-most rack notches at MIN
PAWL_SEAT_CLEAR = 0.10   # PLACEHOLDER (print-tolerance-expert): tooth flank clearance (wall and ramp, normal offset)
SHOE_END_MARGIN = 1.5    # DESIGNED: shoe end past the first tooth wall (-X) / the last ramp end (+X)
SHOE_CLEAR_X = 0.20      # PLACEHOLDER: shoe -> pocket clearance per side in X
SHOE_CLEAR_Z = 0.20      # PLACEHOLDER: shoe -> pocket clearance per side in Z (pocket Z = the rack channel Z)
SHOE_ROOF = 4.0          # PROPOSED: shoe face (on the rack lands) -> nut slot top
SHOE_SLOT_X = 10.3       # PLACEHOLDER (fit DIN 557 s 10): nut slot width in X; its ±X walls stop the nut turning
SHOE_SLOT_Y = 5.3        # PLACEHOLDER (DIN 557 m 5 + 0.3): nut slot height; the slot runs through Z
SHOE_FLOOR = 3.0         # PROPOSED: slot bottom -> shoe bottom; Ø SCREW_HOLE_D teardrop hole (apex +Z)
SHOE_HOLE_TOP_WALL = 1.8  # DESIGNED r8 fix 2 (1C-i, user 2026-10-18): the shoe's teardrop is cut flat this far under
                          # the shoe's +Z face (Z 8.3 = top of the Ø6.6 circle); the flat is a ~2.73 wide bridge
SHOE_RELEASE_GAP = 0.30  # DESIGNED: released tooth tips this far under the channel floor (sets the travel)
SCREW_D = 6.0            # ASSUMED: M6 nominal (clearance volume only; the screw is bought, not printed)
SCREW_L = 20.0           # ASSUMED: DIN 464 M6 x 20 shank length (head top -> tip)
SCREW_HEAD_D = 24.0      # ASSUMED: DIN 464 M6 knurled head Ø (not in the sizing; measure the purchased screw)
SCREW_HEAD_H = 7.5       # ASSUMED (r8 sizing): head height
SCREW_AXIAL_PLAY = 0.20  # PLACEHOLDER: head top -> block floor underside
SCREW_HOLE_D = 6.6       # PROPOSED: clearance hole in the block floor and the shoe floor (teardrop, apex +Z)
NUT_S = 10.0             # ASSUMED: DIN 557 M6 width across flats
NUT_M = 5.0              # ASSUMED: DIN 557 M6 height
NUT_E = 14.14            # ASSUMED: DIN 557 M6 corner diameter (the jam nut turns with the screw: swept Ø)
WASHER_D = 12.0          # ASSUMED: DIN 125-A M6 outer Ø (6.4 / 12 / 1.6)
WASHER_T = 1.6           # ASSUMED: DIN 125-A M6 thickness
JAM_GAP = 0.20           # DESIGNED (r8 sizing): released shoe bottom -> jam nut top (jam top at lock -23.692)
JAM_BORE_D = 14.6        # DESIGNED: bore for the washer + turning jam nut, open to the +Z face
JAM_BORE_TOP_CLEAR = 0.30  # DESIGNED r8 build (deviation): the bore runs this far above the jam nut top, because
                           # the nut top is 1.3 above the pocket bottom, where the pocket is only 10.6 wide in Z
BLOCK_FLOOR_T = 5.5      # PROPOSED (SF 3.51): block floor under the jam stack; the screw head bears under it
BLOCK_WALL_X = 3.0       # DESIGNED: lower block ±X walls beside the pocket
POCKET_INSERT_MARGIN = 1.5  # DESIGNED: pocket bottom (insertion level) this far under the released shoe bottom
WINDOW_TOP_BELOW_CHANNEL = 1.0  # DESIGNED (user decision r8): +Z assembly window top, under the channel floor

# ── Handle coupling, round 6 (concept D, coupling_sizing.md + bar_and_snap.md; all PROPOSED by
#    print-tolerance-expert, user-approved round). Frame lug (tenon) in a blind square socket in the handle head,
#    held by an external snap finger on the frame. Push stop = lug end on the socket floor (modelled seated pose);
#    pull stop = the hook ridge on the notch roof after the axial slack. ──
LUG_W = 14.0             # DESIGNED: lug width in X, centred on the handle axis; Z = 0..T_Z
LUG_END_Y = -29.85       # DESIGNED: lug end (= socket floor in the seated pose)
LUG_ROOT_R = 3.0         # DESIGNED: in-plane root fillets lug -> bar bottom (Kt 1.3 in D2)
LUG_FOOT_CHAMFER = 0.4   # DESIGNED: 45° elephant's-foot chamfer on the lug's Z 0 edges (straight edges only)
HEAD_W_X = 22.4          # DESIGNED: square head, X
HEAD_W_Z = 22.0          # DESIGNED: square head, Z (centred on Z_MID: Z -6..16)
HEAD_TOP_Y = -9.85       # DESIGNED: head top = socket mouth
HEAD_H = 23.0            # DESIGNED: head height in Y (bottom Y -32.85)
SOCKET_CLEAR = 0.20      # PLACEHOLDER (print-tolerance-expert): socket = lug + this per side (14.4 x 10.4)
SOCKET_DEPTH = 20.0      # DESIGNED: blind socket depth from the head top (floor 3.0)
SOCKET_MOUTH_X = 2.0     # DESIGNED (round 6 build): 45° mouth chamfer on the +-X socket edges. The head top is only
                         # 0.53-0.82 below the bar bottom, so the r 3 lug root fillets enter the socket mouth; 2.0
                         # leaves >= 0.17 to the fillet (1.5 would leave 0.05). Not in the sizing: see report.
SOCKET_MOUTH_Z = 0.5     # DESIGNED: 45° lead-in on the +-Z socket edges (coupling_sizing.md)
HEAD_TRANSITION_DEG = 40.0  # DESIGNED: head -> Ø16 core cone, angle from the axis (<= 45°: support-free standing).
                            # Build 2 at 44°: STL triangles along the cone/flat-side intersection curves tilted to
                            # 45.1-48.4° (55 mm2 over the support threshold); 40° leaves margin for the tessellation
HANDLE_CORE_D = 16.0     # DESIGNED (round 3): Ø16 core from inside the grip up into the head
HANDLE_CORE_GRIP_DEPTH = 2.0  # DESIGNED: the Ø16 handle core runs this far below the traced grip top, into the
                              # grip (where the grip radius is >= 12.4, measured on the ring at build time)
# External snap finger (bar_and_snap.md Part 2): on the frame, beside the head's +X face; hook points -X.
FINGER_GAP = 0.20        # PLACEHOLDER: finger -X face to the head +X face
FINGER_T = 1.6           # DESIGNED: finger thickness in X (Z = 0..T_Z)
FINGER_ROOT_R = 1.0      # DESIGNED: in-plane root fillets at the bar bottom
FINGER_TIP_Y = -29.4     # DESIGNED: finger tip (thumb tab)
FINGER_TIP_CHAMFER = 0.5  # DESIGNED: in-plane chamfer on both tip corners
HOOK_Z = (2.0, 8.0)      # DESIGNED: hook width in Z
HOOK_DEPTH = 0.9         # DESIGNED: hook depth in -X from the finger face
HOOK_RAMP_Y = (-26.38, -24.82)  # DESIGNED: 30° insertion ramp, finger face -> hook tip
HOOK_RIDGE_Y = -21.52    # DESIGNED: retention-face ridge at Z_MID (45° gable in Z, flanks to Y -24.52 at the hook Z ends)
HOOK_BACKCUT_DEG = 10.0  # DESIGNED: retention face rises toward the hook tip (a pull pushes the hook in)
HOOK_UNDER_CHAMFER_Z = 0.95  # DESIGNED: chamfer under the hook's Z 2 face, HOOK_DEPTH in X over this in Z (46.5° from
                             # the bed; 0.9 x 45° would sit exactly on the support threshold)
HEAD_TOP_CHAMFER = 1.2   # DESIGNED: 45° chamfer on the head top +X outer edge (hook lead-in)
NOTCH_DEPTH = 1.2        # DESIGNED: blind notch in the head +X face (hook 0.9 + 0.3)
NOTCH_Z = (1.7, 8.3)     # DESIGNED: hook + 0.3 per side
NOTCH_FLOOR_Y = -26.68   # DESIGNED: flat notch floor (faces +Y = up when the handle stands)
NOTCH_APEX_Y = -21.17    # DESIGNED: 45° gable roof apex at the outer face, rising HOOK_BACKCUT_DEG toward -X

# ── Fusion (booleans only fuse where solids OVERLAP) ────────────────────────────
FUSE_OVERLAP = 1.5       # DESIGNED: interpenetration of mating features (riser into collar, etc.)
BUTT_FLAT = 1.5          # USER DECISION (round 6 pass 3, deviation from the trace): face the butt 1.5 mm so the
                         # traced 1.45 mm butt dome is removed and the handle stands on a plane (0.06 left 159.10 mm2
                         # needing support standing). 0.06 was the earlier fix for a degenerate pole triangle.

# ── Opening poses: travel in whole tooth pitches so the pawl is seated in every pose ─────────────────────
# MIN = 0 (photographed pose). MAX = the last seated pose before the collar meets the end-stop pin (DERIVED in
# parameters()). MID = half of MAX, rounded. The pre-fix MAX (37 teeth, 59.57 mm) is unreachable with a pin.

# ── Export ──────────────────────────────────────────────────────────────────────
TESS_TOL = 0.03          # STL chordal tolerance, mm
TESS_ANG = 0.2           # STL angular tolerance, rad
