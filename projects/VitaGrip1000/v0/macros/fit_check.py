"""
VitaGrip1000 - fit check against the real PCH-1000.

`render_check.py` gates topology: watertight, one body, consistent winding. None
of that can tell you whether the console actually goes in. This does, by
sampling the console mesh's surface and testing containment in the grip solid.

It found two defects the topology gates passed clean:
  * the console resting on the channel floor with zero clearance (420 points),
  * the console's front corners fouling the handles, caused by a 4 mm fillet on
    the pocket's plan corners pinching the mouth to +-7.28 mm where the console
    needs +-8.89 (127 points).

Run:  python projects\\VitaGrip1000\\macros\\fit_check.py
Exit code 0 if the console fits, 1 if it does not.
"""

import sys
from pathlib import Path

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[4]
# The version this script lives in, so v0 and v2 each check their OWN
# export. Hard-coding the project folder made both read one file.
GRIP = Path(__file__).resolve().parents[1] / "stl" / "VitaGrip1000.stl"
CONSOLE = ROOT / "sources" / "psvitaGrip" / "Vita 1000" / "psvitaManualJoin_decimated.stl"

N_SAMPLES = 200_000
CONTAINS_BATCH = 5_000

# The console the grip is built around, for reference in the report.
CONSOLE_SPEC = (182.0, 83.55, 18.6)


def main():
    if not GRIP.exists():
        print("grip not built: %s" % GRIP)
        print("run macros/vita_grip.py first")
        return 1
    if not CONSOLE.exists():
        print("console mesh missing: %s" % CONSOLE)
        return 1

    grip = trimesh.load(GRIP)
    console = trimesh.load(CONSOLE)

    # The macro builds in a console-centred frame, so centre the console mesh
    # the same way. Its own bounds are the alignment - it is not watertight
    # (6 bodies, CT-style artefacts) so its centroid is not trustworthy.
    console.apply_translation(-console.bounds.mean(axis=0))

    print("=" * 70)
    print("fit_check - VitaGrip1000 vs PCH-1000")
    print("=" * 70)
    print("  console mesh   %.2f x %.2f x %.2f mm  (spec %.1f x %.2f x %.1f)"
          % (*console.extents, *CONSOLE_SPEC))
    print("  grip           %.2f x %.2f x %.2f mm" % tuple(grip.extents))
    print()

    pts = console.sample(N_SAMPLES)
    # Batched: trimesh's ray-based containment allocates
    # (n_points x n_faces) intermediates, and 200k points against this
    # 600k-face mesh asks for a 2.17 GiB array in one go. The batching
    # changes nothing about what is tested.
    inside = np.concatenate([
        grip.contains(pts[i:i + CONTAINS_BATCH])
        for i in range(0, len(pts), CONTAINS_BATCH)
    ])
    n = int(inside.sum())

    print("  console surface points inside the grip solid: %d / %d (%.4f %%)"
          % (n, N_SAMPLES, 100.0 * n / N_SAMPLES))

    if n:
        p = pts[inside]
        print()
        print("  INTERFERENCE region:")
        print("    X %8.2f .. %8.2f" % (p[:, 0].min(), p[:, 0].max()))
        print("    Y %8.2f .. %8.2f" % (p[:, 1].min(), p[:, 1].max()))
        print("    Z %8.2f .. %8.2f" % (p[:, 2].min(), p[:, 2].max()))
        print()
        print("  Group the points by axis to localise it: a cluster at one Y is")
        print("  usually the channel floor; a cluster at large |X| is the handles.")
        print()
        print("=" * 70)
        print("VERDICT: the console does NOT fit")
        print("=" * 70)
        return 1

    print()
    print("=" * 70)
    print("VERDICT: the console fits - no interference")
    print("=" * 70)
    print()
    print("  NOTE: zero interference means the console is not inside the solid.")
    print("        It does NOT prove the fit is comfortable, that the walls")
    print("        retain it, or that it is reachable in one motion. Only a test")
    print("        print against the real console settles those.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
