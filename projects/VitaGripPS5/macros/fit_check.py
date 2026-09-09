"""
fit_check.py - does a real PCH-1000 actually sit in this grip?

Run:  python projects\\VitaGripPS5\\macros\\fit_check.py

Two questions, and they are NOT the same:

  1. INTERFERENCE - is any part of the console inside the grip's material?
     Sampled on the real decimated PCH-1000 mesh. Must be zero.

  2. RETENTION - is the console actually held? A grip that interferes with
     nothing might simply not touch the console at all. Interference of zero
     is necessary, not sufficient, and the previous project's README records
     exactly this trap.

The console is placed by the SAME datum the build script uses: Z = 0 is the
console's bottom edge, centred in X, and its rear face against the channel's
back wall.
"""

import sys
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
GRIP = HERE.parent / "VitaGripPS5.stl"
MESH = (ROOT / "sources" / "psvitaGrip" / "Vita 1000"
        / "psvitaManualJoin_decimated.stl")

CONSOLE_W, CONSOLE_H, CONSOLE_D = 182.0, 83.55, 18.6
FIT_CLEAR = 0.35
N = 200000


def main():
    if not GRIP.exists():
        print("no grip STL. The swept-tube geometry and its build scripts were "
              "DELETED on 2026-09-08 - the user rejected the figure. See this "
              "project's README. Nothing builds VitaGripPS5.stl right now; the "
              "rebuild starts from the DualSense scan.")
        return 1
    if not MESH.exists():
        print("no console mesh at %s" % MESH)
        return 1

    g = trimesh.load(str(GRIP))
    print("grip    %s mm  watertight=%s  vol %.1f cm3"
          % (np.round(g.extents, 2).tolist(), g.is_watertight,
             g.volume / 1000.0))

    c = trimesh.load(str(MESH))
    # The mesh is not watertight (6 bodies), so centre it by BOUNDS, not by
    # centroid - recorded in the repo's SOURCES.md.
    c.apply_translation(-c.bounds.mean(axis=0))
    print("console raw %s mm  (mesh axes: X=width, Y=HEIGHT, Z=depth)"
          % np.round(c.extents, 2).tolist())

    # THE TWO MODELS DO NOT SHARE AN AXIS CONVENTION.
    #
    # The console mesh is X=width, Y=height, Z=depth (182.14 x 83.73 x 18.53).
    # The build script is X=width, Y=depth, Z=height. Placing the mesh without
    # rotating it lays the console on its face inside the grip, and every
    # interference number measured from that is meaningless - the first runs
    # reported 2,698 and then 860 colliding points and sent me rounding the
    # channel floor to fix a collision that was an axis error.
    #
    # Rotate +90 deg about X so height becomes Z and depth becomes Y.
    R = trimesh.transformations.rotation_matrix(np.pi / 2.0, [1, 0, 0])
    c.apply_transform(R)
    print("console     %s mm (spec %.1f x %.1f x %.1f)"
          % (np.round(c.extents, 2).tolist(), CONSOLE_W, CONSOLE_D, CONSOLE_H))

    # Place it on the build's datum: bottom edge at Z = 0, centred in X and Y.
    c.apply_translation([0.0, 0.0, c.extents[2] / 2.0])

    pts = c.sample(N)

    # BATCHED. contains() ray-casts every point against every candidate
    # triangle, and 200k points against this 600k-face mesh asked for a
    # 4.02 GiB intermediate array and died. The batch size is a memory
    # ceiling, not a change of method - the same points are tested.
    inside = np.zeros(len(pts), dtype=bool)
    B = 5000
    for i in range(0, len(pts), B):
        inside[i:i + B] = g.contains(pts[i:i + B])
    n = int(inside.sum())
    print()
    print("  console surface points inside the grip: %d / %d (%.4f %%)"
          % (n, N, 100.0 * n / N))

    if n:
        bad = pts[inside]
        print("  worst region: X %.1f..%.1f  Y %.1f..%.1f  Z %.1f..%.1f"
              % (bad[:, 0].min(), bad[:, 0].max(),
                 bad[:, 1].min(), bad[:, 1].max(),
                 bad[:, 2].min(), bad[:, 2].max()))

    # RETENTION: how close does the grip come to the console anywhere?
    # Zero interference is necessary, not sufficient - a grip that touches
    # nothing also interferes with nothing. Measured on a SUBSAMPLE, because
    # exact proximity over 200k points is far more expensive than containment
    # and a few thousand samples answer the question just as well.
    sub = pts[np.random.default_rng(0).choice(len(pts), 4000, replace=False)]
    d = np.abs(trimesh.proximity.signed_distance(g, sub))
    print("  closest approach of grip to console: %.2f mm" % d.min())
    print("  sampled points within 1.0 mm of it:  %d / %d"
          % (int((d < 1.0).sum()), len(sub)))

    print()
    if n == 0:
        print("  VERDICT: no interference")
    else:
        print("  VERDICT: FAIL - the console collides with the grip")
    print()
    print("  NOTE: zero interference does NOT prove the console is RETAINED,")
    print("        nor that it can be inserted in one motion. Only a test")
    print("        print settles those.")
    return 0 if n == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
