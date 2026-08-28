"""V1 segmentation: a locally adaptive threshold, so no hollow bone is ever created.

WHY THIS EXISTS
---------------
V0 (BrokeFeet/macros/segment_axial.py) thresholds once, globally:

    mask = volume >= 115

115 is a compromise: high enough to keep the skin rim out, and therefore above
this adolescent patient's trabecular bone, which images at 82-103. Where the
thin cortex is ALSO broken, binary_fill_holes has no closed loop to work on and
the bone segments as a hollow rind -- the defect the operator photographs. V0
then spends four separate passes (_fill_bone_interiors, _fill_axial_pits,
_close_within_envelope, _close_tunnels_gated) trying to put the interior back.

This file is the attempt to never create the hole.

WHAT WAS MEASURED, AND WHAT IT KILLED
-------------------------------------
Every candidate below was run on the real stack. Numbers are per-site void
recruitment, where a site marked FILL must be filled and one marked OPEN must
not be (probe_sites.py):

1. INTENSITY IS INVERTED. Sampled in the source captures:

       hollow calcaneus  (FILL)  void mean  95.1
       navicular/talus   (FILL)  void mean  93.7
       ankle mortise     (OPEN)  void mean  99.7   <- BRIGHTER
       tarsal rind       (OPEN)  void mean  98.0   <- BRIGHTER

   At every candidate threshold the two joints recruit MORE of their void than
   the two hollow bones (at 95: mortise 72.9 % vs calcaneus 49.6 %). No global
   or per-voxel intensity rule can work, in either direction.

2. PLAIN HYSTERESIS FAILS OUTRIGHT (probe_hysteresis.py). Seeding at 115 and
   growing down leaks straight into soft tissue, because tissue at 84-96 is
   contiguous with bone wherever the cortex is broken -- which is precisely
   where the defect is:

       grow>=105   95.2 cm3   29 components
       grow>=100  118.8 cm3   11 components
       grow>= 95  208.1 cm3    2 components   <- the whole foot, one body
       grow>= 85  505.1 cm3    2 components

   The joints recruit more than the voids at every level (85: mortise 93.4 %
   vs calcaneus 91.9 %). Connectivity to bone is necessary but nowhere near
   sufficient: there is no barrier.

3. HYSTERESIS CONFINED TO A SEALED OUTLINE FAILS TOO (probe_confined.py).
   Clipping the flood to fill(close(seed, r)) -- the barrier V0 trusts -- was
   swept over r in {3,5,8} x low in {105..85}, 15 combinations. In ALL FIFTEEN
   the mortise recruits a higher fraction of its void than the calcaneus, and
   the bone count collapses (r=5 low=90: 4 bones; r=8 low=85: ONE). The
   envelope is not a per-bone barrier at the ankle: renders/site_ankle_mortise
   shows the tibia has no continuous lateral cortex there, so the sealed
   outline spans tibia + joint + fibula and the flood crosses.

4. THE SINGLE-BONE GATE HAS NO USABLE SETTING (probe_gated_ring*.py). Gating
   each proposed interior on "touches at most one bone component" is either
   total or vacuous, with nothing in between:
     - counting raw components, the calcaneus window holds 102 seed labels (one
       of 81,391 voxels, the rest <= 206 -- trabecular speckle), so every
       interior touches many and 0.0 % is kept;
     - counting only components above a bone-sized floor, the tarsus is already
       ONE component, so 0-5 blobs of 34-47 cm3 are rejected and the gate does
       nothing.

5. PER-SLICE ADAPTIVE LEVEL -- THE BEST VARIANT, AND STILL NOT GOOD ENOUGH.
   The level at which a cortical ring closes is local not just to the bone but
   to the SLICE. Measured through the calcaneus (enclosed interior px in a
   local window):

     slice  T=115  T=112  T=108  T=104  T=100
        81   6970   6538   5684   4725   3332   <- intact at 115
        83     24     28   7942   6560   4801
        87      0      0     62   8521   6728   <- needs 104
        93     12      8   9638   8589   7076
        99      0  10557   9728   8433   6940

   This is exactly the case for replacing the global constant, and V0's own
   _fill_bone_interiors demonstrably cannot cover it: on slices 85-95 its
   scratch-copy closing at radius 3 recovers 1746 -> 1771 px (+25), because the
   cortical break is wider than the seal, while a plain fill at level 104
   recovers ~8,500 px on the same slices.

   Taking, per ring, the HIGHEST level at which it encloses anything
   (probe_perslice_level.py) is the best-performing method measured here:

     descend to   calcaneus(FILL)   mortise(OPEN)
        108           47.7 %           69.6 %
        104           71.4 %           78.8 %
        100           74.1 %           81.5 %

   It fills 71 % of the calcaneal void -- and the mortise more, at every
   setting. Rendered (renders/level_fill_calc104_mortise108.png) the reason is
   plain and is a picture, not a number: at the calcaneus the recovered
   material lies wholly INSIDE the cortical rim, which is correct; at the
   mortise it spills outside the tibia into soft tissue and around the fibula,
   because the outline that "closed" enclosed the joint rather than a medulla.

THE VERDICT: THE ADAPTIVE THRESHOLD DOES NOT BEAT THE GLOBAL ONE
---------------------------------------------------------------
Five independent discriminators were measured and all five rank the
must-fill sites BELOW the must-not-fill sites:

    discriminator                     calcaneus(FILL)   mortise(OPEN)
    raw void intensity                    95.1              99.7
    threshold recruitment @95             49.6 %            72.9 %
    hysteresis @low=85                    91.9 %            93.4 %
    confined hysteresis (best of 15)      any               always higher
    per-slice adaptive level @104         71.4 %            78.8 %
    ring brightness (mean)               109.8             112.1
    blob compactness (% of bbox)          30.7 %            49.7 %

The last two are worth stating because they invert the heuristics this project
previously relied on: the README's "a cavity inside one bone is a compact blob,
a joint space is a thin rind" is BACKWARDS at these two sites, and so is
"cortex is brighter".

Run end to end at the one operating point where the ordering was briefly
correct (RING_LEVELS = (112,)), V1 is worse than V0 on every acceptance
number -- see compare_v0_v1.py output in the report. The honest conclusion is
that V0's four repair passes, for all their inelegance, are doing work that a
smarter threshold does not replace, and the hollow interiors cannot be
prevented at segmentation time from THIS data.

6. THE HYBRID IS NOT WORTH SHIPPING EITHER. Adding ring_interiors() at level
   112 on top of V0's finished mask is topologically safe -- +1.01 cm3
   (+0.9 %), components 12 -> 12, no two large bodies merged (largest
   56.3 -> 57.3 cm3, its own interior) -- but it lands in the wrong place:

     calcaneus (FILL)  +  8.1 mm3 =  0.32 % of remaining void
     navicular (FILL)  +184.3 mm3 =  1.95 %
     mortise   (OPEN)  +155.6 mm3 = 12.15 %   <- worst offender again
     rind      (OPEN)  + 37.6 mm3 =  3.76 %

   Same inversion, one order of magnitude smaller. Safe and useless.

WHAT THIS FILE THEREFORE IS
---------------------------
The measured negative, kept runnable so the sweep is not repeated. The intended
V1 goal -- prevent the hollow interior at segmentation time by making the
threshold local -- was not achieved and, on this evidence, is not achievable
from these captures. Six discriminators were tested; all six rank the joint
that must stay open above the void that must be filled.

`ring_interiors()` is retained because it is the only pass here that is
provably non-fusing (every large body after it descends from exactly one large
body before it) and because it recovers material V0's radius-3 seal cannot
reach where the cortical break is wider than the seal. It is NOT a replacement
for V0's pipeline and must not be shipped as one.

WHAT WOULD ACTUALLY FIX IT
--------------------------
The discriminating information is absent from the pixels, not merely hard to
extract: the calcaneal medulla and the tibiotalar joint space overlap in
brightness, in local contrast, in ring brightness and in blob compactness, and
in every case the joint scores MORE bone-like. Two things would resolve it and
nothing in this file substitutes for either:

  * the DICOM, where Hounsfield units separate marrow from synovial fluid and
    cartilage outright (BrokeFeet/macros/dicom_pipeline.py already exists);
  * a coronal or sagittal series, in which the mortise is a line rather than a
    ring, so the outline that closes around it in the axial plane does not.

Failing both, V0's approach -- refuse to classify, and instead make the bad
outcome structurally impossible (the component gate in _close_tunnels_gated) --
remains the correct engineering response, and V1 has no improvement on it.

STACK SOURCE
------------
Voxels arrive through stack_source.load_volume() and nothing here opens a file,
so swapping in feed_slices.py is a one-function change.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy import ndimage

HERE = Path(__file__).resolve().parent
WORK = HERE.parent / "work"
OUT_DIR = HERE.parent
sys.path.insert(0, str(HERE))

import stack_source  # noqa: E402

# --- parameters -----------------------------------------------------------

# The SEED level. Same as V0's BONE_THRESHOLD, and for the same reason: it is
# the highest level that still keeps the skin rim out. Nothing below it is
# admitted except through a closed cortical ring.
SEED_THRESHOLD = 115

# Levels at which a cortical outline is re-tested for closure. See the module
# docstring: this is a cliff, not a knob. (112,) is the only member set that
# ranks the must-fill sites above the must-not-fill sites.
RING_LEVELS = (112,)

# A ring enclosing fewer pixels than this is speckle; more than this and it is
# not one bone's medulla. 40,000 px at 0.179 mm is 1,280 mm2, larger than any
# single tarsal cross-section in this foot and smaller than the interosseous
# spaces (V0 measured the largest at 492 mm2 in-plane but they are open, so
# they never present as a hole).
MIN_RING_AREA_PX = 60
MAX_INTERIOR_PX = 40000

# The contralateral limb and the viewer frame both appear in the captures.
FIELD_MARGIN_PX = 12

# Size filters, carried over from V0 unchanged. Set BELOW the smallest real
# bone: a 5th distal phalanx measures 64-113 mm3 here, and limits of 3000
# voxels / 150 mm3 silently deleted three distal phalanges in an earlier build.
MIN_COMPONENT_VOXELS = 1200

# Resampling, carried over from V0 so the two are comparable.
ISO_VOXEL_MM = 0.5
SOURCE_BLUR_SIGMA = (0.8, 2.0, 2.0)
ISO_LEVEL = 0.40


def _clear_margin(mask: np.ndarray) -> np.ndarray:
    mask[:, :FIELD_MARGIN_PX, :] = False
    mask[:, -FIELD_MARGIN_PX:, :] = False
    mask[:, :, :FIELD_MARGIN_PX] = False
    mask[:, :, -FIELD_MARGIN_PX:] = False
    return mask


def ring_interiors(plane: np.ndarray, levels=RING_LEVELS) -> np.ndarray:
    """Interiors enclosed by this slice's cortical outline at a lower level.

    Not a closing. The outline is re-derived from the SOURCE intensities at a
    lower level and filled; only the enclosed holes are taken. Because the
    material added is enclosed by a loop that exists in the image, it cannot
    span the space between two bones unless the image itself closes a loop
    around both -- which the level cliff above is what bounds.
    """
    acc = np.zeros(plane.shape, dtype=bool)
    for level in levels:
        m = plane >= level
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
    return acc


def segment(volume: np.ndarray) -> np.ndarray:
    """Adaptive-threshold segmentation. One pass, no post-hoc repair."""
    mask = _clear_margin(volume >= SEED_THRESHOLD)
    print(f"  seed >= {SEED_THRESHOLD}: {mask.sum():,} voxels")

    gained = np.zeros(volume.shape, dtype=bool)
    for k in range(volume.shape[0]):
        gained[k] = ring_interiors(volume[k]) & ~mask[k]
    print(f"  ring interiors at {RING_LEVELS}: +{gained.sum():,} voxels "
          f"(+{100 * gained.sum() / max(1, mask.sum()):.0f}%)")
    mask |= gained

    # A single opening removes the speckle a lower level admits, without
    # eroding the bones. Carried over from V0.
    struct2 = ndimage.generate_binary_structure(2, 1)
    for k in range(mask.shape[0]):
        mask[k] = ndimage.binary_fill_holes(mask[k])
        mask[k] = ndimage.binary_opening(mask[k], structure=struct2)

    labels, count = ndimage.label(mask)
    if count == 0:
        raise SystemExit("threshold produced no bone")
    sizes = ndimage.sum(mask, labels, range(1, count + 1))
    keep = [i + 1 for i, s in enumerate(sizes) if s >= MIN_COMPONENT_VOXELS]
    cleaned = np.isin(labels, keep)
    print(f"  components: {count} found, {len(keep)} kept")

    # Enclosed 3D cavities. Safe by the same argument V0 uses: a void that never
    # reaches the volume boundary is inside one bone, while a joint space always
    # opens out to the surrounding tissue.
    background, bg = ndimage.label(~cleaned)
    if bg:
        boundary = set(background[0].flat) | set(background[-1].flat)
        boundary |= set(background[:, 0].flat) | set(background[:, -1].flat)
        boundary |= set(background[:, :, 0].flat) | set(background[:, :, -1].flat)
        boundary.discard(0)
        interior = ~np.isin(background, list(boundary)) & ~cleaned
        if interior.any():
            print(f"  filled {int(interior.sum()):,} enclosed cavity voxels")
            cleaned |= interior

    return cleaned


def to_isotropic(mask: np.ndarray, geom) -> np.ndarray:
    """Resample to 0.5 mm. Identical to V0's, minus every repair pass.

    If the adaptive threshold has done its job there is nothing left to repair,
    so _close_within_envelope and _close_tunnels_gated are deliberately absent
    -- their presence or absence is the measurement.
    """
    occupancy = ndimage.gaussian_filter(mask.astype(np.float32),
                                        sigma=SOURCE_BLUR_SIGMA)
    zoom = (
        geom.slice_step_mm / ISO_VOXEL_MM,
        geom.mm_per_px / ISO_VOXEL_MM,
        geom.mm_per_px / ISO_VOXEL_MM,
    )
    iso = ndimage.zoom(occupancy, zoom, order=1) >= ISO_LEVEL

    background, count = ndimage.label(~iso)
    if count:
        boundary = set(background[0].flat) | set(background[-1].flat)
        boundary |= set(background[:, 0].flat) | set(background[:, -1].flat)
        boundary |= set(background[:, :, 0].flat) | set(background[:, :, -1].flat)
        boundary.discard(0)
        enclosed = ~np.isin(background, list(boundary)) & ~iso
        if enclosed.any():
            print(f"  filled {int(enclosed.sum()):,} resample cavities "
                  f"({enclosed.sum() * ISO_VOXEL_MM ** 3:.1f} mm3)")
            iso |= enclosed
    return iso


def main() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    print("loading stack...")
    volume, geom = stack_source.load_volume()
    print(f"  {volume.shape} voxel {geom.mm_per_px:.3f}^2 x "
          f"{geom.slice_step_mm} mm")

    print("segmenting (adaptive)...")
    mask = segment(volume)
    print(f"  bone voxels: {mask.sum():,} "
          f"({mask.sum() * geom.voxel_mm3 / 1000:.1f} cm3)")
    np.save(WORK / "v1_mask.npy", mask)

    print("resampling to isotropic...")
    iso = to_isotropic(mask, geom)
    print(f"  grid {iso.shape}, {iso.sum() * ISO_VOXEL_MM ** 3 / 1000:.1f} cm3")
    np.save(WORK / "v1_iso.npy", iso)


if __name__ == "__main__":
    main()
