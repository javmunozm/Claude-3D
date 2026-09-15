"""
watch_model.py - a window that stays open and REPAINTS WHEN THE MODEL CHANGES.
=============================================================================
Why this exists, and why the other two tools are not this
--------------------------------------------------------
`render_overlay.py` writes a PNG of one pose. `place_cutter.py` opens a window
you drag sliders in and then CLOSE to get numbers out. Both are snapshots: to
see the effect of an edit you go back to a shell and run something again.

That is not what is needed while a model is being worked on. When a script is
being edited - by hand or by an agent - the question is "what did that change
do", asked continuously, and the answer has to arrive without anyone typing a
command.

So this process does one thing: it holds a window open, polls the files the
model is built from, and when any of them changes it rebuilds the geometry and
repaints. Leave it running on a second monitor. Every edit shows up in it a
second or two later.

WHAT IT DRAWS
-------------
Same three layers as render_overlay.py, for the same reason - a translucent
cutter is INVISIBLE where it is submerged, because VTK resolves transparency by
depth order and buried geometry loses:

  body      opaque shell
  socket    OPAQUE RED - the intersection, the material the cut removes.
            The layer that must never be hidden.
  cutter    faint surface + edge cage, so its extent reads even when buried

The heads-up text carries what a picture cannot: percentage of volume removed,
whether the socket has a floor, and the current placement numbers.

WHAT IT WATCHES
---------------
The placement module, the build script, and the input meshes. Editing any of
them repaints the window. Geometry is rebuilt from the SAME
`socket_placement.pose()` the builder calls, so what is on screen is what will
be built - not a second implementation that can drift from it.

Usage
-----
    python tools/watch_model.py                       # VitaGripPS5 socket cut
    python tools/watch_model.py --y -31 --sink 30     # start from a pose
    python tools/watch_model.py --interval 0.5        # poll faster

Leave it open. Edit `socket_placement.py` (or anything it reads) and watch.

Press 'r' to force a rebuild, 'q' to quit.

Requires a display. Headless: use render_overlay.py.

Requirements: pyvista, numpy, trimesh
"""

import argparse
import importlib
import pathlib
import sys
import time
import traceback

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
MACROS = ROOT / "projects" / "VitaGripPS5" / "macros"
sys.path.insert(0, str(MACROS))

BODY_COLOR = "#8fa9c4"
CUT_COLOR = "#e0563f"
EDGE_COLOR = "#8c2f1c"
WIN_COLOR = "#1b7f4b"    # rear touch panel window - green, so it reads apart
                         # from the socket cutter's red at a glance

# Files whose mtime triggers a rebuild. The placement module first: it is the
# one an edit is most likely to touch.
WATCH = [
    MACROS / "socket_placement.py",
    MACROS / "build_socket_grip.py",
    MACROS / "strip_dualsense.py",
    ROOT / "projects" / "VitaGripPS5" / "derived" / "dualsense_stripped.stl",
    ROOT / "projects" / "VitaGripPS5" / "console_solid.stl",
]


def stamps():
    """mtime of every watched file; missing files read as 0."""
    out = {}
    for p in WATCH:
        try:
            out[p] = p.stat().st_mtime
        except OSError:
            out[p] = 0.0
    return out


def _pv(m):
    import pyvista as pv
    faces = np.hstack([np.full((len(m.faces), 1), 3, dtype=np.int64),
                       m.faces]).ravel()
    return pv.PolyData(np.asarray(m.vertices), faces)


class Viewer:
    def __init__(self, pl, args):
        self.pl = pl
        self.args = args
        self.actors = {}
        self.marks = stamps()
        self.grip_cache = None
        self.grip_scale = None
        self.n = 0
        # "overlay" shows the OPERANDS (body + socket + cutter cage), which is
        # what finds a pose. "cut" shows the RESULT of the difference, which is
        # what says whether the pose produced a real pocket. Both are needed:
        # a coherent-looking overlay can still cut almost nothing, and the
        # result view is the only one that shows that.
        self.mode = "overlay"

    def geometry(self):
        """Rebuild from the builder's own module, reimported so edits land.

        importlib.reload is the whole point: without it the process keeps the
        version of the module it imported at startup and the window would show
        stale geometry while claiming to be live.
        """
        import trimesh
        import socket_placement as sp
        # invalidate_caches() before the reload, and drop any stale .pyc.
        #
        # Without this the reload is UNRELIABLE, and it fails in the one case
        # that matters most: undoing an edit. Python's import system caches
        # source mtimes at 1-second granularity, so a file edited and then
        # restored inside the same second reloads to the FIRST version - the
        # window keeps showing a change you already reverted. Measured: sink
        # 10.0 -> 32.0 reloaded correctly, 32.0 -> 10.0 kept reporting 32.0.
        importlib.invalidate_caches()
        sp = importlib.reload(sp)

        y = self.args.y if self.args.y is not None else sp.DEFAULT_Y
        sink = self.args.sink if self.args.sink is not None else sp.DEFAULT_SINK

        if self.grip_cache is None or self.grip_scale != self.args.scale:
            g, f = sp.load_grip(self.args.scale)
            self.grip_cache, self.grip_scale, self.factor = g, self.args.scale, f
        g = self.grip_cache

        c, info = sp.load_cutter(g, y=y, sink=sink)
        info["factor"] = self.factor

        # The rear touch panel window, from the same module, on the same pose.
        # None if this build of socket_placement.py predates it, so the viewer
        # keeps working against an older placement module.
        w = None
        if hasattr(sp, "window_cutter"):
            try:
                w, winfo = sp.window_cutter(g, c)
                info.update(winfo)
            except Exception as e:
                print("window_cutter failed: %s" % e)

        inter, pct, floor = None, 0.0, "?"
        try:
            inter = trimesh.boolean.intersection([g, c])
            if inter is not None and len(inter.faces) and inter.volume > 0:
                pct = 100.0 * inter.volume / g.volume
                zlo = c.bounds[0][2]
                below = g.vertices[(g.vertices[:, 2] < zlo)
                                   & (np.abs(g.vertices[:, 0]) < c.extents[0] / 2.0)
                                   & (np.abs(g.vertices[:, 1] - y) <= c.extents[1] / 2.0)]
                floor = ("YES (%d verts below)" % len(below)) if len(below) > 50 \
                    else "NO - the console cuts clean through"
            else:
                inter = None
                floor = "no intersection - the cutter misses the body"
        except Exception as e:
            floor = "intersection failed: %s" % e
        return g, c, w, inter, info, pct, floor, sp

    def draw(self):
        self.n += 1
        pl = self.pl
        try:
            g, c, w, inter, info, pct, floor, sp = self.geometry()
        except Exception:
            for k in list(self.actors):
                pl.remove_actor(self.actors.pop(k))
            pl.add_text("BUILD FAILED\n\n%s" % traceback.format_exc()[-900:],
                        name="readout", position="upper_left", font_size=8,
                        color="#8c2f1c")
            pl.render()
            return

        for k in list(self.actors):
            pl.remove_actor(self.actors.pop(k))

        cut_line = ""
        if self.mode == "cut":
            # PERFORM THE CUT, IN THE WINDOW, WITHOUT WRITING ANYTHING.
            #
            # Same call the builder makes - trimesh.boolean.difference, i.e.
            # manifold3d - on the same pose from the same module. No STL is
            # exported: the result lives in this process only. Baking a mesh
            # is a separate, explicit act.
            import trimesh
            try:
                part = trimesh.boolean.difference([g, c])
                if part.body_count > 1:
                    part = max(part.split(only_watertight=False),
                               key=lambda m: m.volume)
                # The rear touch panel window, as a second cut - same order the
                # builder uses, so the window shows what will be built.
                if w is not None:
                    part = trimesh.boolean.difference([part, w])
                    if part.body_count > 1:
                        part = max(part.split(only_watertight=False),
                                   key=lambda m: m.volume)
                self.actors["part"] = pl.add_mesh(
                    _pv(part), color=BODY_COLOR, smooth_shading=True,
                    specular=0.45, specular_power=22, diffuse=0.85,
                    ambient=0.22)
                removed = g.volume - part.volume
                cut_line = ("\nCUT: %.1f x %.1f x %.1f mm  vol %.1f cm3\n"
                            "     watertight %s  bodies %d  genus %d\n"
                            "     removed %.1f cm3 (%.1f %%)"
                            % (*part.extents, part.volume / 1000,
                               part.is_watertight, part.body_count,
                               (2 - part.euler_number) // 2,
                               removed / 1000, 100.0 * removed / g.volume))
            except Exception as e:
                cut_line = "\nCUT FAILED: %s" % e
        else:
            self.actors["body"] = pl.add_mesh(
                _pv(g), color=BODY_COLOR, smooth_shading=True, specular=0.4,
                specular_power=20, diffuse=0.85, ambient=0.22)

            if inter is not None:
                self.actors["socket"] = pl.add_mesh(
                    _pv(inter), color=CUT_COLOR, opacity=1.0,
                    smooth_shading=True, specular=0.3, diffuse=0.85,
                    ambient=0.28)

            cm = _pv(c)
            self.actors["cutter"] = pl.add_mesh(cm, color=CUT_COLOR,
                                                opacity=0.15,
                                                smooth_shading=False,
                                                ambient=0.3)
            self.actors["cage"] = pl.add_mesh(
                cm.extract_feature_edges(feature_angle=25),
                color=EDGE_COLOR, line_width=3)

            # The window cutter, drawn as a cage only. It is buried inside the
            # shell, so a translucent surface would be invisible - the same
            # depth-order problem this module already documents for the socket.
            if w is not None:
                self.actors["wincage"] = pl.add_mesh(
                    _pv(w).extract_feature_edges(feature_angle=25),
                    color=WIN_COLOR, line_width=4)

        warn = "" if pct >= sp.MIN_PLAUSIBLE_REMOVAL_PCT else \
            "   <- under %.0f %%, the signature of a bad pose" \
            % sp.MIN_PLAUSIBLE_REMOVAL_PCT
        pl.add_text(
            "[%s]  rebuild #%d   %s\n"
            "Y %.1f   sink %.1f   scale %.4f\n"
            "grip   %.1f x %.1f x %.1f mm\n"
            "cutter %.1f x %.1f x %.1f mm  at Z %.2f\n"
            "removes %.2f %% of the grip%s\n"
            "socket floor: %s%s"
            % (self.mode.upper(), self.n, time.strftime("%H:%M:%S"),
               info["y"], info["sink"], info["factor"],
               *g.extents, *info["placed_extents"], info["z_centre"],
               pct, warn, floor, cut_line),
            name="readout", position="upper_left", font_size=10,
            color="#20303f")
        pl.render()

    def poll(self, *_):
        """Timer tick: repaint only if a watched file actually moved."""
        now = stamps()
        if now != self.marks:
            self.marks = now
            print("[%s] change detected - rebuilding" % time.strftime("%H:%M:%S"))
            self.draw()


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--y", type=float, default=None)
    ap.add_argument("--sink", type=float, default=None)
    ap.add_argument("--scale", type=float, default=None)
    ap.add_argument("--mode", choices=["cut", "overlay"], default="cut",
                    help="what the window opens on: 'cut' is the boolean "
                         "RESULT, 'overlay' is the operands (default: cut)")
    ap.add_argument("--interval", type=float, default=1.0,
                    help="seconds between file checks (default 1.0)")
    a = ap.parse_args()

    import pyvista as pv

    pl = pv.Plotter(window_size=(1280, 900))
    pl.set_background("#e8ecf1", top="#ffffff")
    try:
        pl.enable_depth_peeling(number_of_peels=8, occlusion_ratio=0.0)
    except Exception:
        pass

    v = Viewer(pl, a)
    v.mode = a.mode
    v.draw()
    pl.add_axes()
    pl.camera_position = "iso"
    pl.add_key_event("r", v.draw)

    # No arguments, not even *args: pyvista's add_key_event rejects any
    # callback with a parameter that lacks a default.
    def toggle():
        v.mode = "cut" if v.mode == "overlay" else "overlay"
        print("mode -> %s" % v.mode)
        v.draw()

    pl.add_key_event("c", toggle)

    # A MANUAL UPDATE LOOP, NOT A TIMER CALLBACK.
    #
    # The first version armed `pl.add_timer_event(...)`. It NEVER FIRED - and
    # nothing said so, which is the worst part: the window opened, rendered the
    # startup pose, and sat there looking correct while nine successive edits
    # to the placement never reached the screen. Measured directly:
    #
    #     pl.add_timer_event(max_steps=100, duration=500, callback=tick)
    #         -> ticks fired: 0
    #     pl.iren.add_observer('TimerEvent', cb)
    #     + iren.interactor.CreateRepeatingTimer(400)
    #         -> ticks fired: 0        (so it is not the pyvista wrapper)
    #
    # This VTK build does not dispatch timer events to the interactor at all.
    # What DOES work is driving the event loop by hand: show() with
    # interactive_update=True returns instead of blocking, and each update()
    # call processes input and re-renders. Verified: 21 iterations in 6 s, with
    # a live actor swap mid-loop.
    #
    # The lesson for anything added here later: a callback that is never
    # invoked is indistinguishable from a scene that never changes. Prove the
    # refresh mechanism fires before trusting anything drawn through it.
    print("watching %d files, polling every %.1fs" % (len(WATCH), a.interval))
    for p in WATCH:
        print("   %s" % p.relative_to(ROOT))
    print("\nedit any of them and the window repaints.  'r' forces a rebuild, "
          "close the window to quit.")
    print("'c' toggles OVERLAY (operands) <-> CUT (boolean result).")

    pl.show(interactive_update=True, auto_close=False)
    try:
        while True:
            # render_window goes null once the user closes the window; that is
            # the loop's exit condition, and the only one.
            if pl.render_window is None:
                break
            pl.update()
            v.poll()
            time.sleep(a.interval)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            pl.close()
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
