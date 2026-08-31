"""Ring-close fill with a SINGLE-BONE gate on every proposed interior.

probe_ringclose.py showed the ranking finally inverting the right way at
level 112 (calcaneus 36.2 % of void recovered vs mortise 27.1 %) and collapsing
again by 108 (mortise 64.4 % vs calcaneus 45.5 %). The reason a low level
recruits the mortise is that the ring which "encloses" it at that level is
formed by TWO bones plus the soft tissue between them -- the tibia's lateral
cortex is absent on these slices (see renders/site_ankle_mortise_k119.png),
so the outline closes around the joint rather than around a bone.

That is a checkable property, and this project's own history says the way to
win is to make the bad outcome impossible rather than to classify voxels:

    a proposed interior is accepted only if the bone it is enclosed by is ONE
    3D connected seed component.

A trabecular interior is ringed by its own cortex -- one component. A joint
space is ringed by two bones -- two components -- and is rejected outright, at
any level, however bright it is. The gate is structural, so it does not depend
on the intensity ordering that the measurements show runs backwards.
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
MIN_RING_AREA_PX = 60
MAX_INTERIOR_PX = 40000


def clear_margin(mask):
    mask[..., :FIELD_MARGIN_PX, :] = False
    mask[..., -FIELD_MARGIN_PX:, :] = False
    mask[..., :, :FIELD_MARGIN_PX] = False
    mask[..., :, -FIELD_MARGIN_PX:] = False
    return mask


def propose(volume, seed, levels):
    """Per slice, per level: holes enclosed by the re-thresholded outline."""
    proposal = np.zeros(volume.shape, dtype=bool)
    for k in range(volume.shape[0]):
        src = volume[k]
        acc = np.zeros(src.shape, dtype=bool)
        for level in levels:
            m = src >= level
            m[:FIELD_MARGIN_PX] = False
            m[-FIELD_MARGIN_PX:] = False
            m[:, :FIELD_MARGIN_PX] = False
            m[:, -FIELD_MARGIN_PX:] = False
            holes = ndimage.binary_fill_holes(m) & ~m
            if not holes.any():
                continue
            lab, n = ndimage.label(holes)
            if n == 0:
                continue
            sizes = ndimage.sum(holes, lab, range(1, n + 1))
            ok = [i + 1 for i, s in enumerate(sizes)
                  if MIN_RING_AREA_PX <= s <= MAX_INTERIOR_PX]
            if ok:
                acc |= np.isin(lab, ok)
        proposal[k] = acc & ~seed[k]
    return proposal


def gate_single_bone(proposal, seed, struct3):
    """Discard any proposed blob touching more than one seed component.

    Both the blobs and the bones are labelled in 3D. A blob is kept only when
    the set of seed labels in its 26-neighbourhood has exactly one member; a
    blob touching none is floating debris and is also dropped.
    """
    bones, nb = ndimage.label(seed, structure=struct3)
    blobs, nblob = ndimage.label(proposal, structure=struct3)
    if nblob == 0:
        return proposal, 0, 0

    kept = np.zeros(nblob + 1, dtype=bool)
    dilated_bones = ndimage.grey_dilation(bones, footprint=struct3)
    # neighbouring bone labels per blob voxel
    touch = np.where(proposal, dilated_bones, 0)

    n_multi = n_float = 0
    objs = ndimage.find_objects(blobs)
    for i, sl in enumerate(objs, start=1):
        if sl is None:
            continue
        sub_blob = blobs[sl] == i
        labels_here = np.unique(touch[sl][sub_blob])
        labels_here = labels_here[labels_here > 0]
        if labels_here.size == 1:
            kept[i] = True
        elif labels_here.size == 0:
            n_float += 1
        else:
            n_multi += 1
    return kept[blobs], n_multi, n_float


def main() -> None:
    volume, geom = stack_source.load_volume()
    iso = np.load(WORK / "v0_iso.npy")
    fr = frames.IsoFrame(iso)
    vox = geom.voxel_mm3
    struct3 = ndimage.generate_binary_structure(3, 3)

    seed = clear_margin(volume >= HIGH)
    print(f"seed {seed.sum()*vox/1000:.1f} cm3")

    for levels in ((112,), (112, 108), (112, 108, 104), (112, 108, 104, 100),
                   (112, 108, 104, 100, 96, 92)):
        prop = propose(volume, seed, levels)
        kept, n_multi, n_float = gate_single_bone(prop, seed, struct3)
        print(f"\n=== levels {levels} ===")
        print(f"  proposed {prop.sum()*vox/1000:6.2f} cm3 -> kept "
              f"{kept.sum()*vox/1000:6.2f} cm3 "
              f"(rejected {n_multi} multi-bone blobs, {n_float} floating)")
        for name, centre, radius, verdict in SITES:
            lo, hi = fr.window(centre, radius)
            slo = np.maximum(np.floor(frames.iso_to_source(lo, geom)).astype(int), 0)
            shi = np.minimum(np.ceil(frames.iso_to_source(hi, geom)).astype(int),
                             np.array(volume.shape))
            w = kept[slo[0]:shi[0], slo[1]:shi[1], slo[2]:shi[2]]
            p = prop[slo[0]:shi[0], slo[1]:shi[1], slo[2]:shi[2]]
            ws = seed[slo[0]:shi[0], slo[1]:shi[1], slo[2]:shi[2]]
            void = (~ws).sum()
            flag = "FILL" if "FILL" in verdict else "OPEN"
            print(f"    {name:20s} [{flag}] proposed {p.sum()*vox:7.1f} "
                  f"kept {w.sum()*vox:7.1f} mm3 = {100*w.sum()/max(1,void):5.1f}% of void")


if __name__ == "__main__":
    main()
