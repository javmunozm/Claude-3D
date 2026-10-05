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
FRONT_R = 1.0              # plate front face / handle edges (p1_post.py: 3 and 2 fail, 1 valid);
                           # the 15 deg blend crossing takes no fillet at 3 / 2 / 1

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

# stations, rear to tip (y): REAR_STATIONS + MAIN_STATIONS, one loft
MAIN_STATIONS = [61.0, 57.0, 53.0, 49.0, 45.0, 41.0, 37.0, 33.0, 29.0, 25.0, 21.0, 17.0, 13.0, 9.0, 5.0,
                 1.0, -3.0, -6.0, -8.5, -10.0, -11.0, -12.0, -13.5, -15.0, -17.0, -19.0, -21.5, -24.0,
                 -27.0, -30.0, -33.0, -36.0, -38.5, -40.5, -41.0, -42.0, -42.5, -43.0, -43.5, -45.0, -47.0,
                 -49.5, -52.0, -55.0, -58.0, -61.0, -64.0]
# blend stations: the plate front (PLATE_Y0) plus the grip stations from -10 to the rear (BLEND_Y1); the last
# profile is copied to BLEND_EXTRAP_Y and the blend trimmed at PLATE_Y1
BLEND_STATIONS = [PLATE_Y0] + sorted(y for y in REAR_STATIONS + MAIN_STATIONS if -10.0 <= y <= BLEND_Y1)
BLEND_EXTRAP_Y = 79.05
EXTRAP_STATIONS = [-66.5, -70.0]   # extrapolated linearly from the last two (r16 tip roll starts at -65)
