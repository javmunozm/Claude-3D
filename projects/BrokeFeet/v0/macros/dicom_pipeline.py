"""Reconstruct the foot from the ORIGINAL DICOM study, when it can be obtained.

The current model is built from PACS screenshots because the viewer permits
printing but not export. That costs three things this script recovers:

  1. Hounsfield units. Screenshots arrive with the viewer's window/level
     (W:3500 C:500) already applied and quantised to 8-bit grey, so bone is
     segmented by apparent brightness. DICOM carries real densities, so the
     threshold becomes a physical quantity (~200-300 HU for cortical bone)
     rather than a value tuned by eye against a few slices.
  2. True geometry. Slice spacing, pixel spacing and patient orientation come
     from the file headers instead of being read off an on-screen ruler.
  3. Every acquired plane. The coronal series -- where the calcaneal and talar
     neck varus actually live -- was never captured as screenshots.

Run it the day the study arrives:

    python dicom_pipeline.py <path-to-dicom-folder>

It writes a per-bone STL set plus a combined mesh, in the same coordinate
convention as segment_axial.py, so the downstream build
(brokefeet_axial_b123d.py) works unchanged.

Requires: pydicom, and either SimpleITK or scikit-image.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

PROJECT = Path(__file__).resolve().parent.parent

# --- segmentation parameters, in Hounsfield units --------------------------

# Cortical bone runs 300+ HU in an adult; trabecular bone 100-300. An
# adolescent's bone is less dense than an adult's, so the threshold sits at the
# lower end of the usual 200-300 range. Unlike the screenshot pipeline, this is
# a physical quantity: it does not need retuning per series.
BONE_HU = 200.0

# Bones smaller than this are debris. Sized from the smallest bone that must
# survive -- a 5th distal phalanx, measured at 64-113 mm3 in this patient.
MIN_BONE_MM3 = 40.0

ISO_VOXEL_MM = 0.4  # finer than the screenshot pipeline's 0.5; DICOM supports it


def load_series(folder: Path):
    """Load a DICOM series into a HU volume plus its voxel spacing."""
    try:
        import pydicom
    except ImportError:
        raise SystemExit("pip install pydicom")

    files = sorted(folder.rglob("*.dcm"))
    if not files:
        files = sorted(p for p in folder.rglob("*") if p.is_file())
    if not files:
        raise SystemExit(f"no DICOM files under {folder}")

    slices = []
    for path in files:
        try:
            dataset = pydicom.dcmread(str(path))
        except Exception:
            continue
        if not hasattr(dataset, "PixelData"):
            continue
        slices.append(dataset)

    if not slices:
        raise SystemExit(f"no readable DICOM images under {folder}")

    # Sort along the patient axis rather than by filename -- acquisition order
    # and filename order are not reliably the same.
    slices.sort(key=lambda d: float(d.ImagePositionPatient[2]))

    volume = np.stack([s.pixel_array.astype(np.float32) for s in slices])

    # Rescale to Hounsfield units. Stored pixels are not HU until the slope and
    # intercept from the header are applied.
    first = slices[0]
    slope = float(getattr(first, "RescaleSlope", 1.0))
    intercept = float(getattr(first, "RescaleIntercept", 0.0))
    volume = volume * slope + intercept

    row_mm, col_mm = (float(v) for v in first.PixelSpacing)
    if len(slices) > 1:
        z_mm = abs(
            float(slices[1].ImagePositionPatient[2])
            - float(slices[0].ImagePositionPatient[2])
        )
    else:
        z_mm = float(getattr(first, "SliceThickness", 1.0))

    print(f"  {len(slices)} slices, {volume.shape[2]}x{volume.shape[1]} px")
    print(f"  voxel {col_mm:.3f} x {row_mm:.3f} x {z_mm:.3f} mm")
    print(f"  HU range {volume.min():.0f} .. {volume.max():.0f}")

    return volume, (z_mm, row_mm, col_mm)


def segment(volume: np.ndarray, spacing) -> np.ndarray:
    from scipy import ndimage

    mask = volume >= BONE_HU

    structure = ndimage.generate_binary_structure(2, 1)
    for k in range(mask.shape[0]):
        mask[k] = ndimage.binary_closing(mask[k], structure=structure, iterations=2)
        mask[k] = ndimage.binary_fill_holes(mask[k])

    # Fill marrow cavities in 3D: any background region not connected to the
    # volume boundary is interior to bone.
    background, count = ndimage.label(~mask)
    if count:
        edge = set(background[0].flat) | set(background[-1].flat)
        edge |= set(background[:, 0].flat) | set(background[:, -1].flat)
        edge |= set(background[:, :, 0].flat) | set(background[:, :, -1].flat)
        edge.discard(0)
        mask |= ~np.isin(background, list(edge)) & ~mask

    voxel_mm3 = spacing[0] * spacing[1] * spacing[2]
    min_voxels = MIN_BONE_MM3 / voxel_mm3

    labels, count = ndimage.label(mask)
    sizes = ndimage.sum(mask, labels, range(1, count + 1))
    keep = [i + 1 for i, size in enumerate(sizes) if size >= min_voxels]

    print(f"  {count} components, {len(keep)} above {MIN_BONE_MM3} mm3")
    return np.isin(labels, keep)


def to_mesh(mask: np.ndarray, spacing):
    from scipy import ndimage
    from skimage import measure
    import trimesh

    zoom = tuple(s / ISO_VOXEL_MM for s in spacing)

    # Anti-alias at source resolution before resampling, so cortical shells
    # thinner than the target voxel are not punched through.
    occupancy = ndimage.gaussian_filter(mask.astype(np.float32), sigma=0.8)
    iso = ndimage.zoom(occupancy, zoom, order=1) >= 0.4

    # Pad so bone touching the stack boundary still closes.
    iso = np.pad(iso, 1, mode="constant", constant_values=False)

    verts, faces, _, _ = measure.marching_cubes(iso, level=0.5)
    verts = (verts - 1.0) * ISO_VOXEL_MM

    # (slice, row, col) -> (X medial-lateral, Y heel-toe, Z up), matching
    # segment_axial.py so the downstream build is unchanged.
    verts = np.column_stack([verts[:, 2], -verts[:, 1], verts[:, 0]])

    mesh = trimesh.Trimesh(vertices=verts, faces=faces)
    if mesh.volume < 0:
        mesh.invert()
    mesh.update_faces(mesh.nondegenerate_faces())
    mesh.update_faces(mesh.unique_faces())
    mesh.remove_unreferenced_vertices()
    return mesh


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)

    folder = Path(sys.argv[1])
    if not folder.exists():
        raise SystemExit(f"{folder} does not exist")

    print(f"loading DICOM from {folder}...")
    volume, spacing = load_series(folder)

    print(f"segmenting bone at >= {BONE_HU} HU...")
    mask = segment(volume, spacing)

    print("meshing...")
    mesh = to_mesh(mask, spacing)

    import trimesh

    bodies = [b for b in mesh.split(only_watertight=False)
              if abs(b.volume) >= MIN_BONE_MM3]
    print(f"  {len(bodies)} bones, {sum(abs(b.volume) for b in bodies) / 1000:.1f} cm3")

    out_dir = PROJECT / "bones_dicom"
    out_dir.mkdir(exist_ok=True)
    for i, body in enumerate(sorted(bodies, key=lambda b: -abs(b.volume))):
        body.export(out_dir / f"bone_{i:02d}.stl")

    combined = PROJECT / "BrokeFeet_dicom_raw.stl"
    trimesh.util.concatenate(bodies).export(combined)

    print(f"\nwrote {len(bodies)} bones to {out_dir}")
    print(f"wrote {combined}")
    print()
    print("Next: point brokefeet_axial_b123d.BONE_STL at the file above and")
    print("rebuild. This model IS patient-specific -- remove the embossed")
    print("'MODELO REPRESENTATIVO' warning and re-validate before use.")


if __name__ == "__main__":
    main()
