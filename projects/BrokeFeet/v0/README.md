# BrokeFeet

3D-printable teaching model of a left clubfoot skeleton, reconstructed from a
patient's CT study for pre-operative teaching.

## Goal

A physical model of a **residual congenital clubfoot (pie equinovaro)** with
subtalar coalition, for the treating surgeon to teach the planned reconstructive
procedure to students. The stated need: students lack the spatial abstraction to
read the CT images alone and need something to hold.

### Deformity (as described by the treating surgeon)

Multiplanar deformity of the left foot:

- External rotation of the leg (tibial torsion)
- **Calcaneal varus**
- **Subtalar coalition**
- **Varus of the talar neck**
- Relative forefoot adductus

### Planned procedure

Three-plane correction of the calcaneus and talar neck: **Souchet-type
osteotomy with a modified Dwyer**, plus a cut to the talar neck.

## Status

**Teaching model complete and printable. Not a surgical planning model** — see
Clinical scope below.

| | |
|---|---|
| Printable model | `BrokeFeet_teaching_axial.stl` |
| Bone-only mesh | `BrokeFeet_axial_raw.stl` (120.6 cm³, **1 body**, watertight) |
| Envelope | 95.0 × 177.5 × 144.5 mm |
| Volume | 262.6 cm³ (≈334 g in PETG) |
| Orientation | **Stands on the tibia**, foot cantilevered (see below) |
| Topology | 1 body, watertight, gates pass |
| Bone connections | 6 pins (4 mm tarsal / 2 mm phalanx) + island pillars at **2 mm** |
| Surface quality | area/volume 0.316 (compact bone 0.4–0.9); **genus 91** (was 299 before the tunnel repair) |

## Clinical scope — read before using this model

Built from **screen captures of a PACS viewer**, not from DICOM. The original
study could not be exported: the viewer
(`synapsehggb.ssconcepcion.cl/ImageViewer`) permits printing but not download
from the treating physician's account.

What that costs, concretely:

| Aspect | Status |
|---|---|
| Bone shape | **Measured.** Reconstructed from the patient's own scan. |
| Foot dimensions | **Corroborated.** Two independent series agree to 0.6 mm. |
| Forefoot adductus, rotation | **Measured** (axial plane, 0.625 mm sampling). |
| Equinus | **Measured**, present in both series, preserved in the model. |
| **Calcaneal / talar neck varus** | **Derived, not acquired.** No coronal series. |
| Tibia / fibula (proximal 23 mm) | **Measured**, but **not cross-validated** — the sagittal series does not reach this level. |
| Bone density, cortical thickness | **Not recoverable.** Window/level already applied. |

The screenshots are 8-bit grayscale with the viewer's window/level (W:3500
C:500) already baked in, so Hounsfield units are gone and segmentation is by
apparent brightness rather than density.

**Use for teaching. Do not measure osteotomy wedge angles or cut orientation on
this model.** The base carries that statement embossed in Spanish so it cannot
be separated from the object:

```
MODELO REPRESENTATIVO - NO APTO PARA PLANIFICACION
Pie izq. equinovaro - coalicion subtalar - TAC axial 0.6mm
```

If the original DICOM is obtained later, `dicom_pipeline.py` reruns the whole
reconstruction properly — see "If the DICOM arrives" below.

## Source material

Two CT series of the same left foot, captured as screenshots.

| | Sagittal | **Axial (primary)** |
|---|---|---|
| Folder | `references/brokenfeet/sagitales/` | `references/brokenfeet/axiales/` |
| Captures | 48 | 183 (182 usable) + **38 proximal** |
| Slice thickness | 2.21 mm | **0.63 mm** |
| Slice spacing | 2.0 mm | **0.625 mm** |
| In-plane scale | 0.209 mm/px | **0.179 mm/px** |
| Reconstruction | viewing series | **VOL OSEO** (bone kernel) |
| Anisotropy | 9.5 : 1 | **3.5 : 1** |
| LOC range | 121 → 30 mm | −6.63 → −119.76 mm |

### Proximal extension (ankle / distal leg)

A further **38 axial captures** extend the series upward into the ankle and
distal leg: **LOC +17.75 → −5.38 mm**, same study (accession [REDACTED-ACCESSION]), same
VOL OSEO kernel, same 0.63 mm thickness and 0.625 mm spacing. They end 1.25 mm
— exactly two slices — above where the main series begins, so the two sets are
contiguous rather than overlapping. Combined span: **+17.75 → −118.50 mm**.

Ingested by `macros/deidentify_axial_proximal.py` into
`references/brokenfeet_deid_axial_proximal/`. Two things differ from the main
series, and both would corrupt the stack if ignored:

| | Main series | Proximal |
|---|---|---|
| Viewer layout | single pane | different pane arrangement |
| Scan circle | 1262 px | **1052 px** (1.19962× zoom) |
| Scale | 5.5909 px/mm | 4.6606 px/mm → **resampled to match** |

`find_pane()` from `deidentify_axial.py` does **not** work on these captures —
it returns a clipped 3080×445 band that varies slice to slice. The scan field is
located by its own circular boundary instead, which is layout-independent. The
circle also carries the scale: both series report the same DFOV (~226 mm), so
its diameter is a physical invariant. The viewer's ruler was tried first and
rejected — at this zoom its ticks do not resolve into a uniform run.

**Validated at the junction:** the proximal series' last slice (−5.38) and the
main series' first (−6.63) are 1.25 mm apart and, after resampling, agree to
**0.5 mm in both axes** (0.3 %). A wrong scale factor would show as a ~20 %
error here, not 0.5 mm.

**LOC is read, not derived.** `deidentify_axial.py` computes each slice's LOC
from its position in the sorted file list. That assumption breaks as soon as a
second capture set exists — alphabetical order stops meaning anatomical order.
The proximal LOC values are read off the viewer overlay and recorded in
`LOC_MM`, with a guard that aborts if the capture count or an OCR-read value
disagrees.

Both series were de-identified before use: the captures carried the patient's
name, ID and date of birth burned into the pixels, and the axial ones also
included the browser window and a Windows notification popup. Cropping to the
scan pane removes all of it. **De-identified output is what every downstream
step reads**; the originals are kept only as the unprocessed source.

Scale for each series was measured from the viewer's own ruler (12 ticks over
11 cm), not assumed.

## Cross-validation

The two series were acquired in different planes on the same foot, so they are
an independent check on each other — the closest thing to ground truth
available without the DICOM. `macros/crossvalidate.py` reports:

| Metric | Axial | Sagittal | Δ |
|---|---|---|---|
| Foot length | 144.0 mm | 144.6 mm | **0.6 mm (0.4 %)** |
| Foot width | 62.0 mm | 64.8 mm | **2.8 mm (4.3 %)** |
| Adduction profile | — | — | RMS **1.01 mm** |
| Plantar profile | — | — | RMS **0.30 mm** |

The profile figures were previously reported as 3.9 mm and 9.4 mm. That was not
reconstruction error but a **comparison bug**: the two meshes do not share a Y
direction — the axial puts the heel at Y-max, the sagittal at Y-min — and both
profile functions banded from `y_min` upward regardless, so the two feet were
compared head-to-tail. It survived because the axial mesh stopped at the ankle,
which kept the wrong profiles close enough to read as error. Adding the leg made
it obvious (plantar RMS jumped to 32.3 mm with the columns plainly reversed).
`_bands_heel_to_toes()` now orients both by identifying the heel as the broader
end, and the corrected agreement is **0.3 mm on the equinus profile**.

Two independent reconstructions converging to 0.6 mm on foot length means the
scale and geometry are right. Where they differ, **the difference is the
reconstruction error — measured, not estimated.**

This check earned its keep: it caught the axial reconstruction being built
**upside down**. A Z-axis sign error produced a perfectly valid, fully
watertight mesh that no geometric gate could fault. It showed up only as
plantar and adduction profiles that mirrored the sagittal series instead of
matching it.

## Design

### Coordinate system

Per `docs/system.md` (+Z up), origin at the centre of the base's bottom face:

- **+X** medial-lateral
- **+Y** posterior-anterior (heel → toes)
- **+Z** up (plantar → dorsal)

### The deformity is preserved, never corrected

Nothing in the build levels, straightens or normalises the pose. The foot is in
equinus — its plantar surface rises ~77 mm from heel to forefoot — and that is
the point of the model.

This creates the model's main engineering problem: **a foot in equinus does not
stand on a flat plate.** An early build seated the model by bounding box, which
balanced the whole thing on its toe tips with the heel in mid-air. It passed
every topology gate and would have snapped in a student's hands.

The fix is a **support column under the hindfoot only**, sized per band to the
foot's own plantar profile. The forefoot deliberately stays in free air — that
cantilever *is* the equinus, and burying it would hide the deformity. A first
attempt at supporting every band produced a solid wall that swallowed the
skeleton (487 cm³ of block with the foot inside it); supports now stop once the
plantar surface has climbed 22 mm above the lowest point.

### Individual pins can be removed: `SKIP_PIN_BODY_VOLUMES_MM3`

Pins are skippable one at a time, matched by the **volume of the body they
attach** rather than by index — the bridging order depends on which body happens
to be nearest, so an index is not stable across parameter changes.

`SKIP_PIN_BODY_VOLUMES_MM3` is now **empty**, and the reasoning that populated
it was wrong.

It previously held `919.0`, the 5th-toe ray, on the grounds that the body
"touches the foot over a whole region (431 vertices within 3 mm), so it stays
attached through the contact itself." Re-measured: those **433 vertices are all
at 1.00 mm or more — none of them touch**. The ray was not held by contact at
all; it was held from below by an island pillar under the toe tip. Removing that
pillar (see below) dropped it off as a loose 919 mm³ body and failed the
one-piece gate.

The two exclusions are therefore mutually exclusive, and the pin is the better
one to keep: 2 mm, buried inside a 1.00 mm joint gap where only a sliver of wall
shows, versus an 8 mm pillar standing in open air under the tip of the toe.

**Keep the tolerance tight.** The phalangeal bodies cluster at 868, 919, 974 and
1051 mm³, so a loose window matches several at once: at 60 mm³ it silently
removed three pins instead of one. 15 mm³ absorbs run-to-run drift without
reaching the neighbours, which are 45 mm³ apart at the closest.

Removing a pin does not guarantee the mesh stays one piece — check `body_count`
after changing this list.

### Pillars longer than 12 mm are dropped

`_support_islands()` searches for a floor straight DOWN from the island's
centroid (`matrix[cx, cy, :k]`). When the material that actually supports the
region is offset sideways — common under the metatarsals, where a shaft
overhangs the gap between two rays — that column is empty or the nearest
material is far below, and the pillar gets built as a long rod descending into
open air. The plate filter catches these only in the assembly pass, where a base
plate exists to measure against; in the bone pass there is none, so they
survived. `MAX_PILLAR_LENGTH_MM = 12.0` catches them in both passes: a real
island support bridges a local overhang, not the height of the model.

### The pillar under the 5th toe tip is suppressed

`SKIP_PILLAR_REGIONS_MM` in `segment_axial.py` removes island pillars inside
given `(x, y, radius)` circles. It holds one entry: **(135.2, −57.8, 3.0)**, the
pillar under the 5th toe's distal phalanx.

That pillar was the only one anywhere in the toes — every other one sits at
y ≤ −104 mm, in the midfoot or hindfoot, where surrounding bone hides most of
its wall. This one stood **8 mm in open air beneath the tip of the smallest
toe**, with nothing around it, so it read as a rod stuck to the end of the
pinky. The nearest other pillar is **57.7 mm away**, so the 3 mm radius is not
delicate.

It is not a joint pin, which is why `SKIP_PIN_BODY_VOLUMES_MM3` could not remove
it — the phalanx pins sit on the 2nd–4th toes at x −107, −114 and −123. The toe
is real bone and is unchanged; only the pillar is gone.

**It cost the 5th-toe ray's pin.** That pillar was the ray's only support, so
suppressing it alone left a loose 919 mm³ body. The ray's 2 mm pin is restored
to hold it — see `SKIP_PIN_BODY_VOLUMES_MM3` above.

**Coordinates are in the scan's own frame** (before `MIRROR_X`), which is the
frame this pass computes in. The builder mirrors and rotates the model 180°
before running its own island pass, so it deliberately passes no skip regions —
these values would point somewhere else entirely there. `_support_islands()`
therefore takes `skip_regions` as an argument rather than reading the module
constant, so the caller states which frame it is in.

Trade-off: that tip is now a slicer island, the same trade `DROP_PLATE_PILLARS`
already makes 21 times over. The print checklist already calls for
slicer-generated support under the cantilevered forefoot, and this tip is inside
that region.

### Island pillars are 2 mm, not 4 mm

The pillars `_support_islands()` drops under unsupported regions were the most
visible added geometry in the model, and for a reason the joint pins do not
share: a joint pin sits inside a 0.7-1.4 mm gap between bones that nearly touch,
so only a sliver of its wall is ever in view, while a pillar **spans open air**
— typically between the metatarsals — where its whole length is exposed. At 4 mm
they read as scaffolding rods running through the forefoot, which is what shaded
views of the midfoot show. `PILLAR_DIAMETER_MM = 2.0` halves the visible width;
they are printing aids, not anatomy, so the smallest diameter that prints
reliably is the right one.

### Stair-stepping is the sampling, not a bug

Roughly **15 % of the surface area is exactly horizontal**, with a hard gap at
|nz| 0.90-0.98 — the bimodal signature of slice terracing. It follows from the
acquisition: at 0.625 mm spacing against 0.179 mm in-plane (3.5:1), a surface
lying 20° to the axial plane advances 1.7 mm laterally per slice, so a 1.7 mm
tread is the geometry the scan actually sampled.

Raising the across-slice blur to smooth it was measured and **rejected** — it
makes terracing *worse* and fuses bones:

| `SOURCE_BLUR_SIGMA` z | Components (≥1200 vox) | Terracing |
|---|---|---|
| **0.8** (current) | **7** | **15.3 %** |
| 1.2 | 6 | 16.4 % |
| 1.6 | 6 | 17.2 % |
| 2.0 | 5 | 17.9 % |

No post-hoc filter recovers detail the scan never sampled, and smoothing costs
joint separation. Accept it, or reconstruct from the DICOM.

### Bone connections are pinned to the foot, never to each other

`_bridge_bodies` grows the assembly outward, so each body it attaches becomes an
anchor for the next — which allowed a pin between two bodies that were both
already connected to the foot. `PIN_TO_MAIN_BODY_ONLY` now restricts every
anchor to the main body, so all six pins are bone-to-foot connections. The mesh
is still one piece, because anything pinned to the foot reaches everything else
through it.

In practice the affected pin joined the **fibula to the tibia**, not two
phalanges — the four phalanges (868–1051 mm³) already pinned directly to the
foot. Forcing it to the main body costs almost nothing and is anatomically
better: the fibula is 0.71 mm from the talus versus 0.50 mm from the tibia, so
the pin now sits in the ankle mortise where the bones genuinely articulate.

### Phalanx pins are 2 mm, not 4 mm

The gaps between the phalanges and the foot are only **0.7–1.0 mm**, so a 4 mm
pin is four to five times wider than the joint it crosses, and the bone is no
wider than the pin — the cylinder wall shows in the interdigital space and reads
as a bar welding one toe tip to the next.

It cannot be deleted: the 5th toe's phalanx is **1.00 mm from the foot and
4.6 mm or more from every other body**, so that pin is its only connection.
Removing it drops the toe as a loose body and fails the one-piece gate.

Bodies at or below `PHALANX_MAX_VOLUME_MM3` (3000 mm³) therefore get
`BRIDGE_DIAMETER_PHALANX_MM = 2.0` instead of 4 mm, halving the visible wall
while keeping the toe attached. The four phalangeal bodies measure 868–1051 mm³
and the next body up is the fibula at 9857 mm³, so the threshold sits in a wide
gap and is not delicate.

### Laterality: `MIRROR_X`

**Both** exported STLs are mirrored across X. `MIRROR_X` lives in
`segment_axial.py`, applied after bridging and just before export, so
`BrokeFeet_axial_raw.stl` carries it too; the builder's own `MIRROR_X` is
therefore `False` (mirroring twice would put the model back on the original
side). Applied at the operator's request.

`crossvalidate.py` compensates by mirroring the **sagittal** mesh in memory to
match, since that reconstruction is not mirrored — comparing them directly
measures the mirror rather than the reconstruction error and degrades adduction
agreement from 1.34 mm to 8.67 mm. It reads the flag from `segment_axial` rather
than duplicating it, so the two cannot drift apart. Verified: cross-validation
is unchanged after the mirror (1.34 / 0.30 mm).

**This contradicts the laterality measured from the source study**, recorded
here so the discrepancy is not lost. Measured before the mirror was applied:

- The study header reads `TAC- PIE IZQUIERDO`.
- In slice 165 the hallux — the largest forefoot bone, 2822 px — sits at 81.2 %
  across the bone span, toward high pane-X.
- The axis map is `[col, -row, slice]`: **X is not negated**, so pane column maps
  straight to mesh +X.
- The mesh peaks at X 136–140 mm, matching the un-mirrored prediction of
  138.1 mm rather than the mirrored 117.7 mm.
- The top-view render shows the hallux on one side with the four lesser toes
  stepping shorter away from it — a left foot seen from the dorsum.

On that evidence the un-mirrored geometry was already the patient's left foot.
If the printed part reads as the wrong side, set `MIRROR_X = False`.

If the printed part reads as the wrong side, set `segment_axial.MIRROR_X = False`
— that single flag reverts both STLs and the cross-validation together.

### The model stands on the leg, not on the foot

Including the proximal series changed which end should meet the plate. The
cradle sizes each support band by its height above the model's **lowest** point;
once 25 mm of tibia was added, the heel sat 24–47 mm above that minimum and fell
outside the `SUPPORT_MAX_RISE` window entirely. Support migrated to the midfoot
and forefoot, and the model balanced with its heel and ankle hanging in the air
— precisely the failure the cradle exists to prevent, reintroduced by new data
rather than by new code.

The fix is a rigid 180° rotation about X, standing the model on the **tibia's
proximal cut** — the flat cap marching cubes leaves at the scan limit, which is
a genuine bearing surface rather than a point of bone:

| | Base | Centre-of-mass offset |
|---|---|---|
| Foot down | 26.5 × 40.5 mm | 50.5 mm |
| **Leg down** | 24.0 × 41.0 mm | **24.7 mm** |

Half the overturning offset and 70 % more contact vertices. Seating recovered
from 896 to 3718 bone vertices in the cradle. The rotation is rigid, so the
equinus is untouched — only which end meets the plate changes. The foot now
cantilevers exactly as the deformity requires, and the vertical leg gives the
viewer the reference axis the earlier model lacked. Controlled by
`STAND_ON_LEG`.

### No vertical pillars down to the plate

`_support_islands()` ties down regions a slicer would see as floating by
dropping a vertical pillar from each island to the material beneath it. Where
there is no material beneath — under the cantilevered forefoot — that pillar ran
all the way to the build plate, propping up exactly the part of the foot the
model exists to leave unsupported.

Those are now suppressed (`DROP_PLATE_PILLARS` in `segment_axial.py`): a pillar
is built only when it lands on **bone**. Current counts are 4 kept / 21 dropped
in the bone pass (plus 1 dropped by `SKIP_PILLAR_REGIONS_MM`), and 9 kept /
18 dropped in the assembly pass. (Before the tunnel repair these were 21 and
25 kept — most of those islands were shelves of perforated bone that the repair
removed at the source.)

The plate reference is passed in explicitly as `plate_top_z=BASE_THICKNESS`
rather than inferred from the mesh bounds. A pillar lands on the plate's **top**
face (z = 8.0), while the bounds give its underside (z ≈ 0) — inferring it
matched nothing and the filter reported `0 dropped` while doing nothing at all.

**Trade-off:** those islands are now genuinely unsupported. The islands were
detected because a slicer once rejected this model as having floating pieces, so
the cantilevered forefoot relies on **slicer-generated support material** —
which the print checklist already calls for. Confirm support under the
metatarsals when slicing.

### Bones joined into one piece — in `_raw`, not downstream

The reconstruction resolves the joint spaces, so the phalanges come out as
free-floating bodies: correct anatomy, unusable as a model. Connections are
therefore made in `segment_axial.py`, so **`BrokeFeet_axial_raw.stl` is itself
a single connected solid**. An earlier version added them only in the builder,
which left the base mesh with 7 loose bodies and phalanges floating in space.

Each separated body is pinned to whichever already-connected body it is nearest,
with a **4 mm diameter cylinder**.

Diameter was chosen by measuring, not by eye. The gaps between bodies are only
**0.5–1.0 mm** — the bones nearly touch — so each pin is a short stub rather
than a rod, and diameter costs almost nothing:

| Pin diameter | Material added | % of bone volume |
|---|---|---|
| 2 mm | 26.0 mm³ | 0.03 % |
| 3 mm | 65.6 mm³ | 0.07 % |
| **4 mm** | 131.7 mm³ | **0.14 %** |

The thinnest bones being pinned are phalanges whose rays measure 11–13.5 mm
across, so a 4 mm pin sits well inside their girth and does not alter the
silhouette. 2 mm was tried first and is structurally flimsy for a model that
gets handled in a classroom.

The model is meant to be rigid, so these are fixed pins, not articulations.
Bones that are *already* fused — including the patient's subtalar coalition —
are left untouched; pins are added only where genuinely separate bodies remain.

### Threshold: solid bone versus separated bone

The single most consequential parameter is `BONE_THRESHOLD` in
`segment_axial.py`, and it is a genuine trade-off with no free lunch:

| Threshold | Result |
|---|---|
| 130 | Bones stay separate, but hollow out. Only the thin adolescent cortex passes; being porous, `fill_holes` cannot seal it, so bones come out eaten away — a spongy texture. |
| **115** (current) | Bones fill as solids and the sponge disappears, but more midfoot bones connect to each other. |
| 105–110 | Solid, but the midfoot fuses into one mass. |

### Filling bones the threshold cannot reach

Threshold alone did not remove the sponge. Measured in the source slices, the
**calcaneus and cuboid interiors sit at intensity 82–103** — below the 115
needed to keep skin out, and barely above soft tissue. Their cortical rims are
also broken in places, so the interior leaks outward and `binary_fill_holes`
has nothing enclosed to work on. Those bones segmented as speckled rims: the
sponge visible ~57 mm down the model.

No global threshold fixes this, because bone interior and soft tissue overlap in
brightness. What separates them is **enclosure**, not intensity. So
`_fill_bone_interiors()` seals each cortical outline on a scratch copy, fills
it, erodes back by the same radius, then clips the result to a permissive
intensity floor so a broken rim cannot leak the fill into surrounding tissue.
The closing is never written back, so it cannot bridge joint spaces.

| Metric | Before | After |
|---|---|---|
| Global area/volume | 0.643 | **0.499** |
| 57 mm band | 0.790 | **0.573** |

`CORTEX_SEAL_RADIUS` has a sharp cliff — **3 → 9 bodies, 4 → 5, 5 → the whole
foot collapses into one 98 cm³ mass**. It is set to 3. Raising it produces
better sponge numbers (0.353 at radius 8) and a strictly worse model, with every
joint smoothed away. Do not increase it.

### The remaining sponge is across slices, not within them

`_fill_bone_interiors()` works slice by slice, so it can only see enclosure
in-plane — and measurement shows that is no longer where the defect lives. Mask
boundary transitions per bone voxel, by axis:

| Band | z | y | x |
|---|---|---|---|
| Z 15.9–29.6 | 0.225 | 0.058 | 0.074 |
| Z 56.9–70.5 | 0.315 | 0.050 | 0.055 |
| Z 84.2–138.8 (leg) | 0.054 | 0.021 | 0.023 |

The foot's cross-sections are already as smooth as the leg's in-plane; the mask
is **4–6× more ragged across slices**. Sealing the outline harder cannot help —
a probe closing each slice's outline at radius 8 and filling recovers ~0 mm² on
most midfoot bones, because no unfilled in-plane hole remains.

What is left are **89,958 voxels that are bone in slice k−1 and k+1 but empty at
k**, at intensity 86–113 (mean 101.7) — the trabecular range, just under the 115
threshold. Bone does not have 0.625 mm holes with solid bone on both faces.

`_fill_axial_pits()` closes them, gated on **same-component enclosure**: a void
is filled only where the nearest bone above and below belong to the same 3D
connected component. A trabecular pit is inside one bone; a joint space has a
different bone on each side. Because the rule only adds material inside an
already-connected body, it **cannot create a new connection between two bodies**.

Gating on intensity alone was tried first and is unsafe: it welded the
metatarsals to the tarsus and the fibula to the tibia (12 components → 7).
The same-component gate holds at 12 for every span tested.

| Metric | Before | After |
|---|---|---|
| Volume | 114.4 cm³ | 115.1 cm³ |
| Global area/volume | 0.451 | **0.445** |
| Bodies before bridging | 7 | **7** |
| Tibiofibular gap | 0.950 mm | **0.950 mm** |
| Adduction RMS | 1.34 mm | **1.32 mm** |
| **Genus (through-holes)** | 340 | **330** |

Per-band area/volume improves or holds everywhere — no band traded against
another:

| Band | Before | After |
|---|---|---|
| Z 2.2–15.9 | 0.627 | 0.623 |
| Z 15.9–29.6 | 0.566 | 0.564 |
| Z 29.6–43.2 | 0.480 | 0.478 |
| Z 43.2–56.9 | 0.554 | 0.545 |
| Z 56.9–70.5 | 0.427 | 0.415 |
| Z 70.5–84.2 | 0.533 | 0.520 |
| Z 84.2–138.8 (leg) | 0.225 | 0.225 |

**This is a partial fix, and the genus says so.** Only 10 of 340 through-holes
closed. Most of the area/volume gain is surface smoothing, not perforations
being sealed — which is exactly the illusion area/volume is prone to, so genus
is the metric to trust here. The remaining ~300 tunnels are concentrated in
**Z 43–84 mm (talus and calcaneus), not the midfoot**: genus 93.5 / 105 / 105 in
the three hindfoot bands versus 9–27 across the whole forefoot. Anyone
continuing this work should start there, and should measure genus rather than
area/volume.

### The hindfoot tunnels: where they come from, and what does NOT fix them

Decomposing the topology by stage settles where the defect is born. Using
`b1 = b0 + b2 − χ` (components, cavities, Euler number):

| Stage | Components | Cavities | **Tunnels** |
|---|---|---|---|
| Segmentation mask (0.179 × 0.179 × 0.625) | 12 | **0** | **767** |
| Isotropic grid (0.5 mm) | 33 | 22 | **216** |

Two things follow, and both contradict the obvious plan:

1. **The mask has zero enclosed cavities** — `segment()` already fills them. So
   "fill the enclosed cavities" cannot be the fix: on the finished mesh the
   cavities are only ~24 mm³ across 22 voids, and filling every one removes
   **15 tunnels of 216**.
2. **The tunnels are inherited from the mask, not created by meshing.** They are
   voids that leak sideways to the outside, so `binary_fill_holes` cannot see
   them at any stage.

`to_isotropic()` now fills the cavities the resample itself opens (20 of the 22
are in the hindfoot, where a 0.179 mm trabecular strut cannot survive a 0.5 mm
sample). It is safe — a cavity that does not reach the grid boundary is enclosed
within one bone, whereas a joint space always opens to the outside — and it
costs 24 mm³, 0.02 % of bone volume. It is also **nearly worthless against the
sponge**: whole-mesh genus 330 → 329.

**Rejected: per-component axis fill.** Filling voids enclosed along any axis,
computed on each component in isolation (so it provably cannot bridge two
bones), cuts mask tunnels **767 → 262** and holds the component count at 12.
It is still wrong. Measuring the outer silhouette shows **99.76 % of the added
material lies outside the original per-slice outline**, and the outline area
grows **+27.9 %**, nearly doubling on some slices. It is not filling tunnels
through bone — it is spanning the concave spaces *between* bones inside the
already-fused tarsal mass, welding the hindfoot solid. Constraining it by depth
(local bone fraction ≥ 0.55–0.85) keeps the silhouette but stops closing
tunnels — 767 → 652 at best, and 771 at one setting, because half-filling a
tunnel splits it into several.

**Rejected: lowering `ISO_LEVEL`.** 0.40 → 0.36 closes marginally more tunnels
(216 → 207) while fusing bones: 33 components → 26. Same trade the
`CORTEX_SEAL_RADIUS` cliff makes, for less benefit.

### Closing tunnels without moving the silhouette

The methods above all fail for one reason: they try to *fill*, and a tunnel is
not enclosed. It leaks sideways to the outside, so `binary_fill_holes` cannot
see it, and once the tarsal mass is a single component with zero cavities there
is nothing left for any fill to find.

A **closing** can see a tunnel. The reason this project rejected closing is
that it also bridges joint spaces — but that verdict was measured on an
*unclipped* closing of the 2D mask. Separating **proposing** from **permitting**
removes the failure mode:

```python
env = ndimage.binary_fill_holes(plane)              # what this slice spans
out = plane | (binary_closing(plane, elem) & env)   # nothing outside it allowed
```

A tunnel through a bone lies **inside** that bone's own outline, so it is
filled. Material spanning the concave space **between** two bones lies outside
the outline, so it is discarded — the two bones cannot be joined. This is the
constraint the rejected per-component axis fill lacked, and it is why that one
grew the silhouette 27.9 % while this one does not move it at all.

`_close_within_envelope()` runs on the isotropic grid, after the cavity fill.
The guarantee is verified rather than argued:

| Check | Result |
|---|---|
| Axial slices with a changed outer outline | **0 of 273** |
| Components on the iso grid | **33 → 33** |
| Per-slice area growth | mean 0.20 %, p90 0.46 %, max 6.73 % |
| Material added | **+0.25 %** (0.28 cm³) |

Element size swept at the 0.5 mm pitch — 5×5 (2.5 mm) is the knee, and 7×7 buys
one tunnel for 28 % more material:

| Element | Tunnels (iso) | Material |
|---|---|---|
| 3×3 | 201 → 187 | +0.12 % |
| **5×5** | 201 → **183** | **+0.25 %** |
| 7×7 | 201 → 182 | +0.32 % |

Applied **globally**, not restricted to the hindfoot: measured at +0.25 % versus
+0.24 % for a Z 43–84 restriction with identical per-band tunnel counts. The leg
holds at 2 tunnels either way, so a band restriction buys nothing.

**One axis only.** Running the same clipped pass along all three axes closes far
more tunnels (201 → 124) but each axis admits material the others' envelopes
would forbid, and components fall **33 → 25** — bones fusing. The per-axis
guarantee does not survive composition.

Result on the exported mesh: **genus 340 → 299**, hindfoot bands −30.0 and
−18.5, cross-validation *improved* to 1.29 mm adduction.

### The tunnel repair: anatomy as the prior, not the data

The section below this one records the earlier verdict: the remaining tunnels
could not be closed without the DICOM, because brightness cannot distinguish a
trabecular void from an interosseous space. That verdict was correct **about
the data** and beside the point **about the anatomy**: no talus or calcaneus
has open through-tunnels at the millimetre scale. Every one of those openings
is a segmentation dropout. For a teaching model already embossed NO APTO PARA
PLANIFICACION, anatomy is a legitimate prior — the engineering question was
only how to close them *without* being able to tell them apart from joints
locally.

The answer (`_close_tunnels_gated()` in `segment_axial.py`) is to stop
trying to classify voxels and instead make the dangerous outcome impossible:

- the envelope-clipped closing runs along **all three axes** — exactly the
  variant the earlier sweep rejected (components 33 → 25, bones fusing) —
- and every added blob (26-connected) is **discarded whole if it touches more
  than one bone component**, so fusing two bones is impossible by
  construction, not by hope. The pass aborts if the component count moves.

Element 5 first (trabecular pitting), then 9 (the wide crescent mouths), each
iterated to convergence, then a boundary-connected cavity fill for voids the
new roof encloses.

It first shipped restricted to the hindfoot band (Z 43–84 mm) out of caution.
The slicer then showed the same defect class on the metatarsal shafts —
windows into hollow shaft interiors, the calcaneus story again at smaller
scale — so it was rerun globally: forefoot tunnels 7 → 0 for +0.48 cm³ more,
gate still holding. The band was caution, not necessity
(`TUNNEL_BAND_MM = None`).

Measured on the pipeline's own iso grid: tunnels **182 → 44** (hindfoot bands
41/49/66 → **6/2/31**, forefoot 3/1/3 → 0/0/0), components **33 → 33**, outer
contour **unchanged to the pixel** in the filled projections along all three
axes. The gate threw away 15.2 cm³ of proposals that would have bridged
bones — more than twice what it kept (+6.7 cm³, +5.9 %). Most of the kept
material is the hollow calcaneal interior at Z ~53–60 mm, the documented
"sponge ~57 mm down", which no in-plane fill could reach because the cortical
rim is broken in-plane. On the exported meshes: teaching-model genus
**299 → 91**, area/volume 0.443 → 0.316, and cross-validation *improved*
(adduction RMS 1.29 → 1.01 mm, plantar 0.30 mm unchanged). The bone-pass
island pillars fell 21 → 4, because most "islands" were shelves of perforated
bone that no longer exist.

Depth-shaded before/after renders confirm the crescent openings and the pit
cluster on the medial tarsal wall are closed while every joint fissure line
survives. The ~44 remaining tunnels are dominated by the ankle region
(Z 70–84: 31), where the gate deliberately refuses anything that approaches a
second bone — the price of the guarantee, and the right trade.

**Pillars and craters co-locate; the pillars do not cause the craters.** The
operator observed that every "crater" in the sliced model had a support pillar
in or under it and inferred that the boolean merge was cutting bone to insert
the pillar. Checked directly: every merge in the pipeline is a union (which
only adds material), and ray-casting each pillar axis on the finished model
shows every tip buried 10–30 mm under bone — nothing pierces a surface. The
real coupling runs the other way: an island forms exactly at a broken shelf's
overhanging rim, so the island detector planted a pillar at every crater.
Both were symptoms of the same segmentation dropout, which is why healing the
surfaces removed most pillars (21 → 4) without touching the pillar code.

### Locating a defect: the bottleneck was naming it, not finding it

An STL is one undifferentiated shell, so a defect visible in a viewer has no
name. Every report arrived as a cropped screenshot with no anchor, and
localising it afterwards cost more effort than the repair — one session was
spent analysing holes that were never the ones being pointed at.

`locate/` fixes that, and it should be the first thing used when a defect is
spotted:

- **`locate_*.png`** — the six orthogonal views, each the whole model on a
  **10 mm grid labelled every 50 mm**, axes named in the header, depth-shaded so
  craters and rods read as recessed or raised. Two views give a full position;
  often one is enough.
- **`BrokeFeet_grid_cage.stl`** — a tick cage (10 mm blocks, 50 mm doubles) to
  load *alongside* the model with no repositioning, for reading coordinates in
  the viewer directly.

Both regenerate from the current mesh (`macros/locate_views.py`,
`macros/make_locator.py`) and rescale to whatever it measures.

See `locate/README_LOCATE.md` for the landmark table (which Y/Z range is
tarsus, metatarsal, ankle).

### The five defects the operator located: all craters, none enclosed

Picked in MeshLab with **Get Point Info**, several clicked faces bounding each
region. This is the first time the reported defects were located rather than
inferred from screenshots, and it settled their nature immediately.

| Hole | Centre (X, Y, Z) | Notch volume | Depth | Open to outside |
|---|---|---|---|---|
| **1** | −114.8, −125.0, 67.5 | **516 mm³** | 1.58 mm | 100 % |
| 2 | −106.5, −135.5, 73.5 | 65 mm³ | 1.00 mm | 100 % |
| 3 | −98.4, −112.9, 70.0 | 87 mm³ | 1.46 mm | 100 % |
| **4** | −126.2, −129.5, 73.5 | **286 mm³** | 1.46 mm | 100 % |
| 5 | −130.0, −138.1, 56.4 | 152 mm³ | 1.50 mm | 100 % |

All five lie in **Y −113…−138, Z 56…74** — tarsus, talus and calcaneus, the
same region the genus measurement already identified. Total ~1.1 cm³, under 1 %
of bone volume.

**Every one is a crater, not a cavity**: 100 % of the empty space in each
window reaches the exterior, and the mesh contains **zero enclosed cavities**
anywhere. They are 1.0–1.6 mm deep — cortical wall eaten thin by segmentation
dropout, not holes punched through bone.

A first classifier reported them as "inside ONE bone — safe to fill". That was
**wrong**: it asked how many bones were in the window and answered one, which
says nothing about enclosure. Rendering the slices showed open notches with the
picked box sitting in black exterior space. The measured "void volume" of
0.0–0.1 mm³ for holes 1 and 2 was the tell — there was nothing enclosed to
measure. *Ask whether the void is enclosed, not how many bones are nearby.*

### Patching a named crater works, and costs a support pillar — rejected

The global crater passes fail because a rule that must be safe *everywhere* is
forced to be weak. A **named** crater is a different problem: inside a known box
the fill can be aggressive and touch nothing else, and the one thing that must
not happen — bridging two real bones — is verified directly.

Implemented as `_patch_named_craters()` and measured on the operator's traced
463 mm³ crater. Only one radius leaves the topology untouched, so it is not a
smooth trade:

| radius | added | tunnels (45 base) | crater removed |
|---|---|---|---|
| 1.0 mm | 54 mm³ | 50 (+5) | 11.7 % |
| 1.5 mm | 100 mm³ | 46 (+1) | 21.6 % |
| 2.0 mm | 144 mm³ | 47 (+2) | 31.1 % |
| **2.5 mm** | **168 mm³** | **45 (+0)** | **36.4 %** |
| 3.0 mm | 139 mm³ | 48 (+3) | 30.0 % |

On the full pipeline it held every gate — grid tunnels 45, real bones 8,
1 body, watertight, cross-validation *improved* to 1.00 mm adduction with
plantar unchanged at 0.30 mm.

**It is off anyway** (`PATCH_NAMED_CRATERS = False`). Filling the crater
created new bone surface, `_support_islands()` read that surface as a floating
island, and planted a **5th support pillar** at (111.8, −126.8) — exported
genus 79 → 85, all of it the pillar. Trading a 36 %-reduced crater for a
visible 2 mm rod in open air is a bad deal on a teaching model, and the
operator rejected it on sight.

Anything that adds material near an overhang must be checked against the pillar
count, not only against tunnels and components. The two passes interact and
neither knows about the other.

**A counting error to avoid.** The first measurement of this crater reported
components 33 → 31 and read as *three bones fusing*, which killed the idea for
an hour. The window in fact holds **one 73.85 cm³ bone plus specks of 26 and 1
voxels** — the closing was absorbing specks. Count components above a volume
floor (`CRATER_MIN_BONE_MM3`), never raw.

### Local accretion fill: also rejected, and a warning about proxy metrics

Closing fails because it *roofs* a dent. The obvious alternative is to fill
from the floor up: add any empty voxel that (a) touches bone by a face and
(b) sees bone within a short ray on ≥5 of the 6 axis directions, iterated to
convergence. A joint space — bone on two opposing sides only — never satisfies
the rule, so it looked structurally safe.

**Measured on the exported mesh it looked good: genus 174 → 39, watertight,
craters 13–41 % removed.** Measured on the pipeline's own iso grid, the same
method removes **at most 4.0 % of any crater**:

| sides | ray | passes | added | tunnels (45 base) | best crater removal |
|---|---|---|---|---|---|
| 5 | 1.0 mm | 8 | 0.156 cm³ | 41 (−4) | 3.6 % |
| 5 | 1.5 mm | 4 | 0.236 cm³ | **95 (+50)** | 4.0 % |
| 6 | 2.0 mm | 8 | 0.136 cm³ | 45 (0) | 2.4 % |

The exported-mesh figures were inflated by re-voxelisation — **the same proxy
error recorded in "A failed fix"**. A crater that reads as a fillable concavity
in a re-voxelisation of the output is not one in the grid that generated it.
Two independent measurements of the same idea, five hours apart, both fooled by
the same substitution.

Three implementation traps, each initially misread:

1. **"20 bodies" was not fracturing.** Adding material cannot disconnect a
   solid. The rule was depositing **debris in mid-air** — a voxel can see bone
   within 2 mm on 5 sides while touching none of it (226 floating voxels, 96
   single-voxel specks in one pass). Every speck becomes a body.
2. **Contact must be face adjacency, not corner.** Corner-touching voxels are
   one component under 26-connectivity but marching cubes renders them as
   separate surfaces: a "1 component" grid meshed to 17 non-watertight bodies.
3. **The iso grid's axis order is not the mesh's.** `main()` maps
   `verts = [v2, -v1, v0]` and then `MIRROR_X`, so index→mm negates two axes.
   A first sweep derived the scale by matching bounding boxes, got
   `[0.23, 0.50, 1.09]` instead of `[0.5, 0.5, 0.5]`, and reported 0.0 mm³ for
   every crater. A window built as `a=to_idx(lo), b=to_idx(hi)` is also empty
   on the negated axes — take min/max per axis after mapping.

### The visible craters cannot be closed by closing — measured and rejected

The defects the operator circles in a shaded render are **craters**: dents open
to the outer surface. They survive a repair that took genus 340 → 91 for a
structural reason, not an oversight. Both existing passes clip every proposal
to each slice's **filled outline**, and a crater lies *outside* that outline —
the one place those passes are built never to touch. They were never
candidates.

`_close_craters_gated()` proposes them with an unclipped 3D closing and relies
on the existing component gate for safety. It is **off** (`CRATER_REPAIR =
False`), because it does not work:

| Element | Added | Tunnels (45 baseline) | Δ |
|---|---|---|---|
| 0.5 mm | 0.65 cm³ | 76 | **+31** |
| 1.0 mm | 1.20 cm³ | 53 | +8 |
| **1.5 mm** | 0.67 cm³ | **42** | **−3** |
| 2.0 mm | 0.51 cm³ | 46 | +1 |
| 3.0 mm | 0.54 cm³ | 44 | −1 |

Roofing a crater converts an open dent into a **covered channel**, so it trades
a visible defect for a tunnel roughly one-for-one. The best case is −3 for
+0.67 cm³ and the series is not monotonic, so that is noise. Components held at
33 throughout — the pass is safe, just useless.

**The gate needed a second guarantee.** `_gate_to_single_component()` only
forbids *joining* two bones. Adding material can also *split* one: roofing a
crater seals a narrow neck of background and pinches a component in two. First
run aborted at **33 → 36 components**. Acceptance is now also conditioned on
the count holding, per blob where a whole sweep would fail. The abort worked as
designed and caught it before any mesh was written.

Kept in the file, disabled, so the sweep is not repeated. These craters are
real and visible — they are simply not fixable by a morphological closing, and
hand repair is the remaining option.

### Hand-repair export, and why "enclosed" does not mean "defect"

`macros/prep_sculpt.py` exports the bone mesh at full resolution for manual
patching, plus a marker sphere sitting on each hole and a CSV of coordinates.
See `sculpt/README_SCULPT.md`.

**Parametric CAD is the wrong tool for this and no export format fixes it.**
Fusion 360 was tried first: a CT reconstruction is a triangle mesh with no
faces, edges or features, so Fusion imports it as a mesh body and converting it
to a solid yields one enormous freeform surface that cannot meaningfully be
edited. STL, STEP, `.f3d` and `.FCStd` would all carry the same unstructured
geometry — `.f3d` additionally cannot be written outside Autodesk's own
software. Mesh sculptors (Meshmixer, Blender) operate on the triangles directly
and are the right class of tool.

Finding the holes exposed a trap worth recording. The obvious detector — a void
that `binary_fill_holes` closes on any of the three axes — reports **31 sites,
4710 mm³**. Two of those, holding **63 % of that volume**, are joint spaces, and
filling them would weld the ankle.

They evade the obvious tests:

- **Enclosure fails.** Ray-casting 26 directions from each centroid reported
  every one of the 31 as "inside bone", the two joints included, at median
  distance 0.50 mm. The centroid of a thin void wrapping *around* a bone lands
  in bone, so every ray hits instantly. Another good metric on the wrong object.
- **Aspect ratio fails.** The ankle site's extent is 25.5 × 52.5 × 29.5 mm — not
  flat, because it curves around the mortise.

What does separate them is **how much of its own bounding box the void fills**.
A cavity inside one bone is a compact blob; a joint space is a thin rind with a
large bounding box and little of it occupied. The ankle site fills 6 %.

Confirmed by rendering slices rather than trusting the number: the excluded
sites show red material wrapping around and between two distinct grey bones,
while the kept 1477 mm³ site shows red filling the inside of a single bone with
an intact cortical rim — the documented hollow calcaneus, 85 % of the material
actually worth adding.

This is the same lesson as the rejected per-component fill: a method that
closes more holes while quietly spanning the space *between* bones scores well
and produces a worse model.

### The earlier verdict, kept for the record (superseded above)

Genus was down 12 % and the fine pitting across the calcaneal body had largely
closed, but a shaded render of the talus and calcaneus at Z 43–84 still showed
**distinct tunnels** — the round and crescent-shaped openings through the tarsal
body were essentially unchanged.

Those were wider than the 2.5 mm element and genuinely open
through the bone in the axial plane, so no per-slice method bounded by the
silhouette could close them. Doing so requires distinguishing a trabecular void
from an interosseous space, which this 8-bit window/levelled source may not
support: the two overlap in brightness, and the tarsal mass is already one
connected component, so "inside one bone" stops being a usable constraint
exactly where the tunnels are. The DICOM would resolve it — but as the section
above shows, closing them safely never actually required deciding voxel by
voxel; it required making the failure mode structurally impossible.

### A failed fix, recorded so it is not retried

`MAX_FILLED_HOLE_MM2` fills in-plane holes up to 28 mm² outright in
`_close_within_envelope()`. **It does not work, and the constant is retained only
because it is harmless** (+0.27 % material).

The reasoning that led to it was sound and the measurement behind it was not:
389 of the 518 in-plane holes measure under 1.1 mm across — far below any
anatomical feature and below a print nozzle — and a bench test on the exported
mesh predicted genus 333 → 232. Implemented, it delivered **301 → 300**.

The bench test measured a different object than the pipeline produces. It
voxelised the *exported mesh* at 0.5 mm and re-filled it, where those holes read
as enclosed; in the pipeline's own isotropic grid the same holes are **open in
3D**, so `binary_fill_holes` cannot see them. A hole that is enclosed in a
re-voxelisation of a mesh is not necessarily enclosed in the grid that generated
that mesh.

The lesson generalises: **validate a proposed fix on the actual pipeline
intermediate, not on a re-derived proxy of its output.**

At 115 a 54 cm³ body spans much of the midfoot. Part of that is the patient's
real subtalar coalition; part is joint spaces narrower than the 0.625 mm
sampling. **The reconstruction cannot distinguish the two**, so the model shows
less midfoot joint separation than the anatomy has. Adequate for teaching the
deformity and the coalition; not for counting individual midfoot bones.

Two smoothing approaches were tried and rejected before settling on a Gaussian
blur of the occupancy field:

- **Morphological closing** (on the 2D mask, **unclipped**) bridges any gap
  narrower than its structuring element. The joint spaces here are narrower than
  the cortical pores it was meant to seal, so it welded the midfoot into a
  66 cm³ mass. *This verdict applies to unclipped closing on the mask only* — a
  closing clipped to each slice's filled outline is a different operation and is
  used in `to_isotropic()`; see "Closing tunnels without moving the silhouette".
- **Median filtering** is non-linear on a binary mask and *severs* thin
  structures rather than smoothing them. Every window size fragmented the stack
  (21 components → 92–133) and destroyed the distal phalanges, which are only
  ~8 mm across.

## Files

| File | Description |
|---|---|
| `macros/deidentify.py` | Strips PHI from the 48 sagittal captures |
| `macros/deidentify_axial.py` | Strips PHI, browser chrome and notification popup from the 182 axial captures |
| `macros/deidentify_axial_proximal.py` | Strips PHI from the 38 proximal captures (ankle/distal leg); detects the scan field by its circle and rescales to the main series |
| `macros/slice_positions.py` | Sagittal slice geometry (LOC values, scale) |
| `macros/segment_bone.py` | Sagittal reconstruction — kept as the cross-check |
| `macros/segment_axial.py` | **Primary reconstruction** from the axial stack |
| `macros/crossvalidate.py` | Compares the two reconstructions, reports real error |
| `macros/prep_sculpt.py` | Exports the bone mesh + located repair markers for hand-patching in a mesh sculptor |
| `macros/mark_operator_craters.py` | Marker spheres for the operator-located craters and for every pillar and pin, for hand editing |
| `macros/export_step.py` | STEP + 3MF export at several face budgets, for editing in CAD |
| `cad/README_CAD.md` | Which STEP level to open, and why build123d cannot rebuild the bone |
| `macros/locate_views.py` | Six labelled 10 mm-grid renders, for reading a defect's coordinates off a screenshot |
| `macros/make_locator.py` | Grid cage + axis marker STLs, to load alongside the model in a viewer |
| `macros/brokefeet_axial_b123d.py` | **Builds the printable model** |
| `macros/brokefeet_b123d.py` | Earlier sagittal-based build (superseded) |
| `BrokeFeet_axial_raw.stl` | Bone-only mesh, 24 bones |
| `BrokeFeet_teaching_axial.stl` | Printable teaching model |
| `ForOpus.md` | Why the "needs DICOM" block was beatable: reframing from voxel classification to structural guarantees |
| `sculpt/README_SCULPT.md` | Hand-repair guide: which holes to patch, which two must **not** be filled, and the gates to re-check |
| `locate/README_LOCATE.md` | **How to report where a defect is** — labelled grid renders and a loadable coordinate cage |

## How this session's work was done — agents and tooling

Recorded so the reasoning behind the current parameters is auditable, and so the
rejected approaches are not retried.

### Agent created: `bone-morphologist`

`.claude/agents/bone-morphologist.md` — a trauma & orthopaedic surgeon
specialising in osseous morphology, scoped to one job: **close holes that
anatomy says should not be there, while leaving every real space untouched.**

It was given this project's hard-won constraints up front, so it could not
re-walk paths already known to fail:

- the measured `CORTEX_SEAL_RADIUS` cliff (3 → 9 bodies, 4 → 5, 5 → the foot
  collapses into one 98 cm³ mass)
- morphological closing on the mask and median filtering, both already tried
  and rejected here with recorded reasons
- the rule that a better global metric is **not** the goal: radius 8 scores
  better on area/volume (0.353) and produces a strictly worse model
- the distinction that matters — bone interior and soft tissue overlap in
  brightness, so what separates them is **enclosure**, not intensity

Not for authoring geometry (`cad-designer`), tolerances or structural sizing
(`print-tolerance-expert`), or slice-to-measurement work (`reference-analyst`).

### What the agent contributed, across three runs

| Run | Target | Outcome |
|---|---|---|
| 1 | Midfoot sponge | `_fill_axial_pits()`. Genus 340 → 330 — **reported as largely a negative result** |
| 2 | Hindfoot tunnels | No improvement. Established tunnels are **inherited from the mask**, not created downstream |
| 3 | Silhouette-clipped closing | `_close_within_envelope()`. Genus → 299, 0 of 273 slice outlines changed |

Its most valuable outputs were the **negative** ones, and two premise
corrections that redirected the whole effort:

1. **The damage is not in the midfoot.** Measured genus put 310 of 330 tunnels
   in Z 43–84 mm — the talus and calcaneus. The original task premise was wrong.
2. **There are zero enclosed cavities.** Every defect leaks sideways to the
   outside, so no fill-based method can see them at any stage. This killed the
   cavity-filling approach outright.
3. It **rejected a per-component fill of its own** that closed 66 % of tunnels,
   because 99.76 % of the added material lay outside the original per-slice
   outline and silhouette area grew +27.9 % — it was welding the hindfoot solid
   while reporting an excellent genus number.

That last one is the failure mode this project keeps hitting, and the reason
**genus replaced area/volume** as the tracked metric: area/volume improved twice
while the visible sponge did not.

### Skills used

None. No skill from the available set applied to this work: it is
measurement-driven CAD repair, not visualisation (`dataviz`), artifact
publishing (`artifact-*`), harness configuration (`update-config`), or review
(`code-review`, `simplify`). The verification loop used this repo's own tools —
`tools/render_check.py` and `macros/crossvalidate.py` — as `CLAUDE.md` requires.

### Method that actually worked

Every claim in this session was settled by measurement against the source, not
by inspection of the code:

- laterality — read from the study header and the hallux position in slice 165,
  not assumed from the axis map
- the proximal series' scale — from the scan circle diameter, cross-checked at
  the seam to 0.5 mm
- the pillar and pin diameters — from the measured gaps they span
- terracing — from the face-normal distribution, then a parameter sweep that
  **disproved** the proposed fix

Three defects were found only by the user's own shaded screenshots after the
numeric gates had passed: the exposed pillars, the free-hanging rod under the
metatarsals, and the sub-millimetre pitting. That is the pattern this project's
history predicts, and the reason `CLAUDE.md` insists on looking at renders.

## How to regenerate

```
pip install build123d ocp-vscode trimesh manifold3d scikit-image scipy pillow

python BrokeFeet\macros\deidentify_axial.py
python BrokeFeet\macros\deidentify_axial_proximal.py
python BrokeFeet\macros\segment_axial.py
python BrokeFeet\macros\brokefeet_axial_b123d.py
```

`segment_axial.py` consumes both de-identified stacks: 182 main + 2 interpolated
across the uncaptured seam + 38 proximal = **222 slices**. Run both de-identify
scripts before it, or the proximal extension is silently omitted (it warns and
builds from the main series alone).

Verify (required after any geometry change):

```
python tools\render_check.py BrokeFeet\BrokeFeet_teaching_axial.stl --views iso right
python BrokeFeet\macros\crossvalidate.py
```

**Open the renders and look at them.** Every defect in this project's history —
the upside-down reconstruction, the soft-tissue blob, the buried skeleton, the
model balanced on its toes — passed the numeric gates and was caught only by
looking.

## Verification checklist before printing

- [ ] **Toe completeness** — all five rays must reach a distal phalanx. The
      distal phalanges of the 2nd, 4th and 5th toes have been lost twice: once
      to a size filter set above their real volume (64–113 mm³), and once to a
      median filter that severed them. Verify by plotting the forefoot from
      above, not by counting bodies (adjacent bones may be fused).
- [ ] **Support contact** — heel supported, forefoot cantilevered. Confirm the
      model does not balance on a point.
- [ ] **Print orientation** — the cantilevered forefoot needs support material.
      Consider printing base-down with tree supports under the metatarsals.
- [ ] **Thin phalanges** — distal phalanges are ~8 mm across; check they survive
      slicing at the chosen layer height and are not dropped as too thin.
- [ ] **Embossed text legibility** — 0.6 mm relief; verify it resolves at the
      chosen layer height, since it carries the model's clinical scope.

## If the DICOM arrives

`macros/dicom_pipeline.py` reruns the reconstruction from the original study
with real Hounsfield units, correct slice geometry and all acquired planes.
That produces a genuine patient-specific model suitable for planning — at which
point the embossed warning should be removed and the model re-validated.

Request to the PACS administrator, if it becomes possible:

> Exportación DICOM del estudio [REDACTED-ACCESSION], paciente [REDACTED-PATIENT-ID] — todas las
> series, incluida la reconstrucción de cortes finos con kernel óseo y las
> series axial y coronal. Para planificación quirúrgica mediante impresión 3D.
