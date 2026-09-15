"""
render_overlay.py - draw the OPERANDS of a boolean, in pose, before it runs.
============================================================================
Why this exists, separately from render_views.py
------------------------------------------------
`render_views.py` renders a finished part. `render_check.py` renders its
silhouette. Neither can show a boolean's INPUTS, and that is where this
project's placement bugs lived.

Three console placements shipped and were diagnosed from a single number - the
percentage of grip volume the cut removed:

    unrotated console, presenting its 19.3 mm edge     1.3 %
    console at Y = -31, hanging in the grips' gap      1.2 %
    sunk from the dome's PEAK instead of its lowest    2.2 %
    the accepted pose                                 13.4 %

Every one of them would have been obvious in one frame showing the two solids
overlapped. Instead each cost a build, a measurement pass and a paragraph of
reconstruction. A percentage says a cut is wrong; it never says WHY.

So: the cutter is drawn TRANSLUCENT over an opaque body, in the exact pose the
boolean will use, imported from the same module the builder uses. The picture
answers the questions a volume fraction cannot - is the cutter even touching,
is it in the right hole, is it sunk far enough to leave a floor, does it hang
past an edge.

WHAT A GOOD OVERLAY LOOKS LIKE
------------------------------
  - the cutter's outline crosses the body's surface, not floating clear of it
  - the submerged part reads DARKER through the body, so depth is legible
  - at least one view shows material UNDER the cutter (the socket's floor)
  - no view shows the cutter poking out a face you did not intend to open

Usage
-----
    # the VitaGripPS5 socket cut, at the pose the builder will use
    python tools/render_overlay.py --preset vitagripps5

    # sweep a placement parameter and see each candidate
    python tools/render_overlay.py --preset vitagripps5 --y -31
    python tools/render_overlay.py --preset vitagripps5 --sink 30

    # any two meshes, already in their final coordinates
    python tools/render_overlay.py body.stl cutter.stl --views front left iso

Output is one PNG per view plus a `_contact_sheet.png` montage, written to the
project's `renders/overlay/` (or --outdir).

Requirements: pyvista, numpy, pillow, trimesh
"""

import argparse
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from tools.render_views import PERIMETER, camera_position, contact_sheet

BODY_COLOR = "#8fa9c4"
CUT_COLOR = "#e0563f"     # warm, so it separates from the cool body at any opacity
BG_TOP = "#ffffff"
BG_BOT = "#e8ecf1"

CUT_OPACITY = 0.42        # low enough to read the body through it, high enough
                          # that the submerged volume is unambiguous


def _pv_mesh(m):
    """trimesh.Trimesh or a path -> pyvista PolyData."""
    import pyvista as pv

    if isinstance(m, (str, pathlib.Path)):
        return pv.read(str(m))
    faces = np.hstack([np.full((len(m.faces), 1), 3, dtype=np.int64),
                       m.faces]).ravel()
    return pv.PolyData(np.asarray(m.vertices), faces)


def render_overlay(body, cutter, out_path, azim, elev, size=900,
                   shadow=True, opacity=CUT_OPACITY):
    """One shaded view of body + translucent cutter, in their given poses.

    Lighting matches render_views.py so an overlay and a finished render of
    the same part are directly comparable.
    """
    import pyvista as pv

    pv.OFF_SCREEN = True
    b_mesh = _pv_mesh(body).compute_normals(
        cell_normals=False, point_normals=True, split_vertices=True,
        feature_angle=45)
    c_mesh = _pv_mesh(cutter)

    pl = pv.Plotter(off_screen=True, window_size=(size, size), lighting="none")
    pl.set_background(BG_BOT, top=BG_TOP)

    pl.add_mesh(b_mesh, color=BODY_COLOR, smooth_shading=True,
                specular=0.45, specular_power=22, diffuse=0.85, ambient=0.22,
                split_sharp_edges=True, feature_angle=45)

    # WHY NOT SIMPLY A TRANSLUCENT CUTTER.
    #
    # The first version of this renderer drew the cutter as one translucent
    # solid. It FAILED, and failed silently: in `front` and `left` the cutter
    # showed as a 2 mm red sliver along the top edge, and in `iso` it was
    # INVISIBLE - depth-sorted behind the opaque shell - while contains() put
    # 16.9 % of the body's vertices inside it. A tool whose entire purpose is
    # to make submerged geometry legible had hidden the submerged geometry.
    #
    # Transparency is the wrong primitive here. VTK resolves it by depth order,
    # so whatever is buried loses. Three layers that do not depend on ordering:
    #
    #   1. the INTERSECTION - the material the cut actually removes - drawn
    #      OPAQUE. This is the socket, made visible as a solid object.
    #   2. the cutter as a WIREFRAME CAGE, which reads through the body because
    #      lines are thin, so its full extent and orientation stay legible.
    #   3. the cutter's surface, faint, for the part standing proud of the body.
    #
    # Depth peeling is enabled as well, so what transparency remains composites
    # correctly instead of by accident.
    try:
        pl.enable_depth_peeling(number_of_peels=8, occlusion_ratio=0.0)
    except Exception:
        pass

    overlap = None
    try:
        import trimesh
        tb = body if not isinstance(body, (str, pathlib.Path)) else trimesh.load(str(body))
        tc = cutter if not isinstance(cutter, (str, pathlib.Path)) else trimesh.load(str(cutter))
        inter = trimesh.boolean.intersection([tb, tc])
        if inter is not None and len(inter.faces) and inter.volume > 0:
            overlap = _pv_mesh(inter)
    except Exception as e:
        print("  (intersection not drawn: %s)" % e)

    if overlap is not None:
        pl.add_mesh(overlap, color=CUT_COLOR, opacity=1.0, smooth_shading=True,
                    specular=0.3, specular_power=18, diffuse=0.85, ambient=0.28)

    pl.add_mesh(c_mesh, color=CUT_COLOR, opacity=opacity * 0.45,
                smooth_shading=False, specular=0.1, diffuse=0.8, ambient=0.3)
    pl.add_mesh(c_mesh, color=CUT_COLOR, style="wireframe", line_width=1.2,
                opacity=0.55)
    pl.add_mesh(c_mesh.extract_feature_edges(feature_angle=25),
                color="#8c2f1c", line_width=3, opacity=1.0)

    # Ground plane and lights are sized on the UNION's bounds, so the cutter
    # cannot fall outside the lit region when it overhangs the body.
    both = np.vstack([np.asarray(b_mesh.bounds).reshape(3, 2),
                      np.asarray(c_mesh.bounds).reshape(3, 2)])
    xmin, xmax = both[0::3].min(), both[0::3].max()
    lo = np.array([np.asarray(b_mesh.bounds)[0::2],
                   np.asarray(c_mesh.bounds)[0::2]]).min(axis=0)
    hi = np.array([np.asarray(b_mesh.bounds)[1::2],
                   np.asarray(c_mesh.bounds)[1::2]]).max(axis=0)
    span = float(np.max(hi - lo))
    cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
    zmin, zmax = lo[2], hi[2]

    floor = pv.Plane(center=(cx, cy, zmin - span * 0.012), direction=(0, 0, 1),
                     i_size=span * 3.2, j_size=span * 3.2)
    pl.add_mesh(floor, color="#f2f4f7", ambient=0.55, diffuse=0.5,
                specular=0.0, show_edges=False)

    key = pv.Light(position=(cx + span, cy - span * 1.4, zmax + span * 1.6),
                   focal_point=(cx, cy, (zmin + zmax) / 2),
                   color="white", intensity=0.86)
    fill = pv.Light(position=(cx - span * 1.5, cy - span, zmax + span * 0.4),
                    focal_point=(cx, cy, (zmin + zmax) / 2),
                    color="#dce6f5", intensity=0.36)
    rim = pv.Light(position=(cx, cy + span * 1.8, zmax + span * 0.9),
                   focal_point=(cx, cy, (zmin + zmax) / 2),
                   color="#ffffff", intensity=0.30)
    for L in (key, fill, rim):
        L.positional = False
        pl.add_light(L)

    # Camera framed on the union, not the body, for the same reason.
    frame = pv.PolyData(np.vstack([lo, hi]))
    pl.camera_position = camera_position(frame, azim, elev)
    pl.camera.SetParallelProjection(False)
    pl.camera.SetViewAngle(24)

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


def preset_vitagripps5(args):
    """The VitaGripPS5 socket cut, posed by the builder's own module."""
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent
                           / "projects" / "VitaGripPS5" / "macros"))
    import socket_placement as sp

    # pose() returns the window cutter as a fourth value; this renderer draws
    # the SOCKET operands, so the window is unpacked and ignored rather than
    # silently changing what the overlay means.
    g, c, _win, info = sp.pose(scale=args.scale,
                               y=args.y if args.y is not None else sp.DEFAULT_Y,
                               sink=args.sink if args.sink is not None
                               else sp.DEFAULT_SINK)
    print("grip    %.2f x %.2f x %.2f mm  (scale %.4f)"
          % (*info["grip_extents"], info["scale"]))
    print("cutter  %.2f x %.2f x %.2f mm  at Y %.2f  Z %.2f"
          % (*info["placed_extents"], info["y"], info["z_centre"]))
    print("        local top of shell %.2f mm, sink %.2f mm"
          % (info["local_top"], info["sink"]))

    # Report the number the picture is meant to replace, so the two can be
    # compared rather than trusted separately.
    import trimesh
    inside = c.contains(g.vertices)
    print("        %d of %d grip vertices fall inside the cutter (%.1f %%)"
          % (inside.sum(), len(g.vertices), 100.0 * inside.mean()))

    outdir = args.outdir or (pathlib.Path(__file__).resolve().parent.parent
                             / "projects" / "VitaGripPS5" / "renders"
                             / "overlay")
    return g, c, pathlib.Path(outdir), "socket_overlay"


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("body", nargs="?", help="body mesh (omit with --preset)")
    ap.add_argument("cutter", nargs="?", help="cutter mesh, already posed")
    ap.add_argument("--preset", choices=["vitagripps5"],
                    help="pose the operands with a project's own placement module")
    ap.add_argument("--scale", type=float, default=None)
    ap.add_argument("--y", type=float, default=None)
    ap.add_argument("--sink", type=float, default=None)
    ap.add_argument("--views", nargs="+", default=["front", "left", "top", "iso"],
                    help="any of: %s" % ", ".join(PERIMETER))
    ap.add_argument("--outdir", default=None)
    ap.add_argument("--size", type=int, default=900)
    ap.add_argument("--opacity", type=float, default=CUT_OPACITY)
    ap.add_argument("--prefix", default=None)
    ap.add_argument("--no-shadow", action="store_true")
    a = ap.parse_args()

    if a.preset:
        body, cutter, outdir, prefix = preset_vitagripps5(a)
    else:
        if not (a.body and a.cutter):
            ap.error("give two meshes, or --preset")
        body, cutter = pathlib.Path(a.body), pathlib.Path(a.cutter)
        for p in (body, cutter):
            if not p.exists():
                sys.exit("missing %s" % p)
        outdir = pathlib.Path(a.outdir) if a.outdir else body.parent / "overlay"
        prefix = body.stem + "__overlay"
    if a.prefix:
        prefix = a.prefix
    outdir.mkdir(parents=True, exist_ok=True)

    bad = [v for v in a.views if v not in PERIMETER]
    if bad:
        sys.exit("unknown view(s) %s - choose from %s"
                 % (", ".join(bad), ", ".join(PERIMETER)))

    paths = []
    for v in a.views:
        azim, elev = PERIMETER[v]
        out = outdir / ("%s__%s.png" % (prefix, v))
        render_overlay(body, cutter, out, azim, elev, size=a.size,
                       shadow=not a.no_shadow, opacity=a.opacity)
        print("wrote %s" % out)
        paths.append(out)

    if len(paths) > 1:
        sheet = outdir / ("%s__contact_sheet.png" % prefix)
        contact_sheet(paths, sheet)
        print("wrote %s" % sheet)
    return 0


if __name__ == "__main__":
    sys.exit(main())
