"""
build_case.py - VitaGripPS5 grip case (rebuild of 2026-09-25).

A PS Vita PCH-1000 case with DualSense handles, built from the 1:1 DualSense
scan by a smooth WARP (not a scale), a straight-walled console pocket, a flat
3.5 mm back wall with the rear touch-panel window, and four flex fingers with
snap lips.

    python build_case.py --out <path.stl>

--out is required and may not point into projects/VitaGripPS5/stl/: the user
approves every STL bake. Nothing runs on import.

Frame: X width, Y fore-aft (handle tips at -Y, Vita top edge / L-R at +Y),
Z up = console face normal (Vita lies screen-up). Units mm.
"""

import argparse
import pathlib
import sys
import time

import numpy as np
import trimesh
from scipy.spatial import ConvexHull, cKDTree
from shapely.geometry import Point, Polygon, box as sbox

HERE = pathlib.Path(__file__).resolve().parent
PROJ = HERE.parent

SCAN = PROJ / "derived" / "dualsense_watertight_200k.stl"   # brief: smooth 1:1 scan
CONSOLE = PROJ / "stl" / "console_solid.stl"                 # brief: plan silhouette source
STL_DIR = PROJ / "stl"                                       # never written by this script

# ---------------------------------------------------------------- frame
SCAN_ZMIN = -25.80          # brief: stripped-frame underside; puts the scan in the brief's Z frame

# ---------------------------------------------------------------- step 1: warp
X_CORE = 20.0               # chosen: |x| below which the centre band stretches uniformly
X_BLEND_END = 35.0          # brief: blend ends inboard of the handle inner edges (~|x| 35)
DX_STATION_Y = -15.6        # brief: 1:1 station where the handle inner edge is solved
HANDLE_INNER_TARGET = 54.6  # brief: handle inner edge target (socket model separation), +-1
Y_JUNCTION = -10.0          # brief: handles are separate below Y ~ -10
Y_BLEND = 8.0               # chosen: length of the C1 blend from 1:1 to stretched in Y
Y_SRC_TOP = 41.0            # measured: 1:1 Y mapped to the pocket top edge. The brief's ~54 kept the
#   L2/R2 trigger levers: scan underside zmin is -21.9 at Y 40, then drops to -24.0 (Y 42) and
#   -25.8 (Y 44-50, x +-45..51) - the triggers - which s 1.426 placed at warped Y 61-75, inside the case.
HANDLE_STATIONS = (-20.0, -30.0, -40.0)  # brief: handle deviation gate stations (1:1)
# Outer line (round 4): each side's outer edge in plan is ONE straight line, the free handle's own outer
# edge continued up the outside of the console end. dx is solved so the handle outer edge (max |x| of the
# 1:1 scan over HANDLE_LINE_Y) lands on X_LINE = pocket half-width + WALL + X_LINE_MARGIN. Above the
# junction a Z-dependent extra dx(Y, Z) moves the scan's outer surface onto the target T(Y) at EVERY Z
# level from the lip-top plane down to X_TAPER_TOP (round 2 sized one extra per Y at the narrowest Z,
# which overshot ~8 mm at mid-Z). T = X_LINE up to the pocket's widest Y, then the pocket outline offset
# by CORNER_OFFSET (the rounded top corner), never beyond X_LINE.
HANDLE_LINE_Y = (-35.0, -15.6)  # measured: 1:1 Y span where the handle outer edge is straight (79.6..80.24)
X_LINE_MARGIN = 0.5         # chosen (brief: "+ margin"): 1.0 would move the handles out 1.18 mm and put
#   the mean handle inner edge at 55.78, outside the socket separation 54.6 +- 1; 0.5 gives 55.28
SHOULDER_DY = 0.5           # chosen: Y sampling step of the extra (mm)
SHOULDER_DZ = 1.0           # chosen: Z sampling step of the extra (mm)
SMOOTH_POS_EPS = 1.0        # chosen: soft clamp width; the surface overshoots T by at most eps/2 = 0.5
SHOULDER_SIGMA = 1.0        # chosen: Gaussian smoothing sigma (mm, Y and Z) of the extra
X_TAPER_LEN = 8.0           # chosen: below X_TAPER_TOP the extra ramps (C1) to 0 over this Z length
# Back-lobe shoulder (round 4, "no L1/R1 knob"): the 1:1 underside has a 1.5-2 mm hump at Y 28-34 (L min Z
# -22.0 at Y 34 vs -18.3 at Y 22; R -22.5 at Y 30-32) that the Y stretch made a knob. Above ROUND_Y0 every
# vertex is lifted with a smooth max onto a quarter-ellipse floor rising from ROUND_Z0 to RIM_BOT at the top
# edge, so the lobe ends in one rounded shoulder. Smooth max is strictly monotone in z: no fold.
ROUND_Y0 = 45.0             # chosen: warped Y of 1:1 Y 22 (L lobe min -18.3), below the hump
ROUND_Z0 = -19.5            # chosen: just under the natural underside at ROUND_Y0 (L -18.3, R -19.0)
ROUND_K = 1.5               # chosen: smooth-max width (mm)

# ---------------------------------------------------------------- step 2: pocket
CONSOLE_W, CONSOLE_D, CONSOLE_T = 182.0, 83.55, 18.6  # brief: PCH-1000 spec
CLEAR_X, CLEAR_Y = 0.65, 0.50   # brief: pocket clearance per side
CLEAR_Z = 0.20                  # brief: lip underside above console face
POCKET_Y_BOTTOM = -5.0          # brief: pocket bottom edge just inside the junction

# ---------------------------------------------------------------- step 3: front plane / lips
LIP_TOP_Z = 17.0            # brief: suggested lip-top plane in the stripped frame
LIP_T = 3.4                 # brief (tolerance report): lip Z thickness
LIP_OVERHANG = 1.5          # brief: lip reach beyond the pocket outline
LIP_LEAD_DEG = 30.0         # brief: lead-in face angle from Z
LIP_RET_DEG = 127.0         # brief r3 (tolerance review r2 s.3): retention face angle from Z. Leaves a
#   0.002 mm top land (t_top 0.898 vs FINGER_T_TIP 0.9)
LIP_FLAT = 0.50             # chosen: flat underside width over the clearance band (= CLEAR_Y)

# ---------------------------------------------------------------- step 6: back wall
BACK_T = 3.5                # brief: back wall under the pocket floor
WALL = 3.0                  # brief: cup walls >= 3.0 (cup = pocket outline offset by this)
BACK_FILLET = 4.0           # chosen (brief: >= 3): wall-to-handle-root fillet radius
BAND_X = 56.5               # chosen: flat centre-band half-width (the r2/r3 derived value, kept when the
#   bottom-corner fingers it was derived from were removed in round 4)
BAND_Y0 = -9.0              # chosen: centre-band cut starts here (junction side), leaves free handles alone

# ---------------------------------------------------------------- step 7: window + camera
# brief r4: rear touch panel ~108 x 55 (diagram estimate), 16 mm below the console's top edge and 12.5
# above its bottom edge, centred in X; cut 1 mm bigger per side. Rear camera ~8 mm, ~7 mm below the top edge.
PANEL_W, PANEL_H = 108.0, 55.0
PANEL_FROM_TOP, PANEL_FROM_BOTTOM = 16.0, 12.5
WINDOW_GROW = 1.0           # brief r4: per side
WINDOW_R = 3.5              # brief r4: ~3-4
CAMERA_FROM_TOP = 7.0       # brief r4
CAMERA_HOLE_D = 12.0        # brief r4 (~12 for an ~8 mm camera)

# ---------------------------------------------------------------- step 8: fingers
# Round 4: 2 fingers per end, both on the pocket outline's END arc (user markup squares), placed
# symmetric about the pocket centre line at YC +- LIP_DY. The top-edge and bottom-corner fingers are gone.
LIP_DY = 26.5              # chosen: markup squares (left end, Y ~63 and ~12 on a perspective render,
#   +-3 mm) -> YC 37.3 +- 25 first; at 25 the upper pit's outer corner broke through the outer line
#   (pinhole at x -95.16, Y 57.1 -> genus +1). 26.5 = Y 63.8 / 10.8 with PIT_CORNER_R keeps >= 1.5 mm skin
PIT_CORNER_R = 2.5          # chosen (= FINGER_GAP): plan radius of the clearance pit's two outer corners
LR_CLEAR_Y = 5.0            # chosen: the upper finger footprint (lip + slots + pit) stays this far below
#   the top edge, where the L/R buttons are (|x| ~58-85 on the top edge, unverified)
FINGER_SKIN = 2.0           # chosen: outer skin behind each finger's flex gap
FINGER_W = 15.0             # brief r3
FINGER_T_ROOT = 1.8         # brief
FINGER_T_TIP = 0.9          # brief
FINGER_ROOT_BELOW_FLOOR = 5.0  # brief: root ~5 mm below the pocket floor
FINGER_ROOT_R = 1.0         # brief r3: root fillet on both bending faces
FINGER_SLOT = 1.0           # brief: ~1 mm through slot each side
FINGER_GAP = 2.5            # chosen (brief: >= 2): gap behind the finger root
FINGER_INNER_SLOT = 1.5     # chosen: trench on the pocket side below the floor so the root is free.
#   Round 2 had 1.0; 1.5 lets the R1.0 inner root fillet end 0.5 mm before the trench wall
RIM_IN = 4.0                # chosen: top rim reach inside the top edge (round 2's value)
RIM_OUT = 1.0               # chosen: top rim reach past the top edge (round 2: 4.3, to carry finger roots)
RIM_DROP = 2.0              # chosen: top rim depth below the flat back (round 2: 4.45)
RIM_BLEND = 3.0             # chosen: concave fillet radius where the rim meets the flat back
RIM_R = 2.0                 # chosen: edge radius of the top rim bar (section and plan ends)
RIM_TOP_DROP = 0.05         # chosen: rim top sits this far below the floor (no coincident faces)
# Shoulder-wrap end at the top corners (round 3, user decision): the wrap stops on the corner arc where
# the wall is still >= WALL thick, cut along the outline normal (rays along earlier normals never cross
# it on a convex outline), plan corner and top edge rounded at WALL_END_R.
WALL_END_R = 3.0            # brief r3
WALL_END_MARGIN = 0.3       # chosen: wall-thickness margin at the end station
RIM_INTO_SHOULDER = 3.0     # chosen: rim ends this far outboard of the flat band, inside the shoulders
OPEN_BAND_BOTTOM = 12.0     # chosen: bottom long edge opened to Y -17, past the DualSense crotch.
#   8.0 (Y -13) grazed the crotch and left 3 sliver bodies; 6.0 (Y -11) left a full-height
#   crotch bar at Y -16..-11, |x| < 54, Z 1.4..17.0 bridging the handles (seen in the render).
OPEN_BAND_TOP = 4.0         # chosen: top long edge band (everything beyond the edge is trimmed anyway)

# ---------------------------------------------------------------- derived Z levels
LIP_U = LIP_TOP_Z - LIP_T                       # lip underside
FACE_Z = LIP_U - CLEAR_Z                        # seated console face
FLOOR_Z = LIP_U - (CONSOLE_T + CLEAR_Z)         # pocket floor
BACK_Z = FLOOR_Z - BACK_T                       # flat back
ROOT_Z = FLOOR_Z - FINGER_ROOT_BELOW_FLOOR      # finger root
POCKET_W = CONSOLE_W + 2 * CLEAR_X              # 183.30
POCKET_D = CONSOLE_D + 2 * CLEAR_Y              # 84.55
POCKET_Y_TOP = POCKET_Y_BOTTOM + POCKET_D
POCKET_YC = POCKET_Y_BOTTOM + POCKET_D / 2.0
X_LINE = POCKET_W / 2.0 + WALL + X_LINE_MARGIN  # 95.15: outer line of both handles and console ends
CORNER_OFFSET = FINGER_T_ROOT + FINGER_GAP + FINGER_SKIN   # 6.3: top-corner outer = pocket offset by this
X_TAPER_TOP = ROOT_Z - 1.0                       # the outer line holds down to 1 mm below the finger roots
CONSOLE_TOP_Y = POCKET_Y_TOP - CLEAR_Y          # console top edge (seated, centred in the clearance)
CONSOLE_BOT_Y = POCKET_Y_BOTTOM + CLEAR_Y
WIN_Y1 = CONSOLE_TOP_Y - PANEL_FROM_TOP + WINDOW_GROW       # window top
WIN_Y0 = CONSOLE_BOT_Y + PANEL_FROM_BOTTOM - WINDOW_GROW    # window bottom
WINDOW_W = PANEL_W + 2 * WINDOW_GROW
WINDOW_H = WIN_Y1 - WIN_Y0                       # 57.05 (the brief's 16 + 55 + 12.5 = 83.5 vs 83.55 spec)
CAMERA_Y = CONSOLE_TOP_Y - CAMERA_FROM_TOP
RIM_BOT = BACK_Z - RIM_DROP                      # rim underside
RIM_X = BAND_X + RIM_INTO_SHOULDER               # rim half-length
BIG = 400.0


# ================================================================ helpers
def bodies(m):
    """Components split by signed volume: (positive list, negative list)."""
    comps = m.split(only_watertight=False)
    pos = [c for c in comps if c.volume > 0]
    neg = [c for c in comps if c.volume <= 0]
    return pos, neg


def boolean(op, a, b, what):
    """Manifold boolean that raises on empty or multi-body output."""
    fn = {"union": trimesh.boolean.union,
          "difference": trimesh.boolean.difference,
          "intersection": trimesh.boolean.intersection}[op]
    r = fn([a, b], engine="manifold")
    if r is None or len(r.faces) == 0:
        raise RuntimeError("%s (%s) returned an empty mesh" % (what, op))
    pos, neg = bodies(r)
    if len(pos) != 1 or neg:
        info = "; ".join("vol %.1f bounds %s" % (c.volume, np.round(c.bounds, 1).tolist())
                         for c in pos + neg)
        raise RuntimeError("%s (%s): %d positive / %d negative shells: %s"
                           % (what, op, len(pos), len(neg), info))
    return r


def prism(poly, z0, z1):
    m = trimesh.creation.extrude_polygon(poly, z1 - z0)
    m.apply_translation([0, 0, z0])
    return m


def box(x0, x1, y0, y1, z0, z1):
    m = trimesh.creation.box(extents=[x1 - x0, y1 - y0, z1 - z0])
    m.apply_translation([(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2])
    return m


def blend_int(t):
    """Integral over [0, t] of the C1 cosine ramp w(s) = (1 - cos(pi s)) / 2."""
    return (t - np.sin(np.pi * t) / np.pi) / 2.0


# ================================================================ step 1: warp
def load_scan():
    g = trimesh.load(str(SCAN))
    g.apply_translation(-g.bounds.mean(axis=0))
    g.apply_translation([0, 0, SCAN_ZMIN - g.bounds[0][2]])
    return g


def inner_edges(mesh, y):
    sec = mesh.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0])
    x = sec.vertices[:, 0]
    return float(x[x < 0].max()), float(x[x > 0].min())


def handle_outer(scan):
    """Max |x| of the 1:1 handle over HANDLE_LINE_Y, per side (sections every 0.5 mm)."""
    out = [0.0, 0.0]
    for y in np.arange(HANDLE_LINE_Y[0], HANDLE_LINE_Y[1] + 1e-6, 0.5):
        x = scan.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0]).vertices[:, 0]
        out = [max(out[0], -x.min()), max(out[1], x.max())]
    return out


def solve_dx(scan):
    """dx that puts the free handle's outer edge on X_LINE (one dx, both sides: rigid copies)."""
    l, r = inner_edges(scan, DX_STATION_Y)
    ho = handle_outer(scan)
    dx = X_LINE - max(ho)
    return dx, l, r, ho


def warp_x(x, dx):
    b = X_BLEND_END - X_CORE
    k = 1.0 + dx / (X_CORE + b / 2.0)
    u = np.abs(x)
    t = np.clip((u - X_CORE) / b, 0.0, 1.0)
    mid = k * X_CORE + (u - X_CORE) + (k - 1.0) * b * (t - blend_int(t))
    f = np.where(u <= X_CORE, k * u, np.where(u >= X_BLEND_END, u + dx, mid))
    return np.sign(x) * f, k


def y_stretch():
    return 1.0 + (POCKET_Y_TOP - Y_SRC_TOP) / (Y_BLEND / 2.0 + Y_SRC_TOP - Y_JUNCTION - Y_BLEND)


def warp_y(y, s):
    t = np.clip((y - Y_JUNCTION) / Y_BLEND, 0.0, 1.0)
    mid = y + (s - 1.0) * Y_BLEND * blend_int(t)
    far = y + (s - 1.0) * (Y_BLEND / 2.0 + (y - Y_JUNCTION - Y_BLEND))
    return np.where(y <= Y_JUNCTION, y, np.where(y >= Y_JUNCTION + Y_BLEND, far, mid))


def shoulder_floor(y):
    """Quarter-ellipse back-lobe floor: -inf below ROUND_Y0, ROUND_Z0 -> RIM_BOT at the top edge."""
    t = np.clip((y - ROUND_Y0) / (POCKET_Y_TOP - ROUND_Y0), 0.0, 1.0)
    h = RIM_BOT - (RIM_BOT - ROUND_Z0) * np.sqrt(1.0 - t * t)
    return np.where(y < ROUND_Y0, -1e3, h)


def warp(scan, dx, s, extra=None, lift=False):
    """extra: optional C1 function (side, 1:1 Y, Z) added to dx (0 at and below the junction).
    lift: smooth-max the back-lobe underside onto shoulder_floor (after the Y warp)."""
    v = scan.vertices.copy()
    d = dx if extra is None else dx + extra(np.sign(v[:, 0]), v[:, 1], v[:, 2])
    v[:, 0], k = warp_x(v[:, 0], d)
    v[:, 1] = warp_y(v[:, 1], s)
    if lift:
        h = shoulder_floor(v[:, 1])
        z = v[:, 2]
        t = np.clip((v[:, 1] - ROUND_Y0) / 6.0, 0.0, 1.0)      # C1 onset over 6 mm (chosen)
        w = (1.0 - np.cos(np.pi * t)) / 2.0
        sm = (z + h + np.sqrt((z - h) ** 2 + ROUND_K ** 2)) / 2.0
        v[:, 2] = np.where(h > -1e2, z + w * (sm - z), z)
    return trimesh.Trimesh(v, scan.faces.copy(), process=False), k


def cup_outer_x(cup_poly, y):
    from shapely.geometry import LineString
    seg = LineString([(-BIG, y), (BIG, y)]).intersection(cup_poly)
    return np.nan if seg.is_empty else max(-seg.bounds[0], seg.bounds[2])


def outer_x(mesh, ys, zs):
    """Outer |X| of the mesh surface per (side, y, z) by rays from outside: shape (2, ny, nz)."""
    out = np.full((2, len(ys), len(zs)), -np.inf)
    yy, zz = np.meshgrid(ys, zs, indexing="ij")
    for i, side in enumerate((-1, 1)):
        o = np.column_stack([np.full(yy.size, side * 250.0), yy.ravel(), zz.ravel()])
        d = np.tile([-side, 0.0, 0.0], (yy.size, 1))
        loc, ri, _ = mesh.ray.intersects_location(o, d, multiple_hits=False)
        flat = out[i].reshape(-1)
        flat[ri] = side * loc[:, 0]
        out[i] = flat.reshape(yy.shape)
    return out


def side_outer_x(poly, y, side):
    """Outer X of a plan polygon at Y on one side (nan if the line misses it)."""
    from shapely.geometry import LineString
    seg = LineString([(-BIG, y), (BIG, y)]).intersection(poly)
    if seg.is_empty:
        return np.nan
    return -seg.bounds[0] if side < 0 else seg.bounds[2]


def target_line(poly, yw, side):
    """T(Y): X_LINE up to the pocket's widest Y, then the pocket offset by CORNER_OFFSET, capped at X_LINE."""
    off = poly.buffer(CORNER_OFFSET, resolution=32)
    px = np.array([side_outer_x(poly, y, side) for y in yw])
    ox = np.array([side_outer_x(off, y, side) for y in yw])
    y_peak = yw[int(np.nanargmax(px))]
    t = np.where(yw <= y_peak, X_LINE, np.minimum(X_LINE, np.nan_to_num(ox, nan=0.0)))
    return t, y_peak


def shoulder_extra(base, poly, cup_poly, s):
    """C1-ish extra dx(side, 1:1 Y, Z): moves the warped scan's outer surface onto T(Y) at every Z from the
    lip-top plane down to X_TAPER_TOP, then ramps to 0 over X_TAPER_LEN. Never below the cup + 0.1."""
    from scipy.interpolate import RegularGridInterpolator
    from scipy.ndimage import gaussian_filter
    yw = np.arange(Y_JUNCTION - 2.0, POCKET_Y_TOP + 1.0 + 1e-6, SHOULDER_DY)
    zs = np.arange(X_TAPER_TOP - X_TAPER_LEN - 1.0, LIP_TOP_Z + 1.0 + 1e-6, SHOULDER_DZ)
    ox = outer_x(base, yw, zs)                                   # (2, ny, nz), -inf where no hit
    tz = np.clip((zs - (X_TAPER_TOP - X_TAPER_LEN)) / X_TAPER_LEN, 0.0, 1.0)
    wz = (1.0 - np.cos(np.pi * tz)) / 2.0
    ys_d = np.linspace(-80.0, 120.0, 8001)
    ysrc = np.interp(yw, warp_y(ys_d, s), ys_d)                # warped Y -> 1:1 Y (warp_y is monotone)
    fns, info = [], {}
    for i, side in enumerate((-1, 1)):
        T, y_peak = target_line(poly, yw, side)
        a = T[:, None] - ox[i]
        a = np.where(np.isfinite(a), a, np.nan)
        # columns without a hit at some Z (above/below the scan there): nearest valid Z value
        for j in range(len(yw)):
            col = a[j]
            ok = np.isfinite(col)
            if ok.any():
                a[j] = np.interp(zs, zs[ok], col[ok])
            else:
                a[j] = 0.0
        e = (a + np.sqrt(a * a + SMOOTH_POS_EPS ** 2)) / 2.0      # soft max(a, 0): overshoot <= eps/2
        e = gaussian_filter(e, SHOULDER_SIGMA / np.array([SHOULDER_DY, SHOULDER_DZ]), mode="nearest")
        # never let the outer surface fall inside the cup (+0.1) between the floor and the lip top
        cx = np.array([side_outer_x(cup_poly, y, side) for y in yw])
        need = np.where(np.isfinite(cx)[:, None], cx[:, None] + 0.1 - np.where(np.isfinite(ox[i]), ox[i], -BIG), 0.0)
        need = np.where((zs >= FLOOR_Z)[None, :] & (zs <= LIP_TOP_Z)[None, :] & np.isfinite(ox[i]), need, 0.0)
        e = np.maximum(e, need)
        e = e * wz[None, :]
        fns.append(RegularGridInterpolator((ysrc, zs), e, bounds_error=False, fill_value=None))
        info[side] = dict(y_peak=y_peak, emax=float(e.max()), T=T)

    def extra(side, y, z):
        y = np.asarray(y, float)
        t = np.clip((y - Y_JUNCTION) / Y_BLEND, 0.0, 1.0)
        ramp = (1.0 - np.cos(np.pi * t)) / 2.0                   # C1: 0 at and below the junction
        pts = np.column_stack([np.clip(y, ysrc[0], ysrc[-1]), np.clip(z, zs[0], zs[-1])])
        out = np.zeros(len(y))
        for i, sd in enumerate((-1, 1)):
            m = side == sd
            out[m] = fns[i](pts[m])
        return np.clip(out, 0.0, None) * ramp

    return extra, dict(yw=yw, ysrc=ysrc, zs=zs, info=info)


# ================================================================ step 2: pocket outline
def pocket_outline():
    c = trimesh.load(str(CONSOLE))
    xz = c.vertices[:, [0, 2]]          # console_solid: X width, Z height (+Z = top edge)
    ring = xz[ConvexHull(xz).vertices]
    ring = ring - (ring.min(0) + ring.max(0)) / 2.0
    ext = ring.max(0) - ring.min(0)
    ring = ring * np.array([POCKET_W / ext[0], POCKET_D / ext[1]])   # spec + clearance
    ring = ring + np.array([0.0, POCKET_YC])
    return Polygon(ring), ext


def outline_point(poly, x, side):
    """Point on the outline at X=x on the top (+1) or bottom (-1) edge, with outward normal."""
    ys = [poly.bounds[1] - 5, poly.bounds[3] + 5]
    from shapely.geometry import LineString
    seg = LineString([(x, ys[0]), (x, ys[1])]).intersection(poly)
    y = seg.bounds[3] if side > 0 else seg.bounds[1]
    ext = poly.exterior
    s = ext.project(Point(x, y))
    p1, p2 = np.array(ext.interpolate(s - 2.0).coords[0]), np.array(ext.interpolate(s + 2.0).coords[0])
    tg = (p2 - p1) / np.linalg.norm(p2 - p1)
    n = np.array([tg[1], -tg[0]])
    p = np.array([x, y])
    if poly.contains(Point(*(p + 0.5 * n))):
        n = -n
    return p, n


def outline_frame(poly, sd, half):
    """Point at arc length sd on the outline and the outward normal of the chord sd -+ half."""
    ext = poly.exterior
    L = ext.length
    p = np.array(ext.interpolate(sd % L).coords[0])
    p1 = np.array(ext.interpolate((sd - half) % L).coords[0])
    p2 = np.array(ext.interpolate((sd + half) % L).coords[0])
    tg = (p2 - p1) / np.linalg.norm(p2 - p1)
    n = np.array([tg[1], -tg[0]])
    if poly.contains(Point(*(p + 0.3 * n))):
        n = -n
    return p, n


def finger_footprint(p, n):
    """Plan corners of a finger's clearance pit and lip: (min |x| toward the centre, max Y)."""
    tg = np.array([n[1], -n[0]])
    hw = FINGER_W / 2.0 + FINGER_SLOT
    cs = [p + a * n + b * tg for a in (-FINGER_INNER_SLOT, -LIP_OVERHANG, FINGER_T_ROOT + FINGER_GAP)
          for b in (-hw, hw)]
    return cs


def end_arc_station(poly, side, y_target):
    """End-arc outline point (side*x > 60) whose Y is nearest y_target, normal of the finger-wide chord."""
    best = None
    for sd in np.arange(0.0, poly.exterior.length, 0.1):
        p = np.array(poly.exterior.interpolate(sd).coords[0])
        if side * p[0] < 60.0:
            continue
        if best is None or abs(p[1] - y_target) < abs(best[1] - y_target):
            best = (sd, p[1])
    p, n = outline_frame(poly, best[0], FINGER_W / 2.0)
    cs = finger_footprint(p, n)
    info = dict(ang=np.degrees(np.arctan2(abs(n[1]), abs(n[0]))),
                xin=min(side * c[0] for c in cs), ymax=max(c[1] for c in cs), ymin=min(c[1] for c in cs))
    if info["ymax"] > POCKET_Y_TOP - LR_CLEAR_Y:
        raise RuntimeError("finger at %s reaches within %.1f of the top edge (L/R)" % (p, LR_CLEAR_Y))
    return p, n, info


def wall_end_station(poly, side):
    """Highest corner-arc point where the wall to the top trim, less the R corner round, is >= WALL."""
    best = None
    for sd in np.arange(0.0, poly.exterior.length, 0.1):
        p, n = outline_frame(poly, sd, 0.25)
        if side * p[0] < 40.0 or p[1] < POCKET_YC or n[1] < 0.05 or side * n[0] <= 0:
            continue
        d = (POCKET_Y_TOP - p[1]) / n[1]                       # wall along the normal to the top trim
        phi = np.arccos(-abs(n[0]))                            # plan corner angle end face / top trim
        need = WALL + WALL_END_R / np.tan(phi / 2.0) + WALL_END_MARGIN
        if d >= need and (best is None or p[1] > best[0][1]):
            best = (p, n, dict(d=d, need=need, phi=np.degrees(phi)))
    return best


def wall_end_cutters(e, n, d):
    """Plan cutter (end along the normal, plan corner rounded R) and top-edge round-over cutter."""
    R = WALL_END_R
    side = np.sign(e[0])
    t = np.array([-n[1], n[0]])
    if t[1] < 0:
        t = -t                                                 # tangent toward the top edge
    Lh = 500.0
    half = Polygon([e - n * Lh, e + n * Lh, e + n * Lh - t * Lh, e - n * Lh - t * Lh])
    keep = half.intersection(sbox(-BIG, -BIG, BIG, POCKET_Y_TOP))
    keep = keep.buffer(-R, resolution=32).buffer(R, resolution=32)          # opening: round convex corner
    local = sbox(40.0, 50.0, 300.0, 300.0) if side > 0 else sbox(-300.0, 50.0, -40.0, 300.0)
    c1 = prism(local.difference(keep), FLOOR_Z, LIP_TOP_Z + 5.0)
    prof = sbox(-R, LIP_TOP_Z - R, R, LIP_TOP_Z + 2.0).difference(
        Point(-R, LIP_TOP_Z - R).buffer(R, resolution=32))
    c2 = trimesh.creation.extrude_polygon(prof, 2 * (d + 5.0))
    c2.apply_translation([0, 0, -(d + 5.0)])
    t3, z3 = np.array([t[0], t[1], 0.0]), np.array([0.0, 0.0, 1.0])
    m = np.eye(4)
    m[:3, 0], m[:3, 1], m[:3, 2] = t3, z3, np.cross(t3, z3)
    m[:3, 3] = [e[0], e[1], 0.0]
    c2.apply_transform(m)
    return c1, c2, local.difference(keep)


# ================================================================ step 8: fingers
def local_frame(p, n):
    """4x4: local x -> outward normal, local y -> Z, local z -> tangent (det +1)."""
    tg = np.array([n[1], -n[0], 0.0])
    m = np.eye(4)
    m[:3, 0] = [n[0], n[1], 0.0]
    m[:3, 1] = [0.0, 0.0, 1.0]
    m[:3, 2] = tg
    m[:3, 3] = [p[0], p[1], 0.0]
    return m


def local_box(frame, t0, t1, z0, z1, half_w):
    m = trimesh.creation.box(extents=[t1 - t0, z1 - z0, 2 * half_w])
    m.apply_translation([(t0 + t1) / 2, (z0 + z1) / 2, 0.0])
    m.apply_transform(frame)
    return m


def pit_solid(frame):
    """Finger clearance pit: inner trench + slots + flex gap, outer plan corners rounded PIT_CORNER_R."""
    hw = FINGER_W / 2.0 + FINGER_SLOT
    a0, a1, R = -FINGER_INNER_SLOT, FINGER_T_ROOT + FINGER_GAP, PIT_CORNER_R
    prof = sbox(a0, -hw, a1 - R, hw).union(sbox(a0, -hw + R, a1, hw - R))
    prof = prof.union(Point(a1 - R, hw - R).buffer(R, resolution=16)).union(
        Point(a1 - R, -hw + R).buffer(R, resolution=16))
    m = trimesh.creation.extrude_polygon(prof, LIP_TOP_Z + 10.0 - ROOT_Z)
    m.apply_translation([0, 0, ROOT_Z])
    m.apply_transform(np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1]], float))  # (a,b,h)->(a,h,-b)
    m.apply_transform(frame)
    return m


def finger_solid(frame):
    L = LIP_U - ROOT_Z
    t_below = FINGER_T_ROOT + (FINGER_T_ROOT - FINGER_T_TIP) / L * 1.0
    z_tip = LIP_U + (LIP_OVERHANG - LIP_FLAT) / np.tan(np.radians(LIP_RET_DEG))
    t_top = -LIP_OVERHANG + (LIP_TOP_Z - z_tip) * np.tan(np.radians(LIP_LEAD_DEG))
    prof = Polygon([(0.0, ROOT_Z - 1.0), (t_below, ROOT_Z - 1.0),
                    (FINGER_T_TIP, LIP_U), (FINGER_T_TIP, LIP_TOP_Z),
                    (t_top, LIP_TOP_Z), (-LIP_OVERHANG, z_tip),
                    (-LIP_FLAT, LIP_U), (0.0, LIP_U)])
    # root fillets R FINGER_ROOT_R on both bending faces: a strip below the pit floor (inside body
    # material) is closed with the finger's lower part, then the lip part is added back unchanged
    from shapely.ops import unary_union
    strip = sbox(-FINGER_INNER_SLOT + 0.05, ROOT_Z - 1.0, FINGER_T_ROOT + FINGER_GAP - 0.05, ROOT_Z)
    low = unary_union([prof, strip]).intersection(sbox(-5.0, ROOT_Z - 1.0, 10.0, ROOT_Z + 3.0))
    low = low.buffer(FINGER_ROOT_R, resolution=16).buffer(-FINGER_ROOT_R, resolution=16)
    prof = unary_union([prof, low])
    if prof.geom_type != "Polygon":
        raise RuntimeError("finger profile is not one polygon")
    m = trimesh.creation.extrude_polygon(prof, FINGER_W)
    m.apply_translation([0, 0, -FINGER_W / 2.0])
    m.apply_transform(frame)
    return m, {"z_tip": z_tip, "t_top": t_top}


# ================================================================ build
def build():
    log = []
    scan = load_scan()
    dx, l_in, r_in, ho = solve_dx(scan)
    s = y_stretch()
    base, k = warp(scan, dx, s)
    log.append("scan 1:1 extents %s, watertight %s" % (np.round(scan.extents, 2).tolist(), scan.is_watertight))
    log.append("handle outer edge (1:1 max |x| over Y %.1f..%.1f): L %.2f R %.2f -> dx %.3f puts it on "
               "X_LINE %.2f (centre stretch k %.4f)" % (HANDLE_LINE_Y[0], HANDLE_LINE_Y[1], ho[0], ho[1], dx,
                                                        X_LINE, k))
    log.append("  warped handle inner edges at Y %.1f: %.2f / %.2f, mean %.2f (socket target %.1f +-1)"
               % (DX_STATION_Y, l_in - dx, r_in + dx, (abs(l_in) + r_in) / 2 + dx, HANDLE_INNER_TARGET))
    log.append("Y stretch s %.4f (1:1 Y %.1f -> %.2f)" % (s, Y_SRC_TOP, float(warp_y(np.array([Y_SRC_TOP]), s)[0])))

    poly, raw = pocket_outline()
    log.append("console plan raw %.2f x %.2f -> pocket %.2f x %.2f, Y %.2f..%.2f"
               % (raw[0], raw[1], poly.bounds[2] - poly.bounds[0], poly.bounds[3] - poly.bounds[1],
                  poly.bounds[1], poly.bounds[3]))
    log.append("Z: lip top %.2f  lip underside %.2f  face %.2f  floor %.2f  back %.2f  finger root %.2f"
               % (LIP_TOP_Z, LIP_U, FACE_Z, FLOOR_Z, BACK_Z, ROOT_Z))
    cup_poly = poly.buffer(WALL, resolution=24)

    extra, sh = shoulder_extra(base, poly, cup_poly, s)
    body, _ = warp(scan, dx, s, extra, lift=True)
    if not body.is_watertight:
        raise RuntimeError("warp broke watertightness")
    for sd in (-1, 1):
        inf = sh["info"][sd]
        log.append("outer line side %+d: T = X_LINE %.2f up to the pocket's widest Y %.1f, then pocket + %.1f; "
                   "max extra dx %.2f" % (sd, X_LINE, inf["y_peak"], CORNER_OFFSET, inf["emax"]))
    yy = np.array([-10, -5, 0, 10, 20, 30, 41.0])
    for zz in (LIP_TOP_Z, 6.0, FLOOR_Z, ROOT_Z, -16.0):
        log.append("  extra dx (L) at Z %5.1f, 1:1 Y -10/-5/0/10/20/30/41: %s"
                   % (zz, np.round(extra(-np.ones(7), yy, np.full(7, zz)), 2).tolist()))

    # breakout: warped scan outer |X| (min over Z floor..lip top) vs pocket + wall, before and after
    ys_t = np.arange(POCKET_Y_BOTTOM, POCKET_Y_TOP - 2.0 + 0.1, 10.0)
    ys_t = np.append(ys_t, [POCKET_Y_TOP - 2.5, POCKET_Y_TOP - 0.5])
    zs_t = np.linspace(FLOOR_Z, LIP_TOP_Z, 12)
    before = outer_x(base, ys_t, zs_t).min(axis=2)
    after = outer_x(body, ys_t, zs_t).min(axis=2)
    log.append("plan breakout (outer |X| of warped scan, min over Z %.1f..%.1f, L/R) vs pocket+wall:"
               % (FLOOR_Z, LIP_TOP_Z))
    for j, y in enumerate(ys_t):
        c = cup_outer_x(cup_poly, y)
        log.append("  Y %5.1f cup %5.1f | before L %5.1f R %5.1f | after L %5.1f R %5.1f -> margin %+.2f / %+.2f"
                   % (y, c, before[0, j], before[1, j], after[0, j], after[1, j], after[0, j] - c, after[1, j] - c))
    scan_w = body
    # round 4: the cup strip below the pocket's bottom edge is left to the scan (with the bottom-corner
    # fingers gone it stood 1.3 mm proud of the crotch surface: 3.5 mm3 outside the scan at x -61..-55)
    cup_plan = cup_poly.intersection(sbox(-BIG, POCKET_Y_BOTTOM - 0.5, BIG, BIG))
    cup = prism(cup_plan, BACK_Z - 1.0, LIP_TOP_Z + 1.0)
    body = boolean("union", body, cup, "scan + cup")

    body = boolean("difference", body, box(-BIG, BIG, -BIG, BIG, LIP_TOP_Z, BIG), "front plane")
    body = boolean("difference", body, box(-BIG, BIG, POCKET_Y_TOP, BIG, -BIG, BIG), "top trim")

    fingers = []
    for sx in (-1, 1):                  # 2 per end, both on the end arc, at YC +- LIP_DY
        for yt in (POCKET_YC + LIP_DY, POCKET_YC - LIP_DY):
            p, n, info = end_arc_station(poly, sx, yt)
            fingers.append((p, n, local_frame(p, n)))
            log.append("finger side %+d at (%.2f, %.2f) normal (%.3f, %.3f) = %.1f deg from X | footprint "
                       "Y %.2f..%.2f (%.2f below the top edge), inner |x| %.2f"
                       % (sx, p[0], p[1], n[0], n[1], info["ang"], info["ymin"], info["ymax"],
                          POCKET_Y_TOP - info["ymax"], info["xin"]))
    # pocket bottom corners: where the outline leaves the straight bottom edge by 0.1 mm
    xbc = []
    for sx in (-1, 1):
        xs_ = np.arange(40.0, 70.0, 0.1)
        yb = [outline_point(poly, sx * x_, -1)[0][1] for x_ in xs_]
        xbc.append(float(xs_[np.argmax(np.array(yb) > POCKET_Y_BOTTOM + 0.1)]))
    xo = min(xbc)
    # bottom opening: per side a straight inner edge from the free handle's inner edge at Y -17 (0.3 mm
    # into the air beside it) to the pocket's bottom corner
    yb0 = POCKET_Y_BOTTOM - OPEN_BAND_BOTTOM
    l17, r17 = inner_edges(base, yb0)
    open_b = Polygon([(l17 + 0.3, yb0), (r17 - 0.3, yb0), (xbc[1], POCKET_Y_BOTTOM + 0.5),
                      (-xbc[0], POCKET_Y_BOTTOM + 0.5)])
    log.append("pocket bottom corners |x| L %.1f R %.1f | bottom opening from the handle inner edges at Y %.1f "
               "(%.2f / %.2f) to the corners | top open-band half-width %.1f"
               % (xbc[0], xbc[1], yb0, l17, r17, xo))
    open_t = sbox(-xo, POCKET_Y_TOP - OPEN_BAND_TOP, xo, POCKET_Y_TOP + 20.0)
    cut_plan = poly.union(open_b).union(open_t)
    body = boolean("difference", body, prism(cut_plan, FLOOR_Z, LIP_TOP_Z + 10.0), "pocket + open edges")

    band_prof = sbox(-BAND_X + BACK_FILLET, BACK_Z - 80.0, BAND_X - BACK_FILLET,
                     BACK_Z - BACK_FILLET).buffer(BACK_FILLET, resolution=24)
    band = trimesh.creation.extrude_polygon(band_prof, BIG)
    band.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    band.apply_translation([0, BAND_Y0 + BIG, 0])
    body = boolean("difference", body, band, "centre band (flat back)")

    # shoulder-wrap ends at the top corners (above the floor): cut along the outline normal where the
    # wall is still >= WALL, plan corner and top edge rounded at WALL_END_R
    ends, end_plans = [], []
    for sx in (-1, 1):
        w = wall_end_station(poly, sx)
        if w is None:
            raise RuntimeError("no wall-end station on side %d" % sx)
        e, ne, wi = w
        c1, c2, cplan = wall_end_cutters(e, ne, wi["d"])
        body = boolean("difference", body, c1, "wall end plan side %+d" % sx)
        body = boolean("difference", body, c2, "wall end round-over side %+d" % sx)
        ends.append((e, ne, wi))
        end_plans.append(cplan)
        log.append("wall end side %+d at outline (%.2f, %.2f) normal (%.3f, %.3f): wall to the top trim "
                   "%.2f (need %.2f = WALL + R/tan(phi/2) + margin, plan corner %.1f deg), R %.1f plan + top"
                   % (sx, e[0], e[1], ne[0], ne[1], wi["d"], wi["need"], wi["phi"], WALL_END_R))

    # top rim: a thin rounded bar under the top edge (below the floor, i.e. behind the console), blended
    # into the flat back with a concave RIM_BLEND fillet. Round 2's rim carried the top finger roots; the
    # top fingers moved to the end arcs in round 3, so it is kept thin.
    ry0, ry1 = POCKET_Y_TOP - RIM_IN, POCKET_Y_TOP + RIM_OUT
    rz0, rz1 = RIM_BOT, FLOOR_Z - RIM_TOP_DROP
    rprof = sbox(ry0 + RIM_R, rz0 + RIM_R, ry1 - RIM_R, rz1 - RIM_R).buffer(RIM_R, resolution=16)
    slab = sbox(ry0 - 20.0, BACK_Z + 0.02, POCKET_Y_TOP, rz1)   # inside the back wall; 0.02 off its face
    rprof = rprof.union(slab).buffer(RIM_BLEND, resolution=16).buffer(-RIM_BLEND, resolution=16)
    rprof = rprof.intersection(sbox(ry0 - 20.0 + 1.0, rz0 - 1.0, ry1 + 1.0, rz1))
    rim = trimesh.creation.extrude_polygon(rprof, 2 * RIM_X)
    rim.apply_transform(np.array([[0, 0, 1, -RIM_X], [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1]], float))
    rplan = sbox(-RIM_X + RIM_R, ry0 - 10.0, RIM_X - RIM_R, ry1 - RIM_R).buffer(RIM_R, resolution=16)
    rim = boolean("intersection", rim, prism(rplan, rz0 - 1.0, rz1 + 1.0), "top rim plan rounding")
    body = boolean("union", body, rim, "top rim")

    clears, finfo = [], []
    for p, n, fr in fingers:
        clr = pit_solid(fr)
        clears.append(clr)
        body = boolean("difference", body, clr, "finger clearance at %s" % np.round(p, 1).tolist())

    # NEW GATE: the added cup (above the floor, as it survives the cuts) must lie inside the warped scan
    ring_plan = cup_plan.difference(cut_plan).intersection(sbox(-BIG, -BIG, BIG, POCKET_Y_TOP))
    for cp in end_plans:
        ring_plan = ring_plan.difference(cp)
    geoms = list(getattr(ring_plan, "geoms", [ring_plan]))
    ring = trimesh.util.concatenate([prism(g_, FLOOR_Z, LIP_TOP_Z) for g_ in geoms if g_.area > 1e-6])
    exc = trimesh.boolean.difference([ring, scan_w], engine="manifold")
    for c_ in clears:
        if exc is not None and len(exc.faces):
            exc = trimesh.boolean.difference([exc, c_], engine="manifold")
    log.append("cup-outside-scan gate: cup ring above floor %.1f mm3; part of it outside the warped scan %.2f mm3"
               % (ring.volume, exc.volume if exc is not None and len(exc.faces) else 0.0))
    if exc is not None and len(exc.faces):
        for c_ in sorted(exc.split(only_watertight=False), key=lambda c: -abs(c.volume))[:6]:
            log.append("    piece %.2f mm3 bounds %s" % (c_.volume, np.round(c_.bounds, 1).tolist()))
    for p, n, fr in fingers:
        f, fi = finger_solid(fr)
        body = boolean("union", body, f, "finger at %s" % np.round(p, 1).tolist())
        finfo.append((p, n, fi))

    wy = (WIN_Y0 + WIN_Y1) / 2.0
    wprof = sbox(-WINDOW_W / 2 + WINDOW_R, WIN_Y0 + WINDOW_R,
                 WINDOW_W / 2 - WINDOW_R, WIN_Y1 - WINDOW_R).buffer(WINDOW_R, resolution=24)
    body = boolean("difference", body, prism(wprof, BACK_Z - 80.0, FLOOR_Z + 2.0), "window")
    cam = Point(0.0, CAMERA_Y).buffer(CAMERA_HOLE_D / 2.0, resolution=32)
    body = boolean("difference", body, prism(cam, BACK_Z - 80.0, FLOOR_Z + 2.0), "camera hole")
    log.append("window %.2f x %.2f, Y %.2f..%.2f, R %.1f | camera hole D %.1f at Y %.2f (Y %.2f..%.2f); "
               "bridge window-camera %.2f mm" % (WINDOW_W, WINDOW_H, WIN_Y0, WIN_Y1, WINDOW_R, CAMERA_HOLE_D,
                                                 CAMERA_Y, CAMERA_Y - CAMERA_HOLE_D / 2, CAMERA_Y + CAMERA_HOLE_D / 2,
                                                 CAMERA_Y - CAMERA_HOLE_D / 2 - WIN_Y1))

    ctx = dict(scan=scan, dx=dx, s=s, k=k, poly=poly, cup_poly=cup_poly, fingers=finfo,
               xo=xo, wy=wy, open_b=open_b, open_t=open_t, ends=ends, end_plans=end_plans, xbc=xbc,
               y_peak={sd: sh["info"][sd]["y_peak"] for sd in (-1, 1)})
    return body, ctx, log


# ================================================================ gates
def ray_hits(mesh, origins, dirs):
    loc, ri, _ = mesh.ray.intersects_location(np.asarray(origins, float), np.asarray(dirs, float),
                                              multiple_hits=True)
    if len(loc) == 0:
        return [np.zeros(0) for _ in origins]
    return [np.sort(loc[ri == i] @ np.asarray(dirs[i], float)) for i in range(len(origins))]


def section_points(mesh, y, sign):
    sec = mesh.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0])
    pts = np.vstack([d for d in sec.discrete]) if sec is not None else np.zeros((0, 3))
    pts = pts[np.sign(pts[:, 0]) == sign]
    # densify: 0.1 mm along each polyline
    out = []
    for d in sec.discrete:
        d = d[np.sign(d[:, 0]) == sign]
        for a, b in zip(d[:-1], d[1:]):
            nseg = max(1, int(np.linalg.norm(b - a) / 0.1))
            out.append(a + (b - a) * np.linspace(0, 1, nseg + 1)[:, None])
    return np.vstack(out) if out else pts


def gates(m, ctx):
    g = []
    pos, neg = bodies(m)
    g.append("watertight %s | bodies (+vol) %d, internal shells (-vol) %d | euler %d genus %d"
             % (m.is_watertight, len(pos), len(neg), m.euler_number, (2 - m.euler_number) // 2))
    e = m.extents
    g.append("extents X %.2f  Y %.2f  Z %.2f | bounds %s" % (e[0], e[1], e[2], np.round(m.bounds, 2).tolist()))
    g.append("volume %.1f cm3" % (m.volume / 1000))

    # back wall probe: 5 points on the flat back (outside the window) + 2 handle controls
    yc, wy = POCKET_YC, ctx["wy"]
    pts = [(0, POCKET_Y_BOTTOM + 4), (20, POCKET_Y_TOP - 6), (-40, POCKET_Y_TOP - 12),
           (40, POCKET_Y_BOTTOM + 6), (0, (WIN_Y1 + CAMERA_Y - CAMERA_HOLE_D / 2) / 2)]
    ctrl = [(-75, -30), (75, -30)]
    for label, pp in (("back", pts), ("control", ctrl)):
        hits = ray_hits(m, [(x, y, 60) for x, y in pp], [(0, 0, -1)] * len(pp))
        for (x, y), h in zip(pp, hits):
            z = 60 - h
            txt = "%s (%.0f,%.1f): %d hits" % (label, x, y, len(z))
            if len(z) >= 2:
                txt += ", top %.2f bottom %.2f -> thickness %.2f" % (z[0], z[1], z[0] - z[1])
            g.append(txt)

    # window open: 5 inside (expect 0 hits), 2 outside (expect hits)
    wx, wh = WINDOW_W / 2 - 6, WINDOW_H / 2 - 6
    win = [(0, wy), (wx, wy + wh), (-wx, wy + wh), (wx, wy - wh), (-wx, wy - wh)]
    out = [(30, WIN_Y1 + 1.5), (-30, WIN_Y0 - 1.5)]
    h1 = ray_hits(m, [(x, y, 60) for x, y in win], [(0, 0, -1)] * 5)
    h2 = ray_hits(m, [(x, y, 60) for x, y in out], [(0, 0, -1)] * 2)
    g.append("window %.2f x %.2f centre Y %.2f: hits inside %s (expect all 0), outside controls %s (expect >0)"
             % (WINDOW_W, WINDOW_H, wy, [len(h) for h in h1], [len(h) for h in h2]))
    rc = CAMERA_HOLE_D / 2
    cin = [(0, CAMERA_Y)] + [(0.8 * rc * np.cos(a), CAMERA_Y + 0.8 * rc * np.sin(a)) for a in np.arange(4) * np.pi / 2]
    cout = [(rc + 1.5, CAMERA_Y), (-(rc + 1.5), CAMERA_Y)]
    h1 = ray_hits(m, [(x, y, 60) for x, y in cin], [(0, 0, -1)] * len(cin))
    h2 = ray_hits(m, [(x, y, 60) for x, y in cout], [(0, 0, -1)] * 2)
    g.append("camera hole D %.1f at (0, %.2f): hits inside %s (expect 0), controls at r %.1f %s (expect >0)"
             % (CAMERA_HOLE_D, CAMERA_Y, [len(h) for h in h1], rc + 1.5, [len(h) for h in h2]))

    # PLAN GATE 1: outer silhouette (max |x| of material per Y, every 5 mm, from the top edge to the tip)
    ys = np.arange(POCKET_Y_TOP - 0.05, m.bounds[0][1], -5.0)
    sil = {}
    for y in ys:
        sec = m.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0])
        if sec is None:
            continue
        x = sec.vertices[:, 0]
        sil[y] = (-x.min() if (x < 0).any() else np.nan, x.max() if (x > 0).any() else np.nan)
    yk = np.array(sorted(sil))
    g.append("outer silhouette max |x| per Y (L / R):")
    g.append("  " + " ".join("%.1f:%.1f/%.1f" % (y, sil[y][0], sil[y][1]) for y in yk[::-1]))
    for i, sd in enumerate((-1, 1)):
        xs = np.array([sil[y][i] for y in yk])
        y_hi = ctx["y_peak"][sd]
        fit = (yk >= HANDLE_STATIONS[-1]) & (yk <= y_hi)
        c = np.polyfit(yk[fit], xs[fit], 1)
        dev = xs[fit] - np.polyval(c, yk[fit])
        sh = (yk > Y_JUNCTION) & (yk <= y_hi)
        exc = (xs[sh] - np.polyval(c, yk[sh])).max()
        top = yk > y_hi
        g.append("  %s: line fit Y %.1f..%.1f (widest pocket Y to where the tip rounds): x = %.2f %+.4f*Y, "
                 "max |dev| %.2f (target <= 2) | shoulder max excess over the line %.2f (target <= 1) | "
                 "above Y %.1f (top-corner round) x %s"
                 % ("L" if sd < 0 else "R", yk[fit].min(), yk[fit].max(), c[1], c[0], np.abs(dev).max(), exc,
                    y_hi, np.round(xs[top][::-1], 1).tolist()))
        c2 = np.polyfit(yk[yk >= HANDLE_STATIONS[-1]], xs[yk >= HANDLE_STATIONS[-1]], 1)
        d2 = xs[yk >= HANDLE_STATIONS[-1]] - np.polyval(c2, yk[yk >= HANDLE_STATIONS[-1]])
        g.append("     (fit from the top edge instead, corner round included: max |dev| %.2f)" % np.abs(d2).max())

    # PLAN GATE 2: handle inner edge where it meets the pocket bottom edge, vs the pocket bottom corner
    yb = POCKET_Y_BOTTOM - 0.5
    zl = np.linspace(FLOOR_Z + 0.5, LIP_TOP_Z - 0.5, 7)
    for i, sd in enumerate((-1, 1)):
        hh = ray_hits(m, [(0, yb, z) for z in zl], [(sd, 0, 0)] * len(zl))
        xin = min(h[0] for h in hh if len(h))
        g.append("inner edge side %+d at Y %.1f (above the floor): |x| %.2f vs pocket bottom corner %.1f (%+.2f)"
                 % (sd, yb, xin, ctx["xbc"][i], xin - ctx["xbc"][i]))

    # finger outer skin: from inside each flex gap outward along the normal
    for p, n, fi in ctx["fingers"]:
        q = p + n * (FINGER_T_ROOT + FINGER_GAP - 0.2)
        row = []
        for z in (ROOT_Z + 0.5, FLOOR_Z, 5.0, LIP_TOP_Z - 0.5):
            h = ray_hits(m, [(q[0], q[1], z)], [(n[0], n[1], 0)])[0]
            row.append(round(float(h[1] - h[0]), 2) if len(h) >= 2 else (0.0 if len(h) == 0 else -1))
        g.append("finger (%.1f, %.1f) outer skin behind the gap at Z %.1f/%.1f/5/%.1f: %s (0 = open)"
                 % (p[0], p[1], ROOT_Z + 0.5, FLOOR_Z, LIP_TOP_Z - 0.5, row))

    # pocket width at Y centre and depth at |x| 75, at floor+0.5 and mid-height
    for z in (FLOOR_Z + 0.5, FLOOR_Z + (LIP_U - FLOOR_Z) / 2):
        hx = ray_hits(m, [(0, yc, z), (0, yc, z)], [(1, 0, 0), (-1, 0, 0)])
        hy = ray_hits(m, [(-75, yc, z), (-75, yc, z), (75, yc, z), (75, yc, z)],
                      [(0, 1, 0), (0, -1, 0), (0, 1, 0), (0, -1, 0)])
        w = hx[0][0] + hx[1][0] if len(hx[0]) and len(hx[1]) else float("nan")
        d = [hy[0][0] + hy[1][0] if len(hy[0]) and len(hy[1]) else float("nan"),
             hy[2][0] + hy[3][0] if len(hy[2]) and len(hy[3]) else float("nan")]
        g.append("pocket at Z %.2f: width %.3f (outline %.2f) | depth at x-75 %.3f, x+75 %.3f"
                 % (z, w, POCKET_W, d[0], d[1]))

    # cup wall thickness around the outline at mid-height, skipping open edges and fingers
    # rays every 0.5 mm of outline at three Z levels (floor + 0.5, mid, lip underside); a ray with no
    # hit is "no wall" (open edge or past a wall end) and is counted, not measured
    poly = ctx["poly"]
    ext = poly.exterior
    for zr in (FLOOR_Z + 0.5, FLOOR_Z + 9.4, LIP_U):
        orig, dirs, where = [], [], []
        for sdist in np.arange(0, ext.length, 0.5):
            p = np.array(ext.interpolate(sdist).coords[0])
            q = np.array(ext.interpolate(sdist + 0.5).coords[0])
            tg = (q - p) / np.linalg.norm(q - p)
            n = np.array([tg[1], -tg[0]])
            if poly.contains(Point(*(p + 0.3 * n))):
                n = -n
            if abs(p[0]) < ctx["xbc"][0 if p[0] < 0 else 1] + 0.5:     # open long edges (per-side corner)
                continue
            if any(np.linalg.norm(p - f[0]) < FINGER_W / 2 + FINGER_SLOT + 2.0 for f in ctx["fingers"]):
                continue
            orig.append((p[0] - 0.3 * n[0], p[1] - 0.3 * n[1], zr))
            dirs.append((n[0], n[1], 0))
            where.append(p)
        hits = ray_hits(m, orig, dirs)
        th = [(h[1] - h[0]) if len(h) >= 2 else (np.inf if len(h) == 0 else np.inf) for h in hits]
        i = int(np.argmin(th))
        g.append("cup wall at Z %.2f: %d rays, min thickness %.2f at %s, rays with no wall %d"
                 % (zr, len(th), th[i], np.round(where[i], 1).tolist(), sum(1 for h in hits if len(h) == 0)))
        thin = [(np.round(w, 1).tolist(), round(t_, 2), "first hit %.2f" % h_[0])
                for w, t_, h_ in zip(where, th, hits) if t_ < WALL - 0.02]
        g.append("  rays under %.1f: %d %s" % (WALL, len(thin), thin[:8]))
        # the last walled ray before each wall end (ray origin nearest the end station, with a hit)
        for e, ne, wi in ctx["ends"]:
            cand = [(np.linalg.norm(w_ - e), t_, w_) for w_, t_ in zip(where, th) if np.isfinite(t_)]
            dd, t_, w_ = min(cand, key=lambda c: c[0])
            g.append("  nearest walled ray to the wall end (%.1f, %.1f): at %s (%.2f mm away), wall %.2f"
                     % (e[0], e[1], np.round(w_, 1).tolist(), dd, t_))

    # handle deviation vs 1:1 scan (translation undone)
    scan, dx = ctx["scan"], ctx["dx"]
    for y in HANDLE_STATIONS:
        row = []
        for sign in (-1, 1):
            a = section_points(m, y, sign)
            a[:, 0] -= sign * dx
            b = section_points(scan, y, sign)
            d1 = cKDTree(b).query(a)[0].max()
            d2 = cKDTree(a).query(b)[0].max()
            row.append("%s max dev %.3f (girth X %.2f, Z %.2f)" % ("L" if sign < 0 else "R", max(d1, d2),
                                                                  np.ptp(b[:, 0]), np.ptp(b[:, 2])))
        g.append("handle @Y %.0f: %s" % (y, " | ".join(row)))

    v = m.vertices
    g.append("max Z of any material %.3f vs lip-top plane %.2f" % (v[:, 2].max(), LIP_TOP_Z))
    far = np.ones(len(v), bool)
    for p, n, fi in ctx["fingers"]:
        far &= np.hypot(v[:, 0] - p[0], v[:, 1] - p[1]) > 15.0
    g.append("max Y all %.3f | max Y away from fingers %.3f vs pocket top edge %.2f"
             % (v[:, 1].max(), v[far, 1].max(), POCKET_Y_TOP))
    for p, n, fi in ctx["fingers"]:
        g.append("finger at (%.2f, %.2f) normal (%.3f, %.3f), lip tip Z %.2f, lead-in top t %.3f"
                 % (p[0], p[1], n[0], n[1], fi["z_tip"], fi["t_top"]))
    # material under each finger root (rays down from inside the root, at the root centre and both
    # slot-side edges of the finger); control: a ray from the pocket centre below the window must see 0
    for p, n, fi in ctx["fingers"]:
        tg = np.array([n[1], -n[0]])
        th = []
        for off in (0.0, -FINGER_W / 2 + 0.5, FINGER_W / 2 - 0.5):
            q = p + n * (FINGER_T_ROOT / 2) + tg * off
            h = ray_hits(m, [(q[0], q[1], ROOT_Z - 0.5)], [(0, 0, -1)])[0]
            # ray_hits returns projections on the direction (-Z), so the exit Z is -h[0]
            th.append(ROOT_Z - (-h[0]) if len(h) % 2 == 1 else 0.0)   # odd hit count = origin inside
        g.append("material under finger root at (%.1f, %.1f): %s mm (centre, edge, edge; 0 = root in air)"
                 % (p[0], p[1], np.round(th, 2).tolist()))
    h = ray_hits(m, [(0, ctx["wy"], ROOT_Z - 0.5)], [(0, 0, -1)])[0]
    g.append("  control (0, window centre): %d hits below root level (expect 0)" % len(h))
    return g


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="STL path (not inside projects/VitaGripPS5/stl)")
    a = ap.parse_args()
    out = pathlib.Path(a.out).resolve()
    if STL_DIR.resolve() in out.parents:
        sys.exit("refusing to write into %s: the user approves every STL bake" % STL_DIR)
    t = time.time()
    body, ctx, log = build()
    for line in log:
        print(line)
    print("build %.1f s" % (time.time() - t))
    if not body.is_watertight:
        raise RuntimeError("final body not watertight; not written")
    for line in gates(body, ctx):
        print(line)
    body.export(str(out))
    print("wrote %s (%.1f s)" % (out, time.time() - t))


if __name__ == "__main__":
    main()
