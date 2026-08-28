"""Run the V0 pipeline's segmentation stages and cache the intermediates.

Read-only with respect to BrokeFeet/: it imports segment_axial and calls its
functions, writing everything into BrokeFeetV1/work/. The point is to have the
V0 mask and V0 isotropic grid on disk so every V1 measurement is a like-for-like
comparison against the object the old pipeline actually produced, not against a
re-voxelisation of its exported mesh (the proxy trap this project has fallen
into twice).
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
WORK = HERE.parent / "work"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / "BrokeFeet" / "macros"))

import stack_source  # noqa: E402
import segment_axial as v0  # noqa: E402


def main() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    volume, geom = stack_source.load_volume()
    print(f"volume {volume.shape} voxel {geom.mm_per_px:.4f}^2 x "
          f"{geom.slice_step_mm} mm")

    t = time.time()
    mask = v0.segment(volume)
    print(f"  segment(): {mask.sum():,} voxels in {time.time() - t:.0f}s")
    np.save(WORK / "v0_mask.npy", mask)

    t = time.time()
    iso = v0.to_isotropic(mask)
    print(f"  to_isotropic(): {iso.sum():,} voxels in {time.time() - t:.0f}s")
    np.save(WORK / "v0_iso.npy", iso)


if __name__ == "__main__":
    main()
