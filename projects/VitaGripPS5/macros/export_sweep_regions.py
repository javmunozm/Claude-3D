"""Export the macro geometry the form sweep needs into audit/regions.json.

tools/form_sweep.py is generic: it reads the pocket outline, the pit
footprints, the finger stations, the cut-outs and the scalars from this JSON
instead of importing the macro, so a sweep of an old mesh does not change when
the macro does. The values are computed exactly as the r9-r16 review script
v_sweep.py computed them. Re-run after any change to the pocket, the fingers,
the pits, the window or the camera hole.

Run: python "D:/CAD/Claude-Projects/projects/VitaGripPS5/macros/export_sweep_regions.py"
"""
import json
import sys
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_case_ext as E  # noqa: E402

bc = E.bc
P, N = E.oval_loop()
oval = Polygon(P)
Y1 = E.YC + E.CAP_B * np.sqrt(1.0 - ((E.X_LR_END - E.CAP_XC) / E.CAP_A) ** 2)
y_up = None
for yt in np.arange(Y1, E.YC, -0.25):
    p, n = E.arc_station(oval, 1, yt)
    if max(c[1] for c in bc.finger_footprint(p, n)) <= Y1 - E.FINGER_END_CLEAR:
        y_up = yt
        break
fingers = []
for sx in (-1, 1):
    for yt in (y_up, 2 * E.YC - y_up):
        p, n = E.arc_station(oval, sx, yt)
        fingers.append((p, n, bc.local_frame(p, n)))
pit_fps = [E.pit_plan(E.pit_solid(fr)[0]) for p, n, fr in fingers]


def xy(points):
    return [[float(a), float(b)] for a, b in np.asarray(points, dtype=float)[:, :2]]


out = {
    "_comment": ("Inputs for tools/form_sweep.py, exported from macros/build_case_ext.py by "
                 "macros/export_sweep_regions.py. Region rules are tried in order, first match wins; "
                 "each name gets -R (x > 0) or -L. Keys are <x|y|ax>_<lt|le|gt|ge>, ax = abs(x)."),
    "project": "VitaGripPS5",
    "grid": {"step": 0.5, "x": [-112.0, 112.0], "y": [-80.0, 80.0], "offset": [0.013, 0.029]},
    "regions": [
        {"name": "handle", "y_lt": -14},
        {"name": "corner", "y_gt": 52, "ax_gt": 55},
        {"name": "lobe", "ax_ge": 66},
        {"name": "jct-front", "ax_ge": 52, "y_lt": -4},
        {"name": "jct-lobe/bar", "ax_ge": 52},
        {"name": "bar-bottom", "y_lt": -4},
        {"name": "bar-top", "y_gt": 60},
        {"name": "centre"},
    ],
    "thresholds": {"turn": 8.0, "bump": 0.3, "tooth": 0.3, "wall": 3.0, "back": 3.5, "symmetry": 1.0},
    "regression_delta": {"turn": 4.0, "bump": 0.15},
    "pocket": xy(P),
    "wall": float(E.WALL),
    "pits": [xy(q.exterior.coords) for q in pit_fps],
    "fingers": [[float(p[0]), float(p[1])] for p, n, fr in fingers],
    "y1": float(Y1),
    "yc": float(E.YC),
    "back": {
        "floor_z": float(E.FLOOR_Z),
        "pit_root_z": float(E.ROOT_Z),
        "pit_buffer": 0.6,
        "exclude": [
            {"box": [float(-E.WINDOW_W / 2 + E.WINDOW_R), float(E.WIN_Y0 + E.WINDOW_R),
                     float(E.WINDOW_W / 2 - E.WINDOW_R), float(E.WIN_Y1 - E.WINDOW_R)],
             "buffer": float(E.WINDOW_R + 0.6), "what": "rear window"},
            {"circle": [0.0, float(E.CAMERA_Y)], "r": float(E.CAMERA_HOLE_D / 2 + 0.6), "what": "camera hole"},
        ],
    },
    "walls": {
        "z": [-8.3, -6.0, -3.0, 0.0, 3.0, 6.0, 9.0, 10.2, 12.0, 13.0, 13.3, 13.5],
        "end_ax_gt": float(E.CAP_XC),
        "end_y": [-5.0, float(Y1 - 5.0)],
        "finger_clear": float(E.FINGER_W / 2 + E.FINGER_SLOT + 2.0),
    },
    "sections": {"y": [-78.0, 78.01], "step": 0.5, "offset": 0.017, "side_ax_gt": 45.0},
    "plan_bands": [[-78, -14, "handle"], [-14, 52, "lobe"], [52, 79, "corner"]],
    "flank": {"all_round_y_lt": -14, "theta_deg": [-110, 45]},
}
target = HERE.parent / "audit" / "regions.json"
target.write_text(json.dumps(out, indent=1), encoding="utf-8")
print("wrote %s: pocket %d points, %d pits, fingers %s, Y1 %.4f"
      % (target, len(out["pocket"]), len(out["pits"]), np.round(out["fingers"], 2).tolist(), Y1))
