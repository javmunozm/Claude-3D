"""The single swappable entry point for slice data.

Every V1 stage reads its voxels through `load_volume()`. Nothing else in this
project may open a PNG or glob a directory, so when `feed_slices.py` lands its
manifest becomes a one-function change here rather than an edit to the
segmentation.

Two sources are supported:

  FEED     -- BrokeFeetV1/macros/feed_slices.py + its manifest (preferred once
              it exists; it carries per-slice LOC and geometry explicitly)
  LEGACY   -- BrokeFeet/macros/segment_axial.load_stack(), the V0 assembly of
              references/brokenfeet_deid_axial{,_proximal}

The legacy path is the development fallback and is byte-identical to what the
V0 reconstruction consumed, so any V1-vs-V0 measurement compares the same
voxels.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[4]
V0_MACROS = REPO / "projects" / "BrokeFeet" / "v0" / "macros"
CACHE = Path(__file__).resolve().parent.parent / "work" / "stack.npy"


@dataclass(frozen=True)
class Geometry:
    """Voxel geometry of the loaded stack, in millimetres."""

    mm_per_px: float          # in-plane, both row and column
    slice_step_mm: float      # centre-to-centre along the stack axis

    @property
    def voxel_mm3(self) -> float:
        return self.mm_per_px * self.mm_per_px * self.slice_step_mm


def _load_feed():
    """Try the parallel feeder stage. Returns (volume, Geometry) or None."""
    feed = Path(__file__).resolve().parent / "feed_slices.py"
    if not feed.exists():
        return None
    sys.path.insert(0, str(feed.parent))
    try:
        import feed_slices  # type: ignore
    except Exception as exc:  # pragma: no cover - the feeder is still landing
        print(f"  feed_slices.py present but not usable ({exc}); using legacy")
        return None
    for name in ("load_volume", "load_stack", "load"):
        fn = getattr(feed_slices, name, None)
        if callable(fn):
            out = fn()
            if isinstance(out, tuple):
                return out
            geom = Geometry(
                mm_per_px=float(getattr(feed_slices, "MM_PER_PX")),
                slice_step_mm=float(getattr(feed_slices, "SLICE_STEP_MM")),
            )
            return np.asarray(out), geom
    print("  feed_slices.py exposes no load_volume(); using legacy")
    return None


def _load_legacy():
    sys.path.insert(0, str(V0_MACROS))
    import segment_axial as v0  # noqa: E402

    volume = v0.load_stack()
    geom = Geometry(mm_per_px=v0.MM_PER_PX, slice_step_mm=v0.SLICE_STEP_MM)
    return volume, geom


def load_volume(use_cache: bool = True, source: str = "auto"):
    """Return (volume uint8 [slice, row, col], Geometry).

    Slice index 0 is the most distal (toe-end) slice and rises toward the leg,
    matching +Z of the exported mesh.

    `source` pins where the voxels come from:
      "auto"    -- feed_slices.py if it imports and runs, else legacy
      "feed"    -- feed_slices.py, and fail loudly if it is not usable
      "legacy"  -- BrokeFeet's load_stack()/cache ONLY

    Pinning matters during a comparison. feed_slices.py is being written in
    parallel; if it lands (or breaks) between two measurements, the inputs move
    underneath them and the numbers stop being comparable. Every V1-vs-V0
    measurement in this project used source="legacy" for that reason.
    """
    if source not in ("auto", "feed", "legacy"):
        raise ValueError(f"unknown stack source {source!r}")

    if source in ("auto", "feed"):
        fed = _load_feed()
        if fed is not None:
            return fed
        if source == "feed":
            raise SystemExit("feed_slices.py requested but not usable")

    if use_cache and CACHE.exists():
        volume = np.load(CACHE)
        sys.path.insert(0, str(V0_MACROS))
        import segment_axial as v0
        return volume, Geometry(v0.MM_PER_PX, v0.SLICE_STEP_MM)

    volume, geom = _load_legacy()
    if use_cache:
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        # Never silently replace a cache of a DIFFERENT shape. The de-identify
        # output under references/ is shared and is being rewritten by the
        # feeder stage in parallel; a rebuild here once turned a 222x1108x1209
        # stack into 221x1160x1240 while saved masks from the earlier stack were
        # still on disk, which would have made a V1-vs-V0 comparison meaningless
        # without any error being raised.
        if CACHE.exists():
            old = np.load(CACHE, mmap_mode="r")
            if old.shape != volume.shape:
                raise SystemExit(
                    f"stack cache shape changed {old.shape} -> {volume.shape}. "
                    "The de-identified panes under references/ have been "
                    "regenerated. Delete BrokeFeetV1/work/*.npy and re-run every "
                    "stage, or the saved masks describe a different volume."
                )
        np.save(CACHE, volume)
    return volume, geom
