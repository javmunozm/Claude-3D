"""Gates on the exported STL: topology, mirror deviation, deviation from r16's right handle."""
import numpy as np
import trimesh


def topology(mesh):
    parts = mesh.split(only_watertight=False)
    return dict(watertight=bool(mesh.is_watertight), bodies=len(parts), faces=len(mesh.faces),
                volume=float(mesh.volume), bounds=mesh.bounds.round(3).tolist())


def _samples(mesh, n, seed=1):
    pts, _ = trimesh.sample.sample_surface_even(mesh, n, seed=seed)
    return np.vstack([pts, mesh.vertices])


def mirror_deviation(mesh, n=40000):
    pts = _samples(mesh, n)
    mir = pts * np.array([-1.0, 1.0, 1.0])
    _, d, _ = trimesh.proximity.closest_point(mesh, mir)
    return float(d.max()), float(np.sqrt(np.mean(d ** 2)))


def _region(pts, y_lo, y_hi):
    return (pts[:, 0] > 0.0) & (pts[:, 1] >= y_lo) & (pts[:, 1] <= y_hi)


def edge_creases(solid, inside, n=15):
    """[(edge centre, length, geom type, max / median crease deg)] for edges whose centre passes inside(c).
    Crease = angle between the two adjacent faces' normals (0 = tangent, 90 = square corner)."""
    faces = solid.faces()
    out = []
    for e in solid.edges():
        c = e.center()
        if not inside(c):
            continue
        fs = [f for f in faces if any(e.is_same(fe) for fe in f.edges())]
        if len(fs) != 2:
            continue
        a = []
        for t in np.linspace(0.03, 0.97, n):
            p = e.position_at(t)
            n0, n1 = fs[0].normal_at(p), fs[1].normal_at(p)
            a.append(np.degrees(np.arccos(np.clip(n0.dot(n1), -1.0, 1.0))))
        out.append(((round(c.X, 2), round(c.Y, 2), round(c.Z, 2)), round(e.length, 2), e.geom_type.name,
                    round(float(max(a)), 2), round(float(np.median(a)), 2)))
    return out


def round_radii(solid, zone, nu=160, nv=160, r_max=None, box6=None):
    """Principal radius across the round (1 / max |curvature|) on B-spline faces, at uv-grid points p with
    zone(p) True. r_max: leave out radii above it (other faces in the zone); box6: skip faces whose bounding box
    misses it. Returns (n, min, p5, median, p95, max, location of min)."""
    from OCP.BRep import BRep_Tool
    from OCP.BRepTools import BRepTools
    from OCP.GeomLProp import GeomLProp_SLProps
    from OCP.TopoDS import TopoDS
    from OCP.BRepTopAdaptor import BRepTopAdaptor_FClass2d
    from OCP.gp import gp_Pnt2d
    from OCP.TopAbs import TopAbs_IN
    rr, where = [], []
    for f in solid.faces():
        if f.geom_type.name != "BSPLINE":
            continue
        if box6 is not None:
            bb = f.bounding_box()
            if (bb.max.X < box6[0] or bb.min.X > box6[1] or bb.max.Y < box6[2] or bb.min.Y > box6[3]
                    or bb.max.Z < box6[4] or bb.min.Z > box6[5]):
                continue
        face = TopoDS.Face_s(f.wrapped)
        srf = BRep_Tool.Surface_s(face)
        u0, u1, v0, v1 = BRepTools.UVBounds_s(face)
        cls = BRepTopAdaptor_FClass2d(face, 1e-6)
        for u in np.linspace(u0, u1, nu):
            for v in np.linspace(v0, v1, nv):
                if cls.Perform(gp_Pnt2d(u, v)) != TopAbs_IN:
                    continue
                pr = GeomLProp_SLProps(srf, u, v, 2, 1e-7)
                p = pr.Value()
                q = (p.X(), p.Y(), p.Z())
                if not zone(q) or not pr.IsCurvatureDefined():
                    continue
                k = max(abs(pr.MaxCurvature()), abs(pr.MinCurvature()))
                if k > 1e-9 and (r_max is None or 1.0 / k <= r_max):
                    rr.append(1.0 / k)
                    where.append(q)
    if not rr:
        return dict(n=0)
    rr = np.array(rr)
    i = int(np.argmin(rr))
    return dict(n=len(rr), min=round(float(rr.min()), 3), p5=round(float(np.percentile(rr, 5)), 3),
                median=round(float(np.median(rr)), 3), p95=round(float(np.percentile(rr, 95)), 3),
                max=round(float(rr.max()), 3), min_at=[round(c, 2) for c in where[i]])


def handle_smoothness(mesh, y_lo=-63.0, y_hi=-15.0, z_max=8.4, step=0.5):
    """Right handle (x > 0): STL edges with dihedral > 30 / > 8 deg (y < -14.5), and the max turn between
    +-1 mm chords on y-sections every 0.5 mm, loop resampled at 0.5 mm, points with z < z_max."""
    from shapely.geometry import Polygon
    adj = mesh.face_adjacency
    ang = np.degrees(mesh.face_adjacency_angles)
    mid = mesh.vertices[mesh.face_adjacency_edges].mean(axis=1)
    sel = (mid[:, 0] > 0.0) & (mid[:, 1] < -14.5)
    out = dict(dihedral_max=round(float(ang[sel].max()), 2), edges_gt30=int((ang[sel] > 30).sum()),
               edges_gt8=int((ang[sel] > 8).sum()))
    best = (0.0, None)
    for y in np.arange(y_lo, y_hi + 1e-9, step):
        s = mesh.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0])
        if s is None:
            continue
        loops = [e[:, [0, 2]] for e in s.discrete if e[:, 0].mean() > 0 and len(e) > 8]
        if not loops:
            continue
        ring = Polygon(max(loops, key=lambda e: Polygon(e).area)).exterior
        L = ring.length
        pts = np.array([ring.interpolate(t).coords[0] for t in np.arange(0.0, L, step)])
        a = np.roll(pts, 2, axis=0) - pts
        b = np.roll(pts, -2, axis=0) - pts
        cosang = (a * b).sum(1) / (np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1))
        turn = 180.0 - np.degrees(np.arccos(np.clip(cosang, -1, 1)))
        turn[pts[:, 1] >= z_max] = 0.0
        i = int(np.argmax(turn))
        if turn[i] > best[0]:
            best = (float(turn[i]), (round(pts[i, 0], 2), round(float(y), 2), round(pts[i, 1], 2)))
    out["turn_max"] = round(best[0], 2)
    out["turn_max_at"] = best[1]
    return out


def flat_top_outline(mesh, top_z, step=0.5):
    """Points every <= step mm along the boundary of the flat top (faces at top_z with normal +Z)."""
    fn = mesh.face_normals
    c = mesh.triangles_center
    sel = np.where((fn[:, 2] > 0.99999) & (np.abs(c[:, 2] - top_z) < 1e-3))[0]
    e = np.sort(mesh.faces[sel][:, [[0, 1], [1, 2], [2, 0]]].reshape(-1, 2), axis=1)
    u, cnt = np.unique(e, axis=0, return_counts=True)
    pts = []
    for a, b in u[cnt == 1]:
        pa, pb = mesh.vertices[a], mesh.vertices[b]
        k = max(1, int(np.ceil(np.linalg.norm(pb - pa) / step)))
        pts.append(pa + np.linspace(0.0, 1.0, k + 1)[:, None] * (pb - pa))
    return np.vstack(pts)


def deviation(v2, r16, regions, band=None, n=150000):
    """Both directions, per region {name: (x_lo, x_hi, y_lo, y_hi)}: rms, p95, max (mm).
    band: (outline points, d) - points within d of the flat top's outline are left out (the top-round band)."""
    from scipy.spatial import cKDTree
    a = _samples(v2, n, 2)
    b = _samples(r16, n, 3)
    tree = cKDTree(band[0]) if band is not None else None
    out = {}
    for name, (x0, x1, y0, y1) in regions.items():
        row = {}
        for tag, pts, target in (("v2->r16", a, r16), ("r16->v2", b, v2)):
            m = (pts[:, 0] > x0) & (pts[:, 0] < x1) & (pts[:, 1] >= y0) & (pts[:, 1] <= y1)
            if tree is not None:
                m &= tree.query(pts)[0] > band[1]
            p = pts[m]
            _, d, _ = trimesh.proximity.closest_point(target, p)
            row[tag] = dict(n=len(p), rms=round(float(np.sqrt(np.mean(d ** 2))), 3),
                            p95=round(float(np.percentile(d, 95)), 3), max=round(float(d.max()), 3),
                            max_at=p[int(np.argmax(d))].round(2).tolist())
        out[name] = row
    return out


def box_dihedral(mesh, box6, deg=30.0):
    """STL edges with midpoints in box6 (x0, x1, y0, y1, z0, z1): count, count > deg, max dihedral and where."""
    ang = np.degrees(mesh.face_adjacency_angles)
    mid = mesh.vertices[mesh.face_adjacency_edges].mean(axis=1)
    lo, hi = np.array(box6[0::2]), np.array(box6[1::2])
    s = np.all((mid > lo) & (mid < hi), axis=1)
    if not s.any():
        return dict(n=0)
    i = int(np.argmax(np.where(s, ang, -1.0)))
    return dict(n=int(s.sum()), over=int((s & (ang > deg)).sum()), max=round(float(ang[i]), 2),
                max_at=mid[i].round(3).tolist())


def change_vs(new, ref, boxes):
    """Max distance, both ways, of each mesh's vertices to the other mesh, per {name: ([box6, ...], inside)}: inside
    True takes the vertices in any of the boxes, False the vertices outside all of them. Vertices that coincide with a vertex of the other
    mesh (< 1e-7) count 0; the rest are measured to the surface (trimesh closest_point)."""
    from scipy.spatial import cKDTree
    out = {k: dict(max=0.0, max_at=None, n=0) for k in boxes}
    for a, b in ((new, ref), (ref, new)):
        d, _ = cKDTree(b.vertices).query(a.vertices)
        idx = np.where(d > 1e-7)[0]
        if len(idx):
            _, dd, _ = trimesh.proximity.closest_point(b, a.vertices[idx])
            d[idx] = np.minimum(d[idx], dd)
        for k, (b6s, inside) in boxes.items():
            s = np.zeros(len(a.vertices), bool)
            for b6 in b6s:
                lo, hi = np.array(b6[0::2]), np.array(b6[1::2])
                s |= np.all((a.vertices > lo) & (a.vertices < hi), axis=1)
            s = s if inside else ~s
            if s.any():
                i = int(np.argmax(np.where(s, d, -1.0)))
                out[k]["n"] += int(s.sum())
                if d[i] >= out[k]["max"]:
                    out[k]["max"], out[k]["max_at"] = round(float(d[i]), 5), a.vertices[i].round(3).tolist()
    return out


def topology_p2(mesh):
    """Pass 2: watertight, winding, bodies, Euler number and genus (one closed surface: genus = (2 - euler) / 2)."""
    parts = mesh.split(only_watertight=False)
    eu = int(mesh.euler_number)
    return dict(watertight=bool(mesh.is_watertight), winding=bool(mesh.is_winding_consistent), bodies=len(parts),
                euler=eu, genus=(2 - eu) / 2.0 if len(parts) == 1 else None)


def zregion(mesh, z):
    """Material region of the z-section (shapely), loops combined even-odd."""
    from shapely.geometry import Polygon
    s = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    g = Polygon()
    if s is None:
        return g
    for e in s.discrete:
        if len(e) > 3:
            g = g.symmetric_difference(Polygon(e[:, :2]).buffer(0))
    return g


def lip_u(mesh, fingers, zs, u_lo=-4.0, u_hi=0.6):
    """Lip u per finger (p, n) and Z: the smallest u (outward along n from the pocket wall point p) with material on
    the segment u_lo..u_hi of the z-section."""
    from shapely.geometry import LineString
    out = []
    for p, n in fingers:
        p, n = np.asarray(p, float), np.asarray(n, float) / np.linalg.norm(n)
        row = {}
        for z in zs:
            g = zregion(mesh, z)
            seg = LineString([p + u_lo * n, p + u_hi * n])
            hit = g.intersection(seg)
            if hit.is_empty:
                row["%.2f" % z] = None
                continue
            pts = np.array([c for geom in getattr(hit, "geoms", [hit]) for c in geom.coords])
            row["%.2f" % z] = round(float(((pts - p) @ n).min()), 4)
        out.append(dict(p=[round(float(c), 3) for c in p], u=row))
    return out


def pocket_wall_dev(meshes, pocket, zs, keep):
    """Distance of r16's pocket outline points (keep(pt) True) to each mesh's z-section boundary; per z the max over
    the points where the reference mesh (first) lies within 0.005, and the reference's own max."""
    out = {}
    P = np.asarray(pocket, float)
    P = P[[keep(q) for q in P]]
    from shapely.geometry import Point
    for z in zs:
        ds = []
        for m in meshes:
            b = zregion(m, z).boundary
            ds.append(np.array([b.distance(Point(q)) for q in P]))
        ok = ds[0] <= 0.005
        row = dict(n=int(len(P)), n_ref_on=int(ok.sum()), ref_max=round(float(ds[0].max()), 4))
        for k, d in enumerate(ds[1:], 1):
            i = int(np.argmax(np.where(ok, d, -1.0)))
            row["mesh%d_max_where_ref_on" % k] = round(float(d[i]), 4)
            row["mesh%d_max_at" % k] = P[i].round(2).tolist()
        out["z%.1f" % z] = row
    return out


def floor_check(mesh, pts, z_floor, ds=(0.005, 0.02)):
    """Floor plane lock: at each (x, y) the z-section at z_floor + d must be air and at z_floor - d material."""
    import shapely
    out = {}
    for d in ds:
        up, dn = zregion(mesh, z_floor + d), zregion(mesh, z_floor - d)
        out["+-%.3f" % d] = dict(n=len(pts), material_above=int(shapely.contains_xy(up, pts[:, 0], pts[:, 1]).sum()),
                                 air_below=int((~shapely.contains_xy(dn, pts[:, 0], pts[:, 1])).sum()))
    return out


def holes_at(mesh, z, near):
    """Interior rings of the z-section whose centre is within 'near' (x, y, tol) boxes: {name: ring polygon}."""
    from shapely.geometry import Polygon
    g = zregion(mesh, z)
    out = {}
    for pg in getattr(g, "geoms", [g]):
        for r in pg.interiors:
            q = Polygon(r)
            c = q.centroid
            for name, (x, y, tol) in near.items():
                if abs(c.x - x) < tol and abs(c.y - y) < tol:
                    out[name] = q
    return out


def hole_lock(a, b, z, near):
    """Hole outlines of mesh a against mesh b at z: Hausdorff distance, bounds of each, area."""
    ha, hb = holes_at(a, z, near), holes_at(b, z, near)
    out = {}
    for k in near:
        if k not in ha or k not in hb:
            out[k] = dict(found=(k in ha, k in hb))
            continue
        from shapely.geometry import Point
        ra, rb = ha[k].exterior, hb[k].exterior
        sa = [ra.interpolate(t) for t in np.arange(0.0, ra.length, 0.05)]
        da = np.array([rb.distance(q) for q in sa])
        sb = [rb.interpolate(t) for t in np.arange(0.0, rb.length, 0.05)]
        db = np.array([ra.distance(q) for q in sb])
        out[k] = dict(a_to_b_max=round(float(da.max()), 4), a_to_b_at=np.round(sa[int(np.argmax(da))].coords[0], 3).tolist(),
                      b_to_a_max=round(float(db.max()), 4), b_to_a_at=np.round(sb[int(np.argmax(db))].coords[0], 3).tolist(),
                      hausdorff=round(float(ra.hausdorff_distance(rb)), 4),
                      bounds=np.round(ha[k].bounds, 4).tolist(), ref_bounds=np.round(hb[k].bounds, 4).tolist(),
                      area=round(ha[k].area, 3), ref_area=round(hb[k].area, 3))
    return out


def box_dev(a, b, box6):
    """Vertices of each mesh inside box6 to the other mesh's surface: max both ways and where."""
    lo, hi = np.array(box6[0::2]), np.array(box6[1::2])
    out = {}
    for tag, m, t in (("a->b", a, b), ("b->a", b, a)):
        v = m.vertices[np.all((m.vertices > lo) & (m.vertices < hi), axis=1)]
        if not len(v):
            out[tag] = dict(n=0)
            continue
        _, d, _ = trimesh.proximity.closest_point(t, v)
        i = int(np.argmax(d))
        out[tag] = dict(n=len(v), max=round(float(d.max()), 5), p99=round(float(np.percentile(d, 99)), 5),
                        max_at=v[i].round(3).tolist())
    return out


def opening_table(mesh, zs, y_front=-9.3, x0=60.0, x1=75.0, step=0.05, wall_x=None):
    """Bottom opening: per z, the first x (from x0 outward) with material at y < y_front, and (wall_x) the material's
    y extent in front of the pocket line at x = wall_x (ring wall in front of the closed end)."""
    from shapely.geometry import box as sbox
    out = {}
    for z in zs:
        g = zregion(mesh, z)
        hit = None
        for x in np.arange(x0, x1, step):
            if not g.intersection(sbox(x - 0.002, -40.0, x + 0.002, y_front)).is_empty:
                hit = round(float(x), 3)
                break
        row = dict(first_x=hit)
        if wall_x is not None:
            s = g.intersection(sbox(wall_x - 0.002, -40.0, wall_x + 0.002, -9.0))
            row["wall_y_min_at_x%.2f" % wall_x] = None if s.is_empty else round(float(s.bounds[1]), 3)
        out["z%.1f" % z] = row
    return out


def sealed_air(mesh, boxes, step=0.5, reach=60.0):
    """Flood-fill sky test. Air voxels (outside the z-section's material grown 0.02) on a step grid in each box
    (x0, x1, y0, y1, z0, z1); seeds = the top / bottom layer's air voxels whose +Z / -Z ray leaves the mesh (VTK
    OBBTree); air components (6-connected) without a seed are reported as sealed (or connected only outside the box).
    The z-sections are shared between boxes."""
    import shapely
    import vtk
    from scipy import ndimage
    from vtk.util import numpy_support as ns
    pts = vtk.vtkPoints()
    pts.SetData(ns.numpy_to_vtk(np.ascontiguousarray(mesh.vertices, dtype=np.float64), deep=True))
    cells = vtk.vtkCellArray()
    f = np.hstack([np.full((len(mesh.faces), 1), 3), mesh.faces]).astype(np.int64).ravel()
    cells.SetCells(len(mesh.faces), ns.numpy_to_vtkIdTypeArray(f, deep=True))
    pd = vtk.vtkPolyData()
    pd.SetPoints(pts)
    pd.SetPolys(cells)
    tree = vtk.vtkOBBTree()
    tree.SetDataSet(pd)
    tree.BuildLocator()
    hp, hc = vtk.vtkPoints(), vtk.vtkIdList()
    cache = {}
    out = {}
    for name, b in boxes.items():
        xs = np.arange(b[0], b[1] + 1e-9, step)
        ys = np.arange(b[2], b[3] + 1e-9, step)
        zs = np.arange(b[4], b[5] + 1e-9, step)
        X, Y = np.meshgrid(xs, ys, indexing="ij")
        air = np.zeros((len(xs), len(ys), len(zs)), bool)
        for k, z in enumerate(zs):
            key = round(float(z), 4)
            if key not in cache:
                cache[key] = zregion(mesh, z).buffer(0.02)
            air[:, :, k] = ~shapely.contains_xy(cache[key], X, Y)
        seed = np.zeros_like(air)
        for i, x in enumerate(xs):
            for j, y in enumerate(ys):
                if air[i, j, -1] and tree.IntersectWithLine((x, y, zs[-1]), (x, y, zs[-1] + reach), hp, hc) == 0:
                    seed[i, j, -1] = True
                if air[i, j, 0] and tree.IntersectWithLine((x, y, zs[0]), (x, y, zs[0] - reach), hp, hc) == 0:
                    seed[i, j, 0] = True
        lab, n = ndimage.label(air)
        open_ids = set(np.unique(lab[seed]).tolist()) - {0}
        sealed = air & ~np.isin(lab, list(open_ids))
        idx = np.argwhere(sealed)
        out[name] = dict(air=int(air.sum()), seeds=int(seed.sum()), components=int(n), open=len(open_ids),
                         sealed=int(sealed.sum()),
                         first=[[round(float(xs[a]), 2), round(float(ys[c]), 2), round(float(zs[e]), 2)]
                                for a, c, e in idx[:5]])
    return out


def band_dihedral(mesh, box):
    """STL edges with midpoints in box (x0, x1, y0, y1): count, max / p99 dihedral (deg) and where the max is."""
    ang = np.degrees(mesh.face_adjacency_angles)
    mid = mesh.vertices[mesh.face_adjacency_edges].mean(axis=1)
    x0, x1, y0, y1 = box
    s = (mid[:, 0] > x0) & (mid[:, 0] < x1) & (mid[:, 1] > y0) & (mid[:, 1] < y1)
    i = int(np.argmax(np.where(s, ang, -1.0)))
    return dict(n=int(s.sum()), max=round(float(ang[i]), 2), p99=round(float(np.percentile(ang[s], 99)), 2),
                max_at=mid[i].round(2).tolist())


def inner_flank_rate(mesh, y_hi, y_lo, zs=(5.0, 8.0, 9.5, 10.5), step=0.5, x_min=60.0):
    """Right handle: inner-flank x (lowest x of the y-section's row at z) every step mm of y; max |dx/dy| per z
    and where. The rows are on the STL's y-sections, so this measures the loft, not its stations."""
    from shapely.geometry import Polygon, LineString
    ys = np.arange(y_hi, y_lo - 1e-9, -step)
    X = np.full((len(ys), len(zs)), np.nan)
    for i, y in enumerate(ys):
        s = mesh.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0])
        if s is None:
            continue
        loops = [e[:, [0, 2]] for e in s.discrete if e[:, 0].mean() > x_min and len(e) > 8]
        if not loops:
            continue
        P = Polygon(max(loops, key=lambda e: Polygon(e).area)).buffer(0)
        for k, z in enumerate(zs):
            r = P.intersection(LineString([(x_min, z), (300.0, z)]))
            if not r.is_empty:
                X[i, k] = r.bounds[0]
    R = np.abs(np.diff(X, axis=0)) / step
    out = {}
    for k, z in enumerate(zs):
        if np.all(np.isnan(R[:, k])):
            out["z%.1f" % z] = None        # the row leaves the section (the top falls below z)
            continue
        j = int(np.nanargmax(R[:, k]))
        out["z%.1f" % z] = (round(float(R[j, k]), 2), round(float(ys[j] - step / 2), 2))
    return out


def _outer_rows(mesh, y, zs, x_min):
    from shapely.geometry import Polygon, LineString, box
    from shapely.ops import unary_union
    out = np.full(len(zs), np.nan)
    s = mesh.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0])
    if s is None:
        return out
    # the body's section is one loop across both grips (plate): keep the part right of x_min
    P = unary_union([Polygon(e[:, [0, 2]]).buffer(0) for e in s.discrete if len(e) > 8])
    P = P.intersection(box(x_min, -500.0, 500.0, 500.0))
    if P.is_empty:
        return out
    for k, z in enumerate(zs):
        r = P.intersection(LineString([(x_min, z), (300.0, z)]))
        if not r.is_empty:
            out[k] = r.bounds[2]
    return out


def outer_flank_turn(mesh, y_lo, y_hi, zs=(-20.0, -10.0, 0.0, 5.0), chord=1.0, step=0.25, y_shift_map=None,
                     x_min=60.0, morph=None):
    """Ring-line probe: outer-flank x (max x of the right y-section's row at z) every step mm of y, and the turn
    angle (deg) in the (y, x) plane between consecutive chord-mm chords. y_shift_map(y) gives the mesh y to cut for
    output y (r16 tested against v2: r16's handle at y - 16); chords across a jump of the map are left out.
    morph = (shared_y, shift, t): the design floor instead - the root morph applied to the mesh's own flank,
    x = (1 - w) x(y) + w x(y - shift), w = smoothstep((shared_y - y) / t), and x(y - shift) below the morph.
    Returns ys, turn {z: list (nan where the row or a chord is missing)}, and per z the max and its y."""
    ys = np.arange(y_hi, y_lo - 1e-9, -step)
    ym = np.array([y_shift_map(y) if y_shift_map else y for y in ys])
    X = np.full((len(ys), len(zs)), np.nan)
    for i, y in enumerate(ym):
        if morph is None or y >= morph[0]:
            X[i] = _outer_rows(mesh, y, zs, x_min)
            continue
        t = np.clip((morph[0] - y) / morph[2], 0.0, 1.0)
        w = t * t * (3.0 - 2.0 * t)
        b = _outer_rows(mesh, y - morph[1], zs, x_min)
        X[i] = b if w >= 1.0 else (1.0 - w) * _outer_rows(mesh, y, zs, x_min) + w * b
    k = int(round(chord / step))
    T = np.full(X.shape, np.nan)
    for i in range(k, len(ys) - k):
        if abs((ym[i - k] - ym[i + k]) - (ys[i - k] - ys[i + k])) > 1e-6:
            continue
        a = np.stack([ys[i] - ys[i - k] + 0 * X[i], X[i] - X[i - k]], axis=1)
        b = np.stack([ys[i + k] - ys[i] + 0 * X[i], X[i + k] - X[i]], axis=1)
        c = (a * b).sum(1) / (np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1))
        T[i] = np.degrees(np.arccos(np.clip(c, -1.0, 1.0)))
    out = dict(ys=[round(float(y), 3) for y in ys], turn={}, max={})
    for j, z in enumerate(zs):
        key = "z%.0f" % z
        out["turn"][key] = [None if np.isnan(t) else round(float(t), 3) for t in T[:, j]]
        if np.all(np.isnan(T[:, j])):
            out["max"][key] = None
            continue
        i = int(np.nanargmax(T[:, j]))
        out["max"][key] = (round(float(T[i, j]), 2), round(float(ys[i]), 2))
    return out


def turn_vs_reference(test, ref, margin=1.0, at=(-9.0, -13.0, -27.0), win=1.0):
    """Outer-flank turn of test against ref (both from outer_flank_turn on the same ys): per z the worst excess
    test - ref - margin (> 0 fails) and where, and the max of each within +-win of the named ys.
    ref may be a list: the reference is then the larger of them at each y (r16 and the morph's design floor)."""
    ys = np.array(test["ys"])
    refs = ref if isinstance(ref, (list, tuple)) else [ref]
    out = {}
    for key, tv in test["turn"].items():
        t = np.array([np.nan if v is None else v for v in tv], float)
        with np.errstate(all="ignore"):
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                r = np.nanmax(np.stack([np.array([np.nan if v is None else v for v in q["turn"][key]], float)
                                        for q in refs]), axis=0)
        e = t - r - margin
        ok = ~np.isnan(e)
        row = dict(n=int(ok.sum()))
        if ok.any():
            i = int(np.nanargmax(e))
            row.update(worst_excess=round(float(e[i]), 2), worst_at=round(float(ys[i]), 2),
                       test_there=round(float(t[i]), 2), ref_there=round(float(r[i]), 2),
                       n_fail=int((e[ok] > 0).sum()))
            # contiguous failing y ranges: (y_from, y_to, worst excess)
            f = np.where(ok & (np.nan_to_num(e, nan=-1.0) > 0))[0]
            rng = []
            for grp in np.split(f, np.where(np.diff(f) > 1)[0] + 1) if len(f) else []:
                rng.append((round(float(ys[grp[0]]), 2), round(float(ys[grp[-1]]), 2), round(float(e[grp].max()), 2)))
            row["fail_ranges"] = rng
        for y in at:
            w = np.abs(ys - y) <= win
            row["y%.0f" % y] = (None if np.all(np.isnan(t[w])) else round(float(np.nanmax(t[w])), 2),
                                None if np.all(np.isnan(r[w])) else round(float(np.nanmax(r[w])), 2))
        out[key] = row
    return out


def sharp_edges(mesh, box, deg=30.0, cell=2.0):
    """STL edges with dihedral > deg inside box (x0, x1, y0, y1): count, max, and clusters (cell mm) by max angle."""
    ang = np.degrees(mesh.face_adjacency_angles)
    mid = mesh.vertices[mesh.face_adjacency_edges].mean(axis=1)
    x0, x1, y0, y1 = box
    s = (mid[:, 0] > x0) & (mid[:, 0] < x1) & (mid[:, 1] > y0) & (mid[:, 1] < y1) & (ang > deg)
    cl = {}
    for p, a in zip(mid[s], ang[s]):
        k = tuple((np.round(p / cell) * cell).round(1).tolist())
        n, m = cl.get(k, (0, 0.0))
        cl[k] = (n + 1, max(m, float(a)))
    top = sorted(cl.items(), key=lambda kv: -kv[1][1])
    return dict(count=int(s.sum()), max=round(float(ang[s].max()), 2) if s.any() else 0.0,
                clusters=[(k, n, round(m, 1)) for k, (n, m) in top[:25]])
