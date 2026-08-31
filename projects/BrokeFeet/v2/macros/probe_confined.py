"""Hysteresis CONFINED to each bone's own sealed outline.

Plain hysteresis fails outright (probe_hysteresis.py): soft tissue at 84-96 is
contiguous with bone wherever the cortex is broken, so the flood escapes and by
grow>=95 the whole foot is one 208 cm3 component. Connectivity to bone is
necessary but nowhere near sufficient -- there is no barrier.

The barrier this project already trusts is the SEALED OUTLINE: close the mask on
a scratch copy, fill it, erode back. V0 uses it as a fill (_fill_bone_interiors)
and it works but only sees in-plane enclosure at radius 3, which cannot span a
cortical break wider than 3 px (0.54 mm).

The V1 idea measured here is to use the sealed outline as a CONFINEMENT for the
low-threshold growth instead of as a fill:

    envelope = fill(close(seed, r))          # where this bone plausibly is
    grown    = flood(seed, volume >= low) & envelope

The envelope is per-slice and never written back, so it cannot bridge two
bones' silhouettes; the flood cannot leave the bone it started in; and inside
the envelope the low threshold is free to recruit trabecular bone that 115
drops.

Reports, per candidate (seal radius x low threshold), exactly the quantities
the acceptance list asks for.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy import ndimage

HERE = Path(__file__).resolve().parent
WORK = HERE.parent / "work"
sys.path.insert(0, str(HERE))

import frames  # noqa: E402
import stack_source  # noqa: E402
from probe_sites import SITES  # noqa: E402

HIGH = 115
FIELD_MARGIN_PX = 12


def _clear_margin(mask):
    mask[:, :FIELD_MARGIN_PX, :] = False
    mask[:, -FIELD_MARGIN_PX:, :] = False
    mask[:, :, :FIELD_MARGIN_PX] = False
    mask[:, :, -FIELD_MARGIN_PX:] = False
    return mask


def sealed_envelope(seed, radius, struct2):
    """Per-slice: close the seed, fill it. Never written back to the mask."""
    env = np.zeros_like(seed)
    for k in range(seed.shape[0]):
        plane = seed[k]
        if not plane.any():
            continue
        closed = ndimage.binary_closing(plane, structure=struct2,
                                        iterations=radius)
        env[k] = ndimage.binary_fill_holes(closed)
    return env


def confined_growth(volume, seed, envelope, low, struct3):
    """Flood volume>=low from the seed, but never outside the envelope."""
    weak = (volume >= low) & envelope
    weak |= seed                      # the seed is bone by definition
    labels, n = ndimage.label(weak, structure=struct3)
    if n == 0:
        return seed.copy()
    keep = np.unique(labels[seed])
    keep = keep[keep > 0]
    return np.isin(labels, keep)


def report(volume, geom, fr, grown, seed, tag):
    vox = geom.voxel_mm3
    added = grown & ~seed
    lab, n = ndimage.label(grown)
    sizes = ndimage.sum(grown, lab, range(1, n + 1)) * vox / 1000.0
    kept = int((sizes * 1000 / vox >= 1200).sum())
    big = np.sort(sizes)[::-1][:5]
    print(f"  {tag}: grown {grown.sum()*vox/1000:6.1f} cm3 "
          f"(+{added.sum()*vox/1000:5.1f}), components {n} "
          f"({kept} >=1200 vox), largest "
          + ", ".join(f"{s:.1f}" for s in big))
    for name, centre, radius, verdict in SITES:
        lo, hi = fr.window(centre, radius)
        slo = np.maximum(np.floor(frames.iso_to_source(lo, geom)).astype(int), 0)
        shi = np.minimum(np.ceil(frames.iso_to_source(hi, geom)).astype(int),
                         np.array(volume.shape))
        w_add = added[slo[0]:shi[0], slo[1]:shi[1], slo[2]:shi[2]]
        w_seed = seed[slo[0]:shi[0], slo[1]:shi[1], slo[2]:shi[2]]
        void = (~w_seed).sum()
        flag = "FILL" if "FILL" in verdict else "OPEN"
        print(f"      {name:20s} [{flag}] {w_add.sum()*vox:8.1f} mm3 "
              f"= {100*w_add.sum()/max(1,void):5.1f}% of void")


def main() -> None:
    volume, geom = stack_source.load_volume()
    iso = np.load(WORK / "v0_iso.npy")
    fr = frames.IsoFrame(iso)

    struct2 = ndimage.generate_binary_structure(2, 1)
    struct3 = ndimage.generate_binary_structure(3, 1)

    seed = _clear_margin(volume >= HIGH)
    print(f"seed >= {HIGH}: {seed.sum()*geom.voxel_mm3/1000:.1f} cm3")

    for radius in (3, 5, 8):
        env = sealed_envelope(seed, radius, struct2)
        print(f"\n=== sealed envelope radius {radius} "
              f"({env.sum()*geom.voxel_mm3/1000:.1f} cm3) ===")
        for low in (105, 100, 95, 90, 85):
            grown = confined_growth(volume, seed, env, low, struct3)
            report(volume, geom, fr, grown, seed, f"low {low}")


if __name__ == "__main__":
    main()
