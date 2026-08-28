"""
BedLifter — build123d port (v1)
================================
Equivalent of bed_lifter.py (FreeCAD macro v8) using build123d.
Exports each part as STEP + STL so it can be sliced or imported into any CAD tool.

Run with plain Python (no FreeCAD needed):
    python macros/bed_lifter_b123d.py

Requirements:
    pip install build123d

Output (written to the project folder):
    HeadLifter_Lower.step / .stl
    HeadLifter_Upper.step / .stl
    MiddleLifter.step      / .stl

Coordinate system (per piece, local):
    +X = toward foot of bed (direction the angled top slopes DOWN)
    +Z = up
    Origin = centre of bottom face (floor level)
"""

import math
import pathlib

from build123d import (
    Align,
    Axis,
    Box,
    Cone,
    Cylinder,
    Location,
    export_step,
    export_stl,
)

# ── Output directory ──────────────────────────────────────────────────────────
SAVE_DIR = pathlib.Path(__file__).resolve().parent.parent   # …/BedLifter/

# ── Geometry constants ────────────────────────────────────────────────────────
BED_LEN_MM       = 2000.0
HEAD_WHEEL_X_MM  =   50.0
MID_SUPPORT_X_MM = 1000.0          # true centre of 2000 mm bed
HEAD_LIFT_MM     =  300.0

HEAD_WHEEL_PIVOT_DIST = BED_LEN_MM - HEAD_WHEEL_X_MM       # 1950 mm
ANGLE_RAD = math.asin(HEAD_LIFT_MM / HEAD_WHEEL_PIVOT_DIST)
ANGLE_DEG = math.degrees(ANGLE_RAD)

MID_PIVOT_DIST = BED_LEN_MM - MID_SUPPORT_X_MM             # 1000 mm
MID_LIFT_MM    = MID_PIVOT_DIST * math.sin(ANGLE_RAD)

# ── Hardware dimensions ───────────────────────────────────────────────────────
# Bottom socket: sized for the existing Ø10 mm wheel rod (unchanged)
WHEEL_ROD_R  = 5.0                 # existing wheel rod radius
WHEEL_ROD_L  = 50.0
WHEEL_SOCK_R = WHEEL_ROD_R + 0.5  # bottom socket inner radius
WHEEL_SOCK_L = WHEEL_ROD_L + 3.0
# Top rod: new Ø12.5 mm to match bed-side socket
WHEEL_TOP_R  = 6.25
WHEEL_TOP_L  = 20.0

MID_ROD_R  = 7.5
MID_ROD_L  = 40.0
MID_SOCK_R = MID_ROD_R + 0.5
MID_SOCK_L = MID_ROD_L + 3.0
MID_TOP_L  = 20.0

HEAD_BODY_R   = 25.0
HEAD_FLARE_R  = 35.0          # Ø70 mm at the top (tapers from Ø50 at split)
MID_BODY_R    = 20.0
HEAD_COLLAR_H =  8.0
MID_COLLAR_H  =  8.0

# Lower half already printed at split_z=150 mm — new upper half starts at z=230 mm
# (80 mm higher than before, shortening the upper piece by 80 mm)
HEAD_SPLIT_Z    = 230.0
HEAD_TENON_X    =  20.0
HEAD_TENON_Y    =  10.0
HEAD_TENON_H    =  10.0
TENON_CLEARANCE =   0.2

_BASE = (Align.CENTER, Align.CENTER, Align.MIN)   # bottom-face at z = 0


def solve_lift_h_high(target_tip_z, top_r, collar_h, top_rod_l, angle_rad):
    """Compute body high-side height so the rod tip reaches target_tip_z.
    top_r is the radius at the widest point of the top face (flare_r if flared)."""
    return (target_tip_z
            - (collar_h + top_rod_l) * math.cos(angle_rad)
            + top_r * math.tan(angle_rad))


# HeadLifter top face is at flare_r radius, so use HEAD_FLARE_R for the geometry
HEAD_LIFT_HIGH = solve_lift_h_high(HEAD_LIFT_MM, HEAD_FLARE_R, HEAD_COLLAR_H,
                                   WHEEL_TOP_L, ANGLE_RAD)
# Sanity: tenon at z=230 mm clears the bottom socket (ends at z=53 mm, gap=177 mm)
assert HEAD_SPLIT_Z > WHEEL_SOCK_L + 50, "Split plane too close to bottom socket"
MID_LIFT_HIGH  = solve_lift_h_high(MID_LIFT_MM, MID_BODY_R, MID_COLLAR_H,
                                   MID_TOP_L, ANGLE_RAD)


# ── Core builder ──────────────────────────────────────────────────────────────

def build_lifter(
    lift_h_high: float,
    body_r: float,
    top_rod_r: float,
    top_rod_l: float,
    collar_h: float,
    sock_r: float,
    sock_l: float,
    angle_deg: float,
    flare_z: float = None,     # z where taper begins (defaults to full straight body)
    flare_r: float = None,     # outer radius at the top of the taper
):
    """Return the full single-piece lifter as a build123d Compound."""
    angle_rad = math.radians(angle_deg)

    # ── 1. Body: straight cylinder, optionally with a tapered top section ─────
    # The cut plane needs to trim the widest part, so use flare_r for headroom.
    top_r = flare_r if flare_r else body_r
    body_tall = lift_h_high + top_r * math.tan(angle_rad) + 5.0

    if flare_z and flare_r and flare_r > body_r:
        # Lower straight section up to flare_z
        body = Cylinder(radius=body_r, height=flare_z, align=_BASE)
        # Short cone: transitions from body_r to flare_r over 20 mm
        taper_h = 20.0
        cone = Cone(bottom_radius=body_r, top_radius=flare_r, height=taper_h, align=_BASE)
        cone = cone.move(Location((0, 0, flare_z)))
        body = body + cone
        # Wide cylinder from top of taper to body_tall — fully at flare_r
        wide_h = body_tall - (flare_z + taper_h)
        if wide_h > 0:
            wide = Cylinder(radius=flare_r, height=wide_h, align=_BASE)
            wide = wide.move(Location((0, 0, flare_z + taper_h)))
            body = body + wide
    else:
        body = Cylinder(radius=body_r, height=body_tall, align=_BASE)

    # ── 2. Cut the tilted top ─────────────────────────────────────────────────
    # The cut plane passes through (-top_r, 0, lift_h_high) with normal
    # (sin θ, 0, cos θ). top_r is the widest radius at the head-side top edge.
    big = 4000.0
    cutter = Box(big, big, big, align=_BASE)
    cutter = cutter.rotate(Axis.Y, -angle_deg)
    cutter = cutter.move(Location((-top_r, 0, lift_h_high)))
    body = body - cutter

    # ── 3. Collar + rod — perpendicular to the angled cut face ───────────────
    # The cut face mates flush against the tilted bed underside. The bed socket
    # axis is perpendicular to that face, so the rod must tilt at angle_deg from
    # vertical toward the head end (-X): rod_axis = (-sin θ, 0, cos θ).
    top_center_z = lift_h_high - top_r * math.tan(angle_rad)
    rod_dx = -math.sin(angle_rad)
    rod_dz =  math.cos(angle_rad)

    # Collar: small flange (rod_r + 5 mm), overlaps 1 mm into body for clean fuse
    collar_r = top_rod_r + 5.0
    collar = Cylinder(radius=collar_r, height=collar_h + 1.0, align=_BASE)
    collar = collar.rotate(Axis.Y, -angle_deg)
    collar = collar.move(Location((rod_dx * (-1.0), 0.0, top_center_z + rod_dz * (-1.0))))
    body = body + collar

    # Rod: from top of collar along rod_axis
    rod = Cylinder(radius=top_rod_r, height=top_rod_l, align=_BASE)
    rod = rod.rotate(Axis.Y, -angle_deg)
    rod = rod.move(Location((rod_dx * collar_h, 0.0, top_center_z + rod_dz * collar_h)))
    body = body + rod

    # ── 5. Bottom socket (vertical hole from base center) ────────────────────
    socket = Cylinder(radius=sock_r, height=sock_l, align=_BASE)
    body = body - socket

    return body


def make_lifter_split(
    split_z: float,
    tenon_x: float,
    tenon_y: float,
    tenon_h: float,
    clearance: float,
    **lifter_kwargs,
):
    """Build the full lifter then slice into Lower / Upper halves."""
    full = build_lifter(**lifter_kwargs)
    big = 4000.0

    # ── Lower half ────────────────────────────────────────────────────────────
    # Keep everything below split_z, add tenon on top.
    upper_cutter = Box(big, big, big, align=_BASE).move(Location((0, 0, split_z)))
    lower = full - upper_cutter

    # Tenon: centred on body axis, overlaps 0.5 mm below split_z for a clean fuse
    tenon = (Box(tenon_x, tenon_y, tenon_h + 0.5,
                 align=(Align.CENTER, Align.CENTER, Align.MIN))
             .move(Location((0, 0, split_z - 0.5))))
    lower = lower + tenon

    # ── Upper half ────────────────────────────────────────────────────────────
    # Keep everything above split_z, cut pocket for tenon.
    lower_cutter = Box(big, big, big, align=(Align.CENTER, Align.CENTER, Align.MAX)
                       ).move(Location((0, 0, split_z)))
    upper = full - lower_cutter

    # Pocket: slightly wider and deeper than tenon (clearance + glue gap)
    pocket = (Box(tenon_x + 2 * clearance,
                  tenon_y + 2 * clearance,
                  tenon_h + 0.2 + 0.5,
                  align=(Align.CENTER, Align.CENTER, Align.MIN))
              .move(Location((0, 0, split_z - 0.5))))
    upper = upper - pocket

    return lower, upper


def save_part(name: str, shape) -> None:
    step_path = SAVE_DIR / f"{name}.step"
    stl_path  = SAVE_DIR / f"{name}.stl"
    export_step(shape, str(step_path))
    export_stl(shape, str(stl_path))
    print(f"  Saved: {step_path}")
    print(f"  Saved: {stl_path}")


# ── Generate ──────────────────────────────────────────────────────────────────

print(f"\n=== BedLifter build123d port ===")
print(f"Tilt angle      : {ANGLE_DEG:.3f} deg")
print(f"HeadLifter      : high-side h = {HEAD_LIFT_HIGH:.1f} mm, rod tip @ z = {HEAD_LIFT_MM:.1f} mm")
print(f"  split @ z      = {HEAD_SPLIT_Z:.1f} mm, tenon {HEAD_TENON_X:.0f}x{HEAD_TENON_Y:.0f}x{HEAD_TENON_H:.0f} mm")
print(f"MiddleLifter    : high-side h = {MID_LIFT_HIGH:.1f} mm, rod tip @ z = {MID_LIFT_MM:.1f} mm")

print("\nBuilding HeadLifter_Upper (lower half already printed, split now at z=230 mm) …")
_, upper = make_lifter_split(
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
    flare_z     = HEAD_SPLIT_Z,   # taper starts right at the split plane
    flare_r     = HEAD_FLARE_R,   # widens to Ø70 mm at the top
)
save_part("HeadLifter_Upper", upper)

print("\nBuilding MiddleLifter …")
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
save_part("MiddleLifter", middle)

print(f"\nDone. Files written to {SAVE_DIR}\n")
