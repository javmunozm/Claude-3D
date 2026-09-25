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
WRAP_WALL_Z = 3.0        # ASSUMED: collar/carriage side-wall thickness beside the rack (each side)
SLIDE_CLEAR = 0.30       # PLACEHOLDER (print-tolerance-expert, keep 0.30): rack-channel clearance per side in Z
SLIDE_CLEAR_Y = 0.20     # PLACEHOLDER (print-tolerance-expert, round 3): channel clearance per side in Y (only
                         # derive_channel uses it; less Y play = less pawl-overlap loss when the slider cocks)
CARRIAGE_TOP_WALL = 2.5  # DESIGNED (user decision, round 4; 2.0 in round 3 failed 10.86 vs 9.17 MPa at b 5):
                         # carriage top wall over the channel ceiling; the traced top (1.675-1.740) is raised
CARRIAGE_FLOOR = 2.5     # DESIGNED (user decision, round 4; traced floor 1.97-2.05 failed 9.60 vs 9.17 MPa at b 5):
                         # carriage floor under the channel, OUTSIDE the pawl tongue. The tongue keeps the traced
                         # bottom (t 1.97-2.02): its hard-stop stress is displacement-set (3E*delta*c/x^2), so a
                         # thicker tongue would RAISE it past SF 3. A 45° chamfer steps the floor up to the tongue
                         # at the anchor (no square re-entrant corner at the tongue root).
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

# ── Boss pad (user decision: frame locally as thick as the boss, flush both faces, blended into the bar) ──
# Round 3: boss Ø22 -> pad Z -6..16 (6 mm per face). The old 5 mm taper would start at X 106.311, 0.175 mm INSIDE
# the carriage end at MIN (106.486); the taper is shortened/steepened instead of moving the carriage (user rule).
BOSS_PAD_BLEND = 2.8     # DESIGNED: taper length each side, 22 -> 10 mm: 6 mm per face over 2.8 mm = 65.0°
BOSS_PAD_CARRIAGE_CLEAR = 2.0  # DESIGNED: minimum X gap, carriage end at MIN -> start of the pad taper

# ── Rack extension (user decision: extend the rack so the ~74 mm maximum opening is restored) ─────────────
# The traced free end (end face + bottom chamfer) is moved RACK_EXT towards -X; the gap is filled with the rack
# section (top edge Y 0, bottom = the traced bottom line extended); teeth continue in phase at TOOTH_PITCH.
RACK_EXT = 4.6           # DESIGNED (user decision to extend; 4.5 -> 4.6 in round 3, user accepted): length added to
                         # the traced rack at its free end. With PIN_FIT_CLEAR 0.20 and the pin's c/2 slop, 4.5
                         # leaves a worst-case MAX->pin gap of 0.044 (< PIN_STOP_MIN_GAP 0.10): MAX falls to 36
                         # teeth, tip gap 72.432, and the build refuses. 4.6 gives 0.144 worst / 0.244 centred.
TARGET_MAX_GAP = 74.0    # user requirement: tip gap at wire height at the last pawl-seated pose (build asserts)

# ── End-stop pin (user decision: removable printed pin through a Z hole near the rack tip) ─────────────────
PIN_D = 3.0              # DESIGNED: pin diameter
PIN_FIT_CLEAR = 0.20     # PLACEHOLDER (print-tolerance-expert, round 3): hole Ø = PIN_D + this = 3.20, snug
                         # slip fit for a removable pin (coupon 3.15 / 3.20 / 3.25)
PIN_TIP_WALL = 1.7       # DESIGNED: rack material between the hole and the rack's free end
PIN_PROTRUDE = WRAP_WALL_Z + SLIDE_CLEAR  # DESIGNED: pin ends flush with the slider's outer Z faces
PIN_STOP_MIN_GAP = 0.10  # DESIGNED: the seated MAX pose must leave at least this gap to the pin, AFTER the pin's
                         # slop c/2 (round 3; see RACK_EXT)

# ── Wire and bores ──────────────────────────────────────────────────────────────
WIRE_D = 3.0             # ASSUMED (user decision): Ø3 mm K-wire
BORE_D = 3.4             # ASSUMED (user decision): bore drawn Ø3.4, reamed to 3.2 after printing
REAM_D = 3.2             # ASSUMED (user decision): final bore after reaming
TEARDROP_APEX_DIR = +1   # DESIGNED: teardrop point towards +Z (print with the -Z face on the bed)
BORE_OVERRUN = 3.0       # DESIGNED: bore cutters run this far past each traced face (through-hole)

# ── Rack teeth (bottom face, MEASUREMENTS §3b) ──────────────────────────────────
TOOTH_PITCH = 1.61       # MEASURED (cd1 FFT, 3.443 px/mm; 1.58 at the ruler scale)
TOOTH_DEPTH = 0.80       # ASSUMED: unresolved in the photos (upper bound 2.4 mm); chosen for FDM at 1.61 pitch
TOOTH_LAND = 0.20        # DESIGNED: flat tip land between notches (a sharp tip does not print)
TOOTH_CUT_EPS = 0.05     # DESIGNED: cutter lands sit this far below the envelope (no coincident faces)
TEETH_START_MARGIN = 0.20  # DESIGNED: first notch starts this far right of the tip-chamfer end
TEETH_X_END = 100.7      # DERIVED in MEASUREMENTS §3b (teeth end at the "30" graduation), ±1.5 mm
TOOTH_HOOK_DEG = 10.0    # DESIGNED (user decision, round 3; MECHANISM_STRATEGY §3): the rack notch locking wall
                         # and the pawl tooth locking face are undercut by this angle (apex leans -X), so tension
                         # on the jaws pulls the tooth DEEPER into the notch. No-release condition >= 8.6°.

# ── Compliant pawl (DESIGNED substitution: the reference pawl, pivot screw and lever are not photographed
#    internally, U7). Tension tongue anchored at its -X end, tooth at its +X free end, release tab below. ──
PAWL_ANCHOR_X = 72.5     # DESIGNED: tongue root (carriage bottom wall is intact left of this)
PAWL_FREE_X = 94.0       # DESIGNED: tongue free end (tongue length = 21.5 mm)
PAWL_SLOT_W = 0.80       # DESIGNED: free-end slot, in-plane (prints as a vertical gap), >= 2 nozzle widths
PAWL_WINDOW_TOP_Y = -7.5  # DESIGNED: side walls are cut back to this Y over the tongue so the tooth can pass
PAWL_SEAT_CLEAR = 0.10   # PLACEHOLDER (print-tolerance-expert): tooth-to-notch clearance when seated
PAWL_TOOTH_MARGIN = 0.50  # DESIGNED: tooth right face stays this far inside the tongue free end
TAB_W = 3.0              # DESIGNED: release tab width along X (hangs from the tongue free end)
TAB_BOTTOM_Y = -24.0     # DESIGNED: tab reaches ~24 mm below the rack top (reference lever ~27 mm, cd2)
PAD_LEN = 9.0            # DESIGNED: thumb pad length along +X from the tab
PAD_T = 3.0              # DESIGNED: thumb pad thickness in Y
# Tab hard stop (user decision, round 3): a leg down from the carriage floor past the pad's +X end and a beam
# under the pad. Only the block under the tab column touches (gap TAB_STOP_DROP); elsewhere the beam is
# STOP_RELIEF below the pad, so a pad that rotates with the flexure does not land on its +X end first.
TAB_STOP_DROP = 0.73     # DESIGNED (user decision round 5; was 0.80): max tooth drop. Release needs the worst tooth
                         # overlap 0.630 + 0.10 margin; pawl tongue SF 3.29 at the stop (3.00 at 0.80), the stress
                         # being displacement-set (print-tolerance-expert)
STOP_LEG_W = 2.5         # DESIGNED: leg width along X (right face flush with the squared carriage end, round 5)
STOP_BEAM_T = 2.5        # DESIGNED: beam thickness in Y
STOP_RELIEF = 2.0        # DESIGNED: beam-to-pad gap away from the tab column

# ── Handle boss + thread (user decision: FEMALE in a boss under the bar, MALE on the handle) ─────────────
# Round 3 (user decision): Tr16x4 in a Ø22 boss replaces Tr10x2 in Ø16 (handle root Ø7.5 -> Ø11.5).
THREAD_PITCH = 4.0       # DESIGNED (user decision): Tr16x4, ISO 2904 pitch for d = 16
THREAD_MAJOR_D = 16.0    # DESIGNED (user decision): male major diameter
THREAD_H = 2.25          # DESIGNED: male thread height (ISO h3 = 0.5P + ac, ac 0.25) -> male root Ø11.5
THREAD_FLANK_DEG = 15.0  # DESIGNED: half flank angle (30° trapezoidal)
THREAD_CREST_W = 0.366 * THREAD_PITCH  # DESIGNED: ISO crest flat 0.366P
THREAD_RADIAL_CLEAR = 0.30  # PLACEHOLDER (print-tolerance-expert, round 3): female = male + this, radially
THREAD_AXIAL_CLEAR = 0.15   # PLACEHOLDER (print-tolerance-expert, round 3): female groove wider by this per flank
HANDLE_CORE_GRIP_DEPTH = 2.0  # DESIGNED: the Ø16 handle core runs this far below the traced grip top, into the
                              # grip (where the grip radius is >= 12.4, measured on the ring at build time)
THREAD_ENGAGE = 8.0      # DESIGNED: male thread length above the ferrule shoulder
THREAD_TIP_CHAMFER = 1.0  # DESIGNED: 45° lead-in on the MALE tip only (the female mouth never was 45°; see below)
# Female mouth (round 4: named as built; rounds 2-3 described it as the 45° chamfer above, which it never was).
# The cutter ran from r = major + chamfer + 0.5 at 0.5 outside the face to r = MINOR at depth `chamfer`: slope 2.5
# (68.2° from the axis), face radius 8.55, r 8.425 at 0.05 in (form-auditor measured 8.42). Kept: it clears the
# male crest (8.0) at the face by 0.55, leaves full female ridges from depth 1.0, and leaves a 2.45 mm seating
# annulus (8.55 -> 11.0) for the collar. A true 45° countersink to r 9.3 would cut it to 1.70 mm.
BOSS_MOUTH_FACE_CLEAR = 0.25  # DESIGNED (round 4, = as built): mouth radius at the boss face = female major + this
BOSS_MOUTH_DEPTH = 1.0        # DESIGNED (round 4, = as built): the mouth cone reaches the female minor at this depth
# Handle collar (user decision, round 4, option (a) of MECHANISM_STRATEGY "Round 3 re-check at 25 N"): a Ø22
# collar whose flat top face SEATS ON THE BOSS FACE, so side load puts the thread in tension instead of radial
# bearing. DEVIATION from the traced ferrule (r 7.19-7.49), accepted by the user.
HANDLE_COLLAR_OD = 22.0       # DESIGNED (user decision, round 4): = BOSS_OD, flush with the boss
HANDLE_COLLAR_T = 3.0         # DESIGNED (round 4): cylindrical length of the collar below its seating face
HANDLE_COLLAR_TAPER_R = 7.0   # DESIGNED (round 4): under the collar a 45° cone runs from r 11 down to this radius
                              # (inside the Ø16 core), so the flange has no square root corner
THREAD_CAM_N = 72        # DESIGNED: cam-section resolution (5° steps); see cam_thread()
BOSS_OD = 22.0           # ASSUMED (user decision, round 3): boss diameter (reference post Ø4.85 + nut Ø9.8 are
                         # replaced by this); the pad's flat band is +-BOSS_OD/2 about the handle axis
BOSS_HOLE_FLOOR = 1.2    # DESIGNED: blind-hole floor left under the bar (hole never opens into the bar)

# ── Fusion (booleans only fuse where solids OVERLAP) ────────────────────────────
FUSE_OVERLAP = 1.5       # DESIGNED: interpenetration of mating features (riser into collar, etc.)
BUTT_FLAT = 0.06         # DESIGNED: the traced butt rises only 0.05 mm over its 4.45 mm radius; revolved, that
                         # near-flat cone tessellated to a degenerate pole triangle (STL not watertight, measured
                         # 2026-09-23). Facing the butt 0.06 mm makes it a plane (also a stable print face).

# ── Opening poses: travel in whole tooth pitches so the pawl is seated in every pose ─────────────────────
# MIN = 0 (photographed pose). MAX = the last seated pose before the collar meets the end-stop pin (DERIVED in
# parameters()). MID = half of MAX, rounded. The pre-fix MAX (37 teeth, 59.57 mm) is unreachable with a pin.

# ── Export ──────────────────────────────────────────────────────────────────────
TESS_TOL = 0.03          # STL chordal tolerance, mm
TESS_ANG = 0.2           # STL angular tolerance, rad
