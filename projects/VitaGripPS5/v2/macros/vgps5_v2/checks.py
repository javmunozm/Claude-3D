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


def handle_deviation(v2, r16, regions, n=120000):
    """Both directions, per region {name: (y_lo, y_hi)}: rms, p95, max (mm)."""
    a = _samples(v2, n, 2)
    b = _samples(r16, n, 3)
    out = {}
    for name, (lo, hi) in regions.items():
        row = {}
        for tag, pts, target in (("v2->r16", a, r16), ("r16->v2", b, v2)):
            p = pts[_region(pts, lo, hi)]
            _, d, _ = trimesh.proximity.closest_point(target, p)
            row[tag] = dict(n=len(p), rms=float(np.sqrt(np.mean(d ** 2))), p95=float(np.percentile(d, 95)),
                            max=float(d.max()), max_at=p[int(np.argmax(d))].round(2).tolist())
        out[name] = row
    return out
