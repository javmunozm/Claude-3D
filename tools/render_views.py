"""
render_views.py — perimeter views WITH DEPTH PERCEPTION
=======================================================
Why this exists, separately from render_check.py
------------------------------------------------
`render_check.py` renders every triangle in ONE flat colour (`facecolor=
"#8fa9c4"`, no light source). That is a SILHOUETTE, not a shaded image: a
40 mm-deep volumetric handle and a 3 mm flat plate produce the identical
picture. Every form error found in VitaGripPS5 survived that renderer because
of exactly this — the part "looked like the reference" in outline while its
cross-section was half the required width.

This renderer restores the three cues the eye actually uses to read 3D form:

  1. DIFFUSE + SPECULAR SHADING — a lit surface. Curvature becomes visible as
     a gradient; a cylinder stops looking like a rectangle.
  2. DEPTH-OF-FIELD SUBSTITUTE (SSAO) — ambient occlusion darkens crevices and
     concave junctions, which is what makes a channel read as a channel rather
     than a painted stripe.
  3. A GROUND PLANE + CAST SHADOW — the reference photographs all sit on a
     white sweep with a visible contact shadow. Without one, nothing anchors
     the part in space and relative depth is unreadable.

Perimeter views = the full turntable, not just front/back. A form error that
hides in one azimuth is visible in the neighbouring one; the two square end
blocks on VitaGripPS5 are invisible in `back` and obvious at `front_left`.

Usage
-----
    python tools/render_views.py projects/VitaGripPS5/stl/VitaGripPS5.stl
    python tools/render_views.py part.stl --views front back left right
    python tools/render_views.py part.stl --outdir renders --size 1000

Output is one PNG per view plus a `_contact_sheet.png` montage.

Requirements: pyvista, numpy, pillow
"""

import argparse
import pathlib
import sys

import numpy as np

# Azimuth around +Z, measured from the -Y axis (the "front" of the part, the
# side a photographer stands on). Elevation is above the horizon.
# These are PERIMETER views: a full 45-degree turntable at a natural
# eye-height, plus the three orthographic principal views.
PERIMETER = {
    "front":        (0,   12),
    "front_left":   (45,  12),
    "left":         (90,  12),
    "rear_left":    (135, 12),
    "back":         (180, 12),
    "rear_right":   (225, 12),
    "right":        (270, 12),
    "front_right":  (315, 12),
    "top":          (0,   88),
    "iso":          (35,  28),
}

BODY_COLOR = "#2b6fd4"      # the reference part is a saturated blue print
BG_TOP = "#ffffff"
BG_BOT = "#e8ecf1"


def camera_position(mesh, azim_deg, elev_deg, zoom=2.4):
    """Camera at a spherical position around the mesh centre.

    azim is measured so that 0 puts the camera on -Y (in front of the part)
    and increases counter-clockwise viewed from +Z.
    """
    c = np.asarray(mesh.center)
    radius = float(np.linalg.norm(np.ptp(np.asarray(mesh.bounds).reshape(3, 2), axis=1))) * zoom
    a = np.radians(azim_deg)
    e = np.radians(elev_deg)
    # 0 deg -> -Y ; +90 deg -> -X (so the turntable spins the way the names read)
    x = -np.sin(a) * np.cos(e)
    y = -np.cos(a) * np.cos(e)
    z = np.sin(e)
    pos = c + np.array([x, y, z]) * radius
    return (tuple(pos), tuple(c), (0, 0, 1))


def render(mesh_path, out_path, azim, elev, size=900, shadow=True):
    import pyvista as pv

    pv.OFF_SCREEN = True
    mesh = pv.read(str(mesh_path))
    # Smooth normals so curvature shades continuously instead of faceting into
    # flat triangles, which is what makes a swept tube read as a prism.
    mesh = mesh.compute_normals(cell_normals=False, point_normals=True,
                                split_vertices=True, feature_angle=45)

    pl = pv.Plotter(off_screen=True, window_size=(size, size), lighting="none")
    pl.set_background(BG_BOT, top=BG_TOP)

    pl.add_mesh(
        mesh,
        color=BODY_COLOR,
        smooth_shading=True,
        specular=0.45,
        specular_power=22,
        diffuse=0.85,
        ambient=0.22,
        split_sharp_edges=True,
        feature_angle=45,
    )

    # A GROUND PLANE, sized to the part and placed at its underside, so the
    # cast shadow has something to land on. Without a floor the part floats and
    # depth is unreadable.
    b = np.asarray(mesh.bounds)
    xmin, xmax, ymin, ymax, zmin, zmax = b
    span = max(xmax - xmin, ymax - ymin, zmax - zmin)
    cx, cy = (xmin + xmax) / 2, (ymin + ymax) / 2
    floor = pv.Plane(center=(cx, cy, zmin - span * 0.012),
                     direction=(0, 0, 1),
                     i_size=span * 3.2, j_size=span * 3.2)
    pl.add_mesh(floor, color="#f2f4f7", ambient=0.55, diffuse=0.5,
                specular=0.0, show_edges=False)

    # Three-point lighting: a bright key that creates the primary gradient, a
    # softer fill opposite it so the shadow side is not black, and a rim light
    # behind to separate the silhouette from the background.
    key = pv.Light(position=(cx + span, cy - span * 1.4, zmax + span * 1.6),
                   focal_point=(cx, cy, (zmin + zmax) / 2),
                   color="white", intensity=0.86)
    key.positional = False
    fill = pv.Light(position=(cx - span * 1.5, cy - span, zmax + span * 0.4),
                    focal_point=(cx, cy, (zmin + zmax) / 2),
                    color="#dce6f5", intensity=0.36)
    fill.positional = False
    rim = pv.Light(position=(cx, cy + span * 1.8, zmax + span * 0.9),
                   focal_point=(cx, cy, (zmin + zmax) / 2),
                   color="#ffffff", intensity=0.30)
    rim.positional = False
    for L in (key, fill, rim):
        pl.add_light(L)

    pl.camera_position = camera_position(mesh, azim, elev)
    pl.camera.SetParallelProjection(False)   # a photo is a lens, and these
    pl.camera.SetViewAngle(24)               # views are compared to photos

    # Ambient occlusion: darkens concave junctions and channels. This is the
    # single cue that makes an open C-channel distinguishable from a painted
    # line on a flat face.
    try:
        pl.enable_ssao(radius=span * 0.16, bias=0.004, blur=True)
    except Exception:
        pass
    try:
        pl.enable_anti_aliasing("ssaa")
    except Exception:
        pass
    if shadow:
        try:
            pl.enable_shadows()
        except Exception:
            pass

    pl.screenshot(str(out_path))
    pl.close()
    return out_path


def contact_sheet(paths, out_path, cols=4, label=True):
    """Montage every rendered view into one sheet, each tile labelled."""
    from PIL import Image, ImageDraw

    imgs = [Image.open(p).convert("RGB") for p in paths]
    w, h = imgs[0].size
    scale = 380 / w
    tw, th = int(w * scale), int(h * scale)
    rows = (len(imgs) + cols - 1) // cols
    pad = 8
    sheet = Image.new("RGB", (cols * tw + pad * (cols + 1),
                              rows * th + pad * (rows + 1)), "white")
    d = ImageDraw.Draw(sheet)
    for i, (im, p) in enumerate(zip(imgs, paths)):
        r, c = divmod(i, cols)
        x = pad + c * (tw + pad)
        y = pad + r * (th + pad)
        sheet.paste(im.resize((tw, th), Image.LANCZOS), (x, y))
        if label:
            d.text((x + 6, y + 6), pathlib.Path(p).stem.split("__")[-1],
                   fill="#222222")
    sheet.save(out_path)
    return out_path


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mesh")
    ap.add_argument("--views", nargs="+", default=list(PERIMETER),
                    help=f"views to render (default: all). {' '.join(PERIMETER)}")
    ap.add_argument("--outdir", default=None)
    ap.add_argument("--size", type=int, default=900)
    ap.add_argument("--no-shadow", action="store_true")
    ap.add_argument("--prefix", default=None)
    args = ap.parse_args()

    mesh_path = pathlib.Path(args.mesh)
    if not mesh_path.exists():
        sys.exit(f"no such mesh: {mesh_path}")
    # Models sit in stl/ or step/; PNGs go to the sibling renders/.
    base = mesh_path.parent.parent if mesh_path.parent.name in ("stl", "step") else mesh_path.parent
    outdir = pathlib.Path(args.outdir) if args.outdir else base / "renders"
    outdir.mkdir(parents=True, exist_ok=True)
    prefix = args.prefix or mesh_path.stem

    made = []
    for v in args.views:
        if v not in PERIMETER:
            sys.exit(f"unknown view {v!r}; choose from {sorted(PERIMETER)}")
        azim, elev = PERIMETER[v]
        out = outdir / f"{prefix}__{v}.png"
        render(mesh_path, out, azim, elev, size=args.size,
               shadow=not args.no_shadow)
        made.append(str(out))
        print(f"  {v:<12} -> {out}")

    if len(made) > 1:
        sheet = contact_sheet(made, outdir / f"{prefix}__contact_sheet.png")
        print(f"  contact sheet -> {sheet}")


if __name__ == "__main__":
    main()
