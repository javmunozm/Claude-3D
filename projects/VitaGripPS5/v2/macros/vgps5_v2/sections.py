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


def station_loops(mesh, ys, p, rowfill_from=None, log=print):
    """Cleaned, smoothed loops [(y, Nx2 array)] for the given stations. p: dict of section parameters."""
    out = []
    ref = raw_section(mesh, p["cap_ref_y"], p["inner_x"])
    for y in ys:
        poly = raw_section(mesh, y, p["inner_x"])
        if poly is None:
            raise RuntimeError("no section at y %.2f" % y)
        a0 = poly.area
        body = rowfill_from is not None and y >= rowfill_from
        if body:
            poly = row_fill(poly, p["inner_x"], p["rowfill_z0"])
            if y <= p["force_ext_y"]:
                poly = cap_sweep(poly, y, ref, p)
        elif poly.bounds[3] >= p["top_z"] - 0.05:
            poly = cap_sweep(poly, y, ref, p)
        loop = smooth_loop(poly, p["n_pts"], p["rms"])
        b = poly.bounds
        log("  station y %7.2f  x %6.2f..%6.2f  z %6.2f..%6.2f  area r16 %7.1f -> %7.1f"
            % (y, b[0], b[2], b[1], b[3], a0, poly.area))
        out.append((y, loop))
    return out


def shrunk(loop, scale):
    """Loop scaled about its centroid (keeps an overlap section strictly inside its neighbour)."""
    c = loop.mean(axis=0)
    return c + (loop - c) * scale


def extrapolate(loops, ys_new):
    """Linear point-wise extrapolation from the last two stations."""
    (y1, a), (y2, b) = loops[-2], loops[-1]
    return [(y, b + (b - a) * (y - y2) / (y2 - y1)) for y in ys_new]
