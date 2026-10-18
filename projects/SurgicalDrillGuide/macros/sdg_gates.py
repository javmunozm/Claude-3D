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

D, TRAVEL, CHAN, TEETH, BORE, COUP, PAWL = sdg.parameters()
LUG, HEAD, SOCK, FIN, HOOK, NOTCH, BAR = (COUP[k] for k in ("lug", "head", "socket", "finger", "hook", "notch", "bar"))
WY = D["wire_y"]
ZM = sdg.Z_MID
PIN = D["pin"]
CT = D["ctip"]
PARTS = ["main_frame", "l_arm_slider", "handle", "end_stop_pin"]
from sdg_model.parts.l_arm_slider import pawl_layout  # noqa: E402  (r7: the builder's own layout, probe origins only)
from sdg_model.rings import rack_flat_poly  # noqa: E402
A_LIST = sdg.rack_notches(D, TEETH)
A_SEATS, K_SEATS = sdg.seat_notch(A_LIST, PAWL, D)
LAY = pawl_layout(D, CHAN, PAWL, A_SEATS)
Y0 = CHAN["y0"]
PITCH = TEETH["pitch"]
XF = HEAD["x0"]                                   # r7 handle flat plane = head -X face


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
for x, yy, lab in ((100.0, -4.0, "bar"), (COUP["hx"], -4.0, "bar"), (140.0, -4.0, "bar"), (140.0, 5.0, "raised bar"),
                   (COUP["hx"], 0.5 * (LUG["y_end"] - 9.0), "lug"), (0.5 * (FIN["x0"] + FIN["x1"]), -15.0, "finger")):
    zz = 30.0 - hits_along(fr, np.array([x, yy, 30.0]), [0, 0, -1])
    print(f"  frame Z at {lab:10s} X {x:7.3f} Y {yy:7.3f}: surfaces Z {np.round(zz, 3).tolist()}")
print(f"  ROUND 6 uniform Z: frame STL Z {fr.bounds[0][2]:.4f}..{fr.bounds[1][2]:.4f} (T_Z {sdg.T_Z})")

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
o = np.array([COUP["hx"], 0.0, ZM])
hs_ = hits_along(hd, o, [0, -1, 0])
o2 = np.array([COUP["hx"], -60.0, ZM])
print(f"  handle socket: ray down the axis from Y 0: first handle hit Y {-hs_[0]:.3f} (socket floor; head top "
      f"{hd.bounds[1][1]:.3f}); lug end on the frame STL (ray up from Y -60) Y {o2[1] + first_hit(fr, o2, [0, 1, 0]):.3f}")
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
boss_zone = unary_union([box2(LUG["x0"] - LUG["r"] - 0.5, FIN["x1"] + FIN["r"] + 0.5, LUG["y_end"] - 1.0,
                               D["bar_bottom_at_axis"] + 0.3),                       # round 6 lug + finger
                          box2(BAR["x0"] - 0.05, BAR["x_hook"] + 2 * BAR["blend_r"], -1.0, BAR["y_top"] + 3 * BAR["blend_r"])])
pad_zone = box2(CT["x_entry"] - 0.3, CT["x_exit"] + 0.3, WY - CT["half_h"] - CT["blend_r"] - 1, WY + CT["half_h"] + CT["blend_r"] + 1)
bore_zone = box2(BORE["ctip_x0"], BORE["ctip_x1"], WY - sdg.BORE_D / 2 - 0.3, WY + sdg.BORE_D / 2 + 0.3)
bx0 = D["rack_bottom_line"][0]
ext_zone = box2(D["rack_tip_x"] - 1.0, bx0 + 0.6, -12, 1.0)
HO = D["hook_outer"]
hook_reg = sdg.hook_outer_region(D, HO)                                   # round 6 pass 2 (designed region)
hook_zone = hook_reg.buffer(0.3)
# r7 flat rack underside: the designed wedge between the flat level and the traced line (same x_end rule as the
# builder: inside the last notch), grown 0.3 as the exclusion window.
_x_flat_end = A_LIST[-1] + 0.5 * (TEETH["depth"] * math.tan(math.radians(TEETH["hook"])) + PITCH - TEETH["land"])
_wedge = rack_flat_poly(D, _x_flat_end)
flat_zone = _wedge.buffer(0.3)
_s1 = section_poly(fr, 1.0)
_wadd = _s1.intersection(flat_zone).difference(fr_ring)
_wadd = unary_union([g for g in getattr(_wadd, "geoms", [_wadd]) if g.area > 1e-4])
_ys = [sdg.vertical_chord(_s1, x)[0] for x in np.arange(1.0, TEETH["x1"] - 0.5, 0.25)
       if sdg.vertical_chord(_s1, x) is not None]
print(f"  r7 FLAT RACK UNDERSIDE zone (excluded): X {flat_zone.bounds[0]:.3f}..{flat_zone.bounds[2]:.3f}, area "
      f"{flat_zone.area:.2f} mm2 (designed wedge {_wedge.area:.2f}, incl. its 0.5 overlap up into the rack); STL Z=1 adds "
      f"{_wadd.area:.2f} mm2 below the traced line there, max offset {max(p.distance(fr_ring) for p in boundary_samples(_wadd, 0.05)):.3f};"
      f" rack bottom Y on vertical chords X 1..{TEETH['x1'] - 0.5:.1f}: {min(_ys):.4f}..{max(_ys):.4f} (min = the lands,"
      f" max = notch roofs; flat level "
      f"{sdg.rack_bottom_y(D, 0.0):.4f})")
for z in (1.0, ZM):
    sec = section_poly(fr, z)
    outline_survival(f"main_frame  Z={z}", fr_ring, sec,
                     [teeth_zone, flat_zone, boss_zone, pad_zone, ext_zone, hook_zone] + ([bore_zone] if z == ZM else []))
# HOOK OUTER OFFSET = allowed, documented deviation (round 6 pass 2): measured on the STL sections; the designed
# region is used only as the window (grown 0.3 so the measured material is fully inside it)
for z in (0.2, ZM, 9.8):
    sec = section_poly(fr, z)
    addh = sec.intersection(hook_zone).difference(fr_ring)
    addh = unary_union([g for g in getattr(addh, "geoms", [addh]) if g.area > 1e-3])
    offh = [p.distance(fr_ring) for p in boundary_samples(addh, 0.05)]
    lost = fr_ring.intersection(hook_zone).difference(sec).area
    far = sec.intersection(box2(CT["x_exit"] + 1e-3, 400, -100, 200))
    print(f"  HOOK OUTER deviation (STL Z={z} vs ring): added {addh.area:.2f} mm2 in {len(getattr(addh, 'geoms', [addh]))}"
          f" region(s) (designed {hook_reg.area:.2f}), max offset from the traced outline {max(offh):.3f} mm "
          f"(designed {HO['d_full']}); traced material removed {lost:.4f} mm2; STL X max {sec.bounds[2]:.3f}; wire axis "
          f"-> frame material beyond the bore exit X {CT['x_exit']:.3f}: {far.distance(shapely.LineString([(CT['x_exit'] + 1e-3, WY), (400, WY)])):.3f}"
          f" (designed region alone {HO['wire_clear']:.3f}; hold 3.6 ends at s {HO['s_hold_end']}, 0 at s {HO['s_hold_end'] + HO['end_len']})")


def outer_smoothness(sec, ring, p_start, p_end, step=1.0, end_ext=3.0, fillet_zone=8.0, dev=0.05, r_flat=100.0,
                     stop=None):
    """Round 6 pass 3: smoothness of the frame's outer boundary over the hook band, on an STL section.
    Walks the section's outer boundary from the projection of p_start to p_end (+ end_ext past it), on the arc
    through the larger X, resampled every `step` mm. Each 3-point window (i-1, i, i+1) gives a circumradius; it is
    concave when the chord midpoint (i-1, i+1) lies outside the section. A concave run = consecutive concave
    windows with R < r_flat (R >= r_flat is read as straight). The band's two junctions are the first / last
    samples more than `dev` off the traced ring; a run centred within `fillet_zone` (arc mm) of one is an intended
    end fillet. PASS = min R >= 3.0 over every window and no concave run outside the fillet zones."""
    poly = max(getattr(sec, "geoms", [sec]), key=lambda g: g.area)
    ext, inside = poly.exterior, poly.buffer(-1e-6)
    L = ext.length
    a, b = ext.project(Point(p_start)), ext.project(Point(p_end))

    def arc(u, v):
        v = v + L if v < u else v
        return u, v
    cand = []
    for u, v, sg in ((a, b + end_ext, 1), (b - end_ext, a, -1)):
        u, v = arc(u, v)
        n = int(round((v - u) / step))
        P = np.array([ext.interpolate((u + (v - u) * k / n) % L).coords[0] for k in range(n + 1)])
        cand.append(P if sg == 1 else P[::-1])
    P = max(cand, key=lambda q: q[:, 0].max())
    corner = None
    if stop is not None:   # end the walk one step before the outline reaches `stop` (the C-tip pad); the corner
        on = np.where(np.array([Point(q).distance(stop) for q in P]) < step)[0]   # there is reported, not filleted
        on = on[on > len(P) // 2]
        if len(on):
            c, a0, a1 = P[on[0]], P[on[0] - 1], P[min(on[0] + 1, len(P) - 1)]
            u, v = a0 - c, a1 - c
            ang = math.degrees(math.acos(np.clip(u @ v / (np.linalg.norm(u) * np.linalg.norm(v)), -1, 1)))
            corner = (c, ang, not inside.contains(Point(0.5 * (a0 + a1))))
            P = P[:on[0]]
        ring = ring.union(stop)
    S = np.arange(len(P)) * float(np.mean(np.linalg.norm(np.diff(P, axis=0), axis=1)))
    R, cc = np.full(len(P), np.inf), np.zeros(len(P), bool)
    for i in range(1, len(P) - 1):
        p0, p1, p2 = P[i - 1], P[i], P[i + 1]
        A2 = abs((p1[0] - p0[0]) * (p2[1] - p0[1]) - (p1[1] - p0[1]) * (p2[0] - p0[0]))
        la, lb, lc = np.linalg.norm(p1 - p0), np.linalg.norm(p2 - p1), np.linalg.norm(p2 - p0)
        R[i] = la * lb * lc / (2 * A2) if A2 > 1e-12 else np.inf
        cc[i] = not inside.contains(Point(0.5 * (p0 + p2)))
    off = np.array([Point(q).distance(ring) for q in P])
    j = np.where(off > dev)[0]
    junc = (S[j[0]], S[j[-1]]) if len(j) else ()
    runs, i = [], 1
    while i < len(P) - 1:
        if cc[i] and R[i] < r_flat:
            k = i
            while k + 1 < len(P) - 1 and cc[k + 1] and R[k + 1] < r_flat:
                k += 1
            seg = P[max(i - 1, 0):k + 2]
            c0, c1 = seg[0], seg[-1]
            t = (c1 - c0) / max(np.linalg.norm(c1 - c0), 1e-9)
            depth = float(np.max(np.abs((seg - c0) @ np.array([-t[1], t[0]]))))
            sm = 0.5 * (S[i] + S[k])
            intended = any(abs(sm - q) <= fillet_zone for q in junc)
            runs.append((S[i], S[k], float(R[i:k + 1].min()), P[(i + k) // 2], depth, intended))
            i = k + 1
        else:
            i += 1
    imin = int(np.argmin(R))
    bad = [r for r in runs if not r[5]]
    ok = R[imin] >= 3.0 and not bad
    return {"P": P, "S": S, "R": R, "imin": imin, "junc": junc, "runs": runs, "pass": ok, "corner": corner}


from sdg_model.parts.main_frame import ctip_pad_region, hook_outer_edge  # noqa: E402
_st = {q[0]: q for q in sdg.HOOK_STATIONS}
_pad = ctip_pad_region(D, CT)[1]
_sm = outer_smoothness(section_poly(fr, ZM), fr_ring, hook_outer_edge(fr_ring, _st[10])[0].coords[0],
                       hook_outer_edge(fr_ring, _st[66])[0].coords[0], stop=_pad)
_P, _R, _im = _sm["P"], _sm["R"], _sm["imin"]
print(f"  HOOK OUTER smoothness (STL Z={ZM}, outer boundary s 10 -> s 66 + 3 mm, stopped at the C-tip pad (walk "
      f"end X {_P[-1][0]:.2f} Y {_P[-1][1]:.2f}), {len(_P)} samples at "
      f"{_sm['S'][1]:.3f} mm): min radius {_R[_im]:.3f} at X {_P[_im][0]:.2f} Y {_P[_im][1]:.2f} (need >= 3.0); band "
      f"junctions at arc {', '.join(f'{q:.1f}' for q in _sm['junc'])}; concave runs (R < 100) {len(_sm['runs'])}:")
for s0, s1, rmin, pc, dep, intd in _sm["runs"]:
    print(f"    arc {s0:6.1f}..{s1:6.1f}  min R {rmin:7.3f}  at X {pc[0]:.2f} Y {pc[1]:.2f}  depth {dep:.3f} mm  "
          f"{'intended end fillet' if intd else 'UNINTENDED (dent)'}")
if _sm["corner"] is not None:
    _c = _sm["corner"]
    print(f"    end corner where the band meets the C-tip pad (not part of the walk): X {_c[0][0]:.2f} Y {_c[0][1]:.2f}, "
          f"3-point angle {_c[1]:.1f}° ({'concave' if _c[2] else 'convex'})")
print(f"  HOOK OUTER smoothness: {'PASS' if _sm['pass'] else 'FAIL'}")
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
added = sec1f.intersection(win).difference(fr_ring).difference(hook_zone)   # the hook offset is reported above
added = unary_union([g for g in getattr(added, "geoms", [added]) if g.area > 1e-3])
offs = [p.distance(fr_ring) for p in boundary_samples(added, 0.05)]
removed = fr_ring.intersection(win).difference(sec1f).area
print(f"  C-tip PAD deviation (STL Z=1 vs ring): added {added.area:.2f} mm2 in {len(getattr(added, 'geoms', [added]))} region(s),"
      f" max offset from the traced outline {max(offs):.3f} mm; traced material removed {removed:.4f} mm2")

la, co, ca = ring_poly("l_arm"), ring_poly("collar"), ring_poly("carriage")
chan_zone = box2(D["collar_x0"] - 1, D["carriage_x1"] + 1, CHAN["y0"] - 0.3, CHAN["y1"] + 0.3)
ST = PAWL["stop"]
beam_bot = LAY["beam_top"] - ST["beam_t"]
y_fl_ = CHAN["y0"] - sdg.CARRIAGE_FLOOR
# r7 pawl zone: flexure, block, 4 teeth, tab, pad, two-point stop, and the 45° root bevel that reaches
# (y_fb - y_floor) to the -X of the anchor into the traced carriage/collar corner.
pawl_zone = box2(PAWL["anchor_x"] - (LAY["y_fb"] - y_fl_) - 0.5, max(D["carriage_x1"], LAY["leg_x1"]) + 0.5, beam_bot - 1.0,
                 PAWL["window_top_y"] + 0.3)
_sec5s = section_poly(sl, ZM)
print(f"  r7 PAWL ZONE (excluded from the slider outline survival): X {pawl_zone.bounds[0]:.3f}..{pawl_zone.bounds[2]:.3f}"
      f" Y {pawl_zone.bounds[1]:.3f}..{pawl_zone.bounds[3]:.3f}, area {pawl_zone.area:.2f} mm2; in it at Z 5 the STL "
      f"adds {_sec5s.intersection(pawl_zone).difference(unary_union([ring_poly('l_arm'), ring_poly('collar'), ring_poly('carriage')])).area:.2f}"
      f" mm2 and removes {unary_union([ring_poly('l_arm'), ring_poly('collar'), ring_poly('carriage')]).intersection(pawl_zone).difference(_sec5s).area:.2f} mm2 of traced material")
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
for x in (70.5, 72.0, 72.3, 73.0, 80.0, 90.0, 95.5, 100.0, 103.0, 106.0, 106.45, 107.0, 107.9):
    yy = 10.0 - hits_along(sl, np.array([x, 10.0, ZM]), [0, -1, 0])
    yy = yy[yy < CHAN["y0"] + 0.01]
    fl.append(f"X {x}: {yy[0] - yy[1]:.3f}" if len(yy) > 1 else f"X {x}: -")
print(f"  carriage FLOOR under the channel (vertical rays, Z 5; tongue X {PAWL['anchor_x']}..{PAWL['free_x']}, leg "
      f"{LAY['leg_x0']:.1f}..{LAY['leg_x1']:.1f} continue down): " + "; ".join(fl))
# Round 5: rays cover the stop leg too (beam bottom up to the top wall), so a leg face behind the end shows.
# r7 reinforce: rows above the floor underside must read the carriage end (lock), rows below it the leg's +X face.
y_floor = CHAN["y0"] - sdg.CARRIAGE_FLOOR


def end_rows(m):
    up, lo = [], []
    for yy in np.linspace(beam_bot + 0.05, CHAN["y1"] + sdg.CARRIAGE_TOP_WALL - 0.05, 41):
        for zz in (-3.0, 12.9):
            h = 130.0 - first_hit(m, np.array([130.0, yy, zz]), [-1, 0, 0])
            (lo if yy < y_floor - 0.01 else up).append(h)
    return np.array(up), np.array(lo)


_up, _lo = end_rows(sl)
print(f"  carriage +X END face (41 rows Y {beam_bot + 0.05:.2f}..{CHAN['y1'] + sdg.CARRIAGE_TOP_WALL - 0.05:.2f}, "
      f"Z -3 / 12.9): rows at/above the floor underside {y_floor:.3f} X {_up.min():.4f}..{_up.max():.4f} (lock "
      f"{D['carriage_end_x']:.4f}; max dev {np.abs(_up - D['carriage_end_x']).max():.5f}); leg rows below it X "
      f"{_lo.min():.4f}..{_lo.max():.4f} (design leg +X {LAY['leg_x1']:.4f}; traced max {D['carriage_x1']:.3f})")
_slc = sl.copy()
_slc.apply_translation([0.1, 0, 0])
_cu, _ = end_rows(_slc)
print(f"  CONTROL slider +0.1 X: end rows above the floor max dev from the lock {np.abs(_cu - D['carriage_end_x']).max():.5f}"
      f" (must be > 1e-3)")
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
rT = HEAD["core_r"]
y_cone = HEAD["y_bot"] - (math.hypot(sdg.HEAD_W_X / 2, sdg.HEAD_W_Z / 2) + 0.05 - (rT - 1.0)) / math.tan(math.radians(HEAD["cone_deg"]))
head_zone = box2(HEAD["x0"] - 5.0, HEAD["x1"] + 5.0, y_cone - 0.5, 0.0)
core_zone = box2(ax - rT - 0.5, ax + rT + 0.5, D["grip_top_y"] - sdg.HANDLE_CORE_GRIP_DEPTH - 0.5, y_cone)
butt_zone = box2(ax - 8, ax + 8, -150, hd.bounds[0][1] + 0.1)
secH = section_poly(hd, ZM)
hflat_zone = box2(XF - 20.0, XF + 0.05, -200.0, 5.0)        # r7 -X flat (user decision): everything at X < XF
print(f"  r7 HANDLE FLAT zone (excluded): X < {XF + 0.05:.3f}; traced silhouette removed there at Z 5 "
      f"{silh.intersection(hflat_zone).difference(secH).area:.2f} mm2 (silhouette X min {silh.bounds[0]:.3f}); STL "
      f"section X min {secH.bounds[0]:.4f} vs plane {XF:.4f}")
outline_survival("handle Z=5 (axis plane) vs halves+mirror", silh, secH, [head_zone, core_zone, butt_zone, hflat_zone])
# HANDLE HEAD (round 6): section widths on the STL at Z 5 (X) and at the axis (Z, Y-normal sections)
hw = [(y, sdg.horizontal_chord(secH, y)) for y in (HEAD["y_top"] - 0.02, HEAD["y_top"] - 3.0, HEAD["y_bot"] + 0.02,
                                                    HEAD["y_bot"] - 4.0, y_cone + 0.5)]
print(f"  HANDLE HEAD (STL Z=5): X extent at " + "; ".join(f"Y {y:.2f}: {c[0]:.3f}..{c[1]:.3f}" for y, c in hw if c))
for yy in (HEAD["y_top"] - 5.0, HEAD["y_bot"] + 1.0):
    s_ = section_y_xz(hd, yy)
    print(f"  HANDLE HEAD Y-section at Y {yy:.2f}: X {s_.bounds[0]:.3f}..{s_.bounds[2]:.3f}, Z {s_.bounds[1]:.3f}..{s_.bounds[3]:.3f}"
          f", area {s_.area:.2f} mm2, holes {sum(len(g.interiors) for g in getattr(s_, 'geoms', [s_]))}")
# HANDLE CORE (round 3, deviation): Ø16 core from inside the grip up into the head cone (traced ferrule inside it)
addh = secH.intersection(core_zone).difference(silh)
addh = unary_union([g for g in getattr(addh, "geoms", [addh]) if g.area > 1e-4])
offh = [p.distance(silh) for p in boundary_samples(addh, 0.05)]
fer = [sdg.horizontal_chord(fh, y) for y in np.linspace(D["ferrule_bot_y"] + 0.5, D["ferrule_top_y"] - 0.5, 40)]
fer_r = [c[1] - ax for c in fer if c]
secr = [sdg.horizontal_chord(secH, y) for y in np.linspace(D["grip_top_y"] - 0.5, y_cone, 60)]
print(f"  HANDLE CORE deviation (STL Z=5): traced ferrule r {min(fer_r):.3f}..{max(fer_r):.3f} (not built: inside the core);"
      f" STL radius from the grip top to the head cone min {min((c[1] - c[0]) / 2 for c in secr if c):.3f}; added "
      f"{addh.area:.2f} mm2, max offset {max(offh):.3f} mm from the traced silhouette")


# ═════════════════════════════════════════════════════════════════════════════
def chord_iv(poly, x):
    """All intervals (y0, y1) of a vertical line at x through poly, sorted by y."""
    g = poly.intersection(shapely.LineString([(x, -300), (x, 300)]))
    segs = [s for s in getattr(g, "geoms", [g]) if s.length > 0]
    return sorted((min(c[1] for c in s.coords), max(c[1] for c in s.coords)) for s in segs)


def first_hits_x(mesh, origins, d):
    """Batched: X of the first hit for each ray (nan if none)."""
    loc, ir, _ = mesh.ray.intersects_location(origins, np.tile(d, (len(origins), 1)), multiple_hits=False)
    out = np.full(len(origins), np.nan)
    out[ir] = loc[:, 0]
    return out


print("=" * 100)
print("GATE 3b: r7 handle -X flat and pawl flexure (measured on the part STLs)")


def flat_rays(h_mesh):
    ys = np.arange(h_mesh.bounds[0][1] + 0.25, h_mesh.bounds[1][1] - 0.2, 0.5)
    zs = np.linspace(ZM - 9.0, ZM + 9.0, 13)
    O = np.array([[XF - 30.0, y, z] for y in ys for z in zs])
    return O, first_hits_x(h_mesh, O, np.array([1.0, 0, 0]))


O_, hx_ = flat_rays(hd)
ok_ = ~np.isnan(hx_)
on_ = ok_ & (np.abs(hx_ - XF) < 1e-3)
print(f"  HANDLE FLAT rays +X from X {XF - 30:.1f} ({len(O_)} rays, Y every 0.5 over the whole length, Z {ZM - 9:.0f}..{ZM + 9:.0f}): "
      f"{int(ok_.sum())} hit; first-hit X min {np.nanmin(hx_):.4f} (plane {XF:.4f} = head x0); hits on the plane (|dX| < 1e-3) "
      f"{int(on_.sum())}, below the plane {int((ok_ & (hx_ < XF - 1e-3)).sum())}; Y of the on-plane rays "
      f"{O_[on_, 1].min():.3f}..{O_[on_, 1].max():.3f}")
_yon = np.unique(O_[on_, 1])
_runs = np.split(_yon, np.where(np.diff(_yon) > 0.51)[0] + 1)
print(f"  HANDLE FLAT on-plane Y runs (Z any): " + "; ".join(f"Y {r[0]:.2f}..{r[-1]:.2f}" for r in _runs))
_hc = hd.copy()
_hc.apply_translation([-0.3, 0, 0])
_, chx = flat_rays(_hc)
print(f"  CONTROL handle -0.3 X: first-hit X min {np.nanmin(chx):.4f}, rays below the plane "
      f"{int((chx < XF - 1e-3).sum())} (must be > 0)")
_n = hd.face_normals
_sel = np.where((_n[:, 0] < -0.9999) & (np.abs(hd.triangles_center[:, 0] - XF) < 1e-3))[0]
_vx = hd.triangles[_sel][:, :, 0]
_g = trimesh.graph.connected_components(hd.face_adjacency[np.isin(hd.face_adjacency, _sel).all(axis=1)], nodes=_sel)
_tri = hd.triangles[_sel].reshape(-1, 3)
print(f"  HANDLE FLAT faces (normal -X within 0.8°, centre on the plane): {len(_sel)} triangles, area "
      f"{hd.area_faces[_sel].sum():.2f} mm2; vertex X spread {_vx.min() - XF:+.5f}..{_vx.max() - XF:+.5f} (one plane); "
      f"Y {_tri[:, 1].min():.3f}..{_tri[:, 1].max():.3f}, Z {_tri[:, 2].min():.3f}..{_tri[:, 2].max():.3f}; "
      f"{len(_g)} connected region(s):")
for g in sorted(_g, key=lambda q: -hd.area_faces[np.asarray(q)].sum()):
    g = np.asarray(g)
    tq = hd.triangles[g].reshape(-1, 3)
    print(f"    area {hd.area_faces[g].sum():8.2f} mm2  Y {tq[:, 1].min():8.3f}..{tq[:, 1].max():8.3f}  "
          f"Z {tq[:, 2].min():7.3f}..{tq[:, 2].max():7.3f}")

# Flexure (unplaced slider STL, section Z 5): thickness on vertical chords, free length from the underside corners
_ss = section_poly(sl, ZM)
_ts = []
for x in np.arange(PAWL["anchor_x"] + 0.5, LAY["xb"] - 0.4, 0.5):
    c = [s for s in chord_iv(_ss, x) if abs(s[1] - Y0) < 0.01]
    _ts.append(c[0][1] - c[0][0] if c else np.nan)
_ts = np.array(_ts)
_tm = float(np.nanmedian(_ts))
_sv = np.array([q for g in getattr(_ss, "geoms", [_ss]) for q in g.exterior.coords])
_cor = _sv[(np.abs(_sv[:, 1] - (Y0 - _tm)) < 1e-4) & (_sv[:, 0] > PAWL["anchor_x"] - 0.6) & (_sv[:, 0] < LAY["xb"] + 0.6)]
print(f"  FLEXURE (slider STL Z 5): t {np.nanmin(_ts):.4f}..{np.nanmax(_ts):.4f} on {len(_ts)} chords X "
      f"{PAWL['anchor_x'] + 0.5:.1f}..{LAY['xb'] - 0.5:.2f} (design {PAWL['flex_t']}); underside corners X "
      + ", ".join(f"{q:.3f}" for q in sorted(set(np.round(_cor[:, 0], 3)))) +
      f" -> free length {_cor[:, 0].max() - _cor[:, 0].min():.4f}")


# r7 fixes D1 / 1h / D2 (slider STL, section Z 5). Concave-radius test = morphological closing at r - 0.01 (chord
# sag of the tessellated arc): a concave corner of radius < r adds area. Each test has a control that rebuilds the
# defect it guards against (the old 45° bevel V; a square beam-leg corner) and must add area.
def hchord_iv(poly, y):
    g = poly.intersection(shapely.LineString([(-300, y), (300, y)]))
    segs = [s for s in getattr(g, "geoms", [g]) if s.length > 0]
    return sorted((min(c[0] for c in s.coords), max(c[0] for c in s.coords)) for s in segs)


def closing_added(poly, r):
    return poly.buffer(r, quad_segs=64).buffer(-r, quad_segs=64).difference(poly).area


_rf, _yfb, _px0 = LAY["root"], LAY["y_fb"], PAWL["anchor_x"]
_wr = box2(_rf["wall"][0] - 1.0, _rf["x_end"] + 1.0, y_fl_ - 0.6, Y0 - 0.3)
_ar = _ss.intersection(_wr)
_old_v = shapely.Polygon([(_px0, _yfb), (_px0 + 1.0, _yfb), (_px0 + 1.0, y_fl_), (_px0 - (_yfb - y_fl_), y_fl_)])
_rt = PAWL["root_r"] - 0.01
_fe = [q[0] for q in _sv if abs(q[1] - _yfb) < 1e-4 and _px0 - 1.0 < q[0] < LAY["xb"] - 1.0]
print(f"  FLEXURE ROOT (Z 5, window X {_wr.bounds[0]:.2f}..{_wr.bounds[2]:.2f} Y {_wr.bounds[1]:.2f}..{_wr.bounds[3]:.2f}):"
      f" closing at r {_rt:.2f} adds {closing_added(_ar, _rt):.5f} mm2 (must be < 0.002); CONTROL old 45° bevel V: "
      f"{closing_added(_ar.difference(_old_v), _rt):.5f} mm2 (must be > 0.002); underside ends at X {min(_fe):.3f} -> "
      f"free length to the block X {LAY['xb']:.3f}: {LAY['xb'] - min(_fe):.4f} (design {LAY['free_len']:.4f}); no "
      f"material at Y >= {Y0}: {_ss.intersection(box2(_wr.bounds[0], _wr.bounds[2], Y0 + 1e-3, Y0 + 0.3)).area:.5f} mm2")
_lx0 = LAY["leg_x0"]
_xm = 0.5 * (LAY["inner_x"] + LAY["outer_x"] - ST["block_w"])
_bm = [s for s in chord_iv(_ss, _xm) if s[1] < LAY["beam_top"] + 0.01]
_lg = {yy: [s for s in hchord_iv(_ss, yy) if s[1] > PAWL["pad_x1"] + 0.01] for yy in (LAY["pad_bot"] + 1.5,
                                                                                         LAY["beam_top"] + 2.0)}
_pd = [s for s in hchord_iv(_ss, LAY["pad_bot"] + 1.5) if LAY["inner_x"] - 5.0 < s[1] <= PAWL["pad_x1"] + 0.01]
# window between the outer stop block's +X face and the leg (excludes the block's own square foot)
_ws = box2(0.5 * (LAY["outer_x"] + _lx0 - ST["fillet_r"]), _lx0 + 1.0, beam_bot - 0.5, LAY["beam_top"] + 2.5)
_as = _ss.intersection(_ws)
_fr = ST["fillet_r"] - 0.01
print(f"  STOP BEAM / LEG / PAD (Z 5): beam Y {_bm[-1][0]:.3f}..{_bm[-1][1]:.3f} at X {_xm:.2f} -> t {_bm[-1][1] - _bm[-1][0]:.4f}"
      f" (design {ST['beam_t']}); leg X " + "; ".join(f"{v[-1][0]:.3f}..{v[-1][1]:.3f} = {v[-1][1] - v[-1][0]:.4f} at Y {k:.2f}"
                                                   for k, v in _lg.items()) +
      f" (design {ST['leg_w']}: X {LAY['leg_x0']:.3f}..{LAY['leg_x1']:.3f}; carriage end {D['carriage_end_x']:.4f}); pad X {_pd[0][0]:.3f}..{_pd[-1][1]:.3f} at Y "
      f"{LAY['pad_bot'] + 1.5:.2f} (design {LAY['pad_x0']:.3f}..{PAWL['pad_x1']}; inner stop X {LAY['inner_x'] - ST['block_w']:.3f}"
      f"..{LAY['inner_x']:.3f}); pad -> leg gap {_lg[LAY['pad_bot'] + 1.5][-1][0] - _pd[-1][1]:.4f}")
print(f"  BEAM-LEG CORNER: closing at r {_fr:.2f} adds {closing_added(_as, _fr):.5f} mm2 (must be < 0.002); CONTROL square "
      f"corner: {closing_added(_as.union(box2(_lx0 - ST['fillet_r'], _lx0 + 0.1, LAY['beam_top'] - 0.1, LAY['beam_top'] + ST['fillet_r'])), _fr):.5f}"
      f" mm2 (must be > 0.002)")
# r7 reinforce: leg-top fillet (leg -X face x floor underside) and the flexure root's top-side fillet (outer Z bands).
_rl = ST["leg_top_r"]
_wl = box2(_lx0 - _rl - 0.6, _lx0 + 0.8, y_fl_ - _rl - 1.0, y_fl_ + 0.8)
_al = _ss.intersection(_wl)
print(f"  LEG-TOP CORNER (Z 5, X {_wl.bounds[0]:.2f}..{_wl.bounds[2]:.2f} Y {_wl.bounds[1]:.2f}..{_wl.bounds[3]:.2f}): closing "
      f"at r {_rl - 0.01:.2f} adds {closing_added(_al, _rl - 0.01):.5f} mm2 (must be < 0.002); CONTROL square corner: "
      f"{closing_added(_al.union(box2(_lx0 - _rl, _lx0 + 0.1, y_fl_ - _rl, y_fl_ + 0.1)), _rl - 0.01):.5f} mm2 (must be > 0.002)"
      f"; chord at Y {y_fl_ - 0.05:.3f}: X from {[s for s in hchord_iv(_ss, y_fl_ - 0.05) if s[1] > _lx0][0][0]:.3f}")
_r2 = PAWL["root_top_r"]
_zb = 0.5 * ((-sdg.SLIDE_CLEAR - sdg.WRAP_WALL_Z) - sdg.SLIDE_CLEAR)
_wt = box2(_px0 - 0.7, _px0 + _r2 + 0.6, Y0 - 0.6, Y0 + _r2 + 0.7)
for _z in (_zb, sdg.T_Z - _zb):
    _sz = section_poly(sl, _z)
    _at = _sz.intersection(_wt)
    _tv = [q[0] for g in getattr(_at, "geoms", [_at]) for q in g.exterior.coords
           if abs(q[1] - Y0) < 1e-4 and q[0] > _px0 - 0.01]
    _sq = _at.difference(box2(_px0 + 1e-4, _px0 + _r2, Y0 + 1e-4, Y0 + _r2)).union(box2(_wt.bounds[0], _px0, Y0, _wt.bounds[3]))
    print(f"  FLEXURE ROOT TOP (Z {_z:.2f}, outer band): closing at r {_r2 - 0.01:.2f} adds {closing_added(_at, _r2 - 0.01):.5f} mm2 "
          f"(must be < 0.002); CONTROL square step: {closing_added(_sq, _r2 - 0.01):.5f} mm2 (must be > 0.002); top face starts at "
          f"X {min(_tv):.3f} -> outer-band free length {LAY['xb'] - max(min(_tv), min(_fe)):.4f} (design {LAY['free_len_outer']:.4f})")
_cz = section_poly(sl, ZM).intersection(_wt)
print(f"  FLEXURE ROOT TOP centre band (Z {ZM}): material at Y >= {Y0:.3f} in the window {_cz.intersection(box2(_wt.bounds[0], _wt.bounds[2], Y0 + 1e-3, _wt.bounds[3])).area:.5f} mm2 "
      f"(must be 0); below it {_cz.area:.4f} mm2 (full window strip {(_wt.bounds[2] - _wt.bounds[0]) * 0.6:.4f})")

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
print(f"  r7 ratchet: {len(A_LIST)} notches, pitch {PITCH}; pawl teeth in notches {K_SEATS} at MIN (a "
      + ", ".join(f"{a:.3f}" for a in A_SEATS) + f"); block start X {LAY['xb']:.3f}, inner tooth face {LAY['x_in']:.3f}")


def pawl_teeth(sec_s, t):
    """The pawl material above the tongue top (Y0) over the block, as separate tooth polygons sorted by X."""
    g = sec_s.intersection(box2(LAY["xb"] - t - 0.1, PAWL["free_x"] - t + 0.1, Y0 + 1e-4, Y0 + 3.0))
    return sorted([q for q in getattr(g, "geoms", [g]) if q.area > 1e-3], key=lambda q: q.bounds[0])


def hline(poly, y, x0, x1):
    g = poly.intersection(shapely.LineString([(x0, y), (x1, y)]))
    return sorted((min(c[0] for c in s.coords), max(c[0] for c in s.coords))
                  for s in getattr(g, "geoms", [g]) if s.length > 0)


def swept_hit(teeth_u, rack_w, drop, sgn, n=131):
    """Max overlap area of the teeth lowered by `drop` and moved sgn*X by s in 0..PITCH (+0.3) against the rack."""
    return max(affinity.translate(teeth_u, sgn * s, -drop).intersection(rack_w).area
               for s in np.linspace(0.0, PITCH + 0.3, n))


def drop_needed(teeth_u, rack_w, sgn):
    lo, hi = 0.0, 3.0
    for _ in range(16):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if swept_hit(teeth_u, rack_w, mid, sgn) > 1e-7 else (lo, mid)
    return hi


def inter(a, b):
    try:
        r = trimesh.boolean.intersection([a, b], engine="manifold")
        return float(r.volume) if r is not None and len(r.faces) else 0.0
    except Exception as e:
        return f"ERR {e}"


def moved(m, dx=0.0, dy=0.0):
    c = m.copy()
    c.apply_translation([dx, dy, 0.0])
    return c


def ray_gap(m_in, m_out, o, d, max_d=30.0):
    """From a point inside m_in: distance to where the ray leaves m_in vs first hit on m_out (gap = out - in)."""
    a, b = first_hit(m_in, np.asarray(o, float), d, max_d), first_hit(m_out, np.asarray(o, float), d, max_d)
    return None if a is None or b is None else b - a


def coupling_gates(frame_c, slider_c, handle_c, t):
    """Round 6: every probe origin derived from the coupling bundle; every number measured on the STLs."""
    hx = COUP["hx"]
    # Carriage clearance: XY distance from slider sections to NEW frame material (section minus traced ring).
    xe = D["carriage_end_x"] - t
    win = box2(xe - 6, xe + 12, -40, 50)
    nm = section_poly(frame_c, ZM).difference(D["frame_poly"].buffer(0.02)).intersection(win)
    nm = unary_union([g for g in getattr(nm, "geoms", [nm]) if g.area > 1e-3])
    dmin = min((section_poly(slider_c, zz).intersection(win).distance(nm), zz) for zz in (-3.0, 1.0, 5.0, 9.0, 13.0))
    ctl = affinity.translate(section_poly(slider_c, ZM).intersection(win), 0.1, 0).distance(nm)
    print(f"   carriage -> NEW frame material (XY, slider sections Z -3/1/5/9/13): min {dmin[0]:.4f} at Z {dmin[1]} "
          f"(rule >= {sdg.COUPLING_CARRIAGE_CLEAR}); CONTROL slider +0.1 X: {ctl:.4f} (must read < rule)")
    for xx in (120.0, 130.0, 135.5):
        top = 20.0 - first_hit(frame_c, np.array([xx, 20.0, ZM]), [0, -1, 0])
        und = 20.0 + first_hit(slider_c, np.array([xx, 20.0, ZM]), [0, 1, 0])
        print(f"   THROAT at X {xx}: bar top Y {top:.3f} -> slider top-bar underside Y {und:.3f} = {und - top:.3f}; "
              f"bar top -> wire line {WY - top:.3f}")

    def lug_rays(h_mesh):
        gx, gz = [], []
        for yy in np.arange(SOCK["y_floor"] + 0.5, HEAD["y_top"] - SOCK["mouth_x"] - 0.2, 0.5):
            for zz in (1.0, ZM, sdg.T_Z - 1.0):
                gx += [ray_gap(frame_c, h_mesh, [hx, yy, zz], [s, 0, 0]) for s in (-1, 1)]
            for xx in (LUG["x0"] + 1.0, hx, LUG["x1"] - 1.0):
                gz += [ray_gap(frame_c, h_mesh, [xx, yy, ZM], [0, 0, s]) for s in (-1, 1)]
        gx, gz = [g for g in gx if g is not None], [g for g in gz if g is not None]
        return np.array(gx), np.array(gz)
    gx, gz = lug_rays(handle_c)
    cgx, _ = lug_rays(moved(handle_c, dx=0.3))
    print(f"   LUG IN SOCKET (rays from inside the lug, Y {SOCK['y_floor'] + 0.5:.2f}..{HEAD['y_top'] - SOCK['mouth_x'] - 0.2:.2f}): "
          f"X per side {gx.min():.4f}..{gx.max():.4f} ({len(gx)} rays), Z per side {gz.min():.4f}..{gz.max():.4f} ({len(gz)} rays);"
          f" CONTROL handle +0.3 X: X min {cgx.min():.4f} (must be < 0)")
    ends = [ray_gap(frame_c, handle_c, [xx, LUG["y_end"] + 3.0, zz], [0, -1, 0])
            for xx in (LUG["x0"] + 1.0, hx, LUG["x1"] - 1.0) for zz in (1.0, ZM, sdg.T_Z - 1.0)]
    print(f"   PUSH STOP lug end -> socket floor: {min(ends):.4f}..{max(ends):.4f} (9 rays; 0 = seated, D8)")
    hb = [ray_gap(handle_c, frame_c, [xx, HEAD["y_top"] - 0.5, zz], [0, 1, 0])
          for xx in (HEAD["x0"] + 0.3, HEAD["x0"] + 1.0, SOCK["x0"] - SOCK["mouth_x"] - 0.3,
                     SOCK["x1"] + SOCK["mouth_x"] + 0.2, HEAD["x1"] - HEAD["top_chamfer"] - 0.2) for zz in (1.0, ZM, 9.0)]
    print(f"   HEAD TOP -> BAR BOTTOM: {min(hb):.4f}..{max(hb):.4f} (15 rays up from inside the head walls)")
    win2 = box2(HEAD["x0"] - 2, FIN["x1"] + 2, LUG["y_end"] + 0.5, -6.0)        # above the push-stop contact
    for zz in (0.2, 1.0, ZM, 9.0, 9.8):
        sf, sh = section_poly(frame_c, zz).intersection(win2), section_poly(handle_c, zz).intersection(win2)
        print(f"   frame <-> handle 2D minimum gap in the section Z {zz}: {sf.distance(sh):.4f} "
              f"(overlap area {sf.intersection(sh).area:.4f} mm2)")
    # Snap: engagement, pull slack, hook to notch floor / sides, finger to head
    face_x = 140.0 - first_hit(handle_c, np.array([140.0, -23.0, 0.5]), [-1, 0, 0])
    tip_x = 131.0 + first_hit(frame_c, np.array([131.0, HOOK["ramp_y"][1] + 0.15, ZM]), [1, 0, 0])
    xs_ = (tip_x + 0.05, 0.5 * (tip_x + face_x), face_x - 0.05)
    sl_ = [ray_gap(frame_c, handle_c, [x_, -23.5, z_], [0, 1, 0]) for x_ in xs_ for z_ in (ZM - 0.5, ZM, ZM + 0.5)]
    fl_ = [ray_gap(frame_c, handle_c, [x_, -23.5, ZM], [0, -1, 0]) for x_ in xs_]
    sd_ = [ray_gap(frame_c, handle_c, [face_x - 0.3, -25.0, ZM], [0, 0, s]) for s in (-1, 1)]
    print(f"   SNAP: head +X face X {face_x:.4f}, hook tip X {tip_x:.4f} -> ENGAGEMENT {face_x - tip_x:.4f}; pull slack "
          f"(hook top -> notch roof) {min(sl_):.4f}..{max(sl_):.4f}; hook -> notch floor {min(fl_):.4f}..{max(fl_):.4f};"
          f" hook -> notch sides -Z / +Z {sd_[0]:.4f} / {sd_[1]:.4f}")
    fg = []
    for yy in (-12.0, -18.0, -28.0):
        for zz in (0.5, 9.5):
            hf_ = hits_along(frame_c, np.array([140.0, yy, zz]), [-1, 0, 0])
            hh_ = first_hit(handle_c, np.array([140.0, yy, zz]), [-1, 0, 0])
            fg.append(hh_ - hf_[1])
    print(f"   FINGER -> HEAD +X face: {min(fg):.4f}..{max(fg):.4f} (6 rays, Z 0.5 / 9.5)")
    s_ = max(sl_)
    for lab, dy in (("pull 0.10", -0.10), (f"pull slack+0.10 ({s_ + 0.1:.2f})", -(s_ + 0.1)), ("push 0.05", 0.05)):
        print(f"   SNAP/STOP handle moved {lab} in Y: handle∩frame {inter(moved(handle_c, dy=dy), frame_c)} mm3")
    dxc = -(face_x - tip_x + 0.05)
    face_c = 140.0 - first_hit(moved(handle_c, dx=dxc), np.array([140.0, -23.0, 0.5]), [-1, 0, 0])
    print(f"   CONTROL handle {dxc:.3f} X: measured engagement {face_c - tip_x:.4f} (must be < 0)")


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
    # r7 reinforce: the stop leg below the floor underside (placed slider sections) -> nearest frame / handle material,
    # XY distance, sections Z -3/1/5/9/13; the leg's +X face from a -X ray at the leg mid-height.
    _lw = box2(LAY["leg_x0"] - t - 0.01, LAY["leg_x1"] - t + 0.01, LAY["beam_top"] - ST["beam_t"] - 0.01, y_fl_ - 1e-3)
    _lgd = []
    for zz in (-3.0, 1.0, 5.0, 9.0, 13.0):
        _lp = section_poly(slider_c, zz).intersection(_lw)
        _fz, _hz = section_poly(frame_c, zz), section_poly(handle_c, zz)
        _lgd.append((_lp.distance(_fz) if not _fz.is_empty else np.inf, _lp.distance(_hz) if not _hz.is_empty else np.inf, zz))
    _lx = 130.0 - first_hit(slider_c, np.array([130.0 - t, 0.5 * (y_fl_ + LAY["beam_top"]), ZM]), [-1, 0, 0]) - t
    _df, _dh = min(_lgd), min(_lgd, key=lambda q: q[1])
    print(f"   STOP LEG +X face X {_lx:.4f} (ray at Y {0.5 * (y_fl_ + LAY['beam_top']):.2f}); leg (below the floor) -> frame "
          f"{_df[0]:.4f} at Z {_df[2]}, -> handle {_dh[1]:.4f} at Z {_dh[2]} (head -X flat {XF:.4f} - leg +X "
          f"{LAY['leg_x1'] - t:.4f} = {XF - LAY['leg_x1'] + t:.4f})")

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

    # r7 pawl, on the STL sections at Z 5 (every pawl feature is an in-plane profile over the full Z). Each tooth
    # is found on the slider section; every probe height is derived from that tooth's own apex and the rack land.
    secF, secS = section_poly(frame_c, ZM), section_poly(slider_c, ZM)
    rack_w = secF.intersection(box2(LAY["xb"] - t - 6.0, PAWL["free_x"] - t + 6.0, -20.0, 1.0))
    tl = pawl_teeth(secS, t)
    rows = []
    for k, g in enumerate(tl):
        ax_, ay_ = max(g.exterior.coords, key=lambda q: q[1])
        land = secF.intersection(box2(ax_ - PITCH, ax_ + PITCH, -20.0, Y0 + 3.0)).bounds[1]
        ov = ay_ - land
        hg = (land + 0.25 * ov, land + 0.75 * ov)
        fx, wx = [], []
        for yy in hg:
            sg_ = [s for s in hline(g, yy, ax_ - 1.5, ax_ + 2.0)]
            fx.append(sg_[0][0])
            wx.append(max(e for _, e in hline(secF, yy, ax_ - 1.5, ax_ + 2.0) if e <= fx[-1] + 1e-6))
        hk_t = math.degrees(math.atan((fx[0] - fx[1]) / (hg[1] - hg[0])))
        hk_w = math.degrees(math.atan((wx[0] - wx[1]) / (hg[1] - hg[0])))
        rows.append((k, ax_, ay_, land, ov, g.distance(secF), fx[0] - wx[0], fx[1] - wx[1], hk_t, hk_w))
    print(f"   pawl: {len(tl)} teeth on the slider section (need {PAWL['n_teeth']})")
    for k, ax_, ay_, land, ov, sg_, b0, b1, hk_t, hk_w in rows:
        print(f"     tooth {k} apex X {ax_:.3f} Y {ay_:.4f}; rack land Y {land:.4f} -> OVERLAP {ov:.4f}; seat gap (2D min "
              f"tooth->rack) {sg_:.4f}; horizontal gap at the locking face {b0:.4f} / {b1:.4f} (land +25 % / +75 % of the "
              f"overlap); hook: pawl face {hk_t:.3f}°, rack wall {hk_w:.3f}°")
    # Stops: pad bottom -> stop block top on vertical chords just -X of each block's +X contact edge
    gaps = {}
    for lab, xs_ in (("inner", LAY["inner_x"]), ("outer", LAY["outer_x"])):
        c = [s for s in chord_iv(secS, xs_ - t - 0.05) if s[1] < -20.0]
        gaps[lab] = c[-1][0] - c[-2][1]
    teeth_u = unary_union(tl)
    need = {lab: drop_needed(teeth_u, rack_w, sgn) for lab, sgn in (("open", -1), ("close", +1))}
    print(f"   pawl stops (chords at X inner {LAY['inner_x'] - t - 0.05:.3f} / outer {LAY['outer_x'] - t - 0.05:.3f}): "
          f"inner gap {gaps['inner']:.4f}, outer gap {gaps['outer']:.4f}; rigid drop of all 4 teeth needed to OPEN (-X one "
          f"pitch) {need['open']:.4f} -> inner-stop margin {gaps['inner'] - need['open']:+.4f}; to CLOSE (+X over the "
          f"ramp) {need['close']:.4f} -> margin {gaps['inner'] - need['close']:+.4f}")
    lift = [(d_, swept_hit(teeth_u, rack_w, d_, -1)) for d_ in (gaps["inner"], min(r[4] for r in rows) - 0.05, 0.0)]
    print(f"   LIFT: teeth lowered by the inner stop gap {lift[0][0]:.4f}, swept -X one pitch: max overlap {lift[0][1]:.6f} mm2"
          f" (must be 0); CONTROL drop {lift[1][0]:.4f} (overlap - 0.05): {lift[1][1]:.4f} mm2, CONTROL drop 0: "
          f"{lift[2][1]:.4f} mm2 (both must be > 0)")

    if pose == "min":
        coupling_gates(frame_c, slider_c, handle_c, t)
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
print("GATE 6: support-free check. Down-facing area (n < -0.70711 along the build axis), bed face excluded")


def down_faces(m, axis):
    n, A, c = m.face_normals[:, axis], m.area_faces, m.triangles_center
    bed = (n < -0.999) & (c[:, axis] < m.bounds[0][axis] + 1e-3)
    sel = np.where((n < -0.70711) & ~bed)[0]
    adj = m.face_adjacency
    keep = np.isin(adj[:, 0], sel) & np.isin(adj[:, 1], sel)
    groups = trimesh.graph.connected_components(adj[keep], nodes=sel)
    out = []
    for g in groups:
        g = np.asarray(g)
        lo, hi = m.triangles[g].reshape(-1, 3).min(0), m.triangles[g].reshape(-1, 3).max(0)
        out.append((A[g].sum(), float(n[g].min()), lo, hi, len(g)))
    out.sort(key=lambda q: -q[0])
    steep = A[sel][n[sel] < -0.7072].sum()
    return A[sel].sum(), steep, A[bed].sum(), out


for tag, m, ax_ in (("main_frame flat (-Z on the bed)", fr, 2), ("handle standing (butt on the bed, +Y up)", hd, 1)):
    tot, steep, bed_a, cl = down_faces(m, ax_)
    print(f"  {tag}: down-facing area {tot:.2f} mm2 ({len(cl)} clusters), of which with n < -0.7072 (clearly past 45°) {steep:.2f} mm2;"
          f" bed face {bed_a:.2f} mm2")
    for a, nmin, lo, hi, nf in cl[:8]:
        print(f"    {a:8.2f} mm2  min n {nmin:.5f}  faces {nf:4d}  X {lo[0]:.2f}..{hi[0]:.2f} Y {lo[1]:.2f}..{hi[1]:.2f} "
              f"Z {lo[2]:.2f}..{hi[2]:.2f}")
# round 6 pass 2: the hook outer region on its own (frame flat): faces whose centre lies in the region (+0.3)
_n, _c = fr.face_normals[:, 2], fr.triangles_center
_in = shapely.contains_xy(hook_zone, _c[:, 0], _c[:, 1])
_bed = (_n < -0.999) & (_c[:, 2] < fr.bounds[0][2] + 1e-3)
print(f"  main_frame flat, hook outer region only: {int(_in.sum())} faces; down-facing (n < -0.70711, bed excluded) "
      f"{fr.area_faces[_in & (_n < -0.70711) & ~_bed].sum():.2f} mm2; bed area there {fr.area_faces[_in & _bed].sum():.2f} mm2")
print("=" * 100)
print("done")
