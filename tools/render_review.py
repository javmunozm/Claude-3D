"""Review renders for judging surface quality: smooth shading without a feature
split, plus zebra stripes. These are the views a user judges and marks.

Why: the region and closeup renders split vertex normals at 35-45 deg under a
specular light, so 0.2 mm facet zig-zags can render as seams. On VitaGripPS5
r13, 6 of the 12 paths the user marked measured as tessellation, not form
(audit/r14/register_r14.md). Here every vertex normal is averaged over all its
faces, so shading changes only where the surface really turns. The zebra pass
reflects a striped environment: a crease or a curvature step breaks or kinks
the stripes, while noisy tessellation on a smooth surface leaves them
continuous.

Cameras: a perimeter view by name, with the same azimuth and elevation as
render_views.py (front, top, iso, ...), or an explicit camera
  --camera <name>:<px>,<py>,<pz>:<fx>,<fy>,<fz>[:<view angle deg, default 30>]
(position, focal point; up is +Z). --flip-x turns the mesh 180 deg about X first,
as the VitaGripPS5 "back" copies were made.

Usage:
  python tools/render_review.py <mesh.stl> --outdir <dir> [--views iso top]
      [--camera cornerR:190,150,-90:90,65,-12:30] [--modes smooth zebra]
      [--stripes 16] [--size 900] [--prefix <name>]
Writes <prefix>_<view>_smooth.png and <prefix>_<view>_zebra.png.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pyvista as pv
from matplotlib.colors import ListedColormap

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_views import PERIMETER, camera_position  # noqa: E402

BODY_COLOR = "#2b6fd4"


def load(path, flip_x=False):
    """The mesh with point normals averaged over all faces (no feature split)."""
    m = pv.read(str(path)).triangulate()
    if flip_x:
        m = m.rotate_x(180.0, point=m.center, inplace=False)
    return m.compute_normals(cell_normals=False, point_normals=True, split_vertices=False,
                             consistent_normals=True, auto_orient_normals=False)


def parse_camera(text):
    """'name:px,py,pz:fx,fy,fz[:angle]' -> (name, position, focal, up, angle)."""
    parts = text.split(":")
    if len(parts) not in (3, 4):
        raise ValueError("camera must be name:px,py,pz:fx,fy,fz[:angle], got %r" % text)
    pos = tuple(float(v) for v in parts[1].split(","))
    foc = tuple(float(v) for v in parts[2].split(","))
    angle = float(parts[3]) if len(parts) == 4 else 30.0
    return parts[0], pos, foc, (0.0, 0.0, 1.0), angle


def zebra_scalar(mesh, cam_pos, up):
    """Elevation (deg) of the view ray reflected at each vertex, against the camera's up axis."""
    n = np.asarray(mesh.point_data["Normals"], dtype=float)
    v = np.asarray(mesh.points, dtype=float) - np.asarray(cam_pos, dtype=float)
    v /= np.linalg.norm(v, axis=1)[:, None]
    r = v - 2.0 * np.sum(v * n, axis=1)[:, None] * n
    return np.degrees(np.arcsin(np.clip(r @ np.asarray(up, dtype=float), -1.0, 1.0)))


def render(mesh, cam, mode, out, size=900, stripes=16):
    name, pos, foc, up, angle = cam
    pl = pv.Plotter(off_screen=True, window_size=(size, size), lighting="none")
    pl.set_background("#ffffff", top="#e8ecf1")
    if mode == "smooth":
        pl.add_mesh(mesh, color=BODY_COLOR, smooth_shading=True, split_sharp_edges=False,
                    ambient=0.15, diffuse=0.8, specular=0.15, specular_power=15)
        key = np.asarray(pos, float) + np.array([0.0, 0.0, 0.25]) * np.linalg.norm(np.subtract(pos, foc))
        pl.add_light(pv.Light(position=tuple(key), focal_point=foc, intensity=0.85))
        pl.add_light(pv.Light(position=tuple(np.asarray(foc) + np.array([0.0, 0.0, 400.0])), focal_point=foc,
                              intensity=0.25))
    elif mode == "zebra":
        mesh = mesh.copy()
        mesh.point_data["zebra"] = zebra_scalar(mesh, pos, up)
        cmap = ListedColormap(["#111111", "#f2f2f2"] * (stripes // 2))
        pl.add_mesh(mesh, scalars="zebra", cmap=cmap, clim=[-90.0, 90.0], interpolate_before_map=True,
                    smooth_shading=True, split_sharp_edges=False, lighting=False, show_scalar_bar=False)
    else:
        raise ValueError("mode must be smooth or zebra")
    pl.camera_position = [tuple(pos), tuple(foc), tuple(up)]
    pl.camera.SetParallelProjection(False)
    pl.camera.SetViewAngle(angle)
    pl.screenshot(str(out))
    pl.close()
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("mesh")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--views", nargs="*", default=[], help="perimeter views: " + " ".join(PERIMETER))
    ap.add_argument("--camera", action="append", default=[], help="name:px,py,pz:fx,fy,fz[:angle]")
    ap.add_argument("--modes", nargs="+", default=["smooth", "zebra"])
    ap.add_argument("--stripes", type=int, default=16)
    ap.add_argument("--size", type=int, default=900)
    ap.add_argument("--prefix", default=None)
    ap.add_argument("--flip-x", action="store_true")
    a = ap.parse_args()
    mesh = load(a.mesh, a.flip_x)
    cams = []
    for v in a.views:
        if v not in PERIMETER:
            sys.exit("unknown view %r; choose from %s" % (v, sorted(PERIMETER)))
        pos, foc, up = camera_position(mesh, *PERIMETER[v])
        cams.append((v, pos, foc, up, 24.0))
    cams += [parse_camera(c) for c in a.camera]
    if not cams:
        sys.exit("give --views and/or --camera")
    out = Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)
    prefix = a.prefix or Path(a.mesh).stem
    for cam in cams:
        for mode in a.modes:
            p = render(mesh, cam, mode, out / ("%s_%s_%s.png" % (prefix, cam[0], mode)), a.size, a.stripes)
            print("wrote", p)


if __name__ == "__main__":
    main()
