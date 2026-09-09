"""
make_console_cutter.py - a WATERTIGHT console solid to boolean against.

Run:  python projects\\VitaGripPS5\\macros\\make_console_cutter.py

WHY THIS EXISTS
---------------
`psvitaManualJoin_decimated.stl` is the real PCH-1000, and it is the right
shape to carve the grip's slot with - a box approximates the console's rounded
ends and tapered edges badly. But it cannot be used as a boolean operand as it
stands:

  * 599,998 faces in 6 significant bodies plus ~18 fragments of 1-38 faces
  * NOT watertight - the largest body (the rear shell, 119,916 faces) is open
  * the front and rear shells are separate solids ~15 mm deep each; only
    together do they make the 18.53 mm console

A boolean against a non-watertight operand is undefined, and Blender's EXACT
solver will either leave garbage or return nothing.

WHAT THIS DOES
--------------
Voxel-remeshes the whole thing into ONE closed solid:

  1. drop the fragments (< 1000 faces) - they are meshing debris, not console
  2. voxelise the union at PITCH, fill it, and marching-cubes it back out
  3. keep the largest resulting body

Voxelising is deliberate. It closes the open rear shell and merges front,
rear, sticks and buttons into a single solid, which is exactly what a cutter
needs to be. The cost is PITCH-scale rounding of sharp detail - irrelevant
here, because this is a CUTTER: it defines a pocket the console drops into,
and the pocket is grown by FIT_CLEAR anyway.

The output is DILATED by FIT_CLEAR so the slot it cuts already carries the
clearance.

The button and stick positions are printed, because the grip must not cover
them and those numbers are needed before any chamfer is placed.
"""

import sys
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SRC = (ROOT / "sources" / "psvitaGrip" / "Vita 1000"
       / "psvitaManualJoin_decimated.stl")
OUT = HERE.parent / "console_solid.stl"

CONSOLE_W, CONSOLE_D, CONSOLE_H = 182.0, 18.6, 83.55
PITCH = 0.6                 # voxel size for the first pass, mm
COARSE = 2.2                # second pass - the cutter that is actually used
FIT_CLEAR = 0.35            # per side - the cutter carries the clearance


def main():
    if not SRC.exists():
        print("missing %s" % SRC)
        return 1

    m = trimesh.load(str(SRC))
    print("source: %d faces, watertight=%s, %d bodies"
          % (len(m.faces), m.is_watertight, m.body_count))

    parts = [c for c in m.split(only_watertight=False) if len(c.faces) >= 1000]
    print("kept %d bodies over 1000 faces (dropped the debris)" % len(parts))
    for c in parts:
        print("   %7d faces  extents %s"
              % (len(c.faces), np.round(c.extents, 1).tolist()))

    big = trimesh.util.concatenate(parts)

    # Centre by BOUNDS, not centroid - the mesh is not watertight and its
    # centroid is meaningless. Recorded in the repo's SOURCES.md.
    big.apply_translation(-big.bounds.mean(axis=0))

    # Match the build's axes: the mesh is X=width, Y=HEIGHT, Z=depth; the
    # build is X=width, Y=depth, Z=height.
    big.apply_transform(
        trimesh.transformations.rotation_matrix(np.pi / 2.0, [1, 0, 0]))
    # Datum: the console's bottom edge sits at Z = 0.
    big.apply_translation([0.0, 0.0, big.extents[2] / 2.0])

    print("\nvoxelising at %.2f mm ..." % PITCH)
    keep = big.bounds.copy()          # remember where it really is
    vg = big.voxelized(pitch=PITCH).fill()

    # marching_cubes returns the surface in VOXEL INDEX space, not world
    # units: the first attempt produced a 305.70 x 31.70 x 141.70 mm "console"
    # because the pitch scaling and the origin were both dropped. Restore
    # both by scaling by PITCH and re-seating the result on the bounds the
    # input actually had.
    sol = vg.marching_cubes
    sol.apply_scale(PITCH)
    sol = max(sol.split(only_watertight=False), key=lambda q: len(q.faces))
    sol.apply_translation(keep[0] - sol.bounds[0])
    trimesh.repair.fix_normals(sol)

    got, want = sol.extents, (keep[1] - keep[0])
    print("  extents %s vs input %s"
          % (np.round(got, 2).tolist(), np.round(want, 2).tolist()))
    if np.any(np.abs(got - want) > 3.0):
        print("  FAIL voxel remesh lost the scale")
        return 1
    print("solid: %d faces, watertight=%s, %d bodies, vol %.1f cm3"
          % (len(sol.faces), sol.is_watertight, sol.body_count,
             sol.volume / 1000.0))

    if not sol.is_watertight:
        sol.fill_holes()
        print("  after fill_holes: watertight=%s" % sol.is_watertight)


    # COARSEN BY RE-VOXELISING, not by quadric decimation.
    #
    # At 0.6 mm pitch the remesh carries 518,228 faces, and cutting the grip
    # with an operand that dense shattered it into 67 components - the solver
    # drowns in near-degenerate slivers off the voxel staircase.
    #
    # simplify_quadric_decimation(6000) got the count right and came back NOT
    # WATERTIGHT, which is exactly the defect this script exists to prevent:
    # a boolean against an open operand is undefined. Repair did not close it.
    #
    # Voxelising again at a coarser pitch is watertight BY CONSTRUCTION - a
    # filled voxel grid has no holes - and it removes the fine detail that
    # produced the slivers in the first place. The cutter only has to define a
    # pocket, and it already carries FIT_CLEAR, so COARSE-scale rounding of
    # sharp corners is not a loss here.
    before = len(sol.faces)
    keep2 = sol.bounds.copy()
    vg2 = sol.voxelized(pitch=COARSE).fill()
    sol = vg2.marching_cubes
    sol.apply_scale(COARSE)
    sol = max(sol.split(only_watertight=False), key=lambda q: len(q.faces))
    sol.apply_translation(keep2[0] - sol.bounds[0])
    trimesh.repair.fix_normals(sol)

    # Voxelising DILATES: each pass adds about a voxel all round, so after two
    # passes the "console" measured 185.60 x 20.80 x 86.40 against the real
    # 182.14 x 18.53 x 83.73. Scale it back onto the true extents, then let
    # the FIT_CLEAR dilation below be the only clearance in the part.
    want = np.array([CONSOLE_W, CONSOLE_D, CONSOLE_H])
    sol.apply_scale(want / sol.extents)
    sol.apply_translation([-sol.bounds.mean(axis=0)[0],
                           -sol.bounds.mean(axis=0)[1],
                           -sol.bounds[0][2]])
    print("  re-voxelised at %.1f mm: %d -> %d faces, watertight=%s"
          % (COARSE, before, len(sol.faces), sol.is_watertight))
    print("  rescaled to %s (true console)"
          % np.round(sol.extents, 2).tolist())

    # SMOOTH THE VOXEL STAIRCASE.
    #
    # The cutter is watertight and the right size, but its surface is a 2.2 mm
    # voxel staircase. Booleaning the grip against it left 10-16 tiny internal
    # voids and an open mesh - the near-parallel step faces produce slivers
    # the solver cannot resolve.
    #
    # Taubin smoothing removes the terracing without the shrinkage a plain
    # Laplacian causes, so the cutter keeps its dimensions. Applied BEFORE the
    # dilation, so the clearance below is measured on the smoothed surface.
    import trimesh.smoothing as _sm
    _sm.filter_taubin(sol, iterations=25)
    sol.apply_scale(want / sol.extents)
    sol.apply_translation([-sol.bounds.mean(axis=0)[0],
                           -sol.bounds.mean(axis=0)[1],
                           -sol.bounds[0][2]])
    trimesh.repair.fix_normals(sol)
    print("  smoothed: watertight=%s, extents %s"
          % (sol.is_watertight, np.round(sol.extents, 2).tolist()))

    # DILATE LAST. The clearance was applied before the rescale at first, and
    # the rescale-to-true-extents then divided it straight back out: the
    # cutter came out exactly 182.00 x 18.60 x 83.55, i.e. a console-sized
    # pocket with ZERO clearance, which no real console would go into.
    sol.vertices += sol.vertex_normals * FIT_CLEAR
    print("  dilated by %.2f mm/side -> %s"
          % (FIT_CLEAR, np.round(sol.extents, 2).tolist()))

    # A boolean against a non-watertight operand is UNDEFINED. Refuse to
    # write one.
    if not sol.is_watertight:
        print("  FAIL cutter is not watertight")
        return 1

    b = sol.bounds
    print("\ncutter placed on the build datum:")
    print("  X %.2f..%.2f   Y %.2f..%.2f   Z %.2f..%.2f"
          % (b[0][0], b[1][0], b[0][1], b[1][1], b[0][2], b[1][2]))
    print("  W %.2f  D %.2f  H %.2f mm" % tuple(sol.extents))

    # ---- where the controls are, so the grip never covers them -----------
    # Anything standing proud of the console's flat faces is a control: the
    # sticks, the shoulder buttons, the d-pad and the face buttons.
    v = sol.vertices
    front = v[v[:, 1] > 7.0]
    rear = v[v[:, 1] < -7.0]
    print("\ncontrols - what must stay clear:")
    for tag, sel in (("front face  (screen, sticks, buttons)", front),
                     ("rear face   (touch panel)", rear)):
        if len(sel):
            print("  %-38s X %7.1f..%6.1f  Z %6.1f..%6.1f"
                  % (tag, sel[:, 0].min(), sel[:, 0].max(),
                     sel[:, 2].min(), sel[:, 2].max()))

    # Shoulder buttons live on the TOP edge, at the outer thirds.
    top = v[v[:, 2] > sol.bounds[1][2] - 6.0]
    if len(top):
        xs = np.abs(top[:, 0])
        print("  %-38s |X| %.1f..%.1f  (top edge band)"
              % ("top edge    (shoulder buttons)", xs.min(), xs.max()))

    sol.export(str(OUT))
    print("\nwrote %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
