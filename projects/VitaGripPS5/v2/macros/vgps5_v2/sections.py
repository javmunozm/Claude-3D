"""Inputs: y-plane sections of the r16 bake, cleaned into smooth closed loops in (x, z).

Planes are y = const (the handle runs along -Y; every r16 section x >= INNER_X is one closed loop).
"""
import numpy as np
import trimesh
from scipy.interpolate import splprep, splev
from shapely.geometry import Polygon, LineString, box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union


def load_mesh(path):
    return trimesh.load(str(path), force="mesh")


def _largest(geom):
    if geom.is_empty:
        return None
    if geom.geom_type == "Polygon":
        return geom
    return max(geom.geoms, key=lambda g: g.area)


def raw_section(mesh, y, x_min):
    """Filled region of the mesh's y-section with x >= x_min, as one shapely polygon (holes dropped)."""
    s = mesh.section(plane_origin=[0.0, y, 0.0], plane_normal=[0.0, 1.0, 0.0])
    if s is None:
        return None
    polys = [Polygon(e[:, [0, 2]]).buffer(0) for e in s.discrete if len(e) >= 4]
    region = unary_union([p for p in polys if not p.is_empty])
    region = region.intersection(box(x_min, -80.0, 250.0, 80.0))
    p = _largest(region)
    return None if p is None else Polygon(p.exterior)


def _row_extent(poly, z):
    seg = poly.intersection(LineString([(-500.0, z), (500.0, z)]))
    if seg.is_empty:
        return None
    b = seg.bounds
    return b[0], b[2]


def row_fill(poly, x_min, z0, dz=0.25):
    """Fill every row z >= z0 from x_min to the row's outer x (closes pocket, pits and slots)."""
    strips = []
    z = z0
    zmax = poly.bounds[3]
    while z < zmax:
        ext = _row_extent(poly, z + dz / 2.0)
        if ext is not None:
            strips.append(box(x_min, z, ext[1], z + dz + 1e-3))
        z += dz
    out = unary_union([poly] + strips).buffer(0.5).buffer(-0.5)
    return Polygon(_largest(out).exterior)


def cap_sweep(poly, y, ref, p):
    """Handle section with r16's flat top: replace z > cut_z by the hull of the section's band below cut_z and
    the domed cap of the uncut reference section, moved up the handle-top slope and across by the centre drift."""
    cut_z = p["cut_z"]
    zr = ref.bounds[3]
    cap = ref.intersection(box(-500.0, zr - p["cap_h"], 500.0, zr + 1.0))
    a = _row_extent(poly, cut_z - 3.0)
    b = _row_extent(ref, cut_z - 3.0)
    dx = 0.5 * (a[0] + a[1]) - 0.5 * (b[0] + b[1])
    dz = p["handle_top_slope"] * (y - p["cap_ref_y"])
    cap = Polygon(np.asarray(cap.exterior.coords) + [dx, dz])
    band = poly.intersection(box(-500.0, cut_z - 2.0, 500.0, cut_z))
    top = unary_union([band, cap]).convex_hull.intersection(box(-500.0, cut_z - 2.0, 500.0, p["ext_max"]))
    low = poly.intersection(box(-500.0, -500.0, 500.0, cut_z))
    out = unary_union([low, top]).buffer(0.3).buffer(-0.3)
    return Polygon(_largest(out).exterior)


def extend_top(poly, y, top_z, cut_z, ext_max, y0, slope, force=False):
    """Replace the flat-top region (z > cut_z) by straight sides extended to the uncut handle top."""
    if poly.bounds[3] < top_z - 0.05 and not force:
        return poly
    z_ext = min(ext_max, top_z + slope * (y - y0) + 1.2)
    z_ext = max(z_ext, top_z + 1.0)
    a = _row_extent(poly, cut_z)
    b = _row_extent(poly, cut_z - 3.0)
    sl = np.clip([(a[0] - b[0]) / 3.0, (a[1] - b[1]) / 3.0], -0.5, 0.5)
    h = z_ext - cut_z
    trap = Polygon([(a[0], cut_z - 0.3), (a[1], cut_z - 0.3), (a[1] + sl[1] * h, z_ext), (a[0] + sl[0] * h, z_ext)])
    low = poly.intersection(box(-500.0, -500.0, 500.0, cut_z))
    out = unary_union([low, trap]).buffer(0.3).buffer(-0.3)
    return Polygon(_largest(out).exterior)


def smooth_poly(poly, rms):
    """Smoothing periodic spline through the outline, returned as a dense polygon (6000 points)."""
    poly = orient(poly, 1.0)
    ring = poly.exterior
    L = ring.length
    m = max(240, int(L / 0.3))
    pts = np.array([ring.interpolate(t).coords[0] for t in np.linspace(0.0, L, m, endpoint=False)])
    tck, _ = splprep([pts[:, 0], pts[:, 1]], s=m * rms ** 2, per=1)
    return Polygon(np.array(splev(np.linspace(0.0, 1.0, 6000, endpoint=False), tck)).T).buffer(0)


def round_top(poly, h, r, band, res=64):
    """Clip at z = h and open (erode, dilate) by r inside the band z >= h - band: the top corners become r-rounds
    tangent to the flat top, built into the section (no fillet afterwards)."""
    q = _largest(poly.intersection(box(-500.0, -500.0, 500.0, h)))
    # GEOS simplifies a dense outline by up to 0.01 * r inside buffer(): on the 4000-vertex section that tilted
    # the eroded top by 0.013 mm and pulled the flat under TOP_Z (p1_dbg3). Simplify to 0.002 first.
    q = q.simplify(0.002)
    o = _largest(q.buffer(-r, resolution=res).buffer(r, resolution=res))
    zb = h - band
    out = unary_union([o.intersection(box(-500.0, zb, 500.0, h + 1.0)),
                       q.intersection(box(-500.0, -500.0, 500.0, zb + 1e-4))]).buffer(1e-4).buffer(-1e-4)
    return Polygon(_largest(out).exterior)


def resample(poly, n_out):
    """n_out points by arc length, ccw in (x, z), starting below the centroid nearest its x."""
    poly = orient(poly, 1.0)
    ring = poly.exterior
    L = ring.length
    xy = np.array([ring.interpolate(t).coords[0] for t in np.linspace(0.0, L, 8000, endpoint=False)])
    cx, cz = poly.centroid.x, poly.centroid.y
    below = np.where(xy[:, 1] < cz)[0]
    i0 = below[np.argmin(np.abs(xy[below, 0] - cx))]
    xy = np.roll(xy, -i0, axis=0)
    closed = np.vstack([xy, xy[:1]])
    s = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(closed, axis=0), axis=1))]
    t = np.linspace(0.0, s[-1], n_out, endpoint=False)
    return np.column_stack([np.interp(t, s, closed[:, 0]), np.interp(t, s, closed[:, 1])])


def _dense_ring(poly, step=0.05):
    xy = np.asarray(orient(poly, 1.0).exterior.coords)
    s = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(xy, axis=0), axis=1))]
    t = np.arange(0.0, s[-1], step)
    return np.column_stack([np.interp(t, s, xy[:, 0]), np.interp(t, s, xy[:, 1])]), poly.centroid


def _seg_resample(pts, n):
    """n points by arc length along an open polyline, first point included, last excluded."""
    s = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
    t = np.linspace(0.0, s[-1], n, endpoint=False)
    return np.column_stack([np.interp(t, s, pts[:, 0]), np.interp(t, s, pts[:, 1])])


def _seg_graded(pts, n, ga, gb):
    """n points along an open polyline (first included, last excluded); the spacing runs smoothly from ga at the
    start to gb at the end (cubic Hermite arc-length map), so a uniform-parameter spline has no speed jump."""
    s = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
    L = s[-1]
    ma, mb = np.clip([ga * n, gb * n], 0.2 * L, 2.5 * L)
    t = np.arange(n) / n
    S = (2 * t ** 3 - 3 * t ** 2 + 1) * 0.0 + (t ** 3 - 2 * t ** 2 + t) * ma + (-2 * t ** 3 + 3 * t ** 2) * L \
        + (t ** 3 - t ** 2) * mb
    S = np.maximum.accumulate(np.clip(S, 0.0, L))
    return np.column_stack([np.interp(S, s, pts[:, 0]), np.interp(S, s, pts[:, 1])])


def resample_aligned(poly, counts, depth):
    """Three segments with fixed point counts, so that index i means the same feature on every station:
    bottom start -> top segment start, top segment (boundary within depth of the section's top), top segment end
    -> bottom start. counts = (n_from_start, n_top, n_to_start). Use with uniform spline parameters.
    The spacing is graded across the segment junctions (geometric mean of the neighbours' mean spacing)."""
    xy, c = _dense_ring(poly)
    m = len(xy)
    below = np.where(xy[:, 1] < c.y)[0]
    xy = np.roll(xy, -below[np.argmin(np.abs(xy[below, 0] - c.x))], axis=0)
    zt = xy[:, 1].max()
    on = xy[:, 1] >= zt - depth
    i_top = int(np.argmax(xy[:, 1]))
    ia = i_top
    while on[(ia - 1) % m] and ia - 1 > 0:
        ia -= 1
    ib = i_top
    while on[(ib + 1) % m] and ib + 1 < m - 1:
        ib += 1
    closed = np.vstack([xy, xy[:1]])
    segs = [closed[:ia + 1], closed[ia:ib + 1], closed[ib:]]
    mean = [np.linalg.norm(np.diff(g, axis=0), axis=1).sum() / n for g, n in zip(segs, counts)]
    j = [np.sqrt(mean[2] * mean[0]), np.sqrt(mean[0] * mean[1]), np.sqrt(mean[1] * mean[2])]
    return np.vstack([_seg_graded(segs[0], counts[0], j[0], j[1]), _seg_graded(segs[1], counts[1], j[1], j[2]),
                      _seg_graded(segs[2], counts[2], j[2], j[0])])


def _ramp(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _band_w(v, a, b, c, d):
    """0 below a, smooth rise to 1 at b, 1 to c, smooth fall to 0 at d."""
    return _ramp((v - a) / (b - a)) * (1.0 - _ramp((v - c) / (d - c)))


def inner_smooth(poly, y, p):
    """S5: Gaussian smoothing (sigma along the outline) of the handle's inner flank below the top round, weighted
    by smooth ramps in z, x and y, so the band's bend gets a larger radius without a new edge at the band ends."""
    s5 = p.get("s5")
    if not s5:
        return poly
    wy = _band_w(y, *s5["y"])
    if wy <= 0.0:
        return poly
    from scipy.ndimage import gaussian_filter1d
    xy, _ = _dense_ring(poly, 0.05)
    sg = s5["sigma"] / 0.05
    sm = np.column_stack([gaussian_filter1d(xy[:, 0], sg, mode="wrap"), gaussian_filter1d(xy[:, 1], sg, mode="wrap")])
    w = wy * _band_w(xy[:, 1], *s5["z"]) * (1.0 - _ramp((xy[:, 0] - s5["x"][0]) / (s5["x"][1] - s5["x"][0])))
    return _largest(Polygon(xy + w[:, None] * (sm - xy)).buffer(0))


def tall_rear(poly, p):
    """Rear-corner station (y > force_ext_y): r16's section below rear_cut_z, extended straight up to ext_max, so
    every grip-end station has the same tall form and one loft runs through the corner (the corner's top is then
    cut by the clip cutter, see shapes.clip_cutter)."""
    cz = p["rear_cut_z"]
    a = _row_extent(poly, cz)
    b = _row_extent(poly, cz - 1.5) or a
    # the lean follows the rows below cz; it leans the outer side out at y 61..64 and leaves a fin at the wall end
    # ((96, 64, 0), 155 deg). A fixed inward lean (-0.1) removed it but broke the tip fillet, the plate-front fillet
    # and the pit cut (builds 2 and 3): open, see audit/p1b/fix_report.md
    sl = np.clip([(a[0] - b[0]) / 1.5, (a[1] - b[1]) / 1.5], -p["rear_lean"], p["rear_lean"])
    h = p["ext_max"] - cz
    trap = Polygon([(a[0], cz - 0.3), (a[1], cz - 0.3), (a[1] + sl[1] * h, p["ext_max"]),
                    (a[0] + sl[0] * h, p["ext_max"])])
    low = poly.intersection(box(-500.0, -500.0, 500.0, cz))
    out = unary_union([low, trap]).buffer(0.3).buffer(-0.3)
    return Polygon(_largest(out).exterior)


def top_heights(poly, xs, h, low):
    """Upper envelope of the polygon's outline on the x grid, capped at h; low where the grid is outside it."""
    xy, _ = _dense_ring(poly, 0.02)
    dx = xs[1] - xs[0]
    i = np.round((xy[:, 0] - xs[0]) / dx).astype(int)
    ok = (i >= 0) & (i < len(xs))
    out = np.full(len(xs), low)
    np.maximum.at(out, i[ok], xy[ok, 1])
    return np.minimum(out, h)


def ball_opening(h0, dx, dy, r):
    """Grey opening of the height field h0 (rows y, columns x) by a ball of radius r: the top surface a ball rolled
    under it can reach (r16's top_cut() rolled edge, here as a section input)."""
    from scipy.ndimage import grey_erosion, grey_dilation
    nx, ny = int(np.ceil(r / dx)), int(np.ceil(r / dy))
    qy, qx = np.meshgrid(np.arange(-ny, ny + 1) * dy, np.arange(-nx, nx + 1) * dx, indexing="ij")
    q2 = qx ** 2 + qy ** 2
    fp = q2 <= r * r
    b = np.where(fp, np.sqrt(np.clip(r * r - q2, 0.0, None)), 0.0)
    c = grey_erosion(h0, footprint=fp, structure=b, mode="nearest")
    return grey_dilation(c, footprint=fp, structure=b, mode="nearest")


def uturn_field(mesh, p, rowfill_from, log=print):
    """3D rolling-ball opening of the handle top around the U-turn (N2). Returns (xs, {y: opened heights})."""
    u = p["uturn"]
    xs = np.arange(u["x"][0], u["x"][1] + 1e-9, u["dx"])
    ys = np.arange(u["y"][0], u["y"][1] + 1e-9, u["dy"])
    ref = raw_section(mesh, p["cap_ref_y"], p["inner_x"])
    low = p["top_z"] - 30.0
    H = np.vstack([top_heights(pre_round(mesh, float(y), ref, p, rowfill_from), xs, p["round_h"], low) for y in ys])
    O = ball_opening(H, u["dx"], u["dy"], p["round_r"])
    # only the top band: below it the field's y ends would step against the stations outside the field
    O = np.maximum(O, np.minimum(H, p["round_h"] - p["round_r"] - 0.5))
    d = np.where(H > p["top_z"] - 6.0, H - O, 0.0)
    i, j = np.unravel_index(int(np.argmax(d)), d.shape)
    log("  U-turn field: %d x %d nodes; within 6 mm of the top the opening takes off up to %.3f mm at "
        "(%.2f, %.2f, %.2f)" % (len(ys), len(xs), float(d[i, j]), xs[j], ys[i], H[i, j]))
    return xs, {round(float(y), 3): O[i] for i, y in enumerate(ys)}


def under(xs, o, z_floor=-100.0):
    return Polygon([(xs[0], z_floor)] + list(zip(xs.tolist(), o.tolist())) + [(xs[-1], z_floor)]).buffer(0)


def pre_round(mesh, y, ref, p, rowfill_from):
    """Section before the top round: r16 section, filled / capped / extended, smoothed, S5 band smoothed."""
    poly = raw_section(mesh, y, p["inner_x"])
    if poly is None:
        raise RuntimeError("no section at y %.2f" % y)
    body = rowfill_from is not None and y >= rowfill_from
    if body:
        poly = row_fill(poly, p["inner_x"], p["rowfill_z0"])
        if y <= p["force_ext_y"]:
            poly = cap_sweep(poly, y, ref, p)
        else:
            poly = tall_rear(poly, p)
    elif poly.bounds[3] >= p["top_z"] - 0.05:
        poly = cap_sweep(poly, y, ref, p)
    return inner_smooth(smooth_poly(poly, p["rms"]), y, p)


def finish_loop(poly, p, z_top=None, cut=None, presmoothed=False):
    """Smooth, build the top round in (p["round_r"] > 0), resample; returns (loop, dense polygon or None).
    cut: optional polygon (the region under the U-turn's 3D rolled top) intersected after the 2D round."""
    if not p.get("round_r"):
        return smooth_loop(poly, p["n_pts"], p["rms"]), None
    sm = poly if presmoothed else smooth_poly(poly, p["rms"])
    sm = round_top(sm, p["round_h"] if z_top is None else z_top, p["round_r"], p["round_band"])
    if cut is not None:
        sm = Polygon(_largest(sm.intersection(cut)).exterior)
    if p.get("seg_counts"):
        return resample_aligned(sm, p["seg_counts"], p["seg_depth"]), sm
    return resample(sm, p["n_pts"]), sm


def smooth_loop(poly, n_out, rms):
    """Smoothing periodic spline through the outline; n_out points, ccw in (x, z), start below the centroid."""
    poly = orient(poly, 1.0)
    ring = poly.exterior
    L = ring.length
    m = max(240, int(L / 0.3))
    pts = np.array([ring.interpolate(t).coords[0] for t in np.linspace(0.0, L, m, endpoint=False)])
    tck, _ = splprep([pts[:, 0], pts[:, 1]], s=m * rms ** 2, per=1)
    xy = np.array(splev(np.linspace(0.0, 1.0, 6000, endpoint=False), tck)).T
    cx, cz = poly.centroid.x, poly.centroid.y
    below = np.where(xy[:, 1] < cz)[0]
    i0 = below[np.argmin(np.abs(xy[below, 0] - cx))]
    xy = np.roll(xy, -i0, axis=0)
    closed = np.vstack([xy, xy[:1]])
    s = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(closed, axis=0), axis=1))]
    t = np.linspace(0.0, s[-1], n_out, endpoint=False)
    return np.column_stack([np.interp(t, s, closed[:, 0]), np.interp(t, s, closed[:, 1])])


def station_loops(mesh, ys, p, rowfill_from=None, log=print, dense=None):
    """Cleaned, smoothed loops [(y, Nx2 array)] for the given stations. p: dict of section parameters.
    dense: optional dict, filled with {y: dense finished polygon} (rounded stations only)."""
    out = []
    ref = raw_section(mesh, p["cap_ref_y"], p["inner_x"])
    field = p.get("uturn_field")
    for y in ys:
        a0 = raw_section(mesh, y, p["inner_x"]).area
        poly = pre_round(mesh, y, ref, p, rowfill_from)
        cut = None
        if field is not None and round(float(y), 3) in field[1]:
            cut = under(field[0], field[1][round(float(y), 3)])
        loop, sm = finish_loop(poly, p, None, cut, presmoothed=True)
        if dense is not None and sm is not None:
            dense[y] = sm
        b = poly.bounds
        log("  station y %7.2f  x %6.2f..%6.2f  z %6.2f..%6.2f  area r16 %7.1f -> %7.1f%s"
            % (y, b[0], b[2], b[1], b[3], a0, poly.area, "" if cut is None else "  3D-rolled top"))
        out.append((y, loop))
    return out


def _zlo(poly, x):
    s = poly.intersection(LineString([(x, -500.0), (x, 500.0)]))
    if s.is_empty:
        raise RuntimeError("no underside at x %.2f" % x)
    return s.bounds[1]


def underside(poly, x, dx=0.5):
    """Lowest z of the polygon at x, and its slope dz/dx (central difference over +-dx)."""
    return _zlo(poly, x), (_zlo(poly, x + dx) - _zlo(poly, x - dx)) / (2.0 * dx)


def blend_profile(poly, b):
    """Plate-to-grip blend section (x, z) for one station, from the grip's finished polygon.
    Bottom: flat at the plate bottom from x_s - 1 to x_h, then a cubic (Bezier) that leaves the plate level
    tangentially and meets the grip's underside at x_a, alpha degrees shallower than it (a clear crossing, so the
    union does not meet a tangent surface), then continues 1.5 mm inside the grip. Top: z_t, under the floor
    (the plate boxes fill up to the floor, so no face of this loft coincides with the floor or the plate bottom).
    Returns dict: bezier (4 control points), corners (polyline from the Bezier's end around to its start)."""
    z0, xs, xh, xa, zt = b["z0"], b["x_s"], b["x_h"], b["x_a"], b["z_t"]
    za, sa = underside(poly, xa)
    s_h = np.tan(np.arctan(sa) + np.radians(b["alpha"]))
    L = xa - xh
    bez = [(xh, z0), (xh + L / 3.0, z0), (xa - L / 3.0, za - s_h * L / 3.0), (xa, za)]
    xe = xa + b["ext"]
    ze = za + s_h * b["ext"]
    corners = [(xa, za), (xe, ze), (xe, zt), (xs - 1.0, zt), (xs - 1.0, z0), (xh, z0)]
    # the blend must stay under the grip between the grip's inner clip and x_a
    t = np.linspace(0.0, 1.0, 41)
    P = np.array(bez)
    curve = ((1 - t) ** 3)[:, None] * P[0] + (3 * (1 - t) ** 2 * t)[:, None] * P[1] \
        + (3 * (1 - t) * t ** 2)[:, None] * P[2] + (t ** 3)[:, None] * P[3]
    margin = min(_zlo(poly, x) - z for x, z in curve if b["grip_x"] + 0.05 <= x < xa - 0.05)
    return dict(bezier=bez, corners=corners, za=za, slope_grip=sa, slope_blend=s_h, margin=margin)


def shrunk(loop, scale):
    """Loop scaled about its centroid (keeps an overlap section strictly inside its neighbour)."""
    c = loop.mean(axis=0)
    return c + (loop - c) * scale


def extrapolate(loops, ys_new):
    """Linear point-wise extrapolation from the last two stations."""
    (y1, a), (y2, b) = loops[-2], loops[-1]
    return [(y, b + (b - a) * (y - y2) / (y2 - y1)) for y in ys_new]
