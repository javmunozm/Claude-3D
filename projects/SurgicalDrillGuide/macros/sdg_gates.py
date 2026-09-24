"""SurgicalDrillGuide gates: measured on the EXPORTED artifacts (STL/STEP on disk), never on constants.

What is imported from the macro, and why:
  * pose travel (placement: a gate must share the placement it tests, docs/lessons.md)
  * nominal bore/probe origins and spans: used ONLY as ray origins / sampling ranges; every reported axis,
    wall and gap is measured on the meshes
  * ring file paths, for the outline-survival comparison
Every number printed below is computed in this run. Nothing is a literal.

Run: python "D:\\CAD\\Claude-Projects\\projects\\SurgicalDrillGuide\\macros\\sdg_gates.py"
"""
import math
import sys
from pathlib import Path

import numpy as np
import shapely
import trimesh
from shapely import affinity
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import surgical_drill_guide as sdg  # noqa: E402  (guarded: importing does not export)

from build123d import import_step  # noqa: E402

D, TRAVEL, CHAN, TEETH, BORE, THREAD, BOSS, PAWL = sdg.parameters()
WY = D["wire_y"]
ZM = sdg.Z_MID
PIN = D["pin"]
CT = D["ctip"]
PARTS = ["main_frame", "l_arm_slider", "handle", "end_stop_pin"]


def load(name):
    return trimesh.load(str(sdg.part_path(name, "stl")), force="mesh")


def hits_along(mesh, origin, direction):
    d = np.asarray(direction, float)
    d /= np.linalg.norm(d)
    loc, _, _ = mesh.ray.intersects_location([origin], [d], multiple_hits=True)
    if len(loc) == 0:
        return np.array([])
    return np.sort((loc - origin) @ d)


def first_hit(mesh, origin, direction, max_d=1e9):
    t = hits_along(mesh, origin, direction)
    t = t[t > 1e-6]
    return float(t[0]) if len(t) and t[0] <= max_d else None


def fit_circle(pts):
    x, y = pts[:, 0], pts[:, 1]
    A = np.c_[2 * x, 2 * y, np.ones(len(x))]
    b = x ** 2 + y ** 2
    (cx, cy, c), *_ = np.linalg.lstsq(A, b, rcond=None)
    r = math.sqrt(c + cx ** 2 + cy ** 2)
    rms = float(np.sqrt(np.mean((np.hypot(x - cx, y - cy) - r) ** 2)))
    return cx, cy, r, rms


def bore_centre(mesh, x, y0, z0):
    """Probe a bore along X at station x (rays in the YZ plane, skipping the teardrop point)."""
    pts = []
    for th in np.radians(np.arange(60, 301, 10)):
        d = np.array([0.0, math.sin(th), math.cos(th)])
        h = first_hit(mesh, np.array([x, y0, z0]), d, max_d=6.0)
        if h is not None:
            pts.append([y0 + h * d[1], z0 + h * d[2]])
    pts = np.array(pts)
    if len(pts) < 8:
        return None
    cy, cz, r, rms = fit_circle(pts)
    return cy, cz, r, rms, len(pts)


def fit_line(P):
    c = P.mean(axis=0)
    _, _, vt = np.linalg.svd(P - c)
    d = vt[0] if vt[0][0] > 0 else -vt[0]
    return c, d


def ring_poly(name):
    return Polygon(sdg.ring_points(name))


def section_poly(mesh, z):
    s = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if s is None:
        return Polygon()
    p2, T = s.to_2D()
    out = []
    for p in p2.polygons_full:
        def back(c):
            c = np.asarray(c)
            h = np.c_[c, np.zeros(len(c)), np.ones(len(c))]
            return (T @ h.T).T[:, :2]
        out.append(Polygon(back(p.exterior.coords), [back(h.coords) for h in p.interiors]))
    return unary_union(out)


def section_y_xz(mesh, y):
    """Y-normal section as a shapely (X, Z) polygon (round 5: pad-to-carriage true 2D minimum)."""
    s = mesh.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0])
    if s is None:
        return Polygon()
    p2, T = s.to_2D()
    out = []
    for p in p2.polygons_full:
        def back(c):
            c = np.asarray(c)
            h = np.c_[c, np.zeros(len(c)), np.ones(len(c))]
            return (T @ h.T).T[:, [0, 2]]
        out.append(Polygon(back(p.exterior.coords), [back(h.coords) for h in p.interiors]))
    return unary_union(out)


def boundary_samples(poly, step=0.25):
    pts = []
    for g in getattr(poly, "geoms", [poly]):
        for ring in [g.exterior] + list(g.interiors):
            for s in np.arange(0, ring.length, step):
                pts.append(ring.interpolate(s))
    return pts


def outline_survival(tag, ring, sec, excl):
    sb = sec.boundary
    d_keep, n_ex = [], 0
    for p in boundary_samples(ring):
        if any(z.contains(p) for z in excl):
            n_ex += 1
        else:
            d_keep.append(p.distance(sb))
    d_keep = np.array(d_keep)
    sym = ring.symmetric_difference(sec).area
    print(f"  {tag:36s} ring area {ring.area:9.2f}  section area {sec.area:9.2f}  sym-diff {sym:8.2f} mm2  "
          f"Hausdorff(all) {ring.boundary.hausdorff_distance(sec.boundary):6.3f}")
    print(f"  {'':36s} ring-boundary samples kept {len(d_keep)} (excluded in feature zones {n_ex}): "
          f"max {d_keep.max():.4f}  p95 {np.percentile(d_keep, 95):.4f}  mean {d_keep.mean():.4f} mm")


def box2(x0, x1, y0, y1):
    return Polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])


def teardrop_poly(y, z, d, grow=0.0):
    r = d / 2.0
    s = r / math.sqrt(2)
    tri = Polygon([(y + s, z + s), (y, z + r * math.sqrt(2)), (y - s, z + s)])
    return Point(y, z).buffer(r, quad_segs=64).union(tri).buffer(grow)


def bore_wall(mesh, x_in, x_out, step=0.25, n_perim=48, y=None, z=None):
    """PERPENDICULAR wall round a bore along X: 3D distance from bore-surface points to the nearest non-bore
    face, using only faces inside the enclosed span x_in..x_out (the mouth planes and anything beyond them are
    the openings, not walls). Returns (stations, per-station minimum)."""
    y = WY if y is None else y
    z = ZM if z is None else z
    cen = mesh.triangles_center
    span = (cen[:, 0] > x_in + 1e-3) & (cen[:, 0] < x_out - 1e-3)
    td = teardrop_poly(y, z, sdg.BORE_D, grow=0.02)
    on_bore = shapely.contains_xy(td, cen[:, 1], cen[:, 2])
    idx = np.where(span & ~on_bore)[0]
    sub = mesh.submesh([idx], append=True)
    per = teardrop_poly(y, z, sdg.BORE_D).exterior
    ring = [per.interpolate(per.length * k / n_perim) for k in range(n_perim)]
    xs = np.arange(x_in + step, x_out - step + 1e-9, step)
    pts = np.array([[x, p.x, p.y] for x in xs for p in ring])
    _, dist, _ = trimesh.proximity.closest_point(sub, pts)
    dist = dist.reshape(len(xs), n_perim)
    return xs, dist.min(axis=1)


# ═════════════════════════════════════════════════════════════════════════════
print("=" * 100)
print("GATE 1: per-part solid validity (STEP on disk) and STL topology")
meshes = {}
for name in PARTS:
    st = import_step(str(sdg.part_path(name, "step")))
    sols = st.solids()
    m = load(name)
    meshes[name] = m
    comps = m.split(only_watertight=False)
    n_void = sum(1 for c in comps if c.volume <= 0)
    print(f"  {name:13s} STEP solids {len(sols)} valid {all(s.is_valid for s in sols)} vol {sum(s.volume for s in sols):10.2f} | "
          f"STL watertight {m.is_watertight} winding {m.is_winding_consistent} shells {len(comps)} "
          f"(sealed voids {n_void}) vol {m.volume:10.2f} euler {m.euler_number} faces {len(m.faces)}")
    b = m.bounds
    print(f"  {'':13s} bbox X {b[0][0]:.3f}..{b[1][0]:.3f}  Y {b[0][1]:.3f}..{b[1][1]:.3f}  Z {b[0][2]:.3f}..{b[1][2]:.3f}")
fr, sl, hd, pn = (meshes[k] for k in PARTS)

# Z layout of the slider (user decision: one 16.6 slab)
for x, lab in ((65.0, "riser"), (100.0, "top bar"), (136.5, "crown")):
    yy = 20.0 if lab == "riser" else 54.5
    zz = 30.0 - hits_along(sl, np.array([x, yy, 30.0]), [0, 0, -1])
    print(f"  slider Z at {lab:7s} (X {x}, Y {yy}): surfaces Z {np.round(zz, 3).tolist()}")
for x in (100.0, 122.311, 140.0):
    zz = 30.0 - hits_along(fr, np.array([x, -4.0, 30.0]), [0, 0, -1])
    print(f"  frame Z at bar X {x:7.3f} (Y -4): surfaces Z {np.round(zz, 3).tolist()}")
# Boss-pad taper (round 3 gate): per-face Z excess along X on vertical Z rays at Y -5, fitted on the taper
for yy in (-1.0, -5.0, -8.5):
    res = []
    for side, xa, xb in (("-X", BOSS["pad_x0"] - 0.6, BOSS["pad_x0"] + BOSS["pad_blend"] + 0.6),
                         ("+X", BOSS["pad_x1"] - BOSS["pad_blend"] - 0.6, BOSS["pad_x1"] + 0.6)):
        P = []
        for x in np.arange(xa, xb, 0.02):
            h = hits_along(fr, np.array([x, yy, -30.0]), [0, 0, 1])
            if len(h):
                P.append((x, -(-30.0 + h[0])))
        P = np.array(P)
        e_max = (BOSS["od"] - sdg.T_Z) / 2.0
        m_ = (P[:, 1] > 0.3) & (P[:, 1] < e_max - 0.3)
        k_, c_ = np.polyfit(P[m_, 0], P[m_, 1], 1)
        x0_, x1_ = -c_ / k_, (e_max - c_) / k_
        res.append(f"{side}: slope {abs(k_):.3f} ({math.degrees(math.atan(abs(k_))):.1f}°), Z-face at X {x0_:.3f}, full at "
                   f"X {x1_:.3f}, length {abs(x1_ - x0_):.3f}")
    print(f"  BOSS PAD taper (Y {yy}): " + "; ".join(res) + f"  [constants: {BOSS['pad_blend']} mm, "
          f"{BOSS['taper_deg']:.1f}°, from X {BOSS['pad_x0']:.3f} / to {BOSS['pad_x1']:.3f}]")

# ═════════════════════════════════════════════════════════════════════════════
print("=" * 100)
print("GATE 2: through-holes (rays from BOTH ends) and open cavities")


def wire_rays(mesh, x_from, x_to, radius, n=16):
    tot, per = 0, []
    for k in range(n):
        a = 2 * math.pi * k / n
        o = np.array([x_from, WY + radius * math.sin(a), ZM + radius * math.cos(a)])
        h = hits_along(mesh, o, [np.sign(x_to - x_from), 0, 0])
        h = h[(h > 0) & (h < abs(x_to - x_from))]
        per.append(len(h))
        tot += len(h)
    return tot, per


for tag, mesh, xa, xb in (("slider wire bore", sl, D["wire_x0"] - 10, D["wire_x1"] + 10),
                          ("frame C-tip bore", fr, CT["x_entry"] - 10, CT["x_exit"] + 10)):
    for (x0, x1, lab) in ((xa, xb, "+X"), (xb, xa, "-X")):
        axis_hits = hits_along(mesh, np.array([x0, WY, ZM]), [np.sign(x1 - x0), 0, 0])
        axis_hits = axis_hits[(axis_hits > 0) & (axis_hits < abs(x1 - x0))]
        r15, _ = wire_rays(mesh, x0, x1, sdg.WIRE_D / 2)
        r16, _ = wire_rays(mesh, x0, x1, sdg.REAM_D / 2)
        r17, per17 = wire_rays(mesh, x0, x1, 1.85)
        print(f"  {tag:18s} dir {lab}: axis-ray hits {len(axis_hits)}; r 1.50 (Ø3.0) hits {r15}; r 1.60 (Ø3.2) hits {r16};"
              f" control r 1.85 hits {r17} ({sum(1 for q in per17 if q)}/16 rays)")
yc = 0.5 * (CHAN["y0"] + CHAN["y1"])
h = hits_along(sl, np.array([D["collar_x0"] - 5, yc, ZM]), [1, 0, 0])
h = h[(h > 0) & (h < D["carriage_x1"] - D["collar_x0"] + 10)]
print(f"  rack channel (Y {yc:.2f}, Z {ZM}) along +X through the slider: hits {len(h)}")
o = np.array([D["handle_axis_x"], D["ferrule_top_y"] - 15, ZM])
hy = first_hit(fr, o, [0, 1, 0])
print(f"  female thread hole: ray up the axis: first frame hit at Y {o[1] + hy:.3f} (mouth {D['ferrule_top_y']:.3f})")
hz = hits_along(fr, np.array([PIN["x"], PIN["y"], -10.0]), [0, 0, 1])
hz = hz[hz < 30]
print(f"  pin hole: axis ray along +Z through the frame: {len(hz)} hits; rays at r {PIN['d'] / 2:.2f} (pin surface): "
      f"{sum(len(hits_along(fr, np.array([PIN['x'] + PIN['d'] / 2 * math.cos(a), PIN['y'] + PIN['d'] / 2 * math.sin(a), -10.0]), [0, 0, 1])) for a in np.linspace(0, 2 * math.pi, 16, endpoint=False))} hits")

# ═════════════════════════════════════════════════════════════════════════════
print("=" * 100)
print("GATE 3: traced outline survives (section vs DXF ring). Excluded zones = designed features, listed.")
yb = lambda x: sdg.rack_bottom_y(D, x)
fr_ring = ring_poly("frame")
teeth_zone = box2(TEETH["x0"] - 0.5, TEETH["x1"] + 0.5, -12, yb(TEETH["x1"]) + TEETH["depth"] + 0.3)
boss_zone = box2(D["handle_axis_x"] - BOSS["od"] / 2 - 0.5, D["handle_axis_x"] + BOSS["od"] / 2 + 0.5, -25, D["bar_bottom_at_axis"] + 0.3)
pad_zone = box2(CT["x_entry"] - 0.3, CT["x_exit"] + 0.3, WY - CT["half_h"] - CT["blend_r"] - 1, WY + CT["half_h"] + CT["blend_r"] + 1)
bore_zone = box2(BORE["ctip_x0"], BORE["ctip_x1"], WY - sdg.BORE_D / 2 - 0.3, WY + sdg.BORE_D / 2 + 0.3)
bx0 = D["rack_bottom_line"][0]
ext_zone = box2(D["rack_tip_x"] - 1.0, bx0 + 0.6, -12, 1.0)
for z in (1.0, ZM):
    sec = section_poly(fr, z)
    outline_survival(f"main_frame  Z={z}", fr_ring, sec,
                     [teeth_zone, boss_zone, pad_zone, ext_zone] + ([bore_zone] if z == ZM else []))
# RACK EXTENSION = allowed, documented deviation: measured on the STL section at Z 5 (teeth band excluded by
# comparing above the notch-apex line) and the free-end X extent
secx = section_poly(fr, ZM).intersection(box2(-20, 6, -8.0, 1.0))
ringx = fr_ring.intersection(box2(-20, 6, -8.0, 1.0))
addx = secx.difference(fr_ring)
print(f"  RACK EXTENSION: STL free end X {fr.bounds[0][0]:.3f} vs traced {min(q[0] for q in sdg.ring_points('frame')):.3f} "
      f"-> length added {min(q[0] for q in sdg.ring_points('frame')) - fr.bounds[0][0]:.3f} mm; area added above the teeth band "
      f"(Y > -8) {addx.area:.2f} mm2; traced material lost there {ringx.difference(secx).area:.4f} mm2 (the pin hole is"
      f" at X {PIN['x']:.3f}, fully in the extension: {PIN['x'] + PIN['hole_d'] / 2 < min(q[0] for q in sdg.ring_points('frame')) + 1.0})")
for x in (-3.0, -1.0, 1.0, 5.0, 30.0):
    c = sdg.vertical_chord(section_poly(fr, 1.0), x)
    print(f"  rack section at X {x:6.2f} (Z=1, measured on STL): Y {c[0]:.3f} .. {c[1]:.3f} (height {c[1] - c[0]:.3f})")
# the entry ledge: traced end-face material in front of the jaw face, below the wire, cut by the bore (open trough)
ledge = fr_ring.intersection(box2(140, CT["x_entry"], WY - 5, WY + 5)).difference(section_poly(fr, ZM))
print(f"  entry-ledge trough (traced material in front of the jaw face removed by the bore at Z=5): {ledge.area:.3f} mm2, "
      f"X {ledge.bounds[0]:.3f}..{ledge.bounds[2]:.3f}" if not ledge.is_empty else "  entry-ledge trough: none")
# C-tip pad = allowed, documented deviation: measure it on the STL section (Z 1, below the bore)
sec1f = section_poly(fr, 1.0)
win = box2(140, 175, 38, 62)
added = sec1f.intersection(win).difference(fr_ring)
added = unary_union([g for g in getattr(added, "geoms", [added]) if g.area > 1e-3])
offs = [p.distance(fr_ring) for p in boundary_samples(added, 0.05)]
removed = fr_ring.intersection(win).difference(sec1f).area
print(f"  C-tip PAD deviation (STL Z=1 vs ring): added {added.area:.2f} mm2 in {len(getattr(added, 'geoms', [added]))} region(s),"
      f" max offset from the traced outline {max(offs):.3f} mm; traced material removed {removed:.4f} mm2")

la, co, ca = ring_poly("l_arm"), ring_poly("collar"), ring_poly("carriage")
chan_zone = box2(D["collar_x0"] - 1, D["carriage_x1"] + 1, CHAN["y0"] - 0.3, CHAN["y1"] + 0.3)
ST = PAWL["stop"]
beam_bot = PAWL["tab_bottom_y"] - PAWL["pad_t"] + 0.5 - ST["relief"] - ST["beam_t"]
pawl_zone = box2(PAWL["anchor_x"] - 0.5, D["carriage_x1"] + 0.5, beam_bot - 1.0, PAWL["window_top_y"] + 0.3)
ctop_zone = box2(D["carriage_x0"] - 0.5, D["carriage_x1"] + 0.5, D["carriage_y1"] - 1.2,
                 CHAN["y1"] + sdg.CARRIAGE_TOP_WALL + 0.3)
slbore_zone = box2(D["wire_x0"] - 1, D["wire_x1"] + 1, WY - sdg.BORE_D / 2 - 0.3, WY + sdg.BORE_D / 2 + 0.3)
junction_zone = box2(D["riser_x0"] - 1.5, D["riser_x1"] + 1.5, D["riser_base_y"] - 2, D["riser_base_y"] + 0.6)
allL = unary_union([la, co, ca])
# Round 4 designed zones: the thickened floor (CARRIAGE_FLOOR) and the squared/trimmed +X end.
floor_zone = box2(D["carriage_x0"] - 2.0, D["carriage_x1"] + 0.5, CHAN["y0"] - sdg.CARRIAGE_FLOOR - 0.3,
                  D["carriage_bottom_max"] + 0.3)
end_zone = box2(D["carriage_end_x"] - 1.2, D["carriage_x1"] + 0.5, CHAN["y0"] - sdg.CARRIAGE_FLOOR - 0.3,
                CHAN["y1"] + sdg.CARRIAGE_TOP_WALL + 0.3)
for z, ex in ((-2.0, [pawl_zone, junction_zone]), (1.0, [chan_zone, pawl_zone, junction_zone]),
              (ZM, [chan_zone, pawl_zone, junction_zone, slbore_zone]), (12.0, [pawl_zone, junction_zone])):
    outline_survival(f"l_arm_slider Z={z} vs L∪collar∪carriage", allL, section_poly(sl, z),
                     ex + [ctop_zone, floor_zone, end_zone])
# CARRIAGE FLOOR / END (round 4): wall below the channel floor on vertical rays at Z 5, and the end face X
fl = []
for x in (70.5, 72.0, 72.3, 73.0, 80.0, 90.0, 95.5, 100.0, 103.0, 106.0, 106.45):
    yy = 10.0 - hits_along(sl, np.array([x, 10.0, ZM]), [0, -1, 0])
    yy = yy[yy < CHAN["y0"] + 0.01]
    fl.append(f"X {x}: {yy[0] - yy[1]:.3f}" if len(yy) > 1 else f"X {x}: -")
print(f"  carriage FLOOR under the channel (vertical rays, Z 5; tongue X {PAWL['anchor_x']}..{PAWL['free_x']}, leg "
      f"~{D['carriage_end_x'] - ST['leg_w']:.1f}..{D['carriage_end_x']:.1f} continue down): " + "; ".join(fl))
# Round 5: rays cover the stop leg too (beam bottom up to the top wall), so a leg face behind the end shows.
ends, ends_leg = [], []
y_floor = CHAN["y0"] - sdg.CARRIAGE_FLOOR
for yy in np.linspace(beam_bot + 0.05, CHAN["y1"] + sdg.CARRIAGE_TOP_WALL - 0.05, 41):
    for zz in (-3.0, 12.9):
        h = first_hit(sl, np.array([130.0, yy, zz]), [-1, 0, 0])
        ends.append(130.0 - h)
        if yy < y_floor:
            ends_leg.append(130.0 - h)
print(f"  carriage +X END face (41 rows Y {beam_bot + 0.05:.2f}..{CHAN['y1'] + sdg.CARRIAGE_TOP_WALL - 0.05:.2f}, "
      f"Z -3 / 12.9): X {min(ends):.4f}..{max(ends):.4f}; leg rows (Y < floor {y_floor:.2f}) "
      f"X {min(ends_leg):.4f}..{max(ends_leg):.4f}; step {max(ends) - min(ends):.4f} "
      f"(derived {D['carriage_end_x']:.4f}; traced max {D['carriage_x1']:.3f})")
# CARRIAGE TOP WALL (round 3, accepted deviation): added outline and the wall over the ceiling, on the STL
secS = section_poly(sl, ZM)
addc = secS.intersection(ctop_zone).difference(allL)
addc = unary_union([g for g in getattr(addc, "geoms", [addc]) if g.area > 1e-4])
offc = [p.distance(allL) for p in boundary_samples(addc, 0.02)]
top_x = np.array([p.distance(allL) for p in boundary_samples(addc, 0.02) if p.x < D["carriage_x1"] - 1.0])
print(f"  CARRIAGE TOP deviation (STL Z=5 vs rings): added {addc.area:.3f} mm2; max offset from the traced outline "
      f"{max(offc):.3f} mm (whole zone incl. the squared +X corner), {top_x.max():.3f} mm along the top (X < "
      f"{D['carriage_x1'] - 1.0:.2f}); traced material removed {allL.intersection(ctop_zone).difference(secS).area:.4f} mm2")
walls = []
for x in (72.0, 80.0, 90.0, 100.0, 105.0, 106.0, 106.3, 106.45):
    ys = 10.0 - hits_along(sl, np.array([x, 10.0, ZM]), [0, -1, 0])
    walls.append(f"X {x}: {ys[0] - ys[1]:.3f}")
print(f"  carriage top wall over the ceiling (vertical rays, Z 5): " + "; ".join(walls))
sec1 = section_poly(sl, 1.0)
upper = sec1.intersection(box2(50, 150, D["riser_base_y"] + 0.01, 70))
la_up = la.intersection(box2(50, 150, D["riser_base_y"] + 0.01, 70))
print(f"  L-arm ring alone (above collar) Z=1: sym-diff {la_up.symmetric_difference(upper).area:.4f} mm2, "
      f"Hausdorff {la_up.exterior.hausdorff_distance(upper.boundary):.4f} mm")
la_img = Polygon(sdg.ring_points_file("l_arm_body_as_imaged.dxf")).intersection(box2(50, 150, D["riser_base_y"] + 0.01, 70))
outline_survival("CONTROL: Z=1 vs AS-IMAGED L ring", la_img, upper, [junction_zone, slbore_zone])
gh, fh = ring_poly("grip_half"), ring_poly("ferrule_half")
ax = D["handle_axis_x"]
silh = unary_union([gh, affinity.scale(gh, -1, 1, origin=(ax, 0)), fh, affinity.scale(fh, -1, 1, origin=(ax, 0))])
rT = THREAD["r_crest"]
thread_zone = box2(ax - rT - 1, ax + rT + 1, D["ferrule_top_y"] - 0.2, D["ferrule_top_y"] + sdg.THREAD_ENGAGE + 1)
core_zone = box2(ax - rT - 0.5, ax + rT + 0.5, D["grip_top_y"] - sdg.HANDLE_CORE_GRIP_DEPTH - 0.5, D["ferrule_top_y"] + 0.2)
butt_zone = box2(ax - 8, ax + 8, -150, hd.bounds[0][1] + 0.1)
SEAT = THREAD["seat"]
y_c1 = D["ferrule_top_y"] - SEAT["collar_t"] - (SEAT["collar_r"] - SEAT["taper_r"])
collar_zone = box2(ax - SEAT["collar_r"] - 0.5, ax + SEAT["collar_r"] + 0.5, y_c1 - 0.5, D["ferrule_top_y"] + 0.2)
secH = section_poly(hd, ZM)
outline_survival("handle Z=5 (axis plane) vs halves+mirror", silh, secH, [thread_zone, core_zone, butt_zone,
                                                                          collar_zone])
# HANDLE COLLAR (round 4, user decision, deviation): section width at the face and under it, vs the trace
addcol = secH.intersection(collar_zone).difference(silh)
cw = [(y, sdg.horizontal_chord(secH, y)) for y in (D["ferrule_top_y"] - 0.02, D["ferrule_top_y"] - SEAT["collar_t"] + 0.02,
                                                    D["ferrule_top_y"] - SEAT["collar_t"] - 2.0, y_c1 - 0.3)]
print(f"  HANDLE COLLAR deviation (STL Z=5): added {addcol.area:.2f} mm2 over the traced silhouette; radius at "
      + "; ".join(f"Y {y:.2f}: {(c[1] - c[0]) / 2:.3f}" for y, c in cw if c))
# HANDLE CORE (round 3, deviation): the Ø(major) core replaces the traced ferrule + Ø8 neck bridge
addh = secH.intersection(core_zone).difference(silh)
addh = unary_union([g for g in getattr(addh, "geoms", [addh]) if g.area > 1e-4])
offh = [p.distance(silh) for p in boundary_samples(addh, 0.05)]
fer = [sdg.horizontal_chord(fh, y) for y in np.linspace(D["ferrule_bot_y"] + 0.5, D["ferrule_top_y"] - 0.5, 40)]
fer_r = [c[1] - ax for c in fer if c]
secr = [sdg.horizontal_chord(secH, y) for y in np.linspace(D["grip_top_y"] - 0.5, D["ferrule_top_y"] - 0.2, 60)]
print(f"  HANDLE CORE deviation (STL Z=5): traced ferrule r {min(fer_r):.3f}..{max(fer_r):.3f}; STL radius from the grip"
      f" top to the shoulder min {min((c[1] - c[0]) / 2 for c in secr if c):.3f}; added {addh.area:.2f} mm2, max offset"
      f" {max(offh):.3f} mm from the traced silhouette; traced removed {silh.intersection(core_zone).difference(secH).area:.4f} mm2")

# ═════════════════════════════════════════════════════════════════════════════
print("=" * 100)
print("GATE 4: wall round the C-tip bore, PERPENDICULAR (3D closest-face distance), whole enclosed span")
xs, wmin = bore_wall(fr, CT["x_entry"], CT["x_exit"])
print(f"  enclosed span X {CT['x_entry']:.3f} .. {CT['x_exit']:.3f} ({CT['x_exit'] - CT['x_entry']:.2f} mm), {len(xs)} stations x 48 points")
print("  X      " + " ".join(f"{x:6.2f}" for x in xs[::4]))
print("  wall   " + " ".join(f"{w:6.3f}" for w in wmin[::4]))
k = int(np.argmin(wmin))
print(f"  MIN WALL {wmin.min():.3f} mm at X {xs[k]:.2f}; stations below 1.5 mm: {int((wmin < 1.5).sum())} of {len(xs)}")
# Z walls at the tip centre
xc = 0.5 * (CT["x_entry"] + CT["x_exit"])
zs = 30.0 - hits_along(fr, np.array([xc, WY, 30.0]), [0, 0, -1])
print(f"  Z walls at X {xc:.2f}: surfaces Z {np.round(zs, 3).tolist()} -> top {zs[0] - zs[1]:.3f}, bottom {zs[2] - zs[3]:.3f}")
print(f"  wire line to C-tip top point: {fr.bounds[1][1] - WY:.3f} mm")
# CONTROL: the same measure on the slider bore (form-auditor measured 1.40 at X 136.0, the crown exit)
xs_c, w_c = bore_wall(sl, D["wire_x0"], 136.25)
kc = int(np.argmin(w_c))
print(f"  CONTROL (same code, slider bore X {D['wire_x0']:.2f}..136.25): min {w_c.min():.3f} at X {xs_c[kc]:.2f}; "
      f"at X 100: {w_c[np.argmin(abs(xs_c - 100))]:.3f}")

# Pin hole walls (round 3 fix). Measured on the STL SECTION at Z 5: for each of 360 points on the hole
# boundary, the distance to the section's outer boundary; reported as the minimum in 90° sectors centred on each
# direction, and as the straight ray wall along each cardinal direction.
sec5 = section_poly(fr, ZM)
hole_pt = Point(PIN["x"], PIN["y"])
host = [g for g in getattr(sec5, "geoms", [sec5]) if g.buffer(1e-6).contains(hole_pt.buffer(PIN["hole_d"] / 2 + 0.2))
        or g.distance(hole_pt) < PIN["hole_d"]][0]
hole_ring = min(host.interiors, key=lambda r: r.centroid.distance(hole_pt))
ext = host.exterior
angs = np.radians(np.arange(0, 360, 1.0))
hr = Polygon(hole_ring).area and math.sqrt(Polygon(hole_ring).area / math.pi)
wall_a = np.array([Point(PIN["x"] + hr * math.cos(a), PIN["y"] + hr * math.sin(a)).distance(ext) for a in angs])
line = lambda a, L: shapely.geometry.LineString([(PIN["x"] + hr * math.cos(a), PIN["y"] + hr * math.sin(a)),
                                                 (PIN["x"] + (hr + L) * math.cos(a), PIN["y"] + (hr + L) * math.sin(a))])
out = []
for lab, c in (("end -X", 180), ("top +Y", 90), ("teeth -Y", 270), ("hook +X", 0)):
    sect = np.array([wall_a[int(d) % 360] for d in range(c - 45, c + 46)])
    k = int(np.argmin(sect))
    g = line(math.radians(c), 30.0).intersection(ext)
    pts_ = [g] if g.geom_type == "Point" else list(getattr(g, "geoms", []))
    ray = min(Point(PIN["x"] + hr * math.cos(math.radians(c)), PIN["y"] + hr * math.sin(math.radians(c))).distance(q)
              for q in pts_) if pts_ else float("nan")
    out.append(f"{lab}: ray {ray:.3f}, sector min {sect.min():.3f} at {c - 45 + k}°")
print(f"  PIN HOLE (STL section Z 5): equivalent Ø {2 * hr:.3f} at X {PIN['x']:.3f} Y {PIN['y']:.3f}; min wall "
      f"{wall_a.min():.3f} at {int(np.degrees(angs[int(np.argmin(wall_a))]))}°")
print("  " + "; ".join(out))
# CONTROL: the round-2 method (triangles filtered by CENTROID distance < 15 mm). Long faces (rack top, rack
# bottom) have far centroids and are dropped, so it reads the walls too thick.
cen = fr.triangles_center
near = np.hypot(cen[:, 0] - PIN["x"], cen[:, 1] - PIN["y"])
idx = np.where((near > PIN["hole_d"] / 2 + 0.02) & (near < 15))[0]
sub = fr.submesh([idx], append=True)
angs = np.linspace(0, 2 * math.pi, 72, endpoint=False)
# sample at mid-thickness only: near Z 0 / 10 the nearest faces are the rack's own Z faces (the hole mouths)
pts = np.array([[PIN["x"] + PIN["hole_d"] / 2 * math.cos(a), PIN["y"] + PIN["hole_d"] / 2 * math.sin(a), ZM]
                for a in angs])
sub = sub.slice_plane([0, 0, 0.5], [0, 0, 1]).slice_plane([0, 0, 9.5], [0, 0, -1])
_, dist, cp = trimesh.proximity.closest_point(sub, pts)
dirs = {"to rack free end (-X)": 180, "to rack top (+Y)": 90, "to teeth (-Y)": 270, "towards hook (+X)": 0}
print(f"  CONTROL old centroid-filtered method: min {dist.min():.3f} mm "
      f"(at {math.degrees(angs[int(np.argmin(dist))]):.0f}°); " +
      "; ".join(f"{k} {dist[int(round(v / 5)) % 72]:.3f}" for k, v in dirs.items()))
print(f"  rack height at the pin X: {PIN['y_top'] - yb(PIN['x']):.3f} (top {PIN['y_top']:.3f}, envelope {yb(PIN['x']):.3f},"
      f" notch apex line {PIN['y_apex']:.3f}); first notch wall X {TEETH['x0']:.3f} vs hole X {PIN['x'] - PIN['hole_d'] / 2:.3f}..{PIN['x'] + PIN['hole_d'] / 2:.3f}")

# ═════════════════════════════════════════════════════════════════════════════
print("=" * 100)
print("GATE 5: assembly at MIN / MID / MAX (measured on the written assembly STLs)")
a_list = sdg.sawtooth_cutter_face(yb, TEETH["x0"], TEETH["x1"], TEETH["pitch"], TEETH["depth"], TEETH["land"], TEETH["eps"])[1]
a_seat = sdg.seat_notch(a_list, PAWL, D)[0]


def inter(a, b):
    try:
        r = trimesh.boolean.intersection([a, b], engine="manifold")
        return float(r.volume) if r is not None and len(r.faces) else 0.0
    except Exception as e:
        return f"ERR {e}"


for pose, t in TRAVEL.items():
    A = trimesh.load(str(sdg.part_path(f"assembly_{pose}", "stl")), force="mesh")
    # Round 4: the seated collar shares its r 11 edge circle with the boss face, so loading the assembly STL merges
    # frame and handle vertices there and split() can no longer separate the parts (it returned 5 non-volume
    # components). The parts are therefore the per-part STLs placed by the macro's own slider_at() transform (same
    # datum as the assembly export); the assembly STL on disk is cross-checked against them (volume + rays).
    frame_c, handle_c, pin_c = load("main_frame"), load("handle"), load("end_stop_pin")
    loc_ = sdg.slider_at(sdg.Solid.make_box(1, 1, 1), t).location.position
    slider_p = load("l_arm_slider")
    slider_p.apply_translation([loc_.X, loc_.Y, loc_.Z])
    rest = [slider_p]
    P_ = trimesh.util.concatenate([frame_c, slider_p, handle_c, pin_c])
    xr = [bool(np.allclose(hits_along(A, o_, [0, 1, 0]), hits_along(P_, o_, [0, 1, 0]), atol=1e-3))
          for o_ in [np.array([x_ - t, -40.0, z_]) for x_ in (65.0, 80.0, 100.0, 105.0) for z_ in (-2.0, ZM, 12.0)]]
    print(f"   assembly STL on disk vs placed parts: volume {A.volume:.1f} vs {P_.volume:.1f}; 12 vertical rays "
          f"through the slider agree: {sum(xr)}/12 (slider offset X {loc_.X:.3f})")
    comps = [frame_c, slider_p, handle_c, pin_c]
    print(f"--- {pose.upper()}  travel {t:.3f} mm ({sdg.D_POSE if hasattr(sdg, 'D_POSE') else D['pose_teeth'][pose]} teeth)"
          f"   components {len(comps)} (frame {frame_c.volume:.1f}, slider {sum(c.volume for c in rest):.1f}, "
          f"handle {handle_c.volume:.1f}, pin {pin_c.volume:.1f})")
    slider_c = rest[0]

    s_st = [x - t for x in (64.0, 80.0, 100.0, 120.0, 134.0)]
    c_st = list(np.linspace(CT["x_entry"] + 1.0, CT["x_exit"] - 1.0, 5))
    Ps, Pc, rs, rc = [], [], [], []
    for x in s_st:
        q = bore_centre(A, x, WY, ZM)
        Ps.append([x, q[0], q[1]]); rs.append((q[2], q[3]))
    for x in c_st:
        q = bore_centre(A, x, WY, ZM)
        Pc.append([x, q[0], q[1]]); rc.append((q[2], q[3]))
    Ps, Pc = np.array(Ps), np.array(Pc)
    cs, ds = fit_line(Ps)
    cc, dc = fit_line(Pc)
    ang = math.degrees(math.acos(min(1.0, abs(float(ds @ dc)))))
    xm = float(np.mean(Pc[:, 0]))
    ps_at = cs + ds * ((xm - cs[0]) / ds[0])
    pc_at = cc + dc * ((xm - cc[0]) / dc[0])
    off = float(np.hypot(*(pc_at[1:] - ps_at[1:])))
    print(f"   bores fitted: slider r {min(r for r, _ in rs):.3f}..{max(r for r, _ in rs):.3f}, C-tip r {min(r for r, _ in rc):.3f}.."
          f"{max(r for r, _ in rc):.3f} (rms <= {max(e for _, e in rs + rc):.4f})")
    print(f"   COAXIALITY at X {xm:.2f}: radial offset {off:.4f} mm, angle {ang:.4f} deg")
    o = cs + ds * ((-30.0 - cs[0]) / ds[0])
    print(f"   axis ray from X -30 along the fitted slider axis: {len(hits_along(A, o, ds))} hits in the whole assembly")
    u = np.cross(ds, [0, 0, 1.0]); u /= np.linalg.norm(u)
    v = np.cross(ds, u)
    n_hit = sum(len(hits_along(A, o + 1.5 * (math.cos(a) * u + math.sin(a) * v), ds)) for a in np.linspace(0, 2 * math.pi, 16, endpoint=False))
    print(f"   16 rays on the Ø3.0 wire surface: {n_hit} hits")
    enc = [x for x in np.arange(140.0, 172.0, 0.1)
           if all(first_hit(frame_c, cs + ds * ((x - cs[0]) / ds[0]), dd, max_d=8.0) is not None
                  for dd in ([0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]))]
    print(f"   axis enclosed by the C-tip: X {min(enc):.2f} .. {max(enc):.2f}" if enc else "   NOT enclosed by the C-tip")
    print(f"   interference: slider∩frame {inter(slider_c, frame_c)}; handle∩frame {inter(handle_c, frame_c)}; "
          f"handle∩slider {inter(handle_c, slider_c)}; pin∩slider {inter(pin_c, slider_c)}; pin∩frame {inter(pin_c, frame_c)} mm3")
    for zz in (1.0, sdg.T_Z - 1.0):
        oo = np.array([D["wire_x1"] - t - 20.0, WY, zz])
        hs = hits_along(slider_c, oo, [1, 0, 0])
        hf = hits_along(frame_c, oo, [1, 0, 0])
        print(f"   tip gap at wire height (Z {zz}): crown X {oo[0] + hs[-1]:.3f} -> C-tip X {oo[0] + hf[hf > hs[-1]][0]:.3f} "
              f"= {hf[hf > hs[-1]][0] - hs[-1]:.3f} mm")

    # Pawl (hooked, round 3). Profiles on vertical rays at Z 5: T(x) = slider top below Y -7 (tooth / tongue),
    # F(x) = first frame surface from below (rack lower envelope, incl. the hooked lips).
    a_now = a_seat - t
    dx_ = 0.01
    xg = np.arange(a_now - 2.6, a_now + 4.0, dx_)

    def top_below(mesh, x):
        ys = -40.0 + hits_along(mesh, np.array([x, -40.0, ZM]), [0, 1, 0])
        ys = ys[ys < -7.0]
        return ys.max() if len(ys) else np.nan

    Fg = np.array([(-40.0 + hits_along(frame_c, np.array([x, -40.0, ZM]), [0, 1, 0]))[0] for x in xg])
    it = (xg >= a_now - 0.6) & (xg <= a_now + 1.9)
    xt = xg[it]
    Tt = np.array([top_below(slider_c, x) for x in xt])
    land_y = Fg[np.argmin(abs(xg - (a_now - 0.1)))]
    apex_y = np.nanmax(Tt)
    # hook angle and backlash: horizontal rays at two heights above the land
    # Heights +0.10 / +0.40: the traced rack underside rises 0.145 mm from the MIN notch to the MAX notch, so the
    # overlap falls 0.605 -> 0.461 and a ray at +0.55 passes over the tooth apex at MID/MAX (cad3 probe, 2026-09-23).
    fx, wx = [], []
    HG = (0.10, 0.40)
    for hgt in HG:
        yy = land_y + hgt
        fx.append(a_now - 1.0 + first_hit(slider_c, np.array([a_now - 1.0, yy, ZM]), [1, 0, 0]))
        wx.append(a_now + 0.2 - first_hit(frame_c, np.array([a_now + 0.2, yy, ZM]), [-1, 0, 0]))
    hook_t = math.degrees(math.atan((fx[0] - fx[1]) / (HG[1] - HG[0])))
    hook_w = math.degrees(math.atan((wx[0] - wx[1]) / (HG[1] - HG[0])))
    # seat gap along the ramp part of the tooth
    ir = (xt >= a_now + 0.5) & (xt <= a_now + 1.2)
    sg = np.array([Fg[np.argmin(abs(xg - x))] for x in xt[ir]]) - Tt[ir]
    # drop needed to move the tooth by s (rigid vertical drop, then X translation), max over the path
    n_s = int(round((TEETH["pitch"] + 0.3) / dx_))
    i0 = int(np.argmin(abs(xg - xt[0])))
    need = {}
    for lab, sgn in (("open -X", -1), ("close +X", +1)):
        worst = -1e9
        for k in range(1, n_s + 1):
            j = i0 + sgn * k + np.arange(len(xt))
            ok = (j >= 0) & (j < len(xg)) & ~np.isnan(Tt)
            worst = max(worst, float(np.max(Tt[ok] - Fg[j[ok]])))
        need[lab] = worst
    # tab stop gap (under the tab column) and relief under the pad end, on the slider mesh
    xs_tab = PAWL["free_x"] - PAWL["tab_w"] / 2 - t
    hs_ = hits_along(slider_c, np.array([xs_tab, PAWL["tab_bottom_y"] - 1.0, ZM]), [0, -1, 0])
    stop_gap = hs_[1] - hs_[0]
    hs2 = hits_along(slider_c, np.array([PAWL["free_x"] + PAWL["pad_len"] - 0.5 - t, PAWL["tab_bottom_y"] - 1.0, ZM]), [0, -1, 0])
    print(f"   pawl: hook tooth face {hook_t:.2f}°, rack wall {hook_w:.2f}°; horizontal backlash {fx[0] - wx[0]:.3f} / "
          f"{fx[1] - wx[1]:.3f} (at land +{HG[0]:.2f} / +{HG[1]:.2f}); apex Y {apex_y:.3f}, land Y {land_y:.3f} -> OVERLAP {apex_y - land_y:.3f};"
          f" seat gap on the ramp {sg.min():.3f}..{sg.max():.3f}")
    print(f"   pawl stop: gap under the tab {stop_gap:.3f} (pad end relief {hs2[1] - hs2[0]:.3f}); drop needed to OPEN "
          f"{need['open -X']:.3f} -> margin {stop_gap - need['open -X']:.3f}; drop needed to CLOSE (ratchet over the "
          f"ramp) {need['close +X']:.3f} -> margin {stop_gap - need['close +X']:.3f}")

    if pose == "min":
        gp = []
        for yy in (-1.0, -5.0, -8.0):
            for zz in (-3.0, -2.0, -1.0, -0.35, 10.35, 11.0, 12.0, 13.0):
                oo = np.array([100.0, yy, zz])
                hs = hits_along(slider_c, oo, [1, 0, 0])
                hf = hits_along(frame_c, oo, [1, 0, 0])
                if len(hs) and len(hf) and hf[0] > hs[-1]:
                    gp.append((hf[0] - hs[-1], yy, zz, 100 + hs[-1], 100 + hf[0]))
        m_ = min(gp)
        print(f"   carriage -> BOSS PAD gap (rays +X beside the rack): min {m_[0]:.3f} mm at Y {m_[1]}, Z {m_[2]} "
              f"(carriage end X {m_[3]:.3f} -> pad X {m_[4]:.3f}); max {max(gp)[0]:.3f}")
        oo = np.array([D["carriage_x1"] - 5.0, -11.0, ZM])
        hs, hf = hits_along(slider_c, oo, [1, 0, 0]), hits_along(frame_c, oo, [1, 0, 0])
        print(f"   carriage -> boss (Y -11, Z 5): {hf[0] - hs[-1]:.3f} mm")
        # Round 5: TRUE 2D pad clearance on Y-normal sections every 0.25 from the leg bottom to Y 3 (form-auditor's
        # method). Pad = frame at Z < -0.0005 or Z > T_Z - Z_pad (the rack in the channel is excluded); below the
        # carriage floor (stop-leg rows) the whole frame counts. Local window X x_end-6 .. x_end+8.
        xe = D["carriage_end_x"] - t
        pad_keep = unary_union([box2(xe - 6, xe + 8, -50, -0.0005), box2(xe - 6, xe + 8, 10.0005, 50)])
        win_s, win_f = box2(xe - 6, xe + 1, -50, 50), box2(xe - 1, xe + 8, -50, 50)
        y_floor_ = CHAN["y0"] - sdg.CARRIAGE_FLOOR
        best, best_leg = (1e9, None), (1e9, None)
        for yy in np.arange(beam_bot - 0.95, 3.0, 0.25):
            ps, pf = section_y_xz(slider_c, yy).intersection(win_s), section_y_xz(frame_c, yy)
            pf = pf.intersection(win_f if yy < y_floor_ else pad_keep)
            if ps.is_empty or pf.is_empty:
                continue
            dd = ps.distance(pf)
            best = min(best, (dd, round(float(yy), 2)))
            if yy < y_floor_:
                best_leg = min(best_leg, (dd, round(float(yy), 2)))
        print(f"   carriage -> BOSS PAD TRUE 2D minimum (Y sections every 0.25, Y {beam_bot - 0.95:.2f}..3): "
              f"{best[0]:.4f} at Y {best[1]}; stop-leg rows (Y < {y_floor_:.2f}): "
              + (f"{best_leg[0]:.4f} at Y {best_leg[1]}" if best_leg[1] is not None else "no frame material near"))
        rm, rf = [], []
        for yy in np.arange(D["ferrule_top_y"] + 2.0, D["ferrule_top_y"] + 6.0, 0.02):
            for a in (0.0, 90.0, 180.0, 270.0):
                dd = np.array([math.cos(math.radians(a)), 0, math.sin(math.radians(a))])
                oo = np.array([D["handle_axis_x"], yy, ZM])
                h1, h2 = first_hit(handle_c, oo, dd, 10), first_hit(frame_c, oo, dd, 10)
                if h1 is not None and h2 is not None:
                    rm.append(h1); rf.append(h2)
        rm, rf = np.array(rm), np.array(rf)
        print(f"   thread: male r {rm.min():.3f}..{rm.max():.3f}, female r {rf.min():.3f}..{rf.max():.3f}; engagement "
              f"{rm.max() - rf.min():.3f}; min radial gap {np.min(rf - rm):.3f}")
        # SEATING GATE (round 4, user decision (a)): on the assembly meshes, i.e. the same datum as the assembly.
        # Every ray starts 1.5 below the boss face INSIDE the handle, runs +Y (into the hole), 24 angles.
        yf, hx = D["ferrule_top_y"], D["handle_axis_x"]
        angs = np.radians(np.arange(0.0, 360.0, 15.0))

        def up(mesh, r, a, y0=yf - 1.5):
            return first_hit(mesh, np.array([hx + r * math.cos(a), y0, ZM + r * math.sin(a)]), [0, 1, 0], 25.0)
        contact, gaps_c = [], []
        for r in np.arange(6.0, 11.3, 0.05):
            g = [(up(frame_c, r, a), up(handle_c, r, a)) for a in angs]
            if all(f is not None and h is not None for f, h in g):
                d_ = [f - h for f, h in g]
                if max(abs(x) for x in d_) < 0.02 and all(abs(h - 1.5) < 0.02 for _, h in g):
                    contact.append(r); gaps_c += d_
        tip = [(up(frame_c, r, a), up(handle_c, r, a)) for r in (0.0, 2.0, 4.0, 5.5) for a in angs]
        tip_gap = min(f - h for f, h in tip)
        # widest handle feature above the face: radial rays from the axis at 0.05 .. 1.0 above the face
        rad = [first_hit(handle_c, np.array([hx, yy, ZM]), [math.cos(a), 0, math.sin(a)], 20.0)
               for yy in (yf + 0.05, yf + 0.3, yf + 1.0) for a in angs]
        fem0 = min(up(frame_c, 7.9, a) for a in angs) - 1.5          # first female material inside r 7.9
        print(f"   SEATING: collar face -> boss face gap {min(gaps_c):+.4f}..{max(gaps_c):+.4f} mm over the contact "
              f"annulus r {min(contact):.2f}..{max(contact):.2f} (width {max(contact) - min(contact) + 0.05:.2f}, 0.05 "
              f"steps, 24 angles, flat: every contact ray exits the handle at the face)")
        print(f"   SEATING: male tip -> hole floor {tip_gap:.3f} mm (> 0); handle max radius above the face "
              f"{max(rad):.3f} (male crest; nothing wider enters the hole); first female material inside r 7.9 is "
              f"{fem0:.3f} mm above the face (> 0); Ø16 core top {THREAD['pitch'] + 0.5:.1f} mm below the face, "
              f"inside the collar")
        for push in (0.02, 0.10):
            hp_ = handle_c.copy()
            hp_.apply_translation([0, push, 0])
            try:
                X_ = trimesh.boolean.intersection([hp_, frame_c], engine="manifold")
                if X_ is not None and len(X_.faces):
                    rr_ = np.hypot(X_.vertices[:, 0] - hx, X_.vertices[:, 2] - ZM)
                    print(f"   SEATING push +{push:.2f} mm into the hole: handle∩frame {X_.volume:.3f} mm3 (annulus "
                          f"π(r_o²-r_i²)·push = {math.pi * (max(contact) ** 2 - min(contact) ** 2) * push:.3f}), at Y "
                          f"{X_.bounds[0][1]:.3f}..{X_.bounds[1][1]:.3f}, r {rr_.min():.3f}..{rr_.max():.3f}")
                else:
                    print(f"   SEATING push +{push:.2f}: NO intersection (collar is not in contact)")
            except Exception as e:
                print(f"   SEATING push +{push:.2f}: ERR {e}")
        for tag, M in (("rotated +1.087 deg (as imaged)",
                        trimesh.transformations.rotation_matrix(math.radians(1.087), [0, 0, 1], [64.79, 6.587, 0])),
                       ("shifted +0.5 mm in Y", trimesh.transformations.translation_matrix([0, 0.5, 0]))):
            bad = slider_c.copy()
            bad.apply_transform(M)
            B = trimesh.util.concatenate([frame_c, bad])
            Pb = []
            for x in s_st:
                yy = WY + (x - 64.79) * math.tan(math.radians(1.087)) if "rotated" in tag else WY + 0.5
                q = bore_centre(B, x, yy, ZM)
                Pb.append([x, q[0], q[1]])
            cb, db = fit_line(np.array(Pb))
            angb = math.degrees(math.acos(min(1.0, abs(float(db @ dc)))))
            pb_at = cb + db * ((xm - cb[0]) / db[0])
            ob = cb + db * ((-30.0 - cb[0]) / db[0])
            nb = sum(len(hits_along(B, ob + 1.5 * (math.cos(a) * u + math.sin(a) * v), db)) for a in np.linspace(0, 2 * math.pi, 16, endpoint=False))
            print(f"   CONTROL {tag:30s}: offset {float(np.hypot(*(pc_at[1:] - pb_at[1:]))):.3f} mm, angle {angb:.3f} deg, "
                  f"wire-surface hits {nb}")
    if pose == "max":
        for zz in (-2.0, 12.0):
            oo = np.array([PIN["x"], PIN["y"], zz])
            hp = first_hit(pin_c, oo, [1, 0, 0])
            hs = first_hit(slider_c, oo, [1, 0, 0])
            slop = (PIN["hole_d"] - PIN["d"]) / 2.0
            print(f"   pin -> collar at MAX (Y {PIN['y']:.3f}, Z {zz}): pin surface X {PIN['x'] + hp:.3f} -> collar face "
                  f"X {PIN['x'] + hs:.3f} = {hs - hp:.3f} mm centred, {hs - hp - slop:.3f} with the pin {slop:.2f} towards "
                  f"the collar; contact at travel {t + hs - hp:.3f} / {t + hs - hp - slop:.3f} mm")
print("=" * 100)
print("done")
