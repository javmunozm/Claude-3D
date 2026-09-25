# VitaGrip1000

A grip for the Sony PS Vita **PCH-1000**, modelled on the Comfort Grips
"PS VITA / PS5 Controller Grip": a slim cross-bar low across the console's
**rear**, with two **DualSense-contoured handles** at its ends.

The console's **front face is exposed** apart from a 2 mm retaining lip on its
outer edge, its **rear touchpad is exposed**, and **nothing goes near the
shoulder buttons**.

## Status

**Builds, fits, and passes every gate. Not yet test-printed.**

| Property | Value |
|----------|-------|
| Bounding box | 223.30 x 105.88 x 40.14 mm |
| Volume | 141.5 cm3 |
| Mesh | watertight, 1 body, euler 2 |
| Handle | 105.9 mm long, 48.6 mm max width, 5 -> 40 mm depth |
| Retaining notch | **3.00 mm** (\|X\| 88.0-91.0), clear of the speakers |
| **Slot depth** | **19.320 mm** (console 18.6 + 2 x 0.35) |
| Console fit | **0 of 200,000 points interfere** |
| Tip | cut flat, 13.4 x 10.7 mm standing pad each side |

Regenerate:

```
python projects\VitaGrip1000\macros\trace_console.py     # console outline
python projects\VitaGrip1000\macros\trace_dualsense.py   # DualSense views
python projects\VitaGrip1000\macros\trace_grip.py        # the grip itself
python projects\VitaGrip1000\macros\vita_grip.py         # build
python projects\VitaGrip1000\macros\fit_check.py         # fit vs real console
python tools\render_check.py projects\VitaGrip1000\VitaGrip1000.stl --views right
```

## This is the third design. Two were deleted.

**v1** replicated a different product — a one-piece moulded slide-in cradle —
and was deleted 2026-09-01. Its console-side findings survive in
[CONSOLE_FACTS.md](CONSOLE_FACTS.md).

**v2** was deleted 2026-09-02. It built the whole part by extruding one flat
plan outline along Z, with a different extrusion depth per Y-station: about 40
stacked prisms. It rendered as a hammer — a bar with two flat paddles — and its
STL was 68 KB, because flat faces and hard corners are all it contained.

Two distinct defects, both of which passed every gate v2 had.

### The trace captured a rim, not a body

v2 traced `BackView.png`, a **200 x 121 px** line drawing. Its own docstring
listed five failed tracing attempts on it. The method it settled on produced a
`vitagrip_front.dxf` with the right bounding box — 223.3 x 104.6 mm — enclosing
**6,211 mm2**. The console alone is 13,984 mm2: the "grip" was 44 % of the area
of the object it wraps around. It had captured the drawing's lit **rim**.

Every gate passed because every gate checked the bounding box, and the bounding
box of a rim is the bounding box of the part.

The fix is the source, not the algorithm. `054-1.webp` is **960 x 960**, a
straight-on rear view of a saturated blue grip on white. HSV colour
segmentation on it cannot return a rim — it returns the filled region or
nothing. One component, fill ratio 0.413, **10,368 mm2**.

### An extrusion cannot express this object

The handles are teardrop solids whose section grows and travels rearward along
their length. A prism has no shape in the direction it is extruded, so v2's
handle had **no hook at all**, and the per-station depth trick left a 2.6 mm
staircase.

There is no orthographic view that describes this shape. It needs a **loft
through 3D sections**, which is what this version does: each station is an
ellipse sized by the plan half-width at that height and the depth at that
height, both measured.

## Refinements (2026-09-02, after the first swept build)

| Change | Value | Effect |
|--------|-------|--------|
| `SLIM` | **5.0 mm** | handle diameter reduced 5 mm overall (2 mm, then 3 mm more) - half off each side of every measured section, verified 5.00 mm at every station |
| `LIP_X` | **88.0 mm** | retaining notch cut from 9 mm to **3.00 mm** - the 9 mm notch covered the speakers |
| bar rear face | follows the handles | the flat plate protruded; the bar now ramps Z -15.81 -> -28.49 to meet the handle contour |
| `TIP_FLAT` | 3.0 mm | handle tips cut off flat: 336 vertices on one plane at Y = -79.93, a 13.4 x 10.7 mm pad per side |
| `CHAMFER` | 1.2 mm | tapered lead-in at the pocket mouth: the half-width opens 91.80 -> 93.00 mm over the last 1.2 mm instead of stepping |
| **slot depth** | **21.30 -> 19.320 mm** | see below |

### The slot was 2 mm too deep, and every gate passed

Measured on the build: the cavity the console drops into was **21.30 mm**
(user-measured 20.743 on an earlier export) against the 19.30 it needs. An
18.6 mm console had **2 mm of slop** and would rattle.

The pocket cut was the right depth the whole time. The handles were pinned at
`Z = HALF_D + FIT_CLEAR + FRONT_LIP` and the cut stopped at
`HALF_D + FIT_CLEAR`, so `FRONT_LIP` mm of handle stood **inside** the pocket.
Nothing could see it: bbox, volume, watertightness, body count, both keep-outs
and `fit_check` all passed, because the console still *fits* in a slot that is
too deep.

The cut now starts ahead of the handles and is inset outboard of `LIP_X`, so
the lip **overhangs** the console's front face - which is what retains it -
rather than deepening the slot.

**A slot-depth gate now ray-probes the exported mesh** and fails the build if
the cavity is more than 0.25 mm off. It runs *after* the export, because
probing before it would measure the previous build. Against the old geometry
it reports 1.55 mm of error and fails.

### The notch covered the speakers

`LIP_X` was 82.0, a **9 mm** notch, and the built lip reached inboard to
\|X\| 78.79. Measured on `psvita.jpg` at 0.3957 mm/px (scale checked against
the annotated 182 mm width), the **stereo speaker dot grid runs \|X\| 79.7 to
86.1 mm at Y -9.7..-12.7** — the notch covered it completely.

The existing front-face gate reported CLEAR throughout, because it only looks
inboard of `ACTIVE_X` = 78 mm and the lip stopped just outside that line. A
gate whose threshold sits 0.9 mm outside the feature it is meant to protect
cannot see the failure.

`LIP_X` is now **88.0** — a 3.00 mm notch, clearing the speaker grid by 1.9 mm
— and a **speaker keep-out gate** tests that band directly.

### The rear wall stuck out of the handles

The bar was a flat plate at a constant `BAR_DEPTH`, stopping at Z = -12.65,
while the handles in the bar's own Y band curve back to Z = -25.5. The plate
floated in front of that curve with nothing blending it.

The bar's rear face now **follows the handle contour**: it is lofted along X
through four stations, thin at mid-span and swelling to meet the handle's own
rear Z where they join, interpolated from the same profiles the handles are
built from. Built rear face: -15.81 (mid) -> -28.49 (at the handles).

## Where every number comes from

| Quantity | Value | Source |
|----------|-------|--------|
| Grip envelope | 223.49 x 113.10 mm | `054-1.webp`, HSV mask, anchored on the console's unoccluded 182 mm |
| Handle plan width | 3.5 -> 26.8 mm half-width, **less `SLIM`/2** | same mask, per-row runs |
| Handle depth | 10.1 -> 45.1 mm, **less `SLIM`** | `dualsense_side.dxf`, verified orthographic |
| Handle length | 106.68 mm measured, **105.88 built** after `TIP_FLAT` | Y extent of the handle rows |
| Bar | Y -36.51 .. -21.69 (14.82 tall) | measured directly: the rows where the mask is one wide run |
| Console | 182 x 83.55 x 18.6 | spec, agreed by the real mesh to 0.15 mm |
| Console pocket | traced outline **unioned with the mesh silhouette** | `psvita_front.dxf` + `psvitaManualJoin_decimated.stl` |
| Trigger keep-out | \|X\| 45.0-81.6, Y > 30 | measured on the PCH-1000 mesh |

### Two independent confirmations of the envelope

- **Width.** `054-1.webp` gives 223.49 mm. `handle-back.jpg` — a different
  photo, a different scale anchor — gave 223.3 mm in the previous pass.
  **0.1 %.**
- **Bar height.** The bar occludes the console's lower 21.5 mm in `054-1.webp`,
  putting its top edge at Y = -20.2 mm. Measured directly off the mask:
  **-21.69 mm.**

### The console's height is NOT a usable anchor in this view

The bar covers the console's lower 21.5 mm, so its dark blob measures
**63.22 mm** against the true 83.55. Dividing by it gives a scale 32 % wrong.
The number is reachable and looks plausible; only the width anchor is valid.

## What the gates caught this time

Every defect below passed watertightness, consistent winding, body count, and
the bounding-box asserts.

| Defect | What it looked like | What caught it |
|--------|--------------------|----------------|
| Smooth loft bulged outside the section hull | outer edge -130.18 mm against measured sections reaching -111.74 | the width assert; fixed with `ruled=True` |
| Console pocket cut through the full depth | handle sections above the bar collapsed 41 -> 16 mm: flat plates again | cross-sectioning the export at seven heights |
| `BAR_DEPTH = 9.0` put the bar 6 mm inside the console | — | `fit_check.py`: 13,593 of 200,000 points (6.8 %), 97 % in the bar's band |
| Pocket cut to the drawing alone | 205 points at X 87.5-91.0 | `fit_check.py` again; fixed by unioning with the mesh silhouette |
| Spine anchored at the tip drove the handle **forward** | front face reached Z +27.3 against the console's +9.3 — the handle lay across the screen | the front-face keep-out |
| Depth *and* spine travel both applied | built depth 57.51 mm on a 45.14 mm handle | the side view's depth already spans the hook; double-counted |
| **Handles stood inside the console pocket** | **slot 21.30 mm against 19.30 - 2 mm of slop, console rattles** | **ray-probing the export; every existing gate passed, `fit_check` included** |
| **A 9 mm retaining notch covered the stereo speakers** | every keep-out gate reported CLEAR | measuring the speaker grid on `psvita.jpg` and comparing it to the built lip |
| The slot gate silently returned `None` once `LIP_X` moved | build printed no slot line and passed | noticing the line was missing; the probe now derives its own X positions and a `None` result **fails** |

### "Nothing over the front face" is the wrong gate

It fails the retaining clip, which is what holds the console on. The gate is
split by X: inboard of \|X\| 78 mm — screen and buttons — nothing may cross the
front face; outboard of it the clip may, and does, by 2.0 mm.

### A probe grid is not a keep-out gate

Kept from the previous pass: a clamp lip overhanging the shoulder zone by
0.2 mm passed a 6x4 probe grid clean, because no sample landed on it. The gates
test the part's **vertices**.

## Verification

1. **Width** asserted on the built solid's bounding box, not on the formula.
2. **Keep-outs** on the part's vertices: shoulder buttons, and screen/buttons
   over the front face.
3. **Fit against the real console** — `fit_check.py` samples 200,000 points on
   the PCH-1000 mesh; **0 inside**.
4. **Slot depth** ray-probed on the exported mesh: **19.320 mm** against the
   19.300 required. `fit_check` cannot see this - a console fits perfectly
   well in a slot that is too deep.
5. **Handle plan area vs the photograph**: 6,740 mm2 built against 6,338 mm2
   measured, **6.3 %** (before `SLIM`).

Zero interference does not prove the fit is comfortable or that the walls
retain it. Only a test print settles that.

## Assumed — revise after a test print

| Dimension | Value | Why it is assumed |
|-----------|-------|-------------------|
| `FRONT_LIP` | 2.0 mm | `handlefront.webp` shows a narrow lip but is a 3/4 view and cannot be measured |
| `LIP_X` | 88.0 mm | how far inboard the lip reaches; constrained by the **speakers** at \|X\| 86.1, not by `ACTIVE_X` |
| `SLIM` | 5.0 mm | a comfort choice, not a measurement |
| `TIP_FLAT` | 3.0 mm | enough to give a standing pad without shortening the grip noticeably |
| `CHAMFER` | 1.2 mm | typical moulded lead-in for this wall thickness |
| `WALL` | 3.0 mm | standard moulded wall for this size |
| `FIT_CLEAR` | 0.35 mm/side | calculated sliding fit, FDM, not measured |

## Reference material

See `sources/psvitaGrip/SOURCES.md` for full provenance.

| File | Role here |
|------|-----------|
| `054-1.webp` | **Primary shape source.** 960x960 straight-on rear view; the HSV mask |
| `dualsenseDiagram.svg` | **Primary depth source**, verified orthographic to 0.04 % |
| `sketchPSvitaHandle.jpg` | The brief. Rotate +90 deg to read |
| `handlefront.webp` | Confirms the front face stays exposed; shows the clip |
| `lateral.jpg` | Handle hook — **perspective, not measured** |
| `Vita 1000/*.stl` | The console the fit test runs against |

**`lateral.jpg` is not a measurement source.** The previous pass took a 50.8 mm
handle "belly" from it; it is a three-quarter view and no orthographic number
can come out of it. Depth comes from the DualSense drawing.

## Before printing

- **Test-fit against a real PCH-1000.** `FIT_CLEAR` and `FRONT_LIP` are
  calculated, not measured.
- The 2 mm lip is the only thing retaining the console. If the grip springs
  off, increase `FRONT_LIP`; if it will not go on, raise `FIT_CLEAR`.
- Print orientation: **handles vertical, bar flat on the bed**. The handle
  bellies will need support.
