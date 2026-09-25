"""
place_cutter.py - pose a boolean's cutter BY EYE, then print the numbers.
========================================================================
Why this exists
---------------
`render_overlay.py` shows one pose per invocation. Finding a pose that way is
edit-run-look, ten seconds a frame. This opens an interactive window with the
two solids and sliders for the placement parameters, so a pose is found by
dragging and the numbers come out at the end.

The point is that it stays REPRODUCIBLE. Nothing is hand-transformed and
baked into a mesh: the sliders drive the same `socket_placement.pose()` the
builder calls, and on close the window prints the exact command line that
rebuilds what you were looking at. Pose by eye, build by number.

WHAT IT SHOWS
-------------
  body      opaque, the grip shell
  socket    OPAQUE RED - the intersection, i.e. the material the cut removes.
            This is the layer that matters. A translucent cutter is invisible
            where it is buried (see render_overlay.py's note); the
            intersection is a solid object and cannot hide.
  cutter    faint surface + wireframe cage, so its full extent reads even
            where it is submerged

The readout under the sliders carries the numbers no picture gives: the
percentage of volume the cut removes, and whether the socket has a FLOOR (the
console must not cut clean through the shell).

Usage
-----
    python tools/place_cutter.py --preset vitagripps5

    # start from a specific pose
    python tools/place_cutter.py --preset vitagripps5 --y -31 --sink 30

Sliders: Y (console fore-aft centre), SINK (how far the console's bottom sits
below the local top face), SCALE (grip scale factor).

Requires a display. On a headless box use render_overlay.py instead.

Requirements: pyvista, numpy, trimesh
"""

import argparse
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

BODY_COLOR = "#8fa9c4"
CUT_COLOR = "#e0563f"


def _pv(m):
    import pyvista as pv
    faces = np.hstack([np.full((len(m.faces), 1), 3, dtype=np.int64),
                       m.faces]).ravel()
    return pv.PolyData(np.asarray(m.vertices), faces)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--preset", choices=["vitagripps5"], default="vitagripps5")
    ap.add_argument("--y", type=float, default=None)
    ap.add_argument("--sink", type=float, default=None)
    ap.add_argument("--scale", type=float, default=None)
    a = ap.parse_args()

    import pyvista as pv
    import trimesh

    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent
                           / "projects" / "VitaGripPS5" / "macros"))
    import socket_placement as sp

    y0 = a.y if a.y is not None else sp.DEFAULT_Y
    sink0 = a.sink if a.sink is not None else sp.DEFAULT_SINK
    scale0 = a.scale

    # The grip is reloaded only when SCALE changes - it is a 265k-face mesh and
    # rescaling it per slider tick would make the window unusable.
    state = {"y": y0, "sink": sink0, "scale": scale0, "grip": None,
             "grip_scale": None}

    pl = pv.Plotter(window_size=(1280, 900))
    pl.set_background("#e8ecf1", top="#ffffff")
    try:
        pl.enable_depth_peeling(number_of_peels=8, occlusion_ratio=0.0)
    except Exception:
        pass

    actors = {}

    def rebuild(*_):
        g = state["grip"]
        if g is None or state["grip_scale"] != state["scale"]:
            g, f = sp.load_grip(state["scale"])
            state["grip"], state["grip_scale"] = g, state["scale"]
            state["factor"] = f
            for k in ("body",):
                if k in actors:
                    pl.remove_actor(actors.pop(k))
            actors["body"] = pl.add_mesh(
                _pv(g), color=BODY_COLOR, smooth_shading=True, specular=0.4,
                specular_power=20, diffuse=0.85, ambient=0.22)

        try:
            c, info = sp.load_cutter(g, y=state["y"], sink=state["sink"])
        except ValueError as e:
            pl.add_text("ABORT: %s" % e, name="readout", position="lower_left",
                        font_size=9, color="#8c2f1c")
            return

        for k in ("socket", "cutter", "cage"):
            if k in actors:
                pl.remove_actor(actors.pop(k))

        # The intersection - the material actually removed. Opaque, because
        # this is the layer that must never be hidden by depth order.
        pct, floor = float("nan"), "?"
        try:
            inter = trimesh.boolean.intersection([g, c])
            if inter is not None and len(inter.faces) and inter.volume > 0:
                actors["socket"] = pl.add_mesh(
                    _pv(inter), color=CUT_COLOR, opacity=1.0,
                    smooth_shading=True, specular=0.3, diffuse=0.85,
                    ambient=0.28)
                pct = 100.0 * inter.volume / g.volume
                # A socket must have a FLOOR: material below the cutter's
                # underside. If the console cuts clean through, the grip is a
                # frame, not a socket - and no view from above shows that.
                zlo = c.bounds[0][2]
                below = g.vertices[(g.vertices[:, 2] < zlo)
                                   & (np.abs(g.vertices[:, 0])
                                      < c.extents[0] / 2.0)
                                   & (np.abs(g.vertices[:, 1] - state["y"])
                                      <= c.extents[1] / 2.0)]
                floor = "YES (%d verts)" % len(below) if len(below) > 50 \
                    else "NO - cuts through"
        except Exception as e:
            floor = "intersection failed: %s" % e

        cm = _pv(c)
        actors["cutter"] = pl.add_mesh(cm, color=CUT_COLOR, opacity=0.18,
                                       smooth_shading=False, ambient=0.3)
        actors["cage"] = pl.add_mesh(cm.extract_feature_edges(feature_angle=25),
                                     color="#8c2f1c", line_width=3)

        warn = "" if pct >= sp.MIN_PLAUSIBLE_REMOVAL_PCT else \
            "   <- under %.0f %%, the signature of a bad pose" \
            % sp.MIN_PLAUSIBLE_REMOVAL_PCT
        pl.add_text(
            "Y %.1f   SINK %.1f   SCALE %.4f\n"
            "grip %.1f x %.1f x %.1f mm\n"
            "removes %.1f %% of the grip%s\n"
            "socket floor: %s\n"
            "local top of shell %.2f mm"
            % (state["y"], state["sink"], state["factor"],
               *g.extents, pct, warn, floor, info["local_top"]),
            name="readout", position="upper_left", font_size=10,
            color="#20303f")

    def set_y(v):
        state["y"] = float(v)
        rebuild()

    def set_sink(v):
        state["sink"] = float(v)
        rebuild()

    def set_scale(v):
        state["scale"] = float(v)
        rebuild()

    # Y range spans the whole shell so the gap between the grips - where the
    # console hangs in air - is reachable and its abort is visible.
    pl.add_slider_widget(set_y, [-70.0, 70.0], value=y0, title="Y centre (mm)",
                         pointa=(0.60, 0.92), pointb=(0.95, 0.92),
                         style="modern", fmt="%.1f")
    pl.add_slider_widget(set_sink, [0.0, 45.0], value=sink0,
                         title="sink (mm)",
                         pointa=(0.60, 0.80), pointb=(0.95, 0.80),
                         style="modern", fmt="%.1f")
    pl.add_slider_widget(set_scale, [1.20, 1.60],
                         value=scale0 if scale0 else sp.REF_GRIP_W
                         / trimesh.load(str(sp.GRIP_SRC)).extents[0],
                         title="grip scale", pointa=(0.60, 0.68),
                         pointb=(0.95, 0.68), style="modern", fmt="%.4f")

    rebuild()
    pl.add_axes()
    pl.camera_position = "iso"
    pl.show()

    print("\nthe pose you closed on:")
    print("  Y     %.2f" % state["y"])
    print("  sink  %.2f" % state["sink"])
    print("  scale %s" % ("%.4f" % state["scale"] if state["scale"]
                          else "default (width-derived)"))
    print("\nrebuild it:")
    cmd = ("  python projects/VitaGripPS5/macros/build_socket_grip.py "
           "--y %.2f --sink %.2f" % (state["y"], state["sink"]))
    if state["scale"]:
        cmd += " --scale %.4f" % state["scale"]
    print(cmd)
    print("\nsee it again as a render:")
    print("  python tools/render_overlay.py --preset vitagripps5 "
          "--y %.2f --sink %.2f" % (state["y"], state["sink"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
