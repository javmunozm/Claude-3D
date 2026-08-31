"""Segment bone from the de-identified sagittal stack and export a mesh.

WHAT THIS CAN AND CANNOT DO
---------------------------
The input is screen-captured 8-bit grayscale, not DICOM. The viewer had already
applied a window/level (W:3500 C:500) before the screenshot was taken, which
maps a 3500 HU-wide range onto 256 gray levels and clips everything outside it.
That mapping is lossy and not invertible, so this script cannot threshold on
Hounsfield units the way a real segmentation does. It thresholds on *apparent
brightness* instead, which tracks bone density well for cortical bone and less
well for trabecular bone next to dense soft tissue.

Consequence: bone SHAPE comes out well, bone BOUNDARIES are approximate, and
anything requiring absolute density (cortical thickness, bone quality) is not
recoverable. The model this produces is a teaching aid, not a planning model.

Geometry is better than an early spot-check suggested: the stack is a regular
2 mm sagittal sweep (see slice_positions.py), so inter-slice spacing is real
rather than guessed. What is still missing is the axial and coronal series --
with sagittal planes only, the medial-lateral bone boundaries are interpolated
between 2 mm samples rather than measured.
"""

from __future__ import annotations

import glob
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

from slice_positions import (
    MM_PER_PX,
    PX_PER_MM,
    SLICE_LOC_MM,
    sorted_slices,
)

REPO = Path(__file__).resolve().parents[4]
DEID_DIR = REPO / "references" / "brokenfeet_deid"
OUT_DIR = Path(__file__).resolve().parent.parent

# --- segmentation parameters ----------------------------------------------

# Apparent-brightness threshold separating bone from soft tissue.
#
# Chosen by overlaying candidate thresholds on a mid-sagittal slice and LOOKING
# at the result, not from the histogram alone. The histogram's valley sits near
# 130-150, but at those levels the tarsals segment as hollow cortical rims: the
# trabecular interior of the talus and calcaneus is darker than the shell, and
# the rim develops gaps that binary_fill_holes then cannot close, so the bones
# come out as open shells rather than solids.
#
# At 110 the rim stays continuous in-plane and every bone -- tibia, talus,
# calcaneus, navicular, cuneiforms, first metatarsal, sesamoid -- fills as a
# closed body. The cost is that 110 also catches the densest soft tissue at the
# skin/tendon boundary, which the connected-component filter below removes.
BONE_THRESHOLD = 110

# The paediatric/adolescent foot has thin cortical shells at this resolution;
# a small closing fills the 1-2 px gaps that thresholding leaves in them so
# each bone comes out as a closed volume rather than a shell with holes.
CLOSING_RADIUS = 2

# Speckle below this voxel count is capture noise or vessel calcification, not
# bone worth modelling.
MIN_COMPONENT_VOXELS = 400

# The viewer burns orientation letters (H at the top, F at the bottom) and a
# ruler into the pane, inside the crop this pipeline keeps. They are bright
# enough to pass BONE_THRESHOLD and, being drawn at a fixed screen position,
# they appear at the SAME pixel in every slice -- so they survive connected-
# component filtering as tall columns spanning the whole stack, and meshed as
# two horizontal bars floating above and below the foot.
#
# Discarding this margin at top and bottom removes them. The foot never reaches
# it: anatomy occupies rows ~50-900 of a ~1045-row pane.
OVERLAY_MARGIN_PX = 30

# A real bone spans a limited run of slices. Anything present in nearly every
# plane at a fixed position is viewer chrome, not anatomy -- a second, more
# specific guard than the margin crop above.
MAX_COMPONENT_SLICE_SPAN = 0.85

# Post-mesh speck removal, in mm3. A sesamoid -- the smallest bone worth
# keeping -- is several hundred mm3; anything under 100 is noise.
MIN_BODY_VOLUME_MM3 = 100.0

# Resample the stack to isotropic voxels before meshing. The in-plane pixel is
# 0.21 mm and the slice step is 2 mm -- a 9.5:1 anisotropy that produces badly
# stair-stepped meshes if fed to marching cubes directly.
ISO_VOXEL_MM = 0.6


def load_stack() -> tuple[np.ndarray, np.ndarray]:
    """Load slices in anatomical order. Returns (volume, loc_positions_mm)."""
    files = sorted(glob.glob(str(DEID_DIR / "slice_*.png")))
    if not files:
        raise SystemExit(f"no de-identified slices in {DEID_DIR}; run deidentify.py")

    by_order = {i: f for i, f in enumerate(files)}
    planes = sorted_slices()

    # Panes differ by a few px in height between captures; crop all to the
    # smallest so they stack. Cross-correlation showed misregistration of at
    # most 2 px (~0.4 mm), so a plain crop is adequate -- no warping needed.
    heights = [Image.open(f).size[1] for f in files]
    widths = [Image.open(f).size[0] for f in files]
    height, width = min(heights), min(widths)

    volume = np.zeros((len(planes), height, width), dtype=np.uint8)
    positions = np.zeros(len(planes))

    for k, (order, loc) in enumerate(planes):
        image = np.array(Image.open(by_order[order]).convert("L"))
        volume[k] = image[:height, :width]
        positions[k] = loc

    return volume, positions


def segment(volume: np.ndarray) -> np.ndarray:
    """Threshold, clean, and keep only substantial connected bone."""
    mask = volume >= BONE_THRESHOLD

    # Drop the bands carrying the viewer's orientation letters and ruler.
    mask[:, :OVERLAY_MARGIN_PX, :] = False
    mask[:, -OVERLAY_MARGIN_PX:, :] = False

    # Close small gaps within each slice plane rather than across slices --
    # 2 mm apart, adjacent slices are too far to close against each other.
    structure = ndimage.generate_binary_structure(2, 1)
    for k in range(mask.shape[0]):
        mask[k] = ndimage.binary_closing(
            mask[k], structure=structure, iterations=CLOSING_RADIUS
        )
        mask[k] = ndimage.binary_fill_holes(mask[k])

    labels, count = ndimage.label(mask)
    if count == 0:
        raise SystemExit("threshold produced no bone -- check BONE_THRESHOLD")

    sizes = ndimage.sum(mask, labels, range(1, count + 1))
    boxes = ndimage.find_objects(labels)
    depth = mask.shape[0]
    span_limit = depth * MAX_COMPONENT_SLICE_SPAN

    keep = []
    for index, size in enumerate(sizes):
        if size < MIN_COMPONENT_VOXELS:
            continue
        z_slice = boxes[index][0]
        if (z_slice.stop - z_slice.start) > span_limit:
            print(f"    dropped label {index + 1}: spans {z_slice.stop - z_slice.start}"
                  f"/{depth} slices -- viewer chrome, not bone")
            continue
        keep.append(index + 1)

    cleaned = np.isin(labels, keep)

    print(f"  components: {count} found, {len(keep)} kept "
          f"(>= {MIN_COMPONENT_VOXELS} voxels, < {span_limit:.0f} slice span)")
    return cleaned


def to_isotropic(mask: np.ndarray, positions: np.ndarray) -> np.ndarray:
    """Resample the anisotropic stack onto an isotropic grid for meshing."""
    span_mm = positions.max() - positions.min()
    depth_out = max(2, int(round(span_mm / ISO_VOXEL_MM)))

    zoom = (
        depth_out / mask.shape[0],
        (MM_PER_PX / ISO_VOXEL_MM),
        (MM_PER_PX / ISO_VOXEL_MM),
    )
    # order=1 on a float view, then re-threshold: nearest-neighbour on a binary
    # mask would preserve the stair-stepping this resample exists to remove.
    resampled = ndimage.zoom(mask.astype(np.float32), zoom, order=1)

    # Linear interpolation alone still leaves visible terracing along the
    # mediolateral axis, because that axis is upsampled ~3.3x from 2 mm slices
    # while the in-plane axes are DOWNsampled from 0.21 mm. Blurring the
    # occupancy field before thresholding lets marching cubes cut a smooth
    # isosurface through it instead of tracking slice boundaries.
    #
    # The blur is deliberately anisotropic -- strongest across slices, where
    # the sampling is coarsest, and light in-plane where the data is already
    # fine and further smoothing would erode genuine detail.
    resampled = ndimage.gaussian_filter(resampled, sigma=(1.6, 0.6, 0.6))

    return resampled >= 0.5


def main() -> None:
    print("loading stack...")
    volume, positions = load_stack()
    print(f"  {volume.shape[0]} planes, {volume.shape[2]}x{volume.shape[1]} px each")
    print(f"  LOC {positions.min():.0f}..{positions.max():.0f} mm, "
          f"in-plane {PX_PER_MM:.3f} px/mm")

    print("segmenting bone...")
    mask = segment(volume)
    print(f"  bone voxels: {mask.sum():,}")

    print("resampling to isotropic...")
    iso = to_isotropic(mask, positions)
    print(f"  isotropic grid {iso.shape} at {ISO_VOXEL_MM} mm/voxel")

    print("meshing...")
    try:
        from skimage import measure
    except ImportError:
        raise SystemExit("scikit-image required for marching cubes: pip install scikit-image")

    verts, faces, normals, _ = measure.marching_cubes(iso, level=0.5)
    verts *= ISO_VOXEL_MM  # voxel index -> mm

    # Map voxel axes to anatomy. The array is (slice, row, col):
    #   axis 0 = slice   -> mediolateral   -> X
    #   axis 1 = row     -> superoinferior -> Z, and the image's +row runs DOWN
    #                       the screen, so it negates to give +Z up
    #   axis 2 = column  -> anteroposterior -> Y
    # Without this the foot meshes standing on end with its long axis vertical.
    verts = np.column_stack([verts[:, 0], verts[:, 2], -verts[:, 1]])

    import trimesh

    # Flipping an axis reverses triangle orientation; reversing the winding
    # restores outward normals (otherwise the mesh reports negative volume).
    faces = faces[:, ::-1]

    mesh = trimesh.Trimesh(vertices=verts, faces=faces)
    # trimesh 4.x replaced remove_degenerate_faces/remove_duplicate_faces with
    # boolean masks fed to update_faces.
    mesh.update_faces(mesh.nondegenerate_faces())
    mesh.update_faces(mesh.unique_faces())
    mesh.remove_unreferenced_vertices()
    mesh.fill_holes()

    # Drop sub-millimetre specks: capture noise and vessel calcification that
    # survived the voxel filter but are not bone anyone wants printed.
    bodies = mesh.split(only_watertight=False)
    if len(bodies) > 1:
        substantial = [b for b in bodies if b.volume >= MIN_BODY_VOLUME_MM3]
        dropped = len(bodies) - len(substantial)
        if dropped:
            print(f"  dropped {dropped} speck bodies (< {MIN_BODY_VOLUME_MM3} mm3)")
        mesh = trimesh.util.concatenate(substantial)

    extents = mesh.extents
    print(f"  mesh: {len(mesh.vertices):,} verts, {len(mesh.faces):,} faces")
    print(f"  extents: {extents[0]:.1f} x {extents[1]:.1f} x {extents[2]:.1f} mm")
    print(f"  volume: {mesh.volume / 1000:.1f} cm3, watertight={mesh.is_watertight}")

    out = OUT_DIR / "BrokeFeet_bone_raw.stl"
    mesh.export(out)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
