"""Coordinate frames: exported-mesh mm <-> isotropic grid <-> source stack.

Three frames are in play and confusing two of them has cost this project real
time (README: "The iso grid's axis order is not the mesh's" -- a sweep once
reported 0.0 mm3 for every crater because a window was built as
a=to_idx(lo), b=to_idx(hi) on axes that negate).

  SOURCE  (k, row, col)   uint8 captures. k rises toward the leg (+Z),
                          row rises toward the heel (-Y), col rises with +X
                          in the SCAN frame (pre-mirror).
  ISO     (i0, i1, i2)    the 0.5 mm resample. Same axis meanings as SOURCE,
                          scaled by zoom = (step/iso, mm_px/iso, mm_px/iso).
  MESH    (x, y, z) mm    what MeshLab reports. Built by segment_axial.main as
                          verts = [i2, -i1, i0] * ISO, then x -> -x if MIRROR_X.

Every operator-supplied coordinate in this project is MESH.
"""

from __future__ import annotations

import numpy as np

ISO_VOXEL_MM = 0.5
MIRROR_X = True


class IsoFrame:
    """Mapping anchored on an isotropic grid's own occupied extent.

    The occupied extent IS the exported mesh's bounding box (marching cubes
    adds at most half a voxel), so the two corners pin the transform without
    needing the mesh on disk.
    """

    def __init__(self, iso: np.ndarray, iso_voxel_mm: float = ISO_VOXEL_MM,
                 mirror_x: bool = MIRROR_X):
        occupied = np.argwhere(iso)
        self.lo_idx = occupied.min(0)
        self.hi_idx = occupied.max(0)
        self.iso_voxel_mm = iso_voxel_mm
        self.mirror_x = mirror_x

        a = self._idx_to_mesh(self.lo_idx)
        b = self._idx_to_mesh(self.hi_idx)
        self.mesh_lo = np.minimum(a, b)
        self.mesh_hi = np.maximum(a, b)

    def _idx_to_mesh(self, idx):
        x = idx[2] * self.iso_voxel_mm
        y = -idx[1] * self.iso_voxel_mm
        z = idx[0] * self.iso_voxel_mm
        if self.mirror_x:
            x = -x
        return np.array([x, y, z], dtype=float)

    def to_index(self, point) -> np.ndarray:
        """MESH mm -> ISO index (float)."""
        x, y, z = point
        i0 = self.lo_idx[0] + (z - self.mesh_lo[2]) / self.iso_voxel_mm
        i1 = self.hi_idx[1] - (y - self.mesh_lo[1]) / self.iso_voxel_mm
        i2 = self.hi_idx[2] - (x - self.mesh_lo[0]) / self.iso_voxel_mm
        return np.array([i0, i1, i2], dtype=float)

    def to_mesh(self, idx) -> np.ndarray:
        """ISO index -> MESH mm. Inverse of to_index."""
        i0, i1, i2 = idx
        z = self.mesh_lo[2] + (i0 - self.lo_idx[0]) * self.iso_voxel_mm
        y = self.mesh_lo[1] + (self.hi_idx[1] - i1) * self.iso_voxel_mm
        x = self.mesh_lo[0] + (self.hi_idx[2] - i2) * self.iso_voxel_mm
        return np.array([x, y, z], dtype=float)

    def window(self, centre_mesh, radius_mm):
        """Axis-aligned ISO index window around a MESH point.

        Takes min/max per axis AFTER mapping, because two axes negate -- the
        documented way this goes wrong is building lo/hi from the two corners
        directly and getting an empty window.
        """
        r = float(radius_mm)
        corners = []
        for dx in (-r, r):
            for dy in (-r, r):
                for dz in (-r, r):
                    c = np.asarray(centre_mesh, float) + np.array([dx, dy, dz])
                    corners.append(self.to_index(c))
        corners = np.array(corners)
        return np.floor(corners.min(0)).astype(int), np.ceil(corners.max(0)).astype(int) + 1


def iso_to_source(idx, geom, iso_voxel_mm: float = ISO_VOXEL_MM):
    """ISO index -> SOURCE stack index (float)."""
    zoom = np.array([
        geom.slice_step_mm / iso_voxel_mm,
        geom.mm_per_px / iso_voxel_mm,
        geom.mm_per_px / iso_voxel_mm,
    ])
    return np.asarray(idx, float) / zoom


def source_to_iso(idx, geom, iso_voxel_mm: float = ISO_VOXEL_MM):
    """SOURCE stack index -> ISO index (float)."""
    zoom = np.array([
        geom.slice_step_mm / iso_voxel_mm,
        geom.mm_per_px / iso_voxel_mm,
        geom.mm_per_px / iso_voxel_mm,
    ])
    return np.asarray(idx, float) * zoom
