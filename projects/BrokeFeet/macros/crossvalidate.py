"""Check the axial reconstruction against the independently-measured sagittal series.

The two CT series were acquired in different planes on the same foot, so they
are an independent check on each other. This is the closest thing available to
ground truth without the original DICOM: if the axial-derived volume and the
sagittal-derived volume agree on a measurement, that measurement is real; where
they disagree, the disagreement IS the reconstruction error, measured rather
than estimated.

Reported per metric:
  - foot skeletal length, width, height
  - forefoot adduction (the deformity component the axial series resolves)
  - plantar profile along the foot's long axis (the equinus)

The surgeon asked what is lost by not having a coronal series. This script
answers the answerable part of that with a number instead of a guess.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import trimesh

PROJECT = Path(__file__).resolve().parent.parent
AXIAL_STL = PROJECT / "BrokeFeet_axial_raw.stl"
SAGITTAL_STL = PROJECT / "BrokeFeet_bone_raw.stl"

# Bodies smaller than this are mesh debris, not bones worth comparing.
MIN_BONE_MM3 = 150.0

# Height above the sole kept as "foot", in mm. 75 mm clears the talar dome on
# an adolescent foot while staying below the malleoli, so both series are
# compared over the same anatomy regardless of how much leg each captured.
ANKLE_CUT_HEIGHT_MM = 75.0

# The axial reconstruction is exported mirrored across X (segment_axial.MIRROR_X,
# applied at the operator's request); the sagittal one is not. Comparing them
# directly measures the mirror rather than the reconstruction error -- adduction
# agreement degrades from 1.36 mm to 8.67 mm, purely as an artefact.
#
# So the SAGITTAL mesh is mirrored here to match the axial. Mirroring the
# comparison copy, in memory, rather than the file on disk: this module exists
# to check the two reconstructions against each other, and neither exported STL
# should be altered to make a check pass.
#
# Read from segment_axial rather than duplicated, so the two cannot drift apart:
# a hand-copied flag left set after MIRROR_X was turned off would break the
# comparison in the other direction, silently.
try:
    from segment_axial import MIRROR_X as MIRROR_SAGITTAL_TO_MATCH_AXIAL
except ImportError:  # segment_axial pulls in scipy/skimage; stay runnable without
    MIRROR_SAGITTAL_TO_MATCH_AXIAL = True


def foot_body(path: Path) -> trimesh.Trimesh:
    """All foot bone below the ankle, as one mesh.

    Taking the single largest connected body does NOT work across both series.
    The sagittal reconstruction fuses the whole foot into one body (its 2 mm
    slices bridge the joint spaces), while the axial reconstruction resolves
    them and yields 17 separate bones. Comparing "largest body" to "largest
    body" therefore measured one tarsal against an entire foot and reported a
    100 mm discrepancy that was an artefact of the selection, not the geometry.

    So: keep every substantial body, then trim the leg. The tibia and fibula
    rise far above the foot and would otherwise dominate the height comparison,
    and the two series captured different lengths of leg.
    """
    mesh = trimesh.load(path)
    bodies = [b for b in mesh.split(only_watertight=False)
              if abs(b.volume) >= MIN_BONE_MM3]
    if not bodies:
        bodies = [mesh]

    combined = trimesh.util.concatenate(bodies)

    # Bring the sagittal mesh into the axial's (mirrored) frame, so the
    # comparison measures reconstruction error and not the mirror.
    if MIRROR_SAGITTAL_TO_MATCH_AXIAL and path == SAGITTAL_STL:
        combined.apply_transform(np.diag([-1.0, 1.0, 1.0, 1.0]))
        combined.fix_normals()

    return _trim_leg(combined)


def _trim_leg(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    """Drop everything above the ankle so both series cover the same anatomy.

    The two captures include different amounts of leg -- the sagittal series
    runs 177 mm tall against the axial series' 110 mm -- so an untrimmed height
    comparison measures the framing, not the foot.

    The cut is placed a fixed distance above the sole rather than at a fraction
    of each mesh's own height. A fraction moves the cut plane between the two
    meshes precisely because they differ in height, which cuts the foot itself
    at different levels and corrupts the very profiles being compared.
    """
    verts = mesh.vertices
    cut = verts[:, 2].min() + ANKLE_CUT_HEIGHT_MM

    keep = verts[:, 2] <= cut
    face_mask = keep[mesh.faces].all(axis=1)

    trimmed = mesh.copy()
    trimmed.update_faces(face_mask)
    trimmed.remove_unreferenced_vertices()
    return trimmed


def _bands_heel_to_toes(verts: np.ndarray, bands: int) -> list[np.ndarray]:
    """Split the foot into bands running heel -> toes, whichever way +Y points.

    The two reconstructions do NOT share a Y direction. The axial mesh puts the
    heel at Y-max and the toes at Y-min; the sagittal mesh is the other way
    round. Both profile functions used to band from y_min to y_max regardless,
    so band 0 was the axial's toes and the sagittal's heel -- the two feet were
    compared head-to-tail.

    That went unnoticed while the axial mesh stopped at the ankle: the profiles
    were wrong but similar enough to pass as reconstruction error (plantar RMS
    9.4 mm). Adding 23 mm of leg made it unmissable -- RMS jumped to 32.3 mm
    with the two columns plainly running in opposite directions.

    The heel is identified by width: it is the broadest part of the foot, while
    the toes splay narrower. Measured on both meshes the margin is clear
    (51.0 vs 36.8 mm axial, 50.4 vs 37.5 mm sagittal), so this is a robust
    discriminator and does not depend on either mesh's coordinate convention.
    """
    y_min, y_max = verts[:, 1].min(), verts[:, 1].max()
    reach = (y_max - y_min) * 0.15
    low_end = verts[verts[:, 1] < y_min + reach]
    high_end = verts[verts[:, 1] > y_max - reach]

    heel_at_y_max = np.ptp(high_end[:, 0]) > np.ptp(low_end[:, 0])

    out = []
    for i in range(bands):
        low = y_min + (y_max - y_min) * i / bands
        high = y_min + (y_max - y_min) * (i + 1) / bands
        out.append(verts[(verts[:, 1] >= low) & (verts[:, 1] < high)])

    return out[::-1] if heel_at_y_max else out


def adduction_profile(mesh: trimesh.Trimesh, bands: int = 10) -> np.ndarray:
    """Mediolateral centroid of the bone in each band along the foot's length.

    A straight foot holds a roughly constant centroid; forefoot adductus bends
    the trace. Reported relative to the hindfoot so the two reconstructions are
    comparable despite sitting in different coordinate origins.
    """
    centres = [band[:, 0].mean() if len(band) else np.nan
               for band in _bands_heel_to_toes(mesh.vertices, bands)]

    centres = np.array(centres)
    return centres - np.nanmean(centres[:3])  # zero on the hindfoot


def plantar_profile(mesh: trimesh.Trimesh, bands: int = 10) -> np.ndarray:
    """Lowest bone surface in each band along the foot -- shows the equinus."""
    lows = [band[:, 2].min() if len(band) else np.nan
            for band in _bands_heel_to_toes(mesh.vertices, bands)]

    lows = np.array(lows)
    return lows - np.nanmin(lows)


def report(name: str, axial: float, sagittal: float, unit: str = "mm") -> float:
    delta = axial - sagittal
    base = max(abs(sagittal), 1e-6)
    print(f"  {name:<26} axial {axial:8.1f}   sagittal {sagittal:8.1f}   "
          f"delta {delta:+7.1f} {unit}  ({abs(delta) / base * 100:4.1f}%)")
    return abs(delta)


def main() -> None:
    for path in (AXIAL_STL, SAGITTAL_STL):
        if not path.exists():
            raise SystemExit(f"missing {path.name} -- run its segmentation script first")

    axial = foot_body(AXIAL_STL)
    sagittal = foot_body(SAGITTAL_STL)

    print("=" * 70)
    print("cross-validation: axial reconstruction vs sagittal series")
    print("=" * 70)
    print()
    print("Overall dimensions (largest bone body):")

    ax_ext, sg_ext = axial.extents, sagittal.extents
    deltas = [
        report("foot width (X)", ax_ext[0], sg_ext[0]),
        report("foot length (Y)", ax_ext[1], sg_ext[1]),
        report("foot height (Z)", ax_ext[2], sg_ext[2]),
    ]

    print()
    print("Forefoot adduction -- mediolateral drift, zeroed on the hindfoot:")
    print("  (this is the component the axial series resolves and the")
    print("   sagittal series can only interpolate across 2 mm gaps)")
    ax_add = adduction_profile(axial)
    sg_add = adduction_profile(sagittal)
    print(f"  {'band (heel->toe)':<20} {'axial':>9} {'sagittal':>10} {'delta':>8}")
    for i, (a, s) in enumerate(zip(ax_add, sg_add)):
        print(f"  {i * 10:3d}-{(i + 1) * 10:3d}% {'':<11} "
              f"{a:9.2f} {s:10.2f} {a - s:8.2f}")

    add_rms = float(np.sqrt(np.nanmean((ax_add - sg_add) ** 2)))

    print()
    print("Plantar profile -- rise above the lowest point (the equinus):")
    ax_pl = plantar_profile(axial)
    sg_pl = plantar_profile(sagittal)
    for i, (a, s) in enumerate(zip(ax_pl, sg_pl)):
        print(f"  {i * 10:3d}-{(i + 1) * 10:3d}% {'':<11} "
              f"{a:9.2f} {s:10.2f} {a - s:8.2f}")

    pl_rms = float(np.sqrt(np.nanmean((ax_pl - sg_pl) ** 2)))

    print()
    print("=" * 70)
    print(f"  overall dimension agreement : max delta {max(deltas):.1f} mm")
    print(f"  adduction profile agreement : RMS {add_rms:.2f} mm")
    print(f"  plantar profile agreement   : RMS {pl_rms:.2f} mm")
    print()
    print("  Interpretation: these are two independent reconstructions of one")
    print("  foot. Where they agree, the geometry is corroborated. Where they")
    print("  differ, the difference bounds the reconstruction error -- it is")
    print("  measured here, not estimated.")
    print("=" * 70)


if __name__ == "__main__":
    main()
