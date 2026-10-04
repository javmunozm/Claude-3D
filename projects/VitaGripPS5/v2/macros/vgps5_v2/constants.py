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
PLATE_X1 = 68.5            # 2.0 mm into the grip-end loft
JUNCTION_R = None          # fillet on the plate / grip-end junction edges; set from --junction-search

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
FORCE_EXT_Y = 61.0         # body stations up to here get the top extension (the clip below ends the top)
CLIP_Y0, CLIP_SLOPE = 59.7, 4.1   # r16 rear corner clip: top contour at y 59.7, falling 4.1 mm z per mm y
N_PTS = 72                # points per smoothed section
SMOOTH_RMS = 0.08          # splprep smoothing, per-point rms (mm)

# stations, rear to tip (y). Main loft: MAIN_STATIONS; rear corner loft: REAR_STATIONS.
MAIN_STATIONS = [61.0, 57.0, 53.0, 49.0, 45.0, 41.0, 37.0, 33.0, 29.0, 25.0, 21.0, 17.0, 13.0, 9.0, 5.0,
                 1.0, -3.0, -6.0, -8.5, -10.0, -11.0, -12.0, -13.5, -15.0, -17.0, -19.0, -21.5, -24.0,
                 -27.0, -30.0, -33.0, -36.0, -38.5, -40.5, -42.0, -43.5, -45.0, -47.0, -49.5, -52.0,
                 -55.0, -58.0, -61.0, -64.0]
EXTRAP_STATIONS = [-66.5, -70.0]   # extrapolated linearly from the last two (r16 tip roll starts at -65)
REAR_STATIONS = [76.5, 74.0, 71.0, 68.0, 65.5, 63.5]
REAR_OVERLAP_Y = 59.0      # rear loft's front section: a copy of its last station, moved to here ...
REAR_OVERLAP_SCALE = 0.92  # ... and shrunk about its centroid (unshrunk, it met the main loft's end face
                           # near-tangentially at (78, 61, -20.5): valid solid, 10 open STL edges)
