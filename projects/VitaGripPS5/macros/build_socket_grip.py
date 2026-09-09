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
    ap.add_argument("--no-write", action="store_true")
    a = ap.parse_args()

    for p in (GRIP_SRC, CONSOLE):
        if not p.exists():
            sys.exit("missing %s" % p)

    g = trimesh.load(str(GRIP_SRC))
    g.apply_translation(-g.bounds.mean(axis=0))
    print("stripped grip  %.2f x %.2f x %.2f mm  vol %.1f cm3  wt=%s"
          % (*g.extents, g.volume / 1000, g.is_watertight))

    f = a.scale if a.scale else REF_GRIP_W / g.extents[0]
    g.apply_scale(f)
    print("scale %.4f -> %.2f x %.2f x %.2f mm  vol %.1f cm3"
          % (f, *g.extents, g.volume / 1000))

    c = trimesh.load(str(CONSOLE))
    c.apply_translation(-c.bounds.mean(axis=0))
    print("console raw    %.2f x %.2f x %.2f mm  wt=%s"
          % (*c.extents, c.is_watertight))

    # ORIENT IT. console_solid.stl is X=width 182.7, Y=DEPTH 19.3, Z=HEIGHT
    # 84.25 - it stands on edge, screen facing along Y. The grip's frame is
    # X=width, Y=fore-aft, Z=up, and the Vita lies FLAT across the grips with
    # its screen facing up: its 84.25 mm height runs fore-aft (Y) and its
    # 19.3 mm depth runs up (Z).
    #
    # Placed unrotated, the console presents only its 19.3 mm edge to the
    # grip and the boolean removed 13.0 cm3 - 1.3 % - which is the console
    # grazing the shell rather than sinking into it. That number is what
    # caught the error: a socket for a 182 x 84 mm object cannot be 1 % of
    # the part.
    c.apply_transform(trimesh.transformations.rotation_matrix(
        np.pi / 2.0, [1, 0, 0]))
    print("console placed %.2f x %.2f x %.2f mm  (rotated 90 deg about X)"
          % tuple(c.extents))

    # Grow the cutter by the fit clearance so the printed socket is not a
    # press fit. Scaling a solid scales it about its centre, which is what is
    # wanted: clearance on every face.
    cw, cd, ch = c.extents
    c.apply_scale([(cw + 2 * FIT_CLEAR) / cw,
                   (cd + 2 * FIT_CLEAR) / cd,
                   (ch + 2 * FIT_CLEAR) / ch])

    # PLACEMENT, AND WHY IT IS NOT AT THE TRIGGER END.
    #
    # The first attempt put the console at Y = -31 (30 % up from the trigger
    # end) and the boolean removed 1.2 %. The reason is in the shell itself:
    # measured on the scaled grip, the CENTRE of the body does not exist below
    # about Y = -15 -
    #
    #     Y -35   centre: no material     outer (grips): Zmax 19.84
    #     Y -15   centre Zmax 33.90       outer          Zmax 27.28
    #     Y +25   centre Zmax 32.24       outer          Zmax 31.42
    #
    # - because that is the open span between the two grips, the gap a
    # DualSense has under the shoulder buttons. A console placed there hangs
    # in air between the grips and touches almost nothing.
    #
    # The console is 84.25 mm deep once laid flat, and solid body runs
    # Y -15..78, so a centre near +20 puts the whole footprint over material.
    ytop = g.bounds[1][1]
    y = a.y if a.y is not None else 20.0
    # Sink: the console's BOTTOM sits this far below the local top face, so
    # the socket has a floor instead of cutting clean through.
    sink = a.sink if a.sink is not None else 10.0
    band = g.vertices[(np.abs(g.vertices[:, 1] - y) <= c.extents[1] / 2.0)
                      & (np.abs(g.vertices[:, 0]) < c.extents[0] / 2.0)]
    if len(band) < 100:
        sys.exit("ABORT: no grip material under the console footprint at "
                 "Y=%.1f - the console would hang in the gap between the "
                 "grips." % y)
    # The top face is a DOME, not a plane - measured under the footprint it
    # runs 35.55 at the middle down to 26.0 at the edges. Sinking from the
    # PEAK therefore only engages the peak, and the cut came out 2.2 %.
    #
    # So the reference is the LOWEST top-of-shell across the footprint: the
    # console has to clear the whole dome, not just its summit. Columns are
    # binned in X-Y and the minimum column top is taken.
    bx = np.round(band[:, 0] / 5.0).astype(int)
    by = np.round(band[:, 1] / 5.0).astype(int)
    key = bx.astype(np.int64) * 100000 + by
    order = np.argsort(key)
    k_s, z_s = key[order], band[order, 2]
    bounds_i = np.flatnonzero(np.diff(k_s)) + 1
    tops = [seg.max() for seg in np.split(z_s, bounds_i) if len(seg) >= 3]
    ztop_local = float(np.percentile(tops, 5)) if tops else float(band[:, 2].max())
    z = ztop_local - sink + c.extents[2] / 2.0
    c.apply_translation([0.0, y, z])
    print("console placed at Y %.2f  Z %.2f  (local top %.2f, sink %.2f mm)"
          % (y, z, ztop_local, sink))

    part = trimesh.boolean.difference([g, c])
    if part.body_count > 1:
        part = max(part.split(only_watertight=False), key=lambda m: m.volume)

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
