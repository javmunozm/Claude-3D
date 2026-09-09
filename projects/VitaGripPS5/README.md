# VitaGripPS5

A PS5-style grip for the Sony PS Vita **PCH-1000**, built in **Blender** as a
swept tube: two drooping DualSense-like grips joined by a slim bar that runs
low across the console's rear. The console's underside **rests on that bar**,
its corners are captured by the grips at each end, and the centre span is
completely open so the rear touch panel is exposed.

Built from scratch. It shares no code, no geometry and no measurements with
`projects/VitaGrip1000`.

## REJECTED 2026-09-08 — the swept-tube geometry is gone

**The user rejected the built figure: it does not match anything.** The grip
STL and the geometry macros that produced it were deleted on that instruction.
The project restarts from the DualSense scan the user is supplying.

What was deleted, and what survives:

| Deleted | Kept |
|---|---|
| `VitaGripPS5.stl` — the built part | `macros/prepare_dualsense.py` — DualSense scan prep |
| `macros/build_grip.py` — Blender swept-tube builder | `derived/dualsense_watertight*.stl` — its verified output |
| `macros/grip_b123d.py` — the build123d builder | `console_solid.stl` + `macros/make_console_cutter.py` |
| `macros/profile_gate.py` — the lobe gate | `macros/fit_check.py` — console-vs-grip interference |
| `renders/`, `VitaGripPS5_*.png` | this README, `sources/VitaGripPs5/SOURCES.md` |

`prepare_dualsense.py` is kept deliberately: it is anchored on the user's own
caliper reading (120 mm tip-to-tip), it is what produced the watertight
DualSense solids in `derived/`, and `SOURCES.md` cites it. It has nothing to
do with the rejected grip figure.

### The lesson, measured

**Every dimensional gate this part had could pass while the part looked like
nothing.** At rejection the geometry was, by its own gates:

- 222.42 x 47.84 x 112.89 mm against a 222.4 x 112.3 measured target
- lobe profile within **3.7 mm** (tol 4.0), RMS **1.4**
- palm section correctly oval, 50.2 x 46.5 vs a 50.8 x 46.7 reference

Those numbers were hard-won — they came from correcting a 6.5 % scale error
and three separate measurement bugs in the gate. **They were also beside the
point.** A width profile plus an aspect ratio does not constrain a shape: the
part matched a table of widths at 41 stations and still read as two lumps on a
stick.

The deeper cause is recorded in `docs/lessons.md` and in *Why Blender* below:
the central shape decision — a swept round bridge tube — came from reading
`psvitarearbackside.webp`, a 3/4 **CAD render**, as an orthographic side view.
Correcting the *dimensions* of a shape taken from a misread reference cannot
make it the right shape. The measurement work was real; it was applied to a
form that was never verified against a photograph of a real object.

**For the rebuild:** the DualSense scan is geometry, not a measurement table.
Match form to it directly — cross-sections against cross-sections — rather
than reducing it to per-station widths and rebuilding from those.

## Status

**NO GEOMETRY. Awaiting a DualSense STL from the user.** Nothing in this
project builds a grip; the swept-tube figure was rejected and deleted (above).

What is on disk and trustworthy:

| Asset | State |
|---|---|
| `derived/dualsense_watertight.stl` | watertight, 1 body, genus 0, tip span **120.442 mm** — matches the user's caliper to 0.4 % |
| `derived/dualsense_watertight_200k.stl` | same, decimated; anchor holds to **0.014 mm** |
| `console_solid.stl` | PCH-1000 solid, for cutting the console pocket |
| `macros/prepare_dualsense.py` | regenerates both DualSense solids; re-measures the 120 mm anchor after every operation and aborts if it moves |
| `macros/make_console_cutter.py` | regenerates `console_solid.stl` |
| `macros/fit_check.py` | console-vs-grip interference; needs a grip STL to run |

Regenerate what remains:

```
python projects\VitaGripPS5\macros\prepare_dualsense.py
python projects\VitaGripPS5\macros\make_console_cutter.py
```

### Numbers that survive the deletion

These were measured, not assumed, and should be reused rather than re-derived:

- **Scale anchor for `054-1.webp`: 0.246279 mm/px** — the console's 182 mm spec
  width over the 739 px where the grip does not occlude it. The grip in that
  photo is **222.4 x 112.3 mm**, agreeing with two independent measurements in
  `sources/psvitaGrip/SOURCES.md` to 0.41 % and 0.09 %. Do not use 0.2635 or
  237.9 x 119.8; those were a 6.5 % scale error. See
  [docs/lessons.md](../../docs/lessons.md).
- **Console: 182 x 83.55 x 18.6 mm**, from the PCH-1000 spec — not a photo
  measurement, and it does not scale with any photo correction.
- **DualSense: 120 mm tip-to-tip**, the user's own caliper reading, and the
  reason the scan in `derived/` is trusted as true-to-scale.

## Why Blender — and why that reasoning was wrong

> **Superseded.** This section is kept because it is the root cause of the
> rejection, not because it is guidance. The argument below is what justified
> a swept tube, and its premise was a misread image.

The original reasoning ran: the object is **a tube that bends**.
`psvitarearbackside.webp` shows the bridge as a round bar with a visible fillet
where it flares into each grip; `lateralFronView.jpg` shows the console held at
its ends with the centre open. Natively that is a curve, a round bevel on it,
and three boolean boxes.

**`psvitarearbackside.webp` is a 3/4 CAD render, not a side view.** Read as
orthographic it makes the bridge look like a round bar, and that became
`R_BRIDGE = 9.5` and the whole swept-tube approach. The real print photo,
`lateralFronView.jpg`, shows a flat-bottomed **C-channel** with a full-span
vertical back wall. Also in that folder: `lateralHAndleview.jpg` is an
AI-generated fake blueprint — it labels "Overall Height: [25]mm", a bracketed
placeholder, for a ~120 mm grip.

So the form was taken from a render, the dimensions from a photograph, and
nothing checked that the two agreed. They did not. Every later correction —
the anchor, the profile table, the oval section — refined a shape that was
never the right shape.

**Before the rebuild picks a construction method, run `perspective-checker` on
every reference and let it say which images may source a cross-section.**

## What the reference images are each good for

| Source | Good for | Why |
|--------|----------|-----|
| `054-1.webp` | **Every dimension** | 960×960, straight-on rear, saturated blue on white, and the console's own 182 mm is visible above the grip as a scale anchor |
| `psvitarearbackside.webp`, `psvitafrontside.webp`, `lateralFronView.jpg` | **Shape only** | Grey CAD renders — no blue to segment, no scale anchor. These are what showed the round tube and the open channel |
| `lateral.jpg`, `lateralrearbackview.png` | Shape confirmation | Perspective photos |
| `psvita.jpg`, `Fixed_dimensions.webp` | The **console** | 182 × 83.55 × 18.6 mm |

**Audited before use, not assumed.** `handle-back.jpg` is 340 px wide and
`FrontViewWithPsVita.png` is a **142×106 thumbnail** whose entire grip is
35 px across. Numbers from those would be noise with a decimal point.

The first measurement pass returned **343.5 mm** overall because the blue mask
had swallowed the product's soft blue-grey shadow. Saturation separates them:
raising the S floor from 110 to 150 drops the shadow.

**That is where this account used to stop, and it was half an explanation.**
Raising the S floor fixes the shadow; it does not produce 237.9 mm. Sweeping
the floor once the shadow is out moves the span **905 px at S>110 to 895 px at
S>200 — 1.1 %**. No S floor yields 237.9 from this image.

The real anchor problem is that `054-1.webp` is an **assembly**: the blue grip
holding the black console. The 182 mm anchor belongs to the *console*, and the
grip covers its lower corners, so the console's span depends on the row read —
**739 px exposed** at image row 282, **514 px median** where the grip wraps it.

At the exposed span the scale is **0.246279 mm/px** and the grip measures
**222.4 x 112.3 mm**, which reproduces the two independent measurements already
in `sources/psvitaGrip/SOURCES.md` (223.3 mm from `handle-back.jpg`, 222.6 mm
from this image) to **0.41 %** and **0.09 %**.

Every photo-derived constant was **6.5 % oversized** until 2026-09-08, by a
single factor of 1.0685 on both axes. See [docs/lessons.md](../../docs/lessons.md).

## Five failures, and what each actually was

Every one of these built cleanly and reported success.

### 1. The console was measured lying on its face

`fit_check` reported 2,698 then 860 interfering points at the channel floor. I
added a cylinder to round the floor to match the console's curved bottom, and
the count went down, which looked like progress.

It was an **axis error**. The console mesh is X=width, **Y=height**, Z=depth;
the build is X=width, **Y=depth**, Z=height. The check was placing the console
flat. Rotating it 90° about X gave **0 interference on a flat floor**, and the
rounding cutter — added for a bug that did not exist — then went on to cause
failure 3.

### 2. Zero interference, and the console still fell through

With the axes fixed the fit was clean: 0 of 200,000. But the closest approach
was **2.99 mm** and *nothing* was within 1 mm — the grip did not touch the
console anywhere. It was a tube with a groove scraped along the top.

Zero interference is necessary, never sufficient. The retention check is what
caught it, and it is why `fit_check.py` reports contact as well as collision.

### 3. Three bodies, chased through five wrong theories

The part reported 3 disjoint bodies. In order, I raised the bridge to fix a
tangent contact, sank the walls into the floor, deleted the rounding cutter
from failure 1, and extended the floor down to the tube. None of it worked.

Then I bisected the pipeline and printed the component count **at each stage**.
The tube alone was already 3 components, before any boolean ran.

The cause was a **convention error**: `primitive_cube_add(size=1.0)` with
`ob.scale = (x, y, z)` gives extents *x, y, z* — scale is the **full** extent,
not the half-extent. Every cradle piece was built at half size, so the floor
spanned X ±47.2 instead of ±94.35 and the walls standing on it reached nothing.
The two floaters were 12-face boxes at exactly ±47.2.

Correcting it the other way then made the *cutters* double size, which deleted
the tube entirely. So the file now has **one** helper,
`box(name, size, at)` — full extents and a centre — stated once at the top.

### 4. The union silently returned an empty mesh

With the sizes right, the cradle union produced **zero faces** — and the build
still wrote a valid STL and reported success.

Bisected: the tube alone was one clean manifold, +252,317 mm³, no non-manifold
edges. The cradle was a clean box, +201,467 mm³. Their union was empty.

The cause is **`use_self`**. The swept tube self-intersects where each grip
curves into the bridge — the bevel is 21 mm and the spine turns back on
itself — and without self-intersection handling the EXACT solver returns
nothing. With `use_self=True` the same union gives the correct 393,926 mm³.

`boolean()` now raises on an empty result. An empty mesh must never be
exported: it writes a valid STL and passes bounding-box gates **vacuously**.

### 5. The width could not be reasoned about, so it was solved

No inset gave 248.0 mm against the 237.9 measured. Insetting the spine by the
tip radius gave **262.0 — worse**, because the rake term pushes the tip further
outboard than the spine point it is measured from.

Built width is a function of spine, rake and bevel together. Measuring it is
quicker than modelling it: sweeping `X_INSET` gives a clean
**width = 290.01 − 2 × X_INSET**, so 237.9 needs **26.06**. Built: **237.89**.

The build **asserts on the solid's own bounding box**, because `X_INSET` was
solved from that relation and nothing else would notice if the spine changed.

## The bar is a shelf, not a spacer

The console's underside **rests on** the bar. It is a structural member that
carries the console's weight, and it sits **below** the console's bottom edge,
low across the rear.

Measured on `054-1.webp` by classifying each row of the blue mask - rows with
two runs are the grips, rows with one wide run are the bar:

| Quantity | Value |
|----------|-------|
| Bar rows | z **−2.6 to −15.3 mm**, i.e. below the console's bottom edge |
| Bar thickness | **12.7 mm** |
| Bar span | 237.9 mm, tip to tip |
| Grip inboard reach at the bar's rows | \|X\| **63–66 mm** |

The console's half-width is 91 mm, so each grip overlaps it in plan by about
**27 mm**: the grips swallow the console's corners, which is what stops it
sliding out sideways, while the bar carries it from beneath.

`BAR_TOP` is **0.0** — the bar's top face *is* the datum, the surface the
console sits on. It was −1.0 at first, and that 1 mm gap left the console
floating: closest approach 0.40 mm with only 17 of 4,000 points in contact.
At 0.0 it is 0.01 mm and 92 points.

### There is no full-length trough

The first version of this build put one box spanning the whole console and
carved a channel out of it. That is a tray. The reference holds the console at
its **two ends only**, with the centre span completely open so the rear touch
panel is exposed — the "OPEN CENTER" the blueprints label.

So the cradle is two end blocks, and the front/back cuts are limited to the
**gap between them**. Run full-width they delete the blocks' front faces.

### A vertex-band count is not a material check

Chasing that, I "found" the end blocks hollow between Z 10 and 30 by counting
vertices in Z bands, and made three fixes for it. The blocks were solid the
whole time: **a box has vertices only at its eight corners**, so any band that
misses a corner reads zero. Ray-probing showed material at \|X\| 93 from Z 5
to 25 exactly as intended.

Count vertices to find where geometry *is defined*; ray-probe to find where
material *is*.

## The console's height cannot be measured in this view

The blue mask reads the console as **63.0 mm** tall against its 83.55 mm spec,
because the bar occludes its lower part. That is a measurement of the
occlusion. Nothing is scaled by it — the width anchor is the only valid one.

## Open defects *(of the deleted part — historical)*

> The part these describe no longer exists. Kept because the mesh defects are
> properties of the *construction method*, and a rebuild that reaches for a
> swept tube again will meet them again.

Three gates failed on the final build. **All three predate the anchor
correction** — each was measured on the previously shipped STL as well, so
they were not consequences of the rescale. Numbers below are shipped → rebuilt.

| Defect | Shipped | Now | Gate |
|---|---|---|---|
| Not watertight | 8 open edges | **4 open edges** | `render_check.py` |
| Genus | 1 tunnel | **4 tunnels** | `profile_gate.py` |
| Console interference | 2.02 % | **2.32 %** | `fit_check.py` |
| ~~Lobe profile~~ | ~~max 42.0 mm~~ | **PASS — max 3.7 mm** | `profile_gate.py` |
| ~~Lobe section~~ | ~~circular~~ | **PASS — oval** | `profile_gate.py` |

**The remaining watertightness defect is tiny and localised**: 4 open edges
meeting at a single point (2 distinct vertices, at X 76.2, Y −3.9, Z 32.2).
That is degenerate geometry from a boolean, not a shape problem.

**The interference is concentrated at the bar**, spanning the full width at
Y −9.2..0.2, Z 3.3..52.9 — the console's own body against the shelf it rests
on, not the end blocks. Note the console is placed by `fit_check.py` at its
own datum; before treating this as a geometry fault, confirm the gate and the
build share a placement (this project has been bitten by exactly that before —
see *Five failures* below).

Neither was attempted here.

### The lobe cross-section, and why it took a gate fix rather than a geometry fix

The profile gate reported the lobe as deviating **29.0 mm** with a circular
palm section. Measuring the same part a second way put the error at 7.8 mm,
and the disagreement was the finding. Three faults were in the *gate*:

1. **It measured the bridge bar as part of the lobe.** `x_cut = -45` keeps
   everything left of X = −45, and below depth ~85 the bar reaches into that
   region. At depth 88 the slice spanned 55.3 mm while the lobe's own cluster
   was **35.1 mm** against a 33.9 reference — a reported +21.4 that was really
   +1.1. The tell: width leapt while the depth beside it stayed smooth.
2. **A horizontal slice through a leaning tube is an ellipse, not the section.**
   The spine droops rearward at a measured **dY/dZ 0.217 (12.2°)**, inflating
   the read Y-extent by 1/cos = 1.0233. That turned a true 46.4 mm palm depth
   into 47.5 and tripped the `|width − depth| < 3` ovality test on a correctly
   oval lobe.
3. **The sampling band reached past the part's own ends.** At depth 0 the ±2 mm
   band sampled above the crown entirely; it read 29.4 against a 21.6
   reference and converged to 21.1 as the band shrank.

One fault *was* real geometry: `lobe_halfwidth()` **clamped** below the table's
last station, so the final 3.66 mm of lobe swept at a constant 12.6 mm width —
a blunt stub instead of a tip. The tail is now closed on a quarter ellipse to
`LOBE_TAIL_END = GRIP_H`, constructed and labelled as such, the same treatment
the top crown already gets.

Result: max deviation **29.0 → 3.7 mm**, RMS **10.8 → 1.4**, ovality passing.
The fixed gate still **fails** the old shipped part (14.6 mm, wrong width and
height, palm still circular), so it was not merely loosened into passing.

## Still outstanding, and still true for the rebuild

These were never done, and none of them was the reason for rejection — they
carry forward regardless of how the form is built.

- **Nothing is shelled.** The reference is a hollow moulding;
  `lateralFronView.jpg` shows that plainly. Whatever the rebuild produces will
  need a wall, not a solid.
- **No ergonomic detail**: no palm swell, no finger grooves, no grip texture.
- **No test print.** `FIT_CLEAR` (0.35 mm/side) and the channel's retention are
  calculated, never measured against a printed part.
- **The console pocket must be a C-channel**, flat-bottomed with a full-span
  back wall — from `lateralFronView.jpg`, the one real print photo. Not a
  milled pocket, and not the round bridge the CAD render suggested.

## Verification

1. `build_grip.py` asserts the built width against the measured 237.9 mm and
   fails if the part is not one connected component. Component count is
   printed **at every stage**, which is what found failure 3.
2. `boolean()` raises on an empty result — failure 4.
3. `fit_check.py` samples 200,000 points on the real PCH-1000 mesh: **0 inside**,
   and separately reports **contact**, because zero interference alone is what
   failure 2 looked like.
4. `render_check.py`: watertight, 1 body, consistent winding.

None of this proves the grip is comfortable, that the console is retained
firmly, or that it can be inserted in one motion. Only a test print settles
those.
