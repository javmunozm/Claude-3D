"""Render the source slices through each named site, with the V0 mask overlaid.

Looking at the render is a standing requirement in this repo -- every defect in
its history passed the numeric gates and was caught only by eye. These panels
show, for one slice through each site: the raw 8-bit capture, the V0 mask, and
the mask boundary drawn on the capture, so the cortical break (or the two intact
cortical plates of a joint) is visible rather than inferred.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent
WORK = HERE.parent / "work"
OUT = HERE.parent / "renders"
sys.path.insert(0, str(HERE))

import frames  # noqa: E402
import stack_source  # noqa: E402
from probe_sites import SITES  # noqa: E402

PAD_MM = 18.0


def panel(volume, mask, extra, k, r0, r1, c0, c1):
    raw = volume[k, r0:r1, c0:c1]
    m = mask[k, r0:r1, c0:c1]
    rgb = np.stack([raw, raw, raw], axis=-1).astype(np.uint8)

    edge = m ^ ndimage.binary_erosion(m)
    over = rgb.copy()
    over[edge] = (255, 40, 40)

    if extra is not None:
        e = extra[k, r0:r1, c0:c1] & ~m
        over[e] = (60, 220, 60)

    mrgb = np.stack([m, m, m], axis=-1).astype(np.uint8) * 255
    gap = np.zeros((raw.shape[0], 6, 3), np.uint8)
    return np.concatenate([rgb, gap, mrgb, gap, over], axis=1)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    volume, geom = stack_source.load_volume()
    mask = np.load(WORK / "v0_mask.npy")
    iso = np.load(WORK / "v0_iso.npy")
    fr = frames.IsoFrame(iso)

    extra = None
    extra_path = WORK / "v1_mask.npy"
    if extra_path.exists():
        extra = np.load(extra_path)

    for name, centre, radius, verdict in SITES:
        if radius > 8:
            continue
        idx = frames.iso_to_source(fr.to_index(centre), geom)
        k = int(round(idx[0]))
        pad_r = int(PAD_MM / geom.mm_per_px)
        r0 = max(int(idx[1]) - pad_r, 0)
        r1 = min(int(idx[1]) + pad_r, volume.shape[1])
        c0 = max(int(idx[2]) - pad_r, 0)
        c1 = min(int(idx[2]) + pad_r, volume.shape[2])

        img = panel(volume, mask, extra, k, r0, r1, c0, c1)
        tag = name.replace("/", "_").replace(" ", "_")
        path = OUT / f"site_{tag}_k{k:03d}.png"
        Image.fromarray(img).resize(
            (img.shape[1] * 2, img.shape[0] * 2), Image.NEAREST).save(path)
        print(f"{name:22s} slice {k:3d} -> {path.name}  [{verdict}]")


if __name__ == "__main__":
    main()
