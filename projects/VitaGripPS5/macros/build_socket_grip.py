"""
build_socket_grip.py - enlarge the stripped DualSense and cut a Vita socket in it.

THE METHOD, AS SPECIFIED
------------------------
1. take the stripped DualSense shell (controls already removed)
2. scale it up until it can hold a PS Vita
3. cut the console solid out of it, so the cut leaves a SOCKET the Vita drops
   into

No smoothing, no shelling, no ergonomic edits. The DualSense's own surface is
the grip's surface; the only subtraction is the console.

THE SCALE FACTOR
----------------
Set by WIDTH, because width is what holds the console.

    stripped DualSense    161.40 x 113.40 x 51.60 mm
    reference grip        222.4 mm wide  (054-1.webp, corrected anchor)
    scale                 222.4 / 161.40 = 1.3779

Uniform scale cannot match the reference on both axes: at 1.3779 the grip
length becomes 156.3 mm against the reference's 112.3, because a DualSense is
proportionally much longer front-to-back than a Vita grip. Width governs and
the extra length is a consequence, not an error - it is stated here so nobody
later reads 156.3 as a defect.

WHY THE CONSOLE DOES NOT SIMPLY FIT IN THE GAP
----------------------------------------------
Measured on the stripped shell, the widest gap between the two grips is
109.8 mm, and at scale 1.50 it is still only 168.3 mm against a 182.7 mm
console. The console was never going to drop through that gap:

    scale 1.35  gap 151.5    scale 1.45  gap 162.7
    scale 1.40  gap 157.1    scale 1.50  gap 168.3

It sits ACROSS the grips and the boolean carves its own socket - which is what
"merge/cut ... with a cut you can create a socket where the ps vita goes"
describes. The gap measurement is kept because it is the evidence that a
pure-fit approach is impossible, not merely worse.

CONSOLE PLACEMENT
-----------------
The console solid is 182.70 x 19.30 x 84.25 mm (X width, Y depth, Z height).
It is laid across the grips at the trigger end (-Y), the end whose gap opens
toward the user, and sunk far enough that the socket has walls.

Run:
    python projects/VitaGripPS5/macros/build_socket_grip.py
    python projects/VitaGripPS5/macros/build_socket_grip.py --scale 1.45 --sink 30

Input   derived/dualsense_stripped.stl   (from strip_dualsense.py)
        console_solid.stl
Output  VitaGripPS5.stl
"""

import argparse
import pathlib
import sys

import numpy as np
import trimesh

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import socket_placement as sp

HERE = pathlib.Path(__file__).resolve().parent
PROJ = HERE.parent
DERIVED = PROJ / "derived"
GRIP_SRC = DERIVED / "dualsense_stripped.stl"
CONSOLE = PROJ / "console_solid.stl"
OUT = PROJ / "VitaGripPS5.stl"

REF_GRIP_W = 222.4      # 054-1.webp at the corrected 0.246279 mm/px anchor
FIT_CLEAR = 0.35        # per side, on the console before it is used as a cutter


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", type=float, default=None,
                    help="override; default sets grip width to %.1f mm"
                         % REF_GRIP_W)
    ap.add_argument("--sink", type=float, default=None,
                    help="how far the console's bottom sits below the grip's "
                         "top face, mm (default: half the console height)")
    ap.add_argument("--y", type=float, default=None,
                    help="console Y centre in grip coords (default: the "
                         "trigger end, where the grips open)")
    ap.add_argument("--tilt", type=float, default=None,
                    help="console tilt about X in degrees (default %.2f)"
                         % sp.DEFAULT_TILT)
    ap.add_argument("--no-window", action="store_true",
                    help="skip the rear touch panel window cut")
    ap.add_argument("--no-write", action="store_true")
    a = ap.parse_args()

    for p in (GRIP_SRC, CONSOLE):
        if not p.exists():
            sys.exit("missing %s" % p)

    # PLACEMENT COMES FROM socket_placement.py, NOT FROM HERE.
    #
    # This block used to recompute the scale factor and the console pose
    # inline. It is now one call, because a second implementation of a
    # placement is exactly how this repo shipped a gate that tested a pose
    # 30 mm off the built one and reported a clean pass (docs/lessons.md,
    # "the gate must share the datum it tests"). The overlay renderer and the
    # live viewer import the same function, so what was seen is what is cut.
    g, c, w, info = sp.pose(scale=a.scale,
                            y=a.y if a.y is not None else sp.DEFAULT_Y,
                            sink=a.sink if a.sink is not None else sp.DEFAULT_SINK,
                            tilt=a.tilt if a.tilt is not None else sp.DEFAULT_TILT,
                            window=not a.no_window)
    print("stripped grip  scaled %.4f -> %.2f x %.2f x %.2f mm  vol %.1f cm3"
          % (info["scale"], *info["grip_extents"], g.volume / 1000))
    print("console        %.2f x %.2f x %.2f mm  (raw %.2f x %.2f x %.2f)"
          % (*info["placed_extents"], *info["raw_extents"]))
    print("placed at      Y %.2f  Z %.2f  tilt %.2f deg"
          % (info["y"], info["z_centre"], info["tilt"]))
    print("               local top of shell %.2f mm, sink %.2f mm, clear %.2f"
          % (info["local_top"], info["sink"], info["clear"]))

    part = trimesh.boolean.difference([g, c])
    if part.body_count > 1:
        part = max(part.split(only_watertight=False), key=lambda m: m.volume)

    # THE REAR TOUCH PANEL WINDOW, AS A SECOND CUT.
    #
    # Applied after the socket, not unioned into it: the window's datum is the
    # placed console's own footprint, so it cannot be computed until the socket
    # cutter exists. Reported separately because a single removal percentage
    # covering both cuts would hide either one going wrong.
    if w is not None:
        seated = part.volume
        part = trimesh.boolean.difference([part, w])
        if part.body_count > 1:
            part = max(part.split(only_watertight=False), key=lambda m: m.volume)
        wr = seated - part.volume
        print("window         %.1f x %.1f mm at Y %.2f  removed %.1f cm3 (%.2f %%)"
              % (info["window_w"], info["window_h"], info["window_y"],
                 wr / 1000, 100.0 * wr / seated))
        if wr <= 0:
            sys.exit("ABORT: the window cut removed nothing.")

    print("\nresult         %.2f x %.2f x %.2f mm  vol %.1f cm3"
          % (*part.extents, part.volume / 1000))
    print("               watertight %s  bodies %d  faces %d"
          % (part.is_watertight, part.body_count, len(part.faces)))
    removed = g.volume - part.volume
    print("               removed %.1f cm3 (%.1f %% of the grip)"
          % (removed / 1000, 100.0 * removed / g.volume))
    if removed <= 0:
        sys.exit("ABORT: the cut removed nothing - the console is not "
                 "intersecting the grip. Check --y and --sink.")

    if not a.no_write:
        part.export(str(OUT))
        print("\nwrote %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
