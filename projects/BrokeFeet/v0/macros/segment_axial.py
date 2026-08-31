"""Reconstruct the foot skeleton from the axial (VOL OSEO) CT stack.

This supersedes segment_bone.py as the primary reconstruction. The axial series
is better on every axis that matters:

                     sagittal        axial
  slice thickness    2.21 mm         0.63 mm
  slice spacing      2.0  mm         0.625 mm
  in-plane           0.209 mm/px     0.179 mm/px
  slices captured    46              182
  reconstruction     viewing series  VOL OSEO (bone kernel)
  anisotropy         9.5 : 1         3.5 : 1

At 0.625 mm spacing the mediolateral axis is genuinely sampled rather than
interpolated across 2 mm gaps, so the forefoot adduction and the rotational
component of the deformity are measured here rather than guessed.

segment_bone.py is kept: re-slicing THIS volume into the sagittal plane and
comparing it against that independently-measured series is what validates the
reconstruction (see crossvalidate.py). Two series of one foot, acquired in
different planes, check each other.

Axis convention of the output mesh follows docs/system.md (+Z up):
  +X medial-lateral, +Y posterior-anterior (heel to toes), +Z plantar to dorsal
"""

from __future__ import annotations

import glob
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image
from scipy import ndimage

from deidentify_axial import (
    MM_PER_PX,
    PX_PER_MM,
    SLICE_STEP_MM,
)

REPO = Path(__file__).resolve().parents[4]
DEID_DIR = REPO / "references" / "brokenfeet_deid_axial"
PROXIMAL_DIR = REPO / "references" / "brokenfeet_deid_axial_proximal"
OUT_DIR = Path(__file__).resolve().parent.parent

# --- segmentation parameters ----------------------------------------------

# Chosen by overlaying candidates across FOUR slices spanning the stack
# (forefoot, midfoot, hindfoot, heel) and looking at all of them.
#
# Two earlier values were wrong in opposite directions:
#
#   100 -- a thin bright rim traces the SKIN boundary on most slices. Filling
#          and stacking it wrapped the foot in a shell that meshed as a
#          soft-tissue blob with toes: 128 cm3 of plausible-looking volume that
#          was largely skin.
#   130 -- above the trabecular bone of this patient. The cuneiforms and
#          metatarsal bases are adolescent bone: thin cortex around a LOW
#          density interior. At 130 only the cortex passed, and because that
#          cortex is porous, fill_holes could not close it -- those bones came
#          out eaten away from the inside, a spongy texture the surgeon
#          correctly described as "huesos en descomposicion".
#
# 115 keeps the trabecular interior while staying clear of the skin rim. Paired
# with CLOSING_RADIUS = 3 (up from 2) it closes the porous cortex so each bone
# fills as a solid. Lower values (110, 105) start fusing adjacent cuneiforms
# into one mass, which destroys the joint detail this series exists to resolve.
BONE_THRESHOLD = 115

# Closing iterations. 3 rather than 2: the porous adolescent cortex needs a
# wider structuring element before fill_holes can treat each bone as enclosed.
CLOSING_RADIUS = 3

# A single opening pass after the fill removes the speckle that a lower
# threshold admits, without eroding the bones themselves.
OPENING_RADIUS = 1

# Radius used to seal a broken cortical rim before filling it. Applied to a
# scratch copy only (see _fill_bone_interiors), then eroded back, so it never
# bridges the gap between two bones. Large enough to close the cortical breaks
# in the calcaneus and cuboid; smaller than the narrowest joint space.
# Swept 3-8. There is a sharp cliff: 3 keeps 9 separate bodies, 4 keeps 5, and
# 5 collapses the entire foot into one 98 cm3 mass because the seal starts
# bridging joint spaces. 3 fills the interiors (88.3 -> 90.9 cm3) while leaving
# the bones anatomically separate.
CORTEX_SEAL_RADIUS = 3

# Intensity floor for material admitted by the interior fill. Trabecular bone
# in this patient's calcaneus runs 82-103; surrounding soft tissue sits below
# it. This bounds the fill so a cortical break cannot leak it into the tissue.
INTERIOR_FLOOR = 78

# Span, in slices, of the axial trabecular-pit fill (see _fill_axial_pits).
#
# 1 fills only a void with solid bone in the IMMEDIATELY adjacent slice above
# and below -- a 0.625 mm hole through the middle of a bone, which is threshold
# noise rather than anatomy. Measured effect per band, at span 1 (voxels added
# as a % of that band's bone):
#
#   Z  2.2- 15.9  +1.73%    Z 43.2- 56.9  +1.76%
#   Z 15.9- 29.6  +0.60%    Z 56.9- 70.5  +6.58%
#   Z 29.6- 43.2  +0.56%    Z 70.5- 84.2  +2.53%
#                           Z 84.2-138.8  +0.31%  (leg, barely touched)
#
# Raising it fills more (span 2 doubles the yield, span 4 quadruples it) and
# the same-component gate still holds the body count at 12 -- but a 2-4 slice
# void is 1.25-2.5 mm, which in the leg is within the range of a genuine
# nutrient canal or medullary space. 1 is the value that cannot be wrong.
AXIAL_PIT_SPAN = 1

# Size filters, set from the smallest bone that must survive.
#
# A distal phalanx of the 5th toe is genuinely tiny: measured here at 64-113
# mm3, i.e. 3200-5600 voxels. Earlier limits of 3000 voxels / 150 mm3 sat right
# on top of that range and silently deleted the distal phalanges of the 2nd,
# 4th and 5th toes -- the model came out with 17 bones and short toes, which
# looks plausible unless you count them against the anatomy.
#
# Set well below the smallest real bone instead. The debris this admits is
# removed by the slice-span and speck filters rather than by size.
MIN_COMPONENT_VOXELS = 1200
MIN_BODY_VOLUME_MM3 = 40.0

# Near-isotropic already (0.179 vs 0.625 mm), so the resample target can be
# fine without the mesh exploding. 0.5 mm keeps articular detail that 0.6 mm
# was starting to round off.
ISO_VOXEL_MM = 0.5

# Anti-aliasing blur applied at SOURCE resolution, before downsampling. Sized
# to the resampling ratio: ~1.4 px in-plane (0.5/0.179 = 2.8, half of that) and
# lightly across slices, which are being upsampled rather than decimated.
# Raised from (0.5, 1.4, 1.4): with the median filter removed this blur is the
# only thing suppressing surface trabeculae, so it does that job alone. Still
# gentle enough across slices that the 0.625 mm sampling is not smeared.
SOURCE_BLUR_SIGMA = (0.8, 2.0, 2.0)

# Bodies whose surface area per unit volume exceeds this are shards, not
# bones. A compact bone runs 0.4-0.9; the fragments this removes measured
# 1.3-5.3. Filtering on shape catches thin flakes that a volume threshold
# alone lets through.
MAX_AREA_VOLUME_RATIO = 1.2

# Connections between separated bones.
#
# 4 mm rather than 2: at 2 mm the pins are flimsy, and the model tolerates the
# larger diameter almost for free. The measured gaps between bodies are only
# 0.5-1.0 mm -- the bones nearly touch -- so each pin is a short stub, not a
# rod. Total material added at 4 mm is 131.7 mm3, 0.14% of bone volume (2 mm
# adds 0.03%, 3 mm 0.07%). The thinnest bones being pinned are phalanges whose
# rays measure 11-13.5 mm across, so a 4 mm pin is well inside their girth and
# does not distort the silhouette.
BRIDGE_DIAMETER_MM = 4.0

# Phalanges get a thinner pin than the tarsals.
#
# The gaps here are only 0.7-1.0 mm, so a 4 mm pin is four to five times wider
# than the joint it crosses and its wall is plainly visible in the interdigital
# space -- it reads as a bar welding one toe tip to the next, which is what the
# top view of the forefoot shows. The bone is the same width as the pin, so
# there is nothing to hide it.
#
# It cannot simply be deleted: the 5th toe's phalanx is 1.00 mm from the foot
# and 4.6 mm or more from every other body, so that pin is its ONLY connection.
# Removing it drops the toe as a loose body and fails the one-piece gate.
#
# Thinning it is the fix that keeps the toe attached. 2 mm halves the visible
# wall while still printing as a solid link at any sane layer height -- the
# value this project used originally, before it was raised to 4 mm for the
# tarsals, where girth is free.
BRIDGE_DIAMETER_PHALANX_MM = 2.0

# Bodies below this volume are treated as phalanges for pin sizing. The four
# phalangeal bodies here measure 868-1051 mm3; the next body up is the fibula
# at 9857 mm3, so the threshold sits in a wide gap and is not delicate.
PHALANX_MAX_VOLUME_MM3 = 3000.0

# Depth each pin end sinks into its bone. A boolean union needs genuine
# interpenetration; ending flush against a curved surface leaves zero-area
# slivers that make the mesh non-manifold.
BRIDGE_BITE_MM = 2.0

# Cap on the bite, as a fraction of the smaller bone's own size.
#
# The bite is applied to BOTH ends, so a 0.71 mm gap became a 4.71 mm cylinder.
# On the tarsals that is invisible, but the distal phalanges are only ~8 mm
# long: a 5 mm pin overshoots the bone it is anchoring and emerges from the far
# side, reading as a rod bridging one toe tip to the next. That is what it looks
# like in a top view of the forefoot, and it is what this cap removes.
#
# Scaling by the smaller body's minimum extent keeps the pin inside its bone:
# big bones still get the full 2 mm, a small phalanx gets proportionally less.
# The bite still has to exceed the surface roughness for the boolean to fuse,
# hence the floor.
BRIDGE_BITE_FRACTION = 0.22
BRIDGE_BITE_MIN_MM = 0.6

# Island detection. The scan pitch is coarser than a real slicer layer, which
# is deliberate -- it finds the islands that matter without generating a pillar
# for every sub-millimetre wisp.
ISLAND_SCAN_PITCH = 0.5

# Islands below this footprint are ignored: a slicer bridges them from the
# surrounding perimeter without complaint.
ISLAND_MIN_AREA_MM2 = 1.0

# Lateral offset between a pillar's two ends, breaking exact axis alignment so
# the boolean does not produce degenerate tangential contacts.
PILLAR_SKEW_MM = 0.15

# Island pillars get their own, thinner diameter.
#
# They are the most VISIBLE added geometry in the model, and for a reason the
# joint pins do not share: a joint pin sits inside a 0.7-1.4 mm gap between two
# bones that nearly touch, so only a sliver of its wall is ever in view, while a
# pillar spans open air -- typically between the metatarsals -- where its entire
# length is exposed. At 4 mm they read as scaffolding rods running through the
# forefoot, which is exactly what the shaded views show.
#
# 2 mm halves the visible width while still printing as a solid column at any
# sane layer height. They are printing aids, not anatomy, so the smallest
# diameter that prints reliably is the right one.
PILLAR_DIAMETER_MM = 2.0

# Regions where an island pillar is suppressed outright, as (x, y, radius) in
# the scan's own frame -- i.e. BEFORE MIRROR_X, the same frame the pin and
# pillar coordinates are computed in.
#
# (135.2, -57.8) is under the 5th toe's distal phalanx. It is the only pillar
# anywhere in the toes: every other one sits at y <= -104, in the midfoot or
# hindfoot, where surrounding bone hides most of its wall. This one stands 8 mm
# in completely open air beneath the tip of the smallest toe, where nothing
# hides it at all, so it reads as a rod stuck to the end of the pinky rather
# than as a printing aid.
#
# The toe it supports is real bone and stays exactly where it is -- only the
# pillar goes. That leaves the tip as a slicer island, which is the same
# trade-off DROP_PLATE_PILLARS already makes 21 times over: the print checklist
# calls for slicer-generated support under the cantilevered forefoot, and this
# tip is inside that region.
#
# The radius must stay small. Pillars cluster 1-2 mm apart in the midfoot, so a
# generous box would silently remove several; 3 mm covers the drift of a single
# centroid without reaching a neighbour.
SKIP_PILLAR_REGIONS_MM = ((135.2, -57.8, 3.0),)

# Pin every loose body to the MAIN body (the foot), never to another loose one.
#
# _bridge_bodies grows the assembly outward: each body it attaches becomes an
# anchor for the next. That let a phalanx be pinned to a phalanx -- a cylinder
# spanning two toe bones that are each already connected to the foot, which is
# both redundant and anatomically wrong, since it welds an interphalangeal joint
# that the scan resolved correctly.
#
# Restricting anchors to the main body keeps every pin a bone-to-foot
# connection. The mesh still comes out as one piece, because a body pinned to
# the foot is connected to everything else through the foot.
PIN_TO_MAIN_BODY_ONLY = True

# Pins to omit, identified by the volume of the body they would attach.
#
# Bodies are matched by volume rather than by index because the bridging order
# depends on which body happens to be nearest, so an index is not stable across
# parameter changes. Listing a volume here removes THAT pin only; every other
# body keeps its own connection.
#
# Removing a pin does NOT guarantee the mesh stays one piece: verify body_count
# after changing this. If a listed body detaches, take it off the list.
#
# The tolerance must stay TIGHT. The phalangeal bodies cluster closely --
# measured 868, 919, 974 and 1051 mm3 -- so a loose window matches several at
# once: at 60 mm3 it silently removed three pins instead of one. 15 mm3 absorbs
# run-to-run drift without reaching the neighbours, which are 45 mm3 apart at
# the closest.
#
# This list is EMPTY, and the entry it used to hold is a cautionary case.
#
# It held 919.0, the 5th-toe ray, on the stated grounds that the body "touches
# the foot over a whole region (431 vertices within 3 mm), so it remains attached
# through that contact." Re-measured, that is false: those 433 vertices are ALL
# at 1.00 mm or more, and none of them touch. The ray was held up from below by
# an island pillar under the toe tip, not by any contact. With that pillar
# suppressed (SKIP_PILLAR_REGIONS_MM) the ray drops off as a separate 919 mm3
# body and the one-piece gate fails.
#
# So the two exclusions are mutually exclusive, and the pin is the better one to
# keep: it is 2 mm and sits inside a 1.00 mm joint gap where the bones nearly
# touch, so only a sliver of its wall is visible, whereas the pillar stood 8 mm
# in open air under the tip of the toe with nothing to hide it.
SKIP_PIN_BODY_VOLUMES_MM3 = ()
SKIP_PIN_TOLERANCE_MM3 = 15.0

# Mirror the reconstruction across X, at the operator's request.
#
# This contradicts the laterality measured from the source study -- see the
# MIRROR_X note in brokefeet_axial_b123d.py for the full evidence (study header
# "TAC- PIE IZQUIERDO", hallux at 81.2 % across the bone span toward high
# pane-X, and an axis map that does not negate X).
#
# Applying it HERE, rather than only in the builder, means the exported
# BrokeFeet_axial_raw.stl carries the mirror too, so both STLs on disk show the
# same side. The cost is that the raw is no longer a faithful record of the
# scan's own coordinate frame: crossvalidate.py compares it against the
# sagittal reconstruction, which is NOT mirrored, and an un-compensated
# comparison degrades the adduction agreement from 1.36 mm to 8.67 mm. That is
# why crossvalidate.py mirrors the sagittal mesh to match (see MIRROR_X there).
MIRROR_X = True

# Pillars that would stand on the build plate are dropped rather than built.
#
# Two cases produce one: an island with NOTHING beneath it in its column (the
# floor search returns empty and falls back to voxel 0), and an island whose
# nearest material below is the base plate itself. Both run a bare vertical
# cylinder from bone down to Z=0, through the open air the equinus cantilever
# is supposed to show -- they read as scaffolding rather than as the deliberate
# hardware the bone-to-bone pins are, and they prop up the forefoot the model
# exists to leave unsupported.
#
# A pillar is treated as plate-touching when its bottom sits within this
# distance of the lowest material in the scan. Sized to a few scan pitches so
# the base plate's own top face counts, not just exact Z=0.
DROP_PLATE_PILLARS = True
PLATE_PILLAR_TOLERANCE_MM = 2.0

# Longest pillar worth building. Beyond this it is not supporting an island, it
# is a rod hanging in open air.
#
# The floor search looks straight DOWN from the island's centroid
# (`matrix[cx, cy, :k]`). When the material that actually supports the region is
# offset sideways -- common under the metatarsals, where a shaft overhangs the
# gap between two rays -- that column is empty, `floor` falls back to voxel 0,
# and the pillar is built all the way down to nothing. Visible in shaded views
# as a lone cylinder descending from a metatarsal into thin air.
#
# The plate filter above catches these only in the assembly pass, where a base
# plate exists to measure against; in the bone pass there is no plate, so they
# survive. A length cap catches them in both. Real island supports are short --
# they bridge a local overhang, not the height of the model.
MAX_PILLAR_LENGTH_MM = 12.0

# Occupancy level for the isotropic threshold. See to_isotropic().
ISO_LEVEL = 0.40

# Envelope-clipped closing of the isotropic grid. See _close_within_envelope().
#
# This is NOT the morphological closing this project rejected. That one ran on
# the 2D mask unclipped, and welded the midfoot into a 66 cm3 mass because a
# closing bridges ANY gap narrower than its element -- including joint spaces.
# Here the closing only PROPOSES material; the per-slice filled outline decides
# what is admitted, and anything spanning the concave space BETWEEN two bones
# falls outside that outline and is discarded. The axial silhouette is
# provably unchanged on every slice, so no bone can grow toward its neighbour.
#
# 5x5 at the 0.5 mm isotropic pitch is 2.5 mm. Swept against 3x3 and 7x7:
#
#   3x3   201 -> 187 tunnels   +0.12 % material
#   5x5   201 -> 183 tunnels   +0.25 % material   <- chosen
#   7x7   201 -> 182 tunnels   +0.32 % material
#
# 7x7 buys one tunnel for 28 % more material, so 5x5 is the knee. The element
# is isotropic rather than sized to the 0.625 mm slice spacing because it acts
# on the ALREADY-RESAMPLED grid, which is 0.5 mm in all three axes.
#
# Applied globally rather than only to the hindfoot: measured at +0.25 % vs
# +0.24 % for a Z 43-84 restriction, with identical per-band tunnel counts. The
# leg is already clean (2 tunnels) and stays at 2, so a band restriction buys
# nothing and adds a magic number.
CLOSE_WITHIN_ENVELOPE = True
ENVELOPE_CLOSE_SIZE = 5

# Largest in-plane hole filled outright, in mm2. Swept on the exported mesh:
#
#   <= 1 mm2   genus 333 -> 270, but components 1 -> 2
#   <= 5 mm2   genus 333 -> 238, components 1 -> 2
#   <= 28 mm2  genus 333 -> 232, components 1 -> 1   +0.25% material
#
# 28 mm2 (a ~6 mm circle) is both the most effective and the only value that
# keeps the mesh one piece. Above it sit the interosseous spaces -- the largest
# is 492 mm2, 38 x 35 mm -- which are anatomy and must stay open.
MAX_FILLED_HOLE_MM2 = 28.0

# Gated tunnel repair. See _close_tunnels_gated().
#
# The talus and calcaneus carried ~150 through-tunnels no data-driven method
# could close (README: "The DICOM would resolve it"), and the metatarsal
# shafts a handful more. The repair is justified by anatomy rather than by the
# source data: no foot bone has open through-tunnels at the millimetre scale
# -- every one is a trabecular-intensity dropout of the 8-bit windowed
# captures. Legitimate for a teaching model that already carries the NO APTO
# PARA PLANIFICACION disclaimer; the guards below are what keep it from
# touching real anatomy.
#
# The pass is the envelope-clipped closing run along ALL THREE axes -- exactly
# what the earlier sweep rejected (components 33 -> 25, bones fusing) -- made
# safe by the restriction that version lacked: a component gate. Every added
# blob (26-connected) is discarded outright if it touches more than one bone
# component, so two bones cannot fuse BY CONSTRUCTION, and the pass aborts if
# the component count moves. Verified 33 -> 33 at every sweep.
#
# First shipped restricted to the hindfoot band (Z 43-84 mm) out of caution;
# the slicer then showed the same defect class on the metatarsal shafts --
# windows into hollow shaft interiors, the calcaneus story again at smaller
# scale. Rerun globally (TUNNEL_BAND_MM = None) the gate holds: forefoot
# tunnels 7 -> 0, +0.48 cm3 over the banded version, components 33 -> 33,
# outer contour still unchanged. The band therefore proved to be caution, not
# necessity, and is retained only as an option.
#
# Measured on the pipeline's own iso grid (validate on the real intermediate,
# never a re-derived proxy): tunnels 182 -> 44 whole-grid, hindfoot bands
# 41/49/66 -> 6/2/31, outer contour unchanged (0 px growth in the filled
# projections along all three axes), +6.9 cm3 (+6.1 %) -- most of it the
# hollow calcaneal interior at Z ~53-60 mm, which the in-plane fill could
# never reach because its cortical rim is broken in-plane. Element sizes 5
# then 9: the 5-pass closes the trabecular pitting, the 9-pass the wide
# crescent mouths; both iterate to convergence. The gate discarded 22 cm3 of
# proposals that would have bridged bones -- more than three times what it
# kept.
TUNNEL_REPAIR = True
TUNNEL_BAND_MM = None  # (lo, hi) in mm to restrict additions; None = whole grid
TUNNEL_CLOSE_SIZES = (5, 9)
TUNNEL_MAX_SWEEPS = 3
TUNNEL_CONVERGED_VOXELS = 2000  # ~0.25 cm3 per full axis sweep

# Crater repair. See _close_craters_gated(). MEASURED AND REJECTED -- OFF.
#
# The tunnel and envelope passes clip every proposal to each slice's filled
# outline, so neither can fill a dent in the OUTER surface -- which is exactly
# what is visible in a shaded render and what the operator circles. This pass
# proposes with an unclipped 3D closing and relies on the component gate for
# safety.
#
# It is safe but it does not work. Roofing a crater converts an open dent into
# a covered channel, so it trades a visible defect for a tunnel roughly
# one-for-one. Swept on the pipeline's own iso grid (baseline 45 tunnels,
# 120.68 cm3, 33 components -- components held at 33 at every radius):
#
#   radius  element  added     tunnels   d
#     1     0.5 mm   0.65 cm3     76    +31
#     2     1.0 mm   1.20 cm3     53     +8
#     3     1.5 mm   0.67 cm3     42     -3
#     4     2.0 mm   0.51 cm3     46     +1
#     6     3.0 mm   0.54 cm3     44     -1
#
# The best case is -3 tunnels for +0.67 cm3 and the series is not monotonic,
# so that is noise rather than a trend. Left in place, disabled, so the
# measurement is not repeated. The craters are real and visible -- they are
# just not fixable by closing. See sculpt/README_SCULPT.md for hand repair.
CRATER_REPAIR = False
CRATER_CLOSE_RADII = (3,)  # 1.5 mm -- the least bad, if ever re-enabled

# Named craters patched individually. See _patch_named_craters().
#
# The global crater pass fails because a rule safe EVERYWHERE must be weak. A
# named region is a different problem: the fill can be aggressive inside it and
# touch nothing else, and the one thing that must not happen -- bridging two
# real bones -- is checked directly rather than prevented structurally.
#
# Each entry is (x_lo, y_lo, z_lo, x_hi, y_hi, z_hi, radius_mm) in the EXPORTED
# mesh frame (post-mirror, the frame MeshLab reports). Located by the operator
# with MeshLab's Get Point Info; see locate/README_LOCATE.md.
#
# Radius swept per crater. For the visible tarsal crater below, on the
# pipeline's own iso grid (baseline 8 real bones, 45 tunnels):
#   1.0 mm -> +5 tunnels   1.5 mm -> +1   2.0 mm -> +2   3.0 mm -> +3
#   2.5 mm -> +0 tunnels, bones unchanged, 36.4 % of the crater removed
# Only 2.5 leaves the topology untouched, so it is not a smooth trade -- re-run
# the sweep rather than nudging the value.
PATCH_NAMED_CRATERS = False
NAMED_CRATERS = (
    # visible in the print; traced by the operator, 463 mm3 notch
    (-118.75, -130.50, 61.50, -113.75, -118.50, 71.00, 2.5),
)
# A component below this is a speck, not a bone. Counting raw components made
# a safe patch look like bone fusion: the crater window holds one 73.85 cm3
# bone plus specks of 26 and 1 voxels, and the closing absorbing a speck moved
# the raw count 33 -> 31.
CRATER_MIN_BONE_MM3 = 50.0

# The scan field is a circle; the surrounding frame and the patient's OTHER leg
# both appear in frame (visible at the left of each slice). Bone from the
# contralateral limb must not enter this model.
FIELD_MARGIN_PX = 12


def load_stack() -> np.ndarray:
    """Assemble the axial volume, proximal extension first.

    Two capture sets cover this foot. The main series runs LOC -6.63 -> -118.50;
    the proximal set (deidentify_axial_proximal.py) runs +17.75 -> -5.38, adding
    23.13 mm of ankle and distal leg. Slice index maps straight to +Z, and LOC
    DECREASES as the stack ascends, so the proximal panes -- higher LOC -- are
    the top of the volume and must be stacked last.

    The two sets are contiguous but not adjacent: -5.38 to -6.63 is 1.25 mm,
    exactly two slice steps, so two slices were never captured. The gap is
    filled by linear interpolation between the bounding slices rather than
    ignored. Dropping it would compress 1.25 mm of leg into one 0.625 mm step
    and shorten the model; leaving it empty would part the tibia in two.

    Both sets are written on one pixel grid by their de-identify scripts (same
    scale, same framing about the scan circle), so they concatenate directly --
    verified at the seam: bone centroids agree to 0.07 x 0.19 mm.
    """
    files = sorted(glob.glob(str(DEID_DIR / "ax_*.png")))
    if not files:
        raise SystemExit(f"no axial panes in {DEID_DIR}; run deidentify_axial.py")

    proximal = sorted(glob.glob(str(PROXIMAL_DIR / "px_*.png")))
    if not proximal:
        print(f"  no proximal panes in {PROXIMAL_DIR}; "
              "building from the main series only")

    height = min(Image.open(f).size[1] for f in files + proximal)
    width = min(Image.open(f).size[0] for f in files + proximal)

    def read(paths: list[str]) -> np.ndarray:
        out = np.zeros((len(paths), height, width), dtype=np.uint8)
        for k, path in enumerate(paths):
            out[k] = np.array(Image.open(path).convert("L"))[:height, :width]
        return out

    # Main series descends in LOC with index; +Z ascends, so reverse it to put
    # the most distal slice at index 0 and the ankle at the top.
    main = read(files)[::-1]
    if not proximal:
        return main

    upper = read(proximal)[::-1]

    # Bridge the two uncaptured slices between LOC -6.63 and -5.38.
    low, high = main[-1].astype(np.float32), upper[0].astype(np.float32)
    bridge = np.stack([
        np.round(low + (high - low) * t).astype(np.uint8)
        for t in (1.0 / 3.0, 2.0 / 3.0)
    ])

    print(f"  {len(main)} main + {len(bridge)} interpolated + {len(upper)} "
          f"proximal = {len(main) + len(bridge) + len(upper)} slices")
    return np.concatenate([main, bridge, upper])


def segment(volume: np.ndarray) -> np.ndarray:
    mask = volume >= BONE_THRESHOLD

    mask[:, :FIELD_MARGIN_PX, :] = False
    mask[:, -FIELD_MARGIN_PX:, :] = False
    mask[:, :, :FIELD_MARGIN_PX] = False
    mask[:, :, -FIELD_MARGIN_PX:] = False

    # Fill each bone's interior. NO morphological closing.
    #
    # Closing looked necessary -- the porous adolescent cortex leaks and
    # fill_holes cannot seal an open outline. But measuring what it actually
    # does settled it: with closing at 3 iterations the midfoot fused into a
    # single 66 cm3 body spanning all 144 mm of the foot, while with fill alone
    # the largest bodies are 21.6 / 16.7 / 16.1 cm3 -- calcaneus, talus and a
    # midfoot group, which is anatomically right.
    #
    # The reason is that closing bridges ANY gap narrower than its structuring
    # element, and the joint spaces here are narrower than the cortical pores
    # it was meant to seal. It cannot tell the two apart. Threshold 115 already
    # admits the trabecular interior, so the outlines close on their own and
    # the closing was solving a problem that no longer exists.
    structure = ndimage.generate_binary_structure(2, 1)
    for k in range(mask.shape[0]):
        mask[k] = _fill_bone_interiors(mask[k], volume[k], structure)
        mask[k] = ndimage.binary_opening(
            mask[k], structure=structure, iterations=OPENING_RADIUS
        )

    labels, count = ndimage.label(mask)
    if count == 0:
        raise SystemExit("threshold produced no bone")

    sizes = ndimage.sum(mask, labels, range(1, count + 1))
    keep = [i + 1 for i, size in enumerate(sizes) if size >= MIN_COMPONENT_VOXELS]
    cleaned = np.isin(labels, keep)

    cleaned = _fill_axial_pits(cleaned, volume)

    # Fill cavities that are enclosed in 3D but not within any single slice.
    #
    # Do NOT do this by running the 2D fill along the other two axes. That was
    # tried and it fuses the foot into one mass: in a sagittal or coronal
    # re-slice, the gap BETWEEN two tarsals often reads as an enclosed hole, so
    # filling it welds the bones together. It took the midfoot from 17 separate
    # bones to a single 77 cm3 blob spanning the whole foot.
    #
    # Labelling the background is the safe equivalent. A void inside a bone is
    # a background component that never reaches the volume boundary; a joint
    # space always connects out to the surrounding soft tissue and so is left
    # alone.
    background, bg_count = ndimage.label(~cleaned)
    if bg_count:
        boundary_labels = set(background[0].flat) | set(background[-1].flat)
        boundary_labels |= set(background[:, 0].flat) | set(background[:, -1].flat)
        boundary_labels |= set(background[:, :, 0].flat) | set(background[:, :, -1].flat)
        boundary_labels.discard(0)

        interior = ~np.isin(background, list(boundary_labels)) & ~cleaned
        filled_voxels = int(interior.sum())
        cleaned = cleaned | interior
        print(f"  filled {filled_voxels:,} interior cavity voxels "
              f"({filled_voxels * 0.179 * 0.179 * SLICE_STEP_MM / 1000:.1f} cm3)")

    print(f"  components: {count} found, {len(keep)} kept")
    return cleaned


def _fill_bone_interiors(
    plane: np.ndarray, plane_source: np.ndarray, structure: np.ndarray
) -> np.ndarray:
    """Fill each bone from its own cortical outline, one slice.

    `plane` is the thresholded mask; `plane_source` the original grey values,
    needed to keep the fill inside the bone (see the clip at the end).

    A plain binary_fill_holes is not enough for this patient. The calcaneus and
    cuboid have trabecular interiors at intensity 82-103 -- below the 115
    threshold that keeps skin out, and barely above soft tissue. Their cortical
    rim is also broken in places, so the interior leaks to the outside and the
    fill has nothing enclosed to work on. Those bones came out as speckled
    rims: the "sponge" visible ~57 mm down the model.

    No single global threshold fixes this, because the calcaneus interior and
    the surrounding soft tissue overlap in intensity. What separates them is
    not brightness but ENCLOSURE -- the interior is surrounded by cortex.

    So: seal each cortical outline with a closing that is applied only to a
    scratch copy, fill it, and keep the filled interior. The closing is never
    written back, so it cannot bridge the joint spaces between bones (which is
    what wrecked an earlier attempt); it exists only to let the fill see a
    closed loop.
    """
    filled = ndimage.binary_fill_holes(plane)

    sealed = ndimage.binary_closing(
        plane, structure=structure, iterations=CORTEX_SEAL_RADIUS
    )
    sealed = ndimage.binary_fill_holes(sealed)

    # Erode back by the seal radius, so the material the closing added at the
    # OUTER surface is given up again and only genuinely enclosed area remains.
    interior = ndimage.binary_erosion(
        sealed, structure=structure, iterations=CORTEX_SEAL_RADIUS
    )

    # Clip to a low-threshold envelope. Erosion alone is not enough: where a
    # cortical break faces soft tissue, the seal spills outward and the fill
    # follows it into the surrounding tissue. Bone interior is dim (82-103 here)
    # but soft tissue is dimmer still, so a permissive intensity floor bounds
    # the fill without having to separate the two by brightness alone.
    return filled | (interior & (plane_source >= INTERIOR_FLOOR))


def _fill_axial_pits(mask: np.ndarray, volume: np.ndarray) -> np.ndarray:
    """Close trabecular voids that are enclosed ALONG Z, within one bone.

    _fill_bone_interiors works slice by slice, so it can only see enclosure
    in-plane. Measuring the finished mask shows that is not where the remaining
    sponge lives. Boundary transitions per bone voxel, by axis:

                        z       y       x
      Z  15.9- 29.6   0.225   0.058   0.074
      Z  56.9- 70.5   0.315   0.050   0.055
      Z  84.2-138.8   0.054   0.021   0.023   (leg -- clean)

    The foot's cross-sections are already smooth (in-plane rates match the
    leg's), but the mask is 4-6x more ragged ACROSS slices. Sealing the outline
    harder cannot help: a probe that closes each slice's outline at radius 8 and
    fills recovers ~0 mm2 on most midfoot bones, because there is no unfilled
    in-plane hole left to find.

    What is left are 89,958 voxels that are bone in slice k-1 and k+1 but empty
    at k, at intensity 86-113 (mean 101.7) -- the same trabecular range the
    calcaneus interior sits in, just under the 115 threshold. Bone does not have
    0.625 mm holes drilled through it with solid bone on both faces; those are
    threshold noise, and they are what the surface renders as sponge.

    Filling them needs a gate that a joint space cannot pass. Intensity is not
    it -- soft tissue in a joint reads in the same range, and gating on
    brightness alone welded the metatarsals to the tarsus and the fibula to the
    tibia (12 components -> 7).

    The gate used instead is SAME-COMPONENT enclosure: fill a void only where
    the nearest bone above and the nearest bone below belong to the same 3D
    connected component. A trabecular pit is surrounded by one bone. A joint
    space has a DIFFERENT bone on each side, so it is never filled -- and since
    the rule only adds material inside a body that is already connected, it
    cannot create a new connection between two bodies at all.

    Verified on the finished mask: of 96,185 voxels added, ZERO are adjacent
    (26-neighbourhood) to more than one component, the component count holds at
    12, and the tibiofibular gap is unchanged at 0.950 mm.
    """
    labels, count = ndimage.label(mask)
    if count == 0:
        return mask

    # Nearest labelled bone within AXIAL_PIT_SPAN slices, above and below.
    below = np.zeros(mask.shape, dtype=labels.dtype)
    above = np.zeros(mask.shape, dtype=labels.dtype)
    for step in range(AXIAL_PIT_SPAN, 0, -1):
        shifted = np.zeros_like(labels)
        shifted[step:] = labels[:-step]
        below = np.where(shifted > 0, shifted, below)

        shifted = np.zeros_like(labels)
        shifted[:-step] = labels[step:]
        above = np.where(shifted > 0, shifted, above)

    pits = (below > 0) & (below == above) & ~mask & (volume >= INTERIOR_FLOOR)

    added = int(pits.sum())
    if added:
        print(f"  filled {added:,} axial trabecular pits "
              f"({added * 0.179 * 0.179 * SLICE_STEP_MM / 1000:.1f} cm3, "
              f"span {AXIAL_PIT_SPAN})")
    return mask | pits


def _support_islands(parts: list, plate_top_z: float | None = None,
                     skip_regions: tuple | None = None) -> list:
    """Tie down regions that a slicer would see as floating.

    A mesh can be one watertight solid and still slice badly. Bone surfaces
    overhang, so as the slicer walks up in layers a region can appear with
    nothing beneath it -- an island. The material is connected in 3D, just not
    downward, which is what a printer needs. This model had 92 such regions and
    the slicer rejected it as having floating pieces.

    Each island gets a vertical pillar down to the material below it. Pillars
    are the same diameter as the joint pins so they read as the same kind of
    deliberate hardware rather than as anatomy.

    `plate_top_z` is the height of the surface a pillar must not stand on. Pass
    the base plate's TOP face when the cradle is part of the geometry -- that is
    what a pillar actually lands on, and it is BASE_THICKNESS above the mesh's
    lowest point, so inferring it from the bounds finds the plate's underside
    and matches nothing. Left as None (bone mesh alone, no plate yet) it falls
    back to the lowest material in the scan.

    `skip_regions` suppresses pillars inside given (x, y, radius) circles. The
    coordinates are frame-dependent and there is no way for this function to
    tell which frame it has been handed, so the CALLER passes them: this module
    works in the scan's own frame and passes SKIP_PILLAR_REGIONS_MM, while the
    builder mirrors and rotates the model first and must therefore pass its own
    values or None. Defaulting to the module constant here would apply scan
    coordinates to a rotated model and suppress a pillar somewhere else
    entirely.
    """
    import trimesh
    from scipy import ndimage

    combined = trimesh.util.concatenate(parts)
    grid = combined.voxelized(pitch=ISLAND_SCAN_PITCH).fill()
    matrix = grid.matrix
    origin = grid.origin if hasattr(grid, "origin") else grid.bounds[0]

    pillars = []
    kept_positions = []
    previous = None
    seen_material = False
    dropped_on_plate = 0
    dropped_too_long = 0
    dropped_in_region = 0

    # Z of the surface a pillar would stand on rather than land on bone.
    if plate_top_z is not None:
        plate_z = plate_top_z
    else:
        occupied_layers = np.where(matrix.any(axis=(0, 1)))[0]
        plate_z = (origin[2] + occupied_layers.min() * ISLAND_SCAN_PITCH
                   if len(occupied_layers) else origin[2])

    for k in range(matrix.shape[2]):
        layer = matrix[:, :, k]
        if not layer.any():
            previous = layer
            continue

        # The first layer carrying material rests on the build plate. It has
        # nothing beneath it by definition and is not an island.
        if not seen_material:
            seen_material = True
            previous = layer
            continue

        if previous is not None:
            labels, count = ndimage.label(layer)
            for index in range(1, count + 1):
                region = labels == index
                if (region & previous).any():
                    continue  # supported from below
                if region.sum() * ISLAND_SCAN_PITCH ** 2 < ISLAND_MIN_AREA_MM2:
                    continue  # too small to matter

                # Drop a pillar from the island's centroid to whatever is under it.
                cx, cy = (int(v.mean()) for v in np.where(region))
                column = matrix[cx, cy, :k]
                below = np.where(column)[0]
                floor = below.max() if len(below) else 0

                top = origin[2] + (k + 1) * ISLAND_SCAN_PITCH
                bottom = origin[2] + floor * ISLAND_SCAN_PITCH
                if top - bottom < ISLAND_SCAN_PITCH:
                    continue

                # Skip pillars that would land on the build plate instead of on
                # bone. `len(below) == 0` is the explicit case -- nothing at all
                # in the column, so `floor` fell back to voxel 0 -- and the
                # distance test catches an island whose nearest material below
                # is the base plate's top face.
                if DROP_PLATE_PILLARS and (
                    len(below) == 0
                    or bottom - plate_z <= PLATE_PILLAR_TOLERANCE_MM
                ):
                    dropped_on_plate += 1
                    continue

                # A pillar this long is spanning open air, not supporting an
                # island: the nearest material straight below the centroid is
                # far away because the real support is offset sideways.
                if top - bottom > MAX_PILLAR_LENGTH_MM:
                    dropped_too_long += 1
                    continue

                x = origin[0] + cx * ISLAND_SCAN_PITCH
                y = origin[1] + cy * ISLAND_SCAN_PITCH

                # A pillar standing in open air under a toe tip is the most
                # exposed geometry on the model: nothing surrounds it to hide
                # its wall, so it reads as a rod stuck to the end of the toe.
                if any((x - sx) ** 2 + (y - sy) ** 2 <= sr ** 2
                       for sx, sy, sr in (skip_regions or ())):
                    dropped_in_region += 1
                    continue

                # Tilt each pillar very slightly off vertical. A perfectly
                # axis-aligned cylinder meeting a bone surface tangentially
                # produces zero-area slivers along the contact ring, which
                # survive as non-manifold edges and leave the mesh
                # non-watertight -- a slicer reads those as holes. A fraction
                # of a degree of skew removes the degeneracy without moving the
                # pillar anywhere a viewer would notice.
                skew = PILLAR_SKEW_MM
                kept_positions.append((x, y, top))
                pillars.append(trimesh.creation.cylinder(
                    radius=PILLAR_DIAMETER_MM / 2.0,
                    segment=np.array([
                        [x - skew, y - skew, bottom - BRIDGE_BITE_MM],
                        [x + skew, y + skew, top + BRIDGE_BITE_MM],
                    ]),
                    sections=16,
                ))
        previous = layer

    if pillars:
        print(f"  added {len(pillars)} pillars under unsupported islands")
        # SKIP_PILLAR_REGIONS_MM is keyed on these coordinates, so a run has to
        # be able to report them.
        for cx, cy, cz in kept_positions:
            print(f"    pillar at ({cx:.1f}, {cy:.1f}) top z {cz:.1f}")
    if dropped_on_plate:
        print(f"  dropped {dropped_on_plate} pillar(s) that would stand on the "
              f"build plate; those islands are left unsupported")
    if dropped_too_long:
        print(f"  dropped {dropped_too_long} pillar(s) longer than "
              f"{MAX_PILLAR_LENGTH_MM} mm (spanning open air)")
    if dropped_in_region:
        print(f"  dropped {dropped_in_region} pillar(s) inside "
              f"SKIP_PILLAR_REGIONS_MM")
    return pillars


def _bridge_bodies(bodies: list) -> "trimesh.Trimesh":
    """Pin every separated bone to the model with a 2 mm cylinder.

    The reconstruction resolves the joint spaces, which leaves the phalanges as
    free-floating bodies -- correct anatomy, unusable as a model. The base mesh
    must already be one connected piece, so the connections belong here rather
    than only in the downstream build.

    A 2 mm cylinder is the least invasive connection that still holds: thin
    enough to read as a deliberate pin rather than as bone, so the proportions
    of the reconstruction are preserved. Bridges are added ONLY between bodies
    that are genuinely separate; anything already fused (including the
    patient's subtalar coalition) is left untouched.

    Each remaining body is joined to whichever already-connected body it is
    closest to, so the connection spans the real gap rather than an arbitrary
    pair.
    """
    import trimesh
    from scipy.spatial import cKDTree

    if len(bodies) <= 1:
        return bodies[0] if bodies else None

    ordered = sorted(bodies, key=lambda b: -abs(b.volume))
    attached, pending = [ordered[0]], list(ordered[1:])
    plugs = []

    while pending:
        best = None
        for index, candidate in enumerate(pending):
            tree = cKDTree(candidate.vertices)
            for anchor_index, anchor in enumerate(attached):
                if PIN_TO_MAIN_BODY_ONLY and anchor_index != 0:
                    continue
                distances, indices = tree.query(anchor.vertices)
                k = int(np.argmin(distances))
                gap = float(distances[k])
                if best is None or gap < best[0]:
                    best = (gap, index, anchor.vertices[k],
                            candidate.vertices[indices[k]], anchor_index)

        gap, index, point_a, point_b, _ = best

        # Each pin is independently skippable by the volume of the body it
        # attaches, so one can be removed without disturbing the others.
        #
        # The 5th-toe ray is the case this exists for: it contacts the foot over
        # a whole region (431 vertices within 3 mm, across a 29.5 mm ray), so it
        # stays connected through that contact and its pin is cosmetic. Listing
        # its volume here drops that pin alone; every other body keeps its own.
        #
        # Volumes are stable between runs for a fixed segmentation, but they do
        # shift if the threshold or the fills change -- so the skip is matched
        # with a tolerance and reported, rather than silently missing.
        body_volume = abs(pending[index].volume)
        if any(abs(body_volume - v) <= SKIP_PIN_TOLERANCE_MM3
               for v in SKIP_PIN_BODY_VOLUMES_MM3):
            print(f"    skipped pin for body {body_volume:.0f} mm3 "
                  f"(SKIP_PIN_BODY_VOLUMES_MM3)")
            attached.append(pending.pop(index))
            continue

        axis = point_b - point_a
        length = float(np.linalg.norm(axis))
        direction = axis / length if length > 1e-9 else np.array([0.0, 0.0, 1.0])

        # Size the bite to the smaller bone, so a pin cannot run through a
        # distal phalanx and out the other side toward its neighbour.
        smallest = min(np.ptp(pending[index].vertices, axis=0).min(),
                       np.ptp(attached[0].vertices, axis=0).min())
        bite = max(BRIDGE_BITE_MIN_MM,
                   min(BRIDGE_BITE_MM, smallest * BRIDGE_BITE_FRACTION))

        # A phalanx is no wider than the pin itself, so a tarsal-sized cylinder
        # shows as a bar across the interdigital space rather than a joint pin.
        diameter = (BRIDGE_DIAMETER_PHALANX_MM
                    if abs(pending[index].volume) <= PHALANX_MAX_VOLUME_MM3
                    else BRIDGE_DIAMETER_MM)

        # Report where each pin lands. The skip lists are keyed on these
        # coordinates and volumes, so they have to be readable from a run
        # rather than rediscovered by instrumenting this function again.
        mid = (point_a + point_b) / 2.0
        print(f"    pin {diameter:.0f} mm for body {body_volume:.0f} mm3, "
              f"gap {gap:.2f} mm, at "
              f"({mid[0]:.1f}, {mid[1]:.1f}, {mid[2]:.1f})")

        plugs.append(trimesh.creation.cylinder(
            radius=diameter / 2.0,
            segment=np.array([
                point_a - direction * bite,
                point_b + direction * bite,
            ]),
            sections=16,
        ))
        attached.append(pending.pop(index))

    print(f"  bridged {len(plugs)} gaps "
          f"({BRIDGE_DIAMETER_MM} mm pins, {BRIDGE_DIAMETER_PHALANX_MM} mm "
          f"on phalanges)")

    # This pass runs in the scan's own frame (the mirror is applied later), so
    # SKIP_PILLAR_REGIONS_MM is expressed in the coordinates it sees.
    plugs.extend(_support_islands(attached + plugs,
                                  skip_regions=SKIP_PILLAR_REGIONS_MM))

    for body in attached:
        if not body.is_watertight:
            body.merge_vertices()
            trimesh.repair.fill_holes(body)
            trimesh.repair.fix_normals(body)

    solid = [b for b in attached if b.is_watertight]
    joined = trimesh.boolean.union(solid + plugs)

    # A pillar that grazes a bone tangentially leaves zero-area slivers, which
    # survive as non-manifold edges and make the export non-watertight -- a
    # slicer treats those as holes. Round-tripping the union rebuilds the
    # surface and resolves them.
    joined.merge_vertices()
    broken = len(trimesh.repair.broken_faces(joined))
    if broken:
        joined.update_faces(joined.nondegenerate_faces())
        joined.remove_unreferenced_vertices()
        joined.merge_vertices()
        trimesh.repair.fix_normals(joined)
        remaining = len(trimesh.repair.broken_faces(joined))
        print(f"  cleaned {broken} sliver faces from pillar contacts"
              f"{f' ({remaining} remain)' if remaining else ''}")

    return joined


def to_isotropic(mask: np.ndarray) -> np.ndarray:
    """Resample the segmented mask onto an isotropic grid.

    Order matters here. The in-plane pixel is 0.179 mm and the isotropic target
    is 0.5 mm, so this DOWNSAMPLES in-plane by 0.36 while upsampling across
    slices. Cortical shells in this bone-kernel series are only 1-2 px thick at
    0.179 mm, which is below the Nyquist limit of a 0.5 mm grid: resampling a
    binary mask directly punched holes through every shell and shattered the
    foot into 2228 components before any smoothing ran.

    Anti-aliasing first fixes it. Blurring the binary mask to a smooth
    occupancy field at the SOURCE resolution, then interpolating that field and
    thresholding once, lets a shell thinner than the target voxel still push
    its neighbourhood above 0.5 and survive as a closed surface.
    """
    # Suppress surface roughness before resampling.
    #
    # Threshold 115 admits the trabecular interior, which is what makes the
    # bones solid -- but surface trabeculae are individually resolved at
    # 0.179 mm, so the bone's outer boundary comes out pitted and the mesh
    # reads as spongy.
    #
    # A median filter is the wrong tool here and was tried: being non-linear on
    # a binary mask, it SEVERS thin structures instead of smoothing them. Every
    # window size fragmented the stack (21 components -> 92-133) and destroyed
    # the distal phalanges, which are only ~8 mm across.
    #
    # Blurring the occupancy field and re-thresholding achieves the same
    # smoothing without cutting anything: pits fill because their neighbourhood
    # is mostly bone, while a thin phalanx stays above the level because its
    # own neighbourhood is too.
    occupancy = ndimage.gaussian_filter(mask.astype(np.float32),
                                        sigma=SOURCE_BLUR_SIGMA)

    zoom = (
        SLICE_STEP_MM / ISO_VOXEL_MM,
        MM_PER_PX / ISO_VOXEL_MM,
        MM_PER_PX / ISO_VOXEL_MM,
    )
    resampled = ndimage.zoom(occupancy, zoom, order=1)

    # Threshold below 0.5: the blur above erodes thin features symmetrically,
    # so a strict half-occupancy cut would thin the cortex further. 0.40
    # restores shell continuity without inflating the bone surface.
    iso = resampled >= ISO_LEVEL

    # Close cavities the RESAMPLE itself opens.
    #
    # The segmentation mask has ZERO enclosed cavities -- segment() already
    # fills them. Measured on the 0.5 mm grid, 22 reappear, and 20 of the 22
    # sit in the hindfoot (Z 43-84 mm): the blur-and-downsample turns a thin
    # trabecular strut into a void, because a 0.179 mm feature cannot survive a
    # 0.5 mm sample.
    #
    # These are safe to fill and nothing else here is. A cavity that reaches
    # the grid boundary is outside-connected -- a joint space always is, since
    # it opens to the surrounding soft tissue. One that does NOT reach the
    # boundary is enclosed within a single bone by definition, so filling it
    # cannot bridge two bones or narrow a joint. It costs 24 mm3 (0.02 % of
    # bone volume) and removes all 22 cavities plus 15 tunnels (216 -> 201).
    #
    # Lowering ISO_LEVEL was tried instead and is worse: it closes marginally
    # more tunnels while FUSING bones (33 components -> 25 at 0.36), which is
    # the failure this reconstruction spends most of its effort avoiding.
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
            iso = iso | enclosed

    if CLOSE_WITHIN_ENVELOPE:
        iso = _close_within_envelope(iso)

    if TUNNEL_REPAIR:
        iso = _close_tunnels_gated(iso)

    if CRATER_REPAIR:
        iso = _close_craters_gated(iso)

    if PATCH_NAMED_CRATERS and NAMED_CRATERS:
        iso = _patch_named_craters(iso)

    return iso


def _mesh_to_index(iso: np.ndarray):
    """Return a function mapping exported-mesh coordinates to grid indices.

    main() maps marching-cubes vertices as

        verts = [v2, -v1, v0] * ISO_VOXEL_MM      then X -> -X if MIRROR_X

    so index axis 2 carries X, axis 1 carries -Y and axis 0 carries Z. Getting
    this wrong points a window at empty space and reports 0 mm3 for a crater
    that is plainly there, which is exactly what a first attempt did.

    The offsets come from the grid's own occupied extent matched to the mesh
    bounds it produces, so this stays correct if the volume is recropped.
    """
    occupied = np.argwhere(iso)
    lo_idx = occupied.min(0)
    hi_idx = occupied.max(0)

    # The grid's occupied extent is exactly the exported mesh's bounding box,
    # so the two corners pin the mapping without needing the mesh itself.
    # Index 0 rises with Z; indices 1 and 2 run OPPOSITE to Y and X, so the
    # grid's high index on those axes is the mesh's low coordinate.
    mesh_lo, mesh_hi = _exported_bounds(lo_idx, hi_idx)

    def to_index(point):
        x, y, z = point
        i0 = lo_idx[0] + (z - mesh_lo[2]) / ISO_VOXEL_MM
        i1 = hi_idx[1] - (y - mesh_lo[1]) / ISO_VOXEL_MM
        i2 = hi_idx[2] - (x - mesh_lo[0]) / ISO_VOXEL_MM
        return np.array([i0, i1, i2])

    return to_index, lo_idx, hi_idx


def _exported_bounds(lo_idx, hi_idx):
    """Mesh-frame bounding box of the occupied grid.

    Derived from the same transform main() applies, so the two cannot drift:
    verts = [i2, -i1, i0] * ISO_VOXEL_MM, then X -> -X when MIRROR_X. Whichever
    end of an axis becomes the minimum after the sign flips is resolved by
    taking min/max of the two mapped corners.
    """
    def to_mesh(idx):
        x = idx[2] * ISO_VOXEL_MM
        y = -idx[1] * ISO_VOXEL_MM
        z = idx[0] * ISO_VOXEL_MM
        if MIRROR_X:
            x = -x
        return np.array([x, y, z])

    a, b = to_mesh(lo_idx), to_mesh(hi_idx)
    return np.minimum(a, b), np.maximum(a, b)


def _real_bone_count(iso: np.ndarray) -> int:
    """Components above CRATER_MIN_BONE_MM3. Raw component counts are useless
    here -- the grid carries single-voxel specks whose absorption by a closing
    looks identical to two bones fusing."""
    labels, n = ndimage.label(iso)
    if n == 0:
        return 0
    sizes = ndimage.sum(iso, labels, range(1, n + 1)) * ISO_VOXEL_MM ** 3
    return int((sizes >= CRATER_MIN_BONE_MM3).sum())


def _patch_named_craters(iso: np.ndarray) -> np.ndarray:
    """Fill individually named craters, verifying topology after each.

    A crater is open to the outside, so no fill-based method can see it and the
    envelope-clipped passes are built never to touch it. Inside a named box a
    plain closing does reach it. Safety is verified, not assumed: the patch is
    kept only if the real-bone count is unchanged and the tunnel count does not
    rise.
    """
    to_index, _, _ = _mesh_to_index(iso)
    struct = ndimage.generate_binary_structure(3, 1)

    bones_before = _real_bone_count(iso)
    tunnels_before = _tunnel_count(iso)

    for entry in NAMED_CRATERS:
        x0, y0, z0, x1, y1, z1, radius_mm = entry
        c1 = to_index((x0, y0, z0))
        c2 = to_index((x1, y1, z1))
        lo = np.maximum(np.floor(np.minimum(c1, c2)).astype(int) - 4, 0)
        hi = np.minimum(np.ceil(np.maximum(c1, c2)).astype(int) + 5,
                        np.array(iso.shape))
        if np.any(hi <= lo):
            print(f"  named crater {entry[:3]} maps outside the grid -- skipped")
            continue
        window = (slice(lo[0], hi[0]), slice(lo[1], hi[1]), slice(lo[2], hi[2]))

        iterations = max(1, int(round(radius_mm / ISO_VOXEL_MM)))
        sub = iso[window]
        proposal = ndimage.binary_closing(sub, structure=struct,
                                          iterations=iterations)
        added = int((proposal & ~sub).sum())
        if not added:
            continue

        trial = iso.copy()
        trial[window] = sub | proposal
        bones = _real_bone_count(trial)
        tunnels = _tunnel_count(trial)
        if bones != bones_before or tunnels > tunnels_before:
            print(f"  named crater at ({x0:.1f}, {y0:.1f}, {z0:.1f}) REJECTED: "
                  f"bones {bones_before} -> {bones}, "
                  f"tunnels {tunnels_before} -> {tunnels}")
            continue

        iso = trial
        tunnels_before = tunnels
        print(f"  patched crater at ({x0:.1f}, {y0:.1f}, {z0:.1f}) r={radius_mm} "
              f"mm: +{added * ISO_VOXEL_MM ** 3:.0f} mm3, "
              f"bones {bones}, tunnels {tunnels}")

    return iso


def _tunnel_count(iso: np.ndarray) -> int:
    """b1 = b0 + b2 - chi. Cavities are background components that do not reach
    the grid boundary."""
    from skimage import measure

    components = ndimage.label(iso)[1]
    background, n = ndimage.label(~iso)
    if n == 0:
        return components - int(measure.euler_number(iso, connectivity=1))
    boundary = set(background[0].flat) | set(background[-1].flat)
    boundary |= set(background[:, 0].flat) | set(background[:, -1].flat)
    boundary |= set(background[:, :, 0].flat) | set(background[:, :, -1].flat)
    boundary.discard(0)
    cavities = n - len(boundary)
    return components + cavities - int(measure.euler_number(iso, connectivity=1))


def _close_craters_gated(iso: np.ndarray) -> np.ndarray:
    """Close craters -- defects open to the OUTSIDE surface.

    _close_within_envelope() and _close_tunnels_gated() both clip every
    proposal to each slice's own filled outline, so by construction neither can
    fill a dent in the outer surface: a crater lies OUTSIDE the outline, which
    is the one place those passes are built never to touch. That is why the
    craters the operator can see and circle survive a repair that takes genus
    from 340 to 91 -- they were never candidates.

    An unclipped 3D closing does propose them. On its own that is the operation
    this project rejected for welding the midfoot into a 66 cm3 mass, so
    nothing here relies on the closing being well behaved: every proposed blob
    goes through _gate_to_single_component(), which discards whole any blob
    touching two bones. Fusing bones is impossible by construction, and the
    pass aborts if the component count moves regardless.

    Adding material can break a bone count in the other direction too, which
    the tunnel pass never had to handle: roofing a crater can seal a narrow
    neck of background and pinch one component into two (measured: 33 -> 36).
    So acceptance is also conditioned on the component count holding, per blob
    where a whole sweep would fail.

    The element is deliberately small. A crater is a local dent a few voxels
    deep; a joint space is wide and long. Sizing the element to the dent means
    most inter-bone gaps are never proposed in the first place, and the gate
    only has to catch the remainder.
    """
    before = int(iso.sum())
    n_components = ndimage.label(iso)[1]
    struct = ndimage.generate_binary_structure(3, 1)
    dropped = 0

    for r in CRATER_CLOSE_RADII:
        closed = ndimage.binary_closing(iso, structure=struct, iterations=r)
        added = closed & ~iso
        if not added.any():
            continue
        gated = _gate_to_single_component(iso, added)
        dropped += int(added.sum()) - int(gated.sum())
        if not gated.any():
            continue

        # _gate_to_single_component only forbids JOINING two bones. Adding
        # material can also SPLIT one: roofing a crater seals a narrow neck of
        # background, and a component that was reaching around that neck gets
        # pinched in two. Measured here as 33 -> 36 components. Accept the
        # sweep only if the count is unchanged; otherwise fall back to
        # per-blob acceptance so one bad blob does not cost the whole sweep.
        trial = iso | gated
        if ndimage.label(trial)[1] == n_components:
            iso = trial
            continue

        blobs, nblobs = ndimage.label(gated, structure=np.ones((3, 3, 3), bool))
        for b in range(1, nblobs + 1):
            blob = blobs == b
            trial = iso | blob
            if ndimage.label(trial)[1] == n_components:
                iso = trial
            else:
                dropped += int(blob.sum())

    added_total = int(iso.sum()) - before
    after_components = ndimage.label(iso)[1]
    print(f"  crater repair: +{added_total * ISO_VOXEL_MM ** 3 / 1000:.2f} cm3 "
          f"(+{added_total / before * 100:.2f}%), "
          f"gated out {dropped * ISO_VOXEL_MM ** 3 / 1000:.2f} cm3, "
          f"components {n_components} -> {after_components}")
    if after_components != n_components:
        raise SystemExit(
            "crater repair changed the component count -- the gate failed, "
            "do not trust this grid")
    return iso


def _close_within_envelope(iso: np.ndarray) -> np.ndarray:
    """Close tunnels through bone without letting the silhouette move.

    The hindfoot tunnels survive every fill-based method because they are not
    enclosed: a tunnel leaks sideways to the outside, so binary_fill_holes
    cannot see it, and by the time the tarsal mass is one connected component
    with zero cavities there is nothing left for a fill to find.

    A closing CAN see them -- but an unclipped closing is exactly what welded
    this midfoot into a 66 cm3 mass, because it bridges any gap narrower than
    its element and the joint spaces here are narrower than the pores.

    The fix is to separate proposing from permitting. The closing proposes
    material; each slice's own filled outline decides what is admitted:

        env = binary_fill_holes(slice)          # what this slice already spans
        out = slice | (closing(slice) & env)    # nothing outside it is allowed

    A tunnel through a bone lies INSIDE that bone's outline, so it is filled.
    Material spanning the concave space BETWEEN two bones lies OUTSIDE the
    outline, so it is discarded and the two bones cannot be joined. The result
    is verifiable rather than argued: the axial outline is byte-identical on
    every slice of the stack, and the component count is unchanged at 33.

    Note the guarantee is per-axis. Running the same pass along all three axes
    closes far more tunnels (201 -> 124) but each axis admits material the
    others' envelopes would forbid, and the component count falls 33 -> 25 --
    bones fusing. One axis only.
    """
    element = np.ones((ENVELOPE_CLOSE_SIZE, ENVELOPE_CLOSE_SIZE), dtype=bool)
    out = iso.copy()
    before = int(iso.sum())

    px_area = ISO_VOXEL_MM ** 2
    for k in range(iso.shape[0]):
        plane = iso[k]
        if not plane.any():
            continue
        envelope = ndimage.binary_fill_holes(plane)
        closed = ndimage.binary_closing(plane, structure=element)
        plane = plane | (closed & envelope)

        # Fill in-plane holes up to MAX_FILLED_HOLE_MM2 outright.
        #
        # Closing can only bridge a hole narrower than its element, so it leaves
        # every wider one open even when the hole is plainly noise -- 389 of the
        # 518 in-plane holes measure under 1.1 mm across, far below any
        # anatomical feature and below a print nozzle. This fills by AREA
        # instead, which reaches them regardless of shape, and adds no dilation
        # at all: material goes only where the slice already encloses it, so the
        # outer silhouette is untouched by construction.
        #
        # The cap is what protects the anatomy. The largest openings in the
        # hindfoot are 200-490 mm2 -- up to 38 x 35 mm -- and those are the
        # interosseous spaces between the calcaneus, talus and tarsals, not
        # perforations. Filling those would weld the hindfoot into one mass.
        holes = ndimage.binary_fill_holes(plane) & ~plane
        if holes.any():
            labels, count = ndimage.label(holes)
            sizes = ndimage.sum(holes, labels, range(1, count + 1)) * px_area
            small = [i + 1 for i, a in enumerate(sizes)
                     if a <= MAX_FILLED_HOLE_MM2]
            if small:
                plane = plane | np.isin(labels, small)

        out[k] = plane

    added = int(out.sum()) - before
    if added:
        print(f"  closed {added:,} tunnel voxels within the slice envelope "
              f"({added * ISO_VOXEL_MM ** 3 / 1000:.2f} cm3, "
              f"+{added / before * 100:.2f}%)")
    return out


def _envelope_close_along(iso: np.ndarray, axis: int, size: int) -> np.ndarray:
    """One envelope-clipped closing sweep of the slices along `axis`.

    Same propose/permit construction as _close_within_envelope, generalised to
    any axis: the closing proposes, each slice's own filled outline permits,
    and in-plane holes up to MAX_FILLED_HOLE_MM2 are filled outright. Returns
    the full proposed grid; the caller decides what is admitted.
    """
    element = np.ones((size, size), dtype=bool)
    prop = iso.copy()
    px_area = ISO_VOXEL_MM ** 2
    for i in range(iso.shape[axis]):
        sl = [slice(None)] * 3
        sl[axis] = i
        plane = iso[tuple(sl)]
        if not plane.any():
            continue
        envelope = ndimage.binary_fill_holes(plane)
        closed = ndimage.binary_closing(plane, structure=element)
        out = plane | (closed & envelope)

        holes = ndimage.binary_fill_holes(out) & ~out
        if holes.any():
            labels, count = ndimage.label(holes)
            sizes = ndimage.sum(holes, labels, range(1, count + 1)) * px_area
            small = [j + 1 for j, a in enumerate(sizes)
                     if a <= MAX_FILLED_HOLE_MM2]
            if small:
                out = out | np.isin(labels, small)
        prop[tuple(sl)] = out
    return prop


def _gate_to_single_component(iso: np.ndarray,
                              added: np.ndarray) -> np.ndarray:
    """Discard every added blob that touches more than one bone component.

    This is the guarantee that lets the closing run along all three axes: a
    blob whose 6-neighbourhood reaches two different components would fuse
    them, so it is dropped whole. A blob touching exactly one component can
    only thicken that component. Blobs are 26-connected so a diagonal chain of
    additions counts as one blob and cannot smuggle a bridge through in parts.
    """
    if not added.any():
        return added
    labels, _ = ndimage.label(iso)
    blobs, nblobs = ndimage.label(added, structure=np.ones((3, 3, 3), bool))
    touched: dict[int, set] = {}
    for axis in range(3):
        for shift in (1, -1):
            neighbour = np.roll(labels, shift, axis=axis)
            edge = [slice(None)] * 3
            edge[axis] = 0 if shift == 1 else -1
            neighbour[tuple(edge)] = 0
            m = added & (neighbour > 0)
            if m.any():
                for b, c in zip(blobs[m].tolist(), neighbour[m].tolist()):
                    touched.setdefault(b, set()).add(c)
    drop = [b for b, comps in touched.items() if len(comps) > 1]
    drop += [b for b in range(1, nblobs + 1) if b not in touched]
    if drop:
        added = added & ~np.isin(blobs, drop)
    return added


def _close_tunnels_gated(iso: np.ndarray) -> np.ndarray:
    """Close through-tunnels the per-axis envelope pass cannot see.

    See the TUNNEL_REPAIR comment for why this is anatomically justified and
    how it was measured. Mechanically: iterate envelope-clipped closings along
    Y, X and Z, and component-gate every blob so bones cannot fuse. Element 5
    first (trabecular pitting), then 9 (wide crescent mouths), each to
    convergence.
    """
    if TUNNEL_BAND_MM is None:
        band = np.ones_like(iso)
    else:
        band = np.zeros_like(iso)
        band[int(TUNNEL_BAND_MM[0] / ISO_VOXEL_MM):
             int(TUNNEL_BAND_MM[1] / ISO_VOXEL_MM)] = True

    before = int(iso.sum())
    n_components = ndimage.label(iso)[1]
    dropped = 0

    for size in TUNNEL_CLOSE_SIZES:
        for _ in range(TUNNEL_MAX_SWEEPS):
            sweep_added = 0
            for axis in (1, 2, 0):
                proposal = _envelope_close_along(iso, axis, size)
                added = proposal & band & ~iso
                gated = _gate_to_single_component(iso, added)
                dropped += int(added.sum()) - int(gated.sum())
                iso = iso | gated
                sweep_added += int(gated.sum())
            if sweep_added < TUNNEL_CONVERGED_VOXELS:
                break

    # The cross-axis additions can roof over a void and turn it into an
    # enclosed cavity. Enclosed-within-one-bone is exactly the safe-to-fill
    # case (same argument as the resample-cavity fill above).
    background, count = ndimage.label(~iso)
    if count:
        boundary = set(background[0].flat) | set(background[-1].flat)
        boundary |= set(background[:, 0].flat) | set(background[:, -1].flat)
        boundary |= set(background[:, :, 0].flat) | set(background[:, :, -1].flat)
        boundary.discard(0)
        enclosed = ~np.isin(background, list(boundary)) & ~iso
        if enclosed.any():
            iso = iso | enclosed

    after_components = ndimage.label(iso)[1]
    added_total = int(iso.sum()) - before
    print(f"  tunnel repair: +{added_total * ISO_VOXEL_MM ** 3 / 1000:.2f} cm3 "
          f"(+{added_total / before * 100:.2f}%), "
          f"gated out {dropped * ISO_VOXEL_MM ** 3 / 1000:.2f} cm3, "
          f"components {n_components} -> {after_components}")
    if after_components != n_components:
        raise SystemExit(
            "tunnel repair changed the component count -- the gate failed, "
            "do not trust this grid")
    return iso


def main() -> None:
    print("loading axial stack...")
    volume = load_stack()
    print(f"  {volume.shape[0]} slices, {volume.shape[2]}x{volume.shape[1]} px")
    print(f"  voxel {MM_PER_PX:.3f} x {MM_PER_PX:.3f} x {SLICE_STEP_MM} mm")

    print("segmenting bone...")
    mask = segment(volume)
    print(f"  bone voxels: {mask.sum():,}")

    print("resampling to isotropic...")
    iso = to_isotropic(mask)
    print(f"  grid {iso.shape} at {ISO_VOXEL_MM} mm")

    print("meshing...")
    from skimage import measure

    # Pad the volume with an empty voxel on every side before meshing.
    #
    # The calcaneus and talus reach the top slice of the stack, so bone touches
    # the array boundary. Marching cubes cannot close a surface against the
    # edge of its own grid: those two bones came out as open shells with
    # hundreds of small boundary holes (Euler -315), which trimesh.fill_holes
    # cannot span and which make the boolean engine reject them outright
    # ("Not all meshes are volumes!").
    #
    # One voxel of empty margin gives the isosurface somewhere to close. It
    # caps the bones flat at the scan limit, which is honest -- the scan simply
    # stops there -- and costs 0.5 mm of envelope.
    iso = np.pad(iso, 1, mode="constant", constant_values=False)

    verts, faces, _, _ = measure.marching_cubes(iso, level=0.5)
    verts -= 1.0  # undo the pad offset so coordinates stay in stack space
    verts *= ISO_VOXEL_MM

    # Voxel axes -> anatomy. Array is (slice, row, col):
    #   axis 0 = slice  -> superoinferior
    #   axis 1 = row    -> anteroposterior (+row toward the heel, so negate)
    #   axis 2 = col    -> mediolateral -> X
    #
    # Slice order: LOC runs -6.63 -> -119.76, i.e. it DECREASES as the index
    # rises. An earlier version negated axis 0 on the assumption that a falling
    # LOC meant the stack descends toward the sole. It does not -- checked
    # against the sagittal reconstruction, which puts the tibia at high Z and
    # the heel at low Y, this stack ascends. Negating it stood the foot upside
    # down, which no topology gate can see and which showed up only as plantar
    # and adduction profiles that mirrored the sagittal series instead of
    # matching it. Slice index maps straight to +Z.
    verts = np.column_stack([verts[:, 2], -verts[:, 1], verts[:, 0]])

    mesh = trimesh.Trimesh(vertices=verts, faces=faces)

    # Two axes are negated above, which mirrors the mesh and reverses triangle
    # orientation. Rather than reasoning about the sign by hand -- the axis
    # map's determinant and marching_cubes' own winding convention compound,
    # and getting it wrong silently yields negative volumes that then make
    # every body fail the size filter -- just measure the result and fix it.
    if mesh.volume < 0:
        mesh.invert()

    mesh.update_faces(mesh.nondegenerate_faces())
    mesh.update_faces(mesh.unique_faces())
    mesh.remove_unreferenced_vertices()
    mesh.fill_holes()

    bodies = mesh.split(only_watertight=False)
    if len(bodies) > 1:
        # Filter on size AND shape. Compare on absolute volume, since a body
        # whose winding came out inverted still represents real bone.
        kept, shards, flakes = [], 0, 0
        for body in bodies:
            volume = abs(body.volume)
            if volume < MIN_BODY_VOLUME_MM3:
                shards += 1
                continue
            if volume > 0 and body.area / volume > MAX_AREA_VOLUME_RATIO:
                flakes += 1
                continue
            kept.append(body)

        if not kept:
            raise SystemExit(
                f"every body fell below {MIN_BODY_VOLUME_MM3} mm3 -- "
                "check segmentation before adjusting the threshold"
            )
        print(f"  dropped {shards} specks and {flakes} thin flakes "
              f"(area/volume > {MAX_AREA_VOLUME_RATIO})")
        mesh = _bridge_bodies(kept)

    # Discard zero-volume shards left by the bridging booleans.
    #
    # The size filter above runs BEFORE _bridge_bodies, so it cannot see these:
    # they are created by the pins and pillars meeting bone tangentially. The
    # face-level cleanup inside _bridge_bodies repairs slivers but does not
    # remove disconnected bodies, so the mesh stayed watertight while exporting
    # as 5 bodies.
    #
    # This matters beyond tidiness. The README certifies this file as one body,
    # brokefeet_axial_b123d.py re-splits it on load, and a zero-volume body is
    # not a closed volume -- the manifold engine rejects it outright ("Not all
    # meshes are volumes!"), which is exactly how the downstream build crashed.
    bodies = mesh.split(only_watertight=False)
    if len(bodies) > 1:
        real = [b for b in bodies if abs(b.volume) >= MIN_BODY_VOLUME_MM3]
        shards = len(bodies) - len(real)
        if shards:
            print(f"  discarded {shards} shard(s) below {MIN_BODY_VOLUME_MM3} mm3 "
                  f"left by bridging")
        if not real:
            raise SystemExit("bridging left nothing above the size filter")
        mesh = trimesh.util.concatenate(real) if len(real) > 1 else real[0]

    # Mirror last, after every body has been bridged and cleaned, so the pin
    # geometry is computed in the scan's own frame and only the finished mesh
    # is reflected. Reflection reverses winding, hence fix_normals().
    if MIRROR_X:
        mesh.apply_transform(np.diag([-1.0, 1.0, 1.0, 1.0]))
        mesh.fix_normals()
        print("  mirrored across X (MIRROR_X)")

    extents = mesh.extents
    print(f"  mesh: {len(mesh.vertices):,} verts, {len(mesh.faces):,} faces")
    print(f"  extents: {extents[0]:.1f} x {extents[1]:.1f} x {extents[2]:.1f} mm")
    print(f"  volume: {mesh.volume / 1000:.1f} cm3, watertight={mesh.is_watertight}")

    out = OUT_DIR / "BrokeFeet_axial_raw.stl"
    mesh.export(out)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
