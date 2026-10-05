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


def round_radii(solid, zone, nu=160, nv=160):
    """Principal radius across the round (1 / max |curvature|) on B-spline faces, at uv-grid points p with
    zone(p) True. Returns (n, min, p5, median, p95, max, location of min)."""
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
                if k > 1e-9:
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
