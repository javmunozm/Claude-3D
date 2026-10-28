"""VitaGripPS5 v2 spike: constants (mm, +Z up, frame of the r16 bake).

Values are r16's (projects/VitaGripPS5/macros/build_case_ext.py overrides build_case.py).
"""
from pathlib import Path

V2_DIR = Path(__file__).resolve().parents[2]          # projects/VitaGripPS5/v2
PROJECT_DIR = Path(__file__).resolve().parents[3]     # projects/VitaGripPS5
R16_STL = PROJECT_DIR / "stl" / "VitaGripPS5_case_r16.stl"

# pocket (r16 build log: 183.30 x 84.55, Y -9.000..75.550, caps centred at x +-70.0)
CAP_XC = 70.0
CAP_A, CAP_B = 21.65, 42.275
YC = 33.275
POCKET_Y_TOP = 75.55
POCKET_Y_BOTTOM = -9.0
FLOOR_Z = -8.8
FACE_Z = 10.0

# lip and finger (r16)
LIP_U = 10.2
LIP_TOP_Z = 11.4
ROOT_Z = -13.8
WALL = 3.0
FINGER_W = 15.0
FINGER_SLOT = 1.0
FINGER_INNER_SLOT = 1.5
FINGER_GAP = 2.5
FINGER_T_ROOT, FINGER_T_TIP = 1.8, 0.9
FINGER_ROOT_R = 1.0
PIT_CORNER_R = 2.5
LIP_OVERHANG = 1.5
LIP_LEAD_DEG = 30.0
LIP_RET_DEG = 127.0
LIP_FLAT = 0.5
LIP_LAND = 0.8
# pass latch (user, 2026-10-06; audit/latch/sizing.md, x2.00 / OH 1.5): double-thickness fingers, root fillet scaled
# with the root (Kt 1.3). The finger's inner face (u 0) and the lip stay; the extra thickness and the pit's outer
# face (u FINGER_T_ROOT + FINGER_GAP) go outward. The main applies LATCH_X2_VALS when on (False = pass plate).
LATCH_X2 = True
LATCH_X2_VALS = dict(FINGER_T_ROOT=3.6, FINGER_T_TIP=1.8, FINGER_ROOT_R=2.0)
# right upper finger station and outline normal (r16 build log)
FINGER_P = (90.61, 46.20)
FINGER_N = (0.986, 0.164)

# flat top and handle tip (r16 locks)
TOP_Z = 11.4
TOP_ROLL = 3.0
TIP_Y = -68.0025
TIP_ROLL = 3.0

# simplified floor plate (r16 x-sections: z -13.3..-8.8, y -11.2..78.55 for |x| < 66)
PLATE_Y0, PLATE_Y1 = -11.2, 78.55
PLATE_Z0 = -13.3
FRONT_R = 0.0              # plate front face / handle edges (p1_post.py: 3 and 2 fail, 1 valid); failed at r 1 in
                           # p1c / p1d; on the fitted loft (pass fit) the attempt crashed the process (segfault), so off
# pass front (S2): the plate front's bottom round, cut into the lone blend loft BEFORE the fuse (0 = pass fit).
# Radius ramps (smoothstep) from 0 at FRONT_ROUND_X0 (the bar-strip lock ends at |x| 62) to FRONT_ROUND at X0 + RAMP.
FRONT_ROUND = 1.0
FRONT_ROUND_X0 = 62.0
FRONT_ROUND_RAMP = 2.0
FRONT_ROUND_START = 0.25   # first cutter section at X0 + this (r 0.047 there; at X0 itself a 0.004 end face folded)
FRONT_ROUND_CROSS = 0.005  # the arc is drawn at r (1 + CROSS) so it crosses both faces instead of touching them
# pass corner: concave rolling-ball round between the plate front (and the front round) and the grip, a lone web
# solid fused into the half (0 = pass front). Junction on pass front: x 66.94 (z -8.8) .. 68.5 (z -13.07) on y -11.2,
# then along the front round to (69.4, -10.6, -13.7), where its crease falls to 22-24 deg (the blend's own crease).
CORNER_ROUND = 1.0
CORNER_ROUND_Z_START = -8.5      # first ball centre (z), above the floor plane; the web is trimmed at FLOOR_Z
CORNER_ROUND_GUESS = (66.3, -12.2)
CORNER_ROUND_ALPHA_END = 25.0    # last station where the crease between the contact normals falls under this
CORNER_ROUND_SINK = 1.0         # over the last mm of ball path the arc sinks into the material (no end face)
CORNER_BOX = (66.0, 70.5, -12.5, -10.2, -14.2, -8.9)   # gate box (right side), from step 1
# pass plate: full half-round on the plate's front (y PLATE_Y0) and rear (PLATE_Y1) edges, r = half the plate (0 = pass
# edge). Cut from the lone plate (boxes + blend) before the fuse with the grip end; it replaces FRONT_ROUND's cutter.
# Full round to NOSE["x1"]; then the top arc (front) / both arcs (rear) shrink to r_end and lift off into air by
# x_shrink + lift, before the grip (inner clip 66.5) and the corner web (contacts from x 65.5); the front bottom arc
# goes to FRONT_ROUND (r 1, crossing 0.005) by x_bf and runs on to the old cutter's end.
PLATE_NOSE_R = 2.25        # half the plate (0 = pass edge, byte-identical)
# Variable-radius fillets on the lone plate (parts/plate.nose_fillet); per edge (x1, x_e, r_e): radius PLATE_NOSE_R - gap
# to x1, smoothstep to r_e at x_e, r_e beyond (into the grip). gap: the two fillets leave a 2 gap flat (a fillet of
# exactly half the face is not buildable).
PLATE_NOSE = dict(gap=0.01,
                  front=dict(top=(58.0, 65.5, 0.15), bottom=(58.0, 64.0, FRONT_ROUND)),
                  # rear bottom: a radius that changes along the blend's underside edges (x > 60) fails to build
                  # (t_fillet.py: (58, 64, 0.5/1.0) fail; constant along x > 60 builds), so it fades by x 60
                  # rear top: r 0.15 at the grip (x 66.3) left 14 open STL edges at the cusp (build 1): 0.5
                  rear=dict(top=(58.0, 66.0, 0.5), bottom=(55.0, 60.0, 0.3)),
                  sides=("front", "rear"),
                  # run 3: these sides' TOP edges are rounded after the fuse, one contour on along the grip's
                  # tangent edges (parts/plate.nose_post_fillet): (r, x1, x_e, r_e, l_end, r_tip). Empty = build 2's
                  # laws (run 3 fallback): rear (2.24, 58, 66, 1.0, 3.0, 0.3) built valid but its STL has folded facets
                  # (179.7 deg, 479 edges at (72, 78, -12)); front not buildable. See audit/plate/fix_report.md
                  post=dict())

# plate built into the grip end (pass 1, S2): boxes for the flat plate, a lofted blend for the junction
BLEND_XS = 60.0            # main slab x 0..60; the blend loft is trimmed at x >= 60 (both planes)
BLEND_XH = 61.0            # blend bottom flat at PLATE_Z0 to here, then a cubic to the grip underside
BLEND_XA = 69.0            # the cubic meets the grip underside here (past the 66.5 clip corner) ...
BLEND_ALPHA = 15.0         # ... this many degrees shallower than it, then runs on inside the grip
                           # (10 deg at x 68.5 left a zero-volume sliver at y 56-57: build 1)
BLEND_EXT = 1.5
BLEND_ZT = -10.0           # blend top, under the floor; the upper slab covers it
PLATE2_X, PLATE2_Z0 = 67.5, -12.0   # upper slab z -12..FLOOR_Z out to x 67.5 (into the grip)
BLEND_Y1 = PLATE_Y1        # pass 1b: blend and slabs run to the rear face (p1's rear slab and its y 61 step: N1)

# top round built into the sections (pass 1, S1)
ROUND_R = 3.0
ROUND_EPS = 0.03           # sections are flat at TOP_Z + eps; the solid is cut at TOP_Z (crease acos(1-eps/r));
                           # 0.01 left two dimple islands in the flat (loft ringing about 0.04 near y -37..-40)
ROUND_BAND = 100.0         # opening on the whole section (it only changes the top corners: p1_probe2)
SEG_COUNTS = (60, 60, 60)  # points: start -> top band, top band (within SEG_DEPTH of the top), -> start
SEG_DEPTH = 2.0

# grip-end loft
INNER_X = 66.5             # inner clip of the grip-end sections (r16 wall inner face 66.7..66.8)
ROWFILL_Y = -11.5          # stations at y >= this get the pocket / pits filled row by row
ROWFILL_Z0 = -14.0         # row fill only above this z (keeps the handle's curved inner underside)
CUT_Z = 8.0                # sections with r16's flat top: replaced above this z ...
EXT_TOP_MAX = 16.0         # ... by an extension up to this z (cut back to TOP_Z afterwards)
HANDLE_TOP_Y0 = -42.6      # r16: the handle's sloped top leaves the flat top at y -42.6 ...
HANDLE_TOP_SLOPE = 0.36    # ... falling 0.36 mm per mm toward the tip (z-sections 11.3 / 10.5 / 9 / 5)
CAP_REF_Y = -46.0          # uncut r16 handle section whose domed cap is swept up the slope over flat-topped stations
CAP_H = 10.0               # cap depth taken from the reference section
FORCE_EXT_Y = 61.0         # body stations up to here get the cap sweep; behind it, tall_rear (REAR_*)
N_PTS = 72                # points per smoothed section
SMOOTH_RMS = 0.08          # splprep smoothing, per-point rms (mm)

# rear corner (pass 1b, N1): part of the grip-end loft. Stations y > FORCE_EXT_Y are r16's section below
# REAR_CUT_Z, extended straight up (lean at most REAR_LEAN mm per mm); the corner's top is one cutter (CLIP_*)
REAR_STATIONS = [77.5, 75.0, 73.0, 71.0, 68.5, 66.0, 63.5]
# (scratch loft trials, box cuts as the test: with 76.5 or 74 / 72 added the loft is invalid under any cut, or the
# trim returns nothing; this set and the 79.05 extrapolation cut validly)
REAR_EXTRAP_Y = 79.05      # extrapolated from the last two, past the rear face; the loft is trimmed at PLATE_Y1
REAR_CUT_Z = -10.5
REAR_LEAN = 0.15           # extension lean limit, mm x per mm z
REAR_OUTER_LEAN = -0.1     # pass 1c (N3): fixed inward lean of the outer side (the free lean left a fin at (96, 64, 0))
# cutter fitted to r16's corner top heights (x 84..outline-2.5, y 56..70, outside the pocket; 938 points):
# rms 1.10 mm (p1's y-plane wedge at slope 4.1: 3.35). Wall line through CLIP_W at CLIP_PHI deg in plan,
# falling CLIP_K mm per mm, CLIP_RF concave foot to the floor; the top round is ROUND_R, tangent to TOP_Z + eps
CLIP_W = (92.0, 61.0)
CLIP_PHI = 25.0
CLIP_K = 20.0
CLIP_RF = 6.5
RIM_RADII = [2.0, 1.5, 1.0]   # rim crest (corner flat at FLOOR_Z to the outer flank); r16 has about 0.5-0.9

# U-turn (pass 1b, N2): the stations in this y range get the 3D ball opening of the top height field
UTURN = dict(x=(64.0, 118.0), y=(-49.0, -34.5), dx=0.1, dy=0.25)
# inner flank band (pass 1b, S5): Gaussian smoothing along the outline, sigma mm, weighted by ramps
# (z: 0 / 1 / 1 / 0 at the four values; x: 1 below x[0], 0 above x[1]; y: as z)
S5 = dict(sigma=2.0, z=(3.5, 5.0, 8.5, 9.8), x=(75.0, 78.0), y=(-41.0, -38.0, -16.0, -13.0))
# (build 1: turn 14.88 -> 12.9 deg, now at z 3.77 on the lower ramp. Build 2 with sigma 2.5, z 0 / 2.5 / 8.5 / 9.8:
# tip fillet, plate-front fillet and the pit cut failed, so it was reverted)

# stations (r16 y), rear to tip. Pass 1c: two lofts sharing the station SHARED_Y. The body/corner loft runs
# REAR_STATIONS + MAIN_STATIONS >= SHARED_Y; the handle loft from SHARED_Y to the tip.
MAIN_STATIONS = [61.0, 57.0, 53.0, 49.0, 45.0, 41.0, 37.0, 33.0, 29.0, 25.0, 21.0, 17.0, 13.0, 9.0, 5.0,
                 1.0, -3.0, -6.0, -8.5, -10.0, -11.0, -12.0, -13.0, -13.5, -15.0, -17.0, -19.0, -21.5, -24.0,
                 -27.0, -30.0, -33.0, -36.0, -38.5, -40.5, -41.0, -42.0, -42.5, -43.0, -43.5, -45.0, -47.0,
                 -49.5, -52.0, -55.0, -58.0, -61.0, -64.0]
SHARED_Y = -13.5           # the station both lofts pass through (each loft also takes the other's first neighbour
                           # and is trimmed at this plane, so both have the same tangent there)
# handle shortened (user, 2026-10-04): the r16 span below SHARED_Y is removed and the rest moved +HANDLE_SHIFT in y.
# r16's root section is 3.6 (z 0) to 6.4 mm (z 10.5) wider on the inner side than r16 at y - 16 (it flares into the
# wall plane x 66.8), so the first HANDLE_BLEND_T mm below SHARED_Y morph point-wise from r16(y) to r16(y - shift)
# (smoothstep weight); below that the stations are r16's, moved, unchanged.
HANDLE_SHIFT = 16.0
# pass 1d: root transition 15 mm (user: 14-16). Inner flank rate on the loops, z 5 / 8: T 10 1.30 / 1.72,
# T 15 1.00 / 1.25 (r16 moved alone 1.00 / 1.06 over the same y)
HANDLE_BLEND_T = 15.0
# new y; -24.5..-27.5 are r16's dense U-turn stations (-40.5..-43.5) moved, so the morph keeps them
MORPH_YS = [-15.0, -17.0, -19.0, -21.0, -22.5, -24.5, -25.0, -26.0, -26.5, -27.0, -27.5]
# seam (pass 1d): both lofts end on the shared section, and each takes one guide station SEAM_GUIDE mm past the
# body's last / before the handle's first ... on its own side: the value at SHARED_Y +- SEAM_GUIDE of a per-point
# cubic spline through SEAM_GUIDE_N stations on each side. Both lofts then leave the shared section along the
# same tangent (scratch trials, crease on 180 seam points: no guide max 67 / median 16; guide 0.25: 9.4 / 1.2;
# 0.1: 3.8 / 0.46; 0.05: 1.9 / 0.23; loft vs spline at y -12.25..-15.75 within 0.08)
# In the full build every guided variant failed: with a guide on the body loft its top cut at TOP_Z returns
# nothing (any extra body station: 0.02..0.25, max degree 3 / 5 / 8, centripetal); a guide on the handle only,
# along the body loft's own end tangent, made the trimmed handle invalid (that tangent is up to 74 deg off the
# handle's chords at (70.4, -12.7)); without guides the T 15 pieces do not fuse (volume off 0.12 %).
# So pass 1d lofts body and handle as ONE loft through all stations (SINGLE_LOFT): no seam at all.
SINGLE_LOFT = True
SEAM_GUIDE = 0.0           # split lofts only (SINGLE_LOFT False): guide distance, 0 = none
SEAM_GUIDE_N = 4
# pass fit (method change, 2026-10-05): the loft no longer passes exactly through every station. Each matched point
# index gets a smoothing spline along y over all stations (sections.fit_along_y); the stations between FIT_Y0 and
# FIT_Y_TIP are replaced by evenly spaced fitted ones; the smoothing tapers in over FIT_RAMP below FIT_Y0 and out
# over FIT_TIP_RAMP above FIT_Y_TIP. Off: the p1d stations (exact interpolation).
FIT_ALONG_Y = True
FIT_Y0 = -3.0              # stations y >= this stay as they are (the body y >= 5 must not move)
FIT_RAMP = 5.0
FIT_Y_TIP = -45.0          # stations y <= this stay as they are (tip roll, extrapolation, tip fillet)
FIT_TIP_RAMP = 6.0
FIT_SPACING = 1.5          # new station spacing, mm (grip-only trials at h 2: 1.0 valid, tip region worse;
                           # 2.0: rim crest fails at r 2 / 1.5 / 1, tip at r 3, grip + blend invalid)
FIT_SMOOTH = 2.0           # smoothing length h, mm (lam = h**4, weights = station y share). Trials, spacing 1.5:
                           # h 1.5 rim crest fails at r 2 / 1.5 / 1; h 2.5 tip fillet only r 1 and the tip moves 0.77
                           # (FIT_Y_TIP -48 at h 2: the loft fails)
BODY_LOFT_OPTS = {}      # ThruSections overrides, e.g. dict(max_deg=3) or dict(par="Centripetal")
HANDLE_LOFT_OPTS = {}
HANDLE_SRC = [y for y in MAIN_STATIONS if y <= SHARED_Y - HANDLE_SHIFT - HANDLE_BLEND_T]   # r16 y, moved +shift
HANDLE_EXTRAP = [-66.5 + HANDLE_SHIFT, -70.0 + HANDLE_SHIFT]      # new y; extrapolated (r16 tip roll from -65)
TIP_Y_NEW = TIP_Y + HANDLE_SHIFT
# blend stations: the plate front (PLATE_Y0) plus the grip stations from -10 to the rear (BLEND_Y1); the last
# profile is copied to BLEND_EXTRAP_Y and the blend trimmed at PLATE_Y1
BLEND_STATIONS = [PLATE_Y0] + sorted(y for y in REAR_STATIONS + MAIN_STATIONS if -10.0 <= y <= BLEND_Y1)
BLEND_EXTRAP_Y = 79.05

# pass 2 (2026-10-05): r16's remaining features as exact B-rep features. Every switch off = pass corner, byte-identical.
# lower finger + lip + pit: r16 mirrors the upper finger's outline station about YC (y_lo = 2 YC - y_up), same profile
LOWER_LIP_ON = True
FINGER_P_LO = (FINGER_P[0], 2.0 * YC - FINGER_P[1])
FINGER_N_LO = (FINGER_N[0], -FINGER_N[1])
# rear window and camera hole through the floor plate (r16 build_case_ext.py: console rectangle from the pocket)
WINDOW_ON = True
CAMERA_ON = True
CLEAR_Y = 0.50
PANEL_W = 108.0
PANEL_FROM_TOP, PANEL_FROM_BOTTOM = 16.0, 12.5
WINDOW_GROW = 1.0
WINDOW_R = 3.5
CAMERA_FROM_TOP = 7.0
CAMERA_HOLE_D = 12.0
CONSOLE_TOP_Y = POCKET_Y_TOP - CLEAR_Y
CONSOLE_BOT_Y = POCKET_Y_BOTTOM + CLEAR_Y
WIN_Y1 = CONSOLE_TOP_Y - PANEL_FROM_TOP + WINDOW_GROW        # 60.05
WIN_Y0 = CONSOLE_BOT_Y + PANEL_FROM_BOTTOM - WINDOW_GROW     # 3.0
WINDOW_W = PANEL_W + 2 * WINDOW_GROW                          # 110
CAMERA_Y = CONSOLE_TOP_Y - CAMERA_FROM_TOP                    # 68.05
HOLE_Z0 = PLATE_Z0 - 5.0                                      # through cutters run from under the plate ...
HOLE_Z1 = FLOOR_Z + 2.0                                       # ... into the pocket's air
# bottom opening: r16 leaves no material above the floor in front of the pocket for |x| < 66.75 (R; L 68.75, accepted
# by the user). v2 is open there already except the grip's inner face at x 66.5-66.6; the cut takes x < OPEN_X_END.
BOTTOM_OPEN_ON = True
OPEN_X_END = 67.4                                             # pass s8: 66.75 left a 1.43 mm y-wall (S8); r16 OPEN_WALL rule
OPEN_Y_LO = -25.0                                             # r16: no material at x < 66.75, y -25..-9.3, z >= -8.8
OPEN_END_R = 1.2                                              # pass edge: round on the closed end / grip edge (0 = s8)
OPEN_END_R_FALLBACK = (1.0,)                                  # tried in order if OPEN_END_R fails

# pass cove (2026-10-27, user): a strip in the console seat corner (pocket wall / floor Z -8.8) along the elliptical
# cap, section COVE_R x COVE_R with its free edge rounded to the full COVE_R (tangent to wall and floor), built alone
# (parts/cove.py) and joined before the pit cuts. Measured: the console clears an r 3 cove by >= 2.45.
# A1 (user report): only along the handle-side wall — from the front (theta -90) to the upper pit; removed over each
# pit's full length. Past y ~60 (the rear/trigger corner) there is no wall and the strip stood alone as a thin fin.
# 0 = pass latch (byte-identical).
COVE_R = 3.0
COVE_EMBED = 0.5                                              # reach into the wall and floor, so the union overlaps
# A2 (user: "reduced too much"): run past the upper pit to where the wall still backs the full height — measured on
# the latch STL: wall at u 0 up to h 4 for theta 32..38 deg, gone at h 4 by 40, gone by 45. Pits stay as breaks.
COVE_THETA_END = 38.0                                         # degrees on the cap ellipse (y 59.3)
