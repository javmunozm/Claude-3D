"""Depth-shaded orthographic renders of a mesh, optionally with labelled
coordinate grid and marker circles, for correlating a screenshot with mesh
coordinates.

Renders faces (not vertices) with a z-buffer, so a crater reads as a recessed
dark patch rather than a hole in a point cloud. locate_views.py in BrokeFeet
splats vertices, which is fast but loses small dents in dense regions.

Usage:
  python render_mesh_views.py <mesh.stl> <outdir> [--views iso right ...]
                              [--mark X,Y,Z,label ...] [--zoom x0,x1,y0,y1]
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image, ImageDraw

W, H = 1400, 1100
MARGIN = 90
GRID = 10.0
AX = "XYZ"

# name -> (camera direction the viewer looks ALONG, up vector)
VIEWS = {
    "right":  ((-1, 0, 0), (0, 0, 1)),
    "left":   ((1, 0, 0), (0, 0, 1)),
    "front":  ((0, 1, 0), (0, 0, 1)),
    "back":   ((0, -1, 0), (0, 0, 1)),
    "top":    ((0, 0, -1), (0, 1, 0)),
    "bottom": ((0, 0, 1), (0, 1, 0)),
    "iso":    ((-1, 1, -0.6), (0, 0, 1)),
    "iso2":   ((1, 1, -0.6), (0, 0, 1)),
    "isolat": ((-0.85, 0.35, -0.35), (0, 0, 1)),
}


def basis(view):
    fwd = np.array(VIEWS[view][0], float)
    fwd /= np.linalg.norm(fwd)
    up = np.array(VIEWS[view][1], float)
    right = np.cross(fwd, up)
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    return right, up, fwd


def render(mesh, view, marks=(), zoom=None, title=""):
    right, up, fwd = basis(view)
    V = mesh.vertices
    h = V @ right
    v = V @ up
    d = -(V @ fwd)          # larger = nearer the camera

    if zoom is not None:
        hlo, hhi, vlo, vhi = zoom
    else:
        hlo, hhi = h.min(), h.max()
        vlo, vhi = v.min(), v.max()
        pad = 0.03 * max(hhi - hlo, vhi - vlo)
        hlo, hhi, vlo, vhi = hlo - pad, hhi + pad, vlo - pad, vhi + pad

    pw, ph = W - 2 * MARGIN, H - 2 * MARGIN
    sc = min(pw / (hhi - hlo), ph / (vhi - vlo))

    def to_px(hv, vv):
        return (MARGIN + (hv - hlo) * sc,
                MARGIN + (vhi - vv) * sc)

    # z-buffered face rasterisation, shaded by facet normal + depth
    F = mesh.faces
    hp = MARGIN + (h - hlo) * sc
    vp = MARGIN + (vhi - v) * sc
    tri_h = hp[F]
    tri_v = vp[F]
    tri_d = d[F].mean(1)

    nrm = mesh.face_normals
    lamb = np.clip(-(nrm @ fwd), 0, 1)

    zbuf = np.full((H, W), -1e9, np.float64)
    img = np.zeros((H, W, 3), np.uint8)
    img[:] = (28, 32, 44)

    order = np.argsort(tri_d)
    dmin, dmax = tri_d.min(), tri_d.max()
    for i in order:
        x0 = int(np.floor(tri_h[i].min())); x1 = int(np.ceil(tri_h[i].max()))
        y0 = int(np.floor(tri_v[i].min())); y1 = int(np.ceil(tri_v[i].max()))
        if x1 < 0 or y1 < 0 or x0 >= W or y0 >= H:
            continue
        x0 = max(x0, 0); y0 = max(y0, 0)
        x1 = min(x1, W - 1); y1 = min(y1, H - 1)
        if x1 < x0 or y1 < y0:
            continue
        t = (tri_d[i] - dmin) / (dmax - dmin + 1e-9)
        shade = 0.30 + 0.70 * t
        c = np.clip(np.array([210, 205, 195]) * (0.25 + 0.75 * lamb[i]) * shade,
                    0, 255).astype(np.uint8)
        ys, xs = np.mgrid[y0:y1 + 1, x0:x1 + 1]
        ax, ay = tri_h[i, 0], tri_v[i, 0]
        bx, by = tri_h[i, 1], tri_v[i, 1]
        cx, cy = tri_h[i, 2], tri_v[i, 2]
        den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(den) < 1e-12:
            continue
        l1 = ((by - cy) * (xs - cx) + (cx - bx) * (ys - cy)) / den
        l2 = ((cy - ay) * (xs - cx) + (ax - cx) * (ys - cy)) / den
        l3 = 1 - l1 - l2
        inside = (l1 >= -0.002) & (l2 >= -0.002) & (l3 >= -0.002)
        if not inside.any():
            continue
        sel = (slice(y0, y1 + 1), slice(x0, x1 + 1))
        better = inside & (tri_d[i] > zbuf[sel])
        if better.any():
            zb = zbuf[sel]; zb[better] = tri_d[i]; zbuf[sel] = zb
            im = img[sel]; im[better] = c; img[sel] = im

    pil = Image.fromarray(img)
    dr = ImageDraw.Draw(pil)

    # grid, labelled -- only meaningful for axis-aligned views
    if view in ("right", "left", "front", "back", "top", "bottom"):
        ha = int(np.argmax(np.abs(right)))
        va = int(np.argmax(np.abs(up)))
        for hv in np.arange(np.floor(hlo / GRID) * GRID, hhi, GRID):
            x, _ = to_px(hv, vlo)
            major = abs(hv % 50.0) < 1e-6
            dr.line([(x, MARGIN), (x, H - MARGIN)],
                    fill=(120, 130, 150) if major else (60, 68, 84),
                    width=2 if major else 1)
            if major:
                dr.text((x - 16, H - MARGIN + 8),
                        f"{AX[ha]}{np.sign(right[ha]) * hv:.0f}",
                        fill=(230, 230, 230))
        for vv in np.arange(np.floor(vlo / GRID) * GRID, vhi, GRID):
            _, y = to_px(hlo, vv)
            major = abs(vv % 50.0) < 1e-6
            dr.line([(MARGIN, y), (W - MARGIN, y)],
                    fill=(120, 130, 150) if major else (60, 68, 84),
                    width=2 if major else 1)
            if major:
                dr.text((MARGIN - 52, y - 7),
                        f"{AX[va]}{np.sign(up[va]) * vv:.0f}",
                        fill=(230, 230, 230))

    for mk in marks:
        p = np.array(mk[:3], float)
        label = mk[3] if len(mk) > 3 else ""
        rad = mk[4] if len(mk) > 4 else 6.0
        x, y = to_px(p @ right, p @ up)
        rr = rad * sc
        dr.ellipse([x - rr, y - rr, x + rr, y + rr],
                   outline=(255, 60, 60), width=3)
        if label:
            dr.text((x + rr + 4, y - 8), label, fill=(255, 120, 120))

    dr.text((MARGIN, 20), f"{view.upper()}   {title}", fill=(255, 255, 255))
    dr.text((MARGIN, 40),
            f"h={hlo:.0f}..{hhi:.0f}  v={vlo:.0f}..{vhi:.0f}  "
            f"(brighter = nearer)", fill=(190, 190, 190))
    return pil


def main():
    args = sys.argv[1:]
    src = args[0]
    outdir = Path(args[1])
    views = ["iso", "right", "top"]
    marks = []
    zoom = None
    i = 2
    while i < len(args):
        if args[i] == "--views":
            views = []
            i += 1
            while i < len(args) and not args[i].startswith("--"):
                views.append(args[i]); i += 1
        elif args[i] == "--mark":
            i += 1
            while i < len(args) and not args[i].startswith("--"):
                parts = args[i].split(",")
                marks.append((float(parts[0]), float(parts[1]),
                              float(parts[2]),
                              parts[3] if len(parts) > 3 else "",
                              float(parts[4]) if len(parts) > 4 else 6.0))
                i += 1
        elif args[i] == "--zoom":
            i += 1
            zoom = tuple(float(x) for x in args[i].split(","))
            i += 1
        else:
            i += 1

    mesh = trimesh.load(src)
    outdir.mkdir(parents=True, exist_ok=True)
    for v in views:
        img = render(mesh, v, marks, zoom, title=Path(src).name)
        p = outdir / f"view_{v}.png"
        img.save(p)
        print(f"wrote {p}")


if __name__ == "__main__":
    main()
