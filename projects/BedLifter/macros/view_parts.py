"""
BedLifter — interactive 3D viewer
===================================
Opens all three parts in the ocp-vscode browser viewer (Three.js-based, no VS Code needed).

Usage:
  1. Start the viewer server in one terminal:
       python -m ocp_vscode --port 3939 --axes --grid_xy --theme dark
  2. Open http://localhost:3939 in any browser.
  3. Run this script in a second terminal:
       python macros/view_parts.py
  Parts appear in the browser immediately.

Requirements: pip install build123d ocp-vscode
"""

import sys
from ocp_vscode import Camera, show, set_defaults

# Adjust camera and rendering defaults once
set_defaults(reset_camera=Camera.RESET, axes=True, axes0=True, grid=(True, True, False),
             angular_tolerance=0.05, deviation=0.01)

# Import the geometry builders (this also prints the dimension summary)
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from bed_lifter_b123d import (
    build_lifter, make_lifter_split,
    HEAD_LIFT_HIGH, HEAD_BODY_R, WHEEL_TOP_R, WHEEL_TOP_L, HEAD_COLLAR_H, HEAD_FLARE_R,
    WHEEL_SOCK_R, WHEEL_SOCK_L,
    MID_LIFT_HIGH, MID_BODY_R, MID_ROD_R, MID_TOP_L, MID_COLLAR_H,
    MID_SOCK_R, MID_SOCK_L,
    HEAD_SPLIT_Z, HEAD_TENON_X, HEAD_TENON_Y, HEAD_TENON_H, TENON_CLEARANCE,
    ANGLE_DEG,
)

print("Building parts …")

lower, upper = make_lifter_split(
    split_z     = HEAD_SPLIT_Z,
    tenon_x     = HEAD_TENON_X,
    tenon_y     = HEAD_TENON_Y,
    tenon_h     = HEAD_TENON_H,
    clearance   = TENON_CLEARANCE,
    lift_h_high = HEAD_LIFT_HIGH,
    body_r      = HEAD_BODY_R,
    top_rod_r   = WHEEL_TOP_R,
    top_rod_l   = WHEEL_TOP_L,
    collar_h    = HEAD_COLLAR_H,
    sock_r      = WHEEL_SOCK_R,
    sock_l      = WHEEL_SOCK_L,
    angle_deg   = ANGLE_DEG,
    flare_z     = HEAD_SPLIT_Z,
    flare_r     = HEAD_FLARE_R,
)

middle = build_lifter(
    lift_h_high = MID_LIFT_HIGH,
    body_r      = MID_BODY_R,
    top_rod_r   = MID_ROD_R,
    top_rod_l   = MID_TOP_L,
    collar_h    = MID_COLLAR_H,
    sock_r      = MID_SOCK_R,
    sock_l      = MID_SOCK_L,
    angle_deg   = ANGLE_DEG,
)

print("Sending to viewer …")

show(
    lower,
    upper,
    middle,
    names=["HeadLifter_Lower", "HeadLifter_Upper", "MiddleLifter"],
    colors=["#4CAF50", "#2196F3", "#FF9800"],
    alphas=[1.0, 0.85, 1.0],     # upper half slightly transparent so split is visible
    reset_camera=Camera.RESET,
)

print("Done — check the OCP CAD Viewer panel in VS Code (or http://localhost:3939).")
