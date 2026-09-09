"""
strip_dualsense.py - remove every control from the DualSense scan, leaving the
bare ergonomic shell.

WHY THIS EXISTS
---------------
The grip's form IS the DualSense. Rebuilding it from a table of widths was
tried and rejected: the part matched the reference at 41 stations and still
read as two lumps on a stick, because a width profile plus an aspect ratio does
not constrain a shape (see docs/lessons.md). So the scan is used as geometry
directly, and the only thing that has to happen first is that the controls come
off - sticks, D-pad, face buttons, touchpad, shoulder buttons - because a grip
is held, not operated.

THREE METHODS WERE MEASURED. TWO FAILED.
----------------------------------------
All numbers on the centred 200k mesh (bbox 160.51 x 112.34 x 60.57).

1. A FLAT Z CUT cannot work. The body's own top surface reaches Z 17-20 mm
   away from any control - 20.31 at the left grip, 17.86 between the sticks -
   while the sticks reach 30.29. Slicing:

       Z > 18   two clusters, X -60..-10 and 12..55  (body shoulders included)
       Z > 20   sticks isolated, BUT the grip pokes through at X -51..-44

   A plane at 17 planes the grips flat; a plane at 20 leaves button stubs.

2. THE CONVEX HULL is worse: it spans the concave gap between the grips and
   inflates the volume from 368 to 668 cm3. The gap is the point of a grip.

3. MORPHOLOGICAL OPEN+CLOSE (ball radius r, 1 mm voxels) removes the small
   stuff but stalls on the sticks:

       r= 5   zmax 28.50    r= 9   zmax 23.50
       r= 7   zmax 24.50    r=11   zmax 22.50

   and what survives above Z=20 is exactly X -34.5..-14.5 and 15.5..35.5 -
   the two stick bosses, ~20 mm across. A ball big enough to remove a 20 mm
   boss is comparable to the grip's own radius, so it eats the grips. No
   morphological filter separates these two features; they are the same size.

THE METHOD THAT WORKS: A LOCAL HEIGHT CAP
-----------------------------------------
The separation that IS clean is vertical, and it is local rather than global:

       around each stick, the surrounding shell tops out at 18.8-20.1 mm
       the stick column itself reaches                      30.1-30.3 mm

Ten millimetres of clear air, everywhere on the face. So the face is capped at
a height taken from the shell AROUND each column rather than from one global
plane: for every (x, y) column, the cap is the shell height in an annulus
around it, and material above that cap is removed. Bumps go, the body's own
curvature stays, and the grips - which are never a local maximum against their
own surroundings - are untouched.

The cap is then smoothed across x-y so the resurfaced face is continuous rather
than terraced, and the result is re-meshed.

WHAT THIS DOES NOT DO
---------------------
It does not thin, shell, scale or reorient. It removes controls and nothing
else, so the output is checkable against the input on the number that matters:
the 120 mm tip-to-tip anchor the user measured with calipers.

Run:
    python projects/VitaGripPS5/macros/strip_dualsense.py
    python projects/VitaGripPS5/macros/strip_dualsense.py --pitch 0.6

Input   derived/dualsense_watertight_200k.stl
Output  derived/dualsense_stripped.stl
"""

import argparse
import pathlib
import sys

import numpy as np
import trimesh

try:
    from scipy import ndimage
except ImportError:
    sys.exit("scipy is required: pip install scipy")

HERE = pathlib.Path(__file__).resolve().parent
DERIVED = HERE.parent / "derived"
SRC = DERIVED / "dualsense_watertight_200k.stl"
OUT = DERIVED / "dualsense_stripped.stl"

# The anchor: the user's caliper reading across the two grip tips. Measured on
# the raw scan as 120.442 mm at Y = 105.75 in the mesh's own frame. Every
# operation re-measures it and the script refuses to write a mesh that moved
# it - the same gate prepare_dualsense.py uses, for the same reason.
ANCHOR_MM = 120.442

# The gate compares the stripped mesh against a VOXEL CONTROL - the same mesh
# voxelised and re-surfaced with NO cap applied - not against the source.
#
# Measured, with the cap disabled entirely:
#     pitch 1.0  ->  +1.572 mm      pitch 0.6  ->  +0.772 mm
#     pitch 0.8  ->  -1.228 mm
#
# Identical shifts appear with the cap ON, so that error is the voxel
# round-trip, not the cap. It shrinks with pitch and CHANGES SIGN, which is
# quantisation, not erosion - a cap eating the grips could only ever make the
# span smaller. A first version compared stripped-vs-source, read that
# round-trip as grip damage, and aborted three good results in a row.
#
# Against the control the cap's own effect on the anchor is isolated, and the
# tolerance can be tight because it is measuring one thing.
ANCHOR_TOL = 0.6

# Radius of the annulus the cap height is read from, in mm. It must exceed the
# widest control (the stick bosses measure ~20 mm across, so ~10 mm from
# centre) and stay below the grip's own curvature scale.
ANNULUS_MM = 16.0

# The face is +Z. Nothing below this is a control; the back shell and the grips
# live there and must not be touched.
FACE_Z_MIN = 8.0


# The anchor measurement is IMPORTED, not re-implemented. A first draft of this
# script wrote its own tip_span() that maximised the X extent over Y slices; it
# read 154.075 mm where the real measurement is 120.442, because the widest
# slice is at the shoulders and the user's calipers were on the TIPS. It then
# "detected" a 1.4 mm drift that did not exist and aborted a good result.
#
# prepare_dualsense.tip_span() selects the slice CLOSEST TO 120 mm, which is
# the measurement the user actually took. Two scripts measuring one anchor two
# ways is the drift docs/lessons.md is about, so there is now one function.
import importlib.util as _ilu

_pd = HERE / "prepare_dualsense.py"
_spec = _ilu.spec_from_file_location("_prepare_dualsense", _pd)
_pdm = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_pdm)
tip_span = _pdm.tip_span          # returns (y_of_slice, span_mm)


def strip(mesh, pitch, annulus_mm=ANNULUS_MM, face_z_min=FACE_Z_MIN,
          apply_cap=True):
    """Remove face controls with a locally-derived height cap.

    apply_cap=False runs the identical voxelise/re-surface path with no cap,
    producing the control the anchor gate compares against.
    """
    vg = mesh.voxelized(pitch=pitch).fill()
    occ = np.asarray(vg.matrix, dtype=bool)      # [x, y, z]
    org = vg.bounds[0]

    if not apply_cap:
        from trimesh.voxel.ops import matrix_to_marching_cubes
        c = matrix_to_marching_cubes(occ, pitch=pitch)
        c.apply_translation(org - c.bounds[0])
        return c

    nz = occ.shape[2]
    zi = np.arange(nz)
    zmm = org[2] + zi * pitch

    # Top occupied voxel per (x, y) column -> a height field of the surface.
    any_col = occ.any(axis=2)
    top_idx = np.where(any_col, occ.shape[2] - 1 -
                       np.argmax(occ[:, :, ::-1], axis=2), -1)
    top_mm = np.where(any_col, org[2] + top_idx * pitch, -np.inf)

    # The cap: for each column, the MEDIAN surface height in an annulus around
    # it. Median, not max - a max would be dragged up by a neighbouring
    # control, which is the very thing being removed. The annulus excludes the
    # column's own neighbourhood so a wide boss cannot vote for itself.
    r_out = max(2, int(round(annulus_mm / pitch)))
    r_in = max(1, int(round(annulus_mm * 0.55 / pitch)))
    k = np.arange(-r_out, r_out + 1)
    yy, xx = np.meshgrid(k, k, indexing="ij")
    d2 = xx * xx + yy * yy
    ring = (d2 <= r_out * r_out) & (d2 >= r_in * r_in)

    filled = np.where(any_col, top_mm, np.nan)
    cap = ndimage.generic_filter(
        filled, lambda v: np.nanmedian(v) if np.any(~np.isnan(v)) else np.nan,
        footprint=ring, mode="nearest")

    # Smooth the cap so the resurfaced face is continuous, not terraced.
    capf = np.where(np.isnan(cap), np.nanmax(cap), cap)
    capf = ndimage.gaussian_filter(capf, sigma=max(1.0, 3.0 / pitch))

    # Remove only material that is BOTH above the local cap AND on the face
    # side. A margin keeps the cap from shaving the shell it was read from.
    cap3 = capf[:, :, None] + 1.0
    z3 = np.broadcast_to(zmm[None, None, :], occ.shape)
    kill = (z3 > cap3) & (z3 > face_z_min)
    out = occ & ~kill

    # Largest connected component: capping can shear a control's tip loose.
    lab, n = ndimage.label(out)
    if n > 1:
        sizes = ndimage.sum(out, lab, range(1, n + 1))
        out = lab == (int(np.argmax(sizes)) + 1)

    from trimesh.voxel.ops import matrix_to_marching_cubes
    m = matrix_to_marching_cubes(out, pitch=pitch)
    m.apply_translation(org - m.bounds[0])
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pitch", type=float, default=0.8)
    ap.add_argument("--annulus", type=float, default=ANNULUS_MM)
    ap.add_argument("--no-write", action="store_true")
    a = ap.parse_args()

    if not SRC.exists():
        sys.exit("missing %s - run prepare_dualsense.py first" % SRC)

    src = trimesh.load(str(SRC))
    src.apply_translation(-src.bounds.mean(axis=0))
    _, a0 = tip_span(src)
    print("source   %6d faces  bbox %.2f x %.2f x %.2f  vol %.1f cm3"
          % (len(src.faces), *src.extents, src.volume / 1000))
    print("         tip span %.3f mm   Zmax %.2f\n" % (a0, src.vertices[:, 2].max()))

    ctl = strip(src, a.pitch, a.annulus, apply_cap=False)
    _, ac = tip_span(ctl)
    print("control  %6d faces  (voxel round-trip, no cap)  tip %.3f  Zmax %.2f"
          % (len(ctl.faces), ac, ctl.vertices[:, 2].max()))
    print("         round-trip shift %+.3f mm vs source\n" % (ac - a0))

    m = strip(src, a.pitch, a.annulus)
    _, a1 = tip_span(m)
    print("stripped %6d faces  bbox %.2f x %.2f x %.2f  vol %.1f cm3"
          % (len(m.faces), *m.extents, m.volume / 1000))
    print("         tip span %.3f mm   Zmax %.2f" % (a1, m.vertices[:, 2].max()))
    print("         watertight %s  bodies %d" % (m.is_watertight, m.body_count))
    print("\n  vs source  %+.3f mm (includes the voxel round-trip)" % (a1 - a0))
    print("  vs control %+.3f mm  <- the cap's own effect (tol %.1f)"
          % (a1 - ac, ANCHOR_TOL))

    if abs(a1 - ac) > ANCHOR_TOL:
        sys.exit("ABORT: the cap is eating the grips, which are the whole "
                 "point of this mesh. Raise --annulus.")

    if not a.no_write:
        m.export(str(OUT))
        print("  wrote %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
