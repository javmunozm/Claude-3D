# VitaGrip

## Goal

An OPEN-CRADLE 3D-printable hand-grip for the Sony PS Vita 1000
(PCH-1000), matching the commercial "gamepad-style" Vita grips seen in
the reference photos: two short, thick handle horns connected by a
substantial back-side bridge that clips onto the Vita's short edges via
two U-shaped side channels. Unlike a clip-on case, the Vita's screen
(front) and back panel both stay fully exposed — the grip only touches
the Vita at the two side channels (front/edge/back margins near each
short edge) plus a proud front corner tab at each top corner.

**Design intent:** recreate the *shape language* seen in reference
photos (the short hook-shaped handle horns, the substantial stepped
back-side bridge, the small corner-tab detail near the shoulder buttons)
using dimensions derived primarily from the Vita's own official body size
plus direct pixel-measurement of the reference photos — not to reproduce
the reference STL mesh itself (its envelope does not match the confirmed
PCH-1000 body; see "Reference material" below).

## Status

⚠️ **Improved but still does not match the reference photos. Do not print it.**

Revision 5 (2026-07-29) rebuilt the part from row-by-row measurement of
`054-1.webp`. Proportions and outer silhouette now match closely, and all
topology gates pass, but the part still reads as a **thin frame** rather
than the reference's **solid mass**. Measured solidity gap:

| Metric | Reference | Revision 5 | Rev 1-4 |
|---|---|---|---|
| Overall envelope | 225.0 × 113.9 mm | 231.2 × 130.1 mm | 242.7 × 130.0 mm |
| Front-projection fill of own bbox | **41.3 %** | — | — |
| Solid fraction of bbox volume | ~*(est.)* | **21.7 %** | — |
| Volume | ~318 cm³ *(est.)* | **229 cm³** | 139 cm³ |

Volume is up 65 % from revision 4 (139 → 229 cm³) and the silhouette is
right, but the part carries roughly **half the reference's mass**. The
remaining defect is the same root cause identified in the audit and not
yet fully fixed: the side lobes are ~20 mm slabs where the reference's are
deep, rounded teardrops. Fixing it means giving the lobes a genuine 3D
teardrop cross-section (varying in Z as well as X), not another parameter
tweak — iterating on constants was explicitly stopped here to avoid
repeating the revision 1-4 pattern.

### What revision 5 fixed

- **Band height corrected by measurement.** Sampling the photo's centre
  column (which isolates the band from the lobes flanking it) showed the
  band is only **16.9 mm tall — 15 % of grip height**, a slim rear strap.
  Revisions 5a-5c had assumed 31 mm, nearly 2×. A render comparison had
  suggested the band needed to be *deeper*; measurement showed the
  opposite, and that the reference's mass is in the **lobes** (45 % of the
  height above the band). Measuring beat eyeballing.
- **Horn re-derived as a blade, not a peg.** Measuring the horn's two
  edges *separately* showed the outer edge stays pinned ~112 mm from the
  centreline while the inner edge sweeps outward. Narrowing a section
  symmetrically about a drifting centreline (revisions 1-4) yields a thin
  vertical peg. Stations are now expressed as **edge positions**, and the
  builder derives width and centre from them.
- **Continuous lobes replace rail + separate horn.** The outboard material
  grows smoothly 0 → ~20 mm from the grip's top edge to the Vita's bottom
  edge with no discontinuity, then runs on into the horn — one lofted
  body per side, not three parts.
- **Three zero-overlap boolean bugs fixed.** Corner tabs sat flush on the
  lobe's front face and horns butted exactly against the lobe's end; a
  union of merely *touching* surfaces does not fuse, so those pieces came
  out as free-floating solids (`ShapeList`, non-watertight). All mating
  features now interpenetrate. The topology gate caught every one.

The macro produces a single watertight solid (`body_count == 1`,
`is_watertight == True`), and every dimensional and topological check
passes — but a side-by-side comparison of a shaded render against
`054-1.webp` shows a **thin flat bracket** where the reference is a **fat,
solid, controller-style grip**. They are not the same object.

Reproduce with:

```
python tools\render_check.py VitaGrip\VitaGrip.stl --views front ^
    --reference references\psvitaGrip\054-1.webp
```

### Known mismatches (measured 2026-07-29)

Reference measured from `054-1.webp`, anchored on the pictured Vita's body
width spanning 740 px (4.031 px/mm):

| Aspect | Reference | Macro builds | |
|---|---|---|---|
| Horn width profile | swells 8 → **53 mm**, then rounds to a tip | tapers 42 → **13 mm**, monotonic | **taper direction inverted** |
| Horn form | fat teardrop with real volume | thin spike | wrong form |
| Bulk | solid throughout | 3 mm walls + 14 mm shelf | reads as skeletal |
| Grip envelope (photo) | ~225 × 114 mm | 242.7 × 130.0 mm | over-large, wrong proportion |

The root cause is `HANDLE_STATIONS` (`macros/vita_grip_b123d.py`), whose
width column decreases monotonically. A hand grip **swells** below the
neck — that swell is what the hand closes around. A monotonically
shrinking profile produces a spike, not a grip.

### Why four revisions missed it

Revisions 1–4 each verified a *local* property — "the centre span is
empty", "`body_count == 1`", "the band reads as solid" — and each check
genuinely passed. None ever put the render beside the photo and asked
whether it was the same object. Correct parts do not compose into a
correct whole. `tools/render_check.py --reference` now makes that
comparison a standard gate; see [docs/commands.md](../docs/commands.md).

### Note on the reference variant

The reference photos show a **PCH-2000** (slim) Vita, while this macro
targets a **PCH-1000** (182 × 83.5 × 18.6 mm, confirmed by the user and
retained). The two bodies differ, notably in depth (18.6 mm vs ~15 mm).
So the photos are the authority for **shape language and proportion**,
and the PCH-1000 spec is the authority for **absolute dimensions** — the
grip's form should be adapted to the PCH-1000 body, not copied
dimensionally from photos of a different model.

**Not yet physically test-fit or printed** — and should not be until the
horn profile is corrected. See the verification checklist at the bottom
of this README.

### Revision note (2026-07-21, part 1)

A prior revision had the handle horns falling nearly vertical/parallel
(barely splayed) and far too long (92 mm), with a thin flat bridge
(12 mm tall x 4 mm thick), producing a bounding box (224 x 176 x 30.6 mm)
almost twice the Vita's own height — clearly disproportionate versus the
reference photos. This revision re-derived the handle and bridge
dimensions by **pixel-measuring 054-1.webp directly** (960x960 px image;
Vita body spans 738 px for its known 182 mm width -> 4.055 px/mm scale
factor), tracking the horn silhouette and bridge/channel boundary
row-by-row. Key corrected findings:

- The horns separate from the continuous bridge/channel body **79.9 mm
  below the Vita's top edge** — i.e. almost exactly at the Vita's own
  83.5 mm bottom edge, confirming the "bridge" is a substantial body
  spanning nearly the Vita's full height, not a thin band near the top.
- Horn length below that neck is only **~46 mm** (not 92 mm).
- The horn taper is **asymmetric**: the outer (away-from-Vita) edge stays
  nearly straight/vertical while the inner edge sweeps in, giving a
  hook/paddle silhouette — not a symmetric pinch to a point, and not a
  large outward "V" splay along the horn's own length (the horn's own
  centreline drifts outward only ~3 mm across its length once past the
  neck; the photo's V impression comes mostly from the neck already
  sitting near the channel's outboard position, not further splay below
  it).

### Revision note (2026-07-21, part 2 — structural fix, not just parameter tuning)

A **shaded** (non-wireframe) render of part 1's output, viewed straight-on
(`elev=90, azim=-90`), revealed a structural modelling bug that the prior
parameter-only pass had not caught: `build_top_bridge()` built a bridge
`Rectangle(2 * span_half_x, ...)` spanning the **entire width** between
the two side channels (~226 mm, ~97% of the grip's total width) — reading
as one solid slab across nearly the whole top of the part. Worse, a
second, independent bug was found in `build_side_channel()`/
`_channel_c_profile()`: the channel's own front/back lips were built from
`x0 = 0.0` (the Vita's own centreline) out to the channel's outer edge —
so the RIGHT channel's lip alone already spanned from the centreline to
the right edge, and mirroring it for the LEFT channel produced a second
lip spanning centreline-to-left-edge. Together the two channels'
lips formed a continuous solid slab across the *entire* grip width, with
or without the separate bridge. Neither bug is visible in wireframe views
or from simple bounding-box/dimension checks — only a shaded render made
it obvious.

Both are now fixed structurally (not just re-parameterized):

- `_channel_c_profile()` / `build_side_channel()`: the front/back lips now
  start at a new `x_lip_in = vita_x_edge - CHAN_LIP_INSET` (14 mm inset
  from the channel's own outer face), a **narrow band local to each
  channel**, instead of reaching all the way to the centreline. Each
  channel is now a self-contained "[" bracket that does not extend across
  the grip's centre at all.
- `build_top_bridge()` was replaced with `build_bridge_stub()`, called
  once per side (mirrored), building a short (16 mm reach) stub that
  extends inward from each channel's own inner face — the two stubs do
  **not** meet in the middle. `BRIDGE_TOP_INSET`/`BRIDGE_HEIGHT`/
  `BRIDGE_THK` replace the old two-band `BRIDGE_UPPER_*`/`BRIDGE_LOWER_*`
  constants.
- `HANDLE_STATIONS`' `outset_x` column was changed from a near-linear ramp
  (0 -> 0.5 -> 1.5 -> 2.5 -> 3.0 -> 3.0, which lofts to a flat diagonal
  edge) to an eased curve that grows slowly near the neck, accelerates
  through the middle, peaks at t=0.85, then eases back inward slightly at
  the tip — producing a continuous hook/S silhouette in the loft instead
  of a straight diagonal line.

**Visual verification performed:** rendered a shaded STL front view
(matplotlib, `elev=90, azim=-90`, confirmed as the correct front-view
camera in the prior revision) after the fix and read it back with the
Read tool. Result: the centre span between the two side channels is now
**completely empty** (no slab, no bridge crossing it) — satisfying the
"most of the central width must be empty" acceptance criterion versus
054-1.webp. A zoomed render of the right channel's top confirms the
bridge stub is present as a small local extension of the channel only,
not a full-width crossbar. A zoomed render of the right horn confirms a
visible concave/hook curve on the inner edge (not a straight diagonal).

### Revision note (2026-07-21, part 3 — full-width bottom shelf, fixes disconnected-body bug)

Part 2's fix went too far: since the two bridge stubs deliberately never
meet, the exported STL had **no full-width connection anywhere** between
the left and right halves — confirmed with `trimesh.load(...).body_count
== 2` (not watertight as a single part, not printable as one piece).

Re-examining 054-1.webp again showed the missing feature: a thin,
**continuous, full-width horizontal strip** low in the central window,
well below the open back-panel area, right where the Vita's own bottom
edge rests and where the two horns begin to diverge into their V. This
strip — not the bridge stubs near the top — is the actual full-width
structural link in the reference part.

Added `build_bottom_shelf()`: a full-width (spans the entire gap between
the two channels' own inner faces, ~180.5 mm), narrow-in-height (10 mm)
strip on the BACK side only (`SHELF_THK` = 5 mm, thinner than the
channel/stub bulk since it acts as a floor/shelf, not a structural wall),
positioned just above `y_bot` (where the handle horns begin) with a 4 mm
gap. Unioned into the final assembly alongside the existing bridge stubs.

**Verification performed (both required checks):**

1. `trimesh.load('VitaGrip.stl').body_count == 1` and `is_watertight ==
   True` — confirmed: the part is now a single connected, printable body
   (previously `body_count == 2`).
2. Shaded renders from both the front (`elev=90, azim=-90`) and back
   (`elev=90, azim=90`) camera: the front view shows the shelf only as
   thin contour lines low in the window (it sits on the back face, so it
   reads as background detail, not a slab blocking the screen — the
   centre of the window above the shelf stays visually empty). The back
   view clearly shows a thin, continuous strip connecting the base of the
   two side channels, with the entire back-panel area above it open —
   matching the low, narrow, full-width strip visible in 054-1.webp.

The obsolete part-2 trade-off note above (more disconnected than the
photo, offering `BRIDGE_STUB_REACH` as a future fix) no longer applies —
the bottom shelf is the intended full-width connector and the bridge
stubs remain short/local as designed.

See the dimensions table and Design section below for the corrected
values.

### Revision note (2026-07-21, part 4 — polish pass: shelf thickness + horn curve magnitude)

Topology unchanged from part 3 (still 2 side channels + bridge stubs +
full-width bottom shelf + 2 horns, one watertight body). Two proportion
fixes, found by direct shaded-render comparison against 054-1.webp:

1. **`SHELF_THK` 5 mm -> 14 mm.** At 5 mm the shelf rendered as a thin
   tie-rod; in the photo the connecting band reads as a substantial solid
   band, nearly as thick in profile as the side channels' own Z bulk
   (~27.6 mm = `VITA_D` + front/back channel reach). Raised to 14 mm so it
   reads as a tray/band, still short of the full channel depth so it
   stays a shelf rather than a wall.
2. **`HANDLE_STATIONS` `outset_x` magnitude roughly 3-4x larger, and
   shifted earlier in the curve.** The part-2 eased curve (peak ~3.55 mm
   drift over the 46 mm horn) still rendered as nearly straight even
   though the ease-in/ease-out timing was correct — the magnitude was too
   small to read at this scale, and the growth was too back-loaded
   (produced a "boot" kink near the tip rather than a curve through the
   whole horn). Re-tuned so the outward sweep starts strongly right after
   the neck (t=0.15 outset now 3.5 mm, was 0.6 mm) and peaks around
   13.8 mm at t=0.85 before easing back to 10.5 mm at the tip — producing
   a continuous comma/hook silhouette through the horn's full length,
   matching 054-1.webp's marked curve.

Envelope grew slightly (232.5 x 130.0 x 30.6 mm -> 242.7 x 130.0 x
30.6 mm) since the horns now splay further outward at their widest point;
still well within reasonable hand-grip proportions.

**Verification performed:** shaded front-view render (`elev=90,
azim=-90`) read back and compared directly against 054-1.webp — the
shelf/bridge band now reads as a solid band rather than a rod, and both
horns show an obvious hook/comma curve rather than a near-straight taper.
`trimesh.load('VitaGrip.stl').body_count == 1` and `is_watertight ==
True` reconfirmed (single connected printable body, unaffected by these
changes).

## Key dimensions and their source

| Parameter | Value | Source |
|-----------|-------|--------|
| Vita body W x H x D | 182 x 83.5 x 18.6 mm | Official Sony PCH-1000 spec, given verbatim by user |
| Vita body corner radius | 15 mm | Given verbatim by user |
| Vita rear taper depth | 15 mm (mid-body thinnest point) | Given verbatim by user |
| Fit clearance | 0.25 mm/side | Standard FDM friction-fit clearance (0.2-0.3 mm range), per repo convention — this is a snap/friction-fit accessory, not a precision mechanical fit |
| Side channel height | 84.0 mm (= Vita H + 2x clearance) | Full short-edge span, so the channel wraps the entire 83.5 mm edge |
| Side channel front/back bite margin | 3.0 mm / 6.0 mm | Engineering judgement — enough overlap onto the Vita's own bezel/rear-taper margins for retention without covering the front screen or back panel beyond a thin lip |
| Side channel lip inset (`CHAN_LIP_INSET`) | 14.0 mm | **Structural fix (part 2)** — the front/back lips are now a narrow band local to each channel's own footprint (14 mm inward from its outer face), not a slab reaching the Vita's centreline. Prevents the two mirrored channels from forming a continuous full-width slab |
| Bridge stub (per side, x2 mirrored) | 16 mm reach x 24 mm tall x 9 mm thick, starting 12.5 mm below the Vita's top edge | **Structural fix (part 2), replaces the old full-width two-band bridge.** A shaded render showed the old bridge as a solid slab spanning ~97% of the grip's width, contradicting 054-1.webp where the centre stays open. Each stub now extends inward only from its own channel and the two stubs do not meet — centre span is fully open |
| Bottom shelf (`build_bottom_shelf`, full width) | ~180.5 mm wide x 10 mm tall x 14 mm thick, starting 4 mm above the handle attach line (`y_bot`), back side only | **Structural fix (part 3) + proportion fix (part 4).** Pixel-reference shows a thin, continuous full-width strip low in the central window (054-1.webp), right where the Vita's bottom edge rests — the part's only full-width connector (without it the two halves were disconnected, `body_count == 2`). Thickness raised 5 mm -> 14 mm in part 4 so it reads as a solid band, not a thin rod, matching the photo's proportions. Confirmed: `body_count == 1`, `is_watertight == True` |
| Handle horn length | 46 mm (was 92 mm) | **Pixel-measured from 054-1.webp** — see Revision note above |
| Handle cross-section (neck -> tip) | 42 mm wide -> 13 mm wide, tapered through a 6-station loft with an **eased outset_x curve, peak ~13.8 mm outward drift** (was ~3.55 mm) | Pixel-measured neck width (~42 mm); asymmetric taper (outer edge nearly straight, inner edge sweeps in) with a curved comma/hook silhouette. Curve magnitude increased ~4x in part 4 after the smaller-magnitude version still rendered as nearly straight — see Revision note (part 4) above |
| Concave finger-wrap scoop | up to 7.0 mm deep | Reference-photo curve style (020-1.webp) — a controller-like concave scoop cut into the outer face of each horn |
| Corner notch/tab | 9 x 4 x 3 mm, proud of the front face | Reference photo 054-1.webp — small square nubs framing the top corners of the Vita's screen |

## Reference material

Located in `D:\CAD\Claude-Projects\references\psvitaGrip\`:

| File | Used for |
|------|----------|
| `054-1.webp` | **Primary reference.** Straight-on rear view — used for direct pixel-measurement of the bridge/channel body height, the horn neck position and length, and horn taper style (this revision's main data source) |
| `020-1.webp` | Concave handle curve profile, comparison to a DualSense-style grip (side/angle view) |
| `039-1.webp` | Overall two-handle shape, angled top-down view of two units (blue/green), used to confirm how the horns curve in 3D rather than just in the frontal plane |
| `ddbcf15aaba055b923aef1a23d982c6ea072c284.webp` | Thumbnail of the reference STL (dumbbell-shaped horns + bar) |
| `newVita_1k_Grip_2.stl` / `reference_aligned.stl` | **Not used for this revision.** Its overall envelope (170 x 170 x 123 mm) does not match the confirmed PCH-1000 body (182 x 83.5 x 18.6 mm) or this design's topology, so per explicit user direction it was skipped entirely; the side-channel inner curvature was instead sculpted by eye from the reference photos, and handle/bridge proportions were pixel-measured from 054-1.webp directly (see above) |

## Design

### Coordinate system (local to this part)

Documented explicitly here per project convention, since this part's
natural symmetry plane is the Vita's own centreline rather than a single
flat bottom face:

- **+X** = right (toward the right handle horn)
- **+Y** = up (toward the Vita's top edge / shoulder-button area)
- **+Z** = toward the front (the Vita's screen faces +Z); Z=0 is the
  Vita's own front-face plane, and the Vita body occupies Z in
  `[-18.6, 0]` mm.
- Origin = centre of the Vita's front face (X=0, Y=0 at the Vita's own
  centreline).

### 1. Side channels (x2, mirrored)

A U-shaped ("[" bracket in cross-section) rail wrapping each of the
Vita's short (83.5 mm) edges: a front lip over the bezel margin
(3.0 mm), an outer rib along the Vita's own side edge (full 18.6 mm
depth), and a back lip over the tapered rear margin (6.0 mm) — so the
Vita's edge slides in and is gripped on three sides while its front/back
FACES beyond those margins stay completely open (no floor, no cover).
Built for the right side and mirrored (`Plane.YZ`) for the left.

### 2. Bridge stubs (x2, mirrored — NOT a full-width bridge)

A short (16 mm reach x 24 mm tall x 9 mm thick) local extension of each
side channel's own inner face, on the BACK side only, starting 12.5 mm
below the Vita's top edge. The two stubs (one per channel) do **not**
meet in the middle — most of the width between the two side channels
stays completely open, matching 054-1.webp where the Vita's own back
panel is visible almost edge to edge. This replaces an earlier two-band
full-width bridge design that, per a shaded-render review, produced a
solid slab across ~97% of the grip's width and did not match the
reference photo.

### 2b. Bottom shelf (full width, the part's only full-width connector)

A solid-banded (10 mm tall, 14 mm thick) strip spanning the **entire** gap
between the two side channels' own inner faces (~180.5 mm), on the BACK
side only, positioned just above the handle horns' attach line (`y_bot`).
Thickness raised from 5 mm to 14 mm in part 4 so it reads as a substantial
band rather than a thin tie-rod, matching 054-1.webp's proportions. Unlike
the bridge stubs above, this shelf **does** span the full width —
it's the single feature that structurally joins the left and right
halves into one printable body, matching the thin, continuous, full-width
strip visible low in the central window of 054-1.webp (right where the
Vita's own bottom edge rests). Everything above the shelf, up to the
bridge stubs, stays completely open.

### 3. Corner tabs (x2, mirrored)

Small 9 x 4 x 3 mm blocks, proud of the channel's front face right at the
top corner — recreating the small nubs visible in 020-1.webp / 054-1.webp
framing the top corners of the Vita's screen.

### 4. Handle horns (x2, mirrored)

Each horn is a 6-station lofted solid, 46 mm long, anchored at the bottom
of the side channel (the Vita's own bottom edge) and extending down. It
tapers from a wide (42 mm) neck to a narrow (13 mm) rounded tip via an
asymmetric loft — the outer (away-from-Vita) face stays close to a
straight vertical line while the inner face sweeps inward — giving the
hook/paddle silhouette seen in 054-1.webp rather than a symmetric pinch
or a bulbous pear shape. The `outset_x` sweep (part 4) now peaks around
13.8 mm outward drift roughly 85% of the way down the horn before easing
back at the tip, producing an obvious comma/hook curve through the
horn's full length rather than a near-straight taper. A concave scoop (up
to 7 mm deep) is cut into the outer face along most of its length for the
finger-wrap curve, and the tip is filleted on all edges for a smooth,
rounded end. The right horn is built directly; the left horn is a mirror
(`Plane.YZ`) of the right, so both stay in sync from one definition.

## Files

| File | Description |
|------|--------------|
| `macros/vita_grip_b123d.py` | build123d script — generates `VitaGrip.step` / `.stl` |
| `macros/view_parts.py` | 3D viewer — sends the assembled grip to ocp-vscode |
| `VitaGrip.step` | Generated CAD interchange file |
| `VitaGrip.stl` | Generated mesh for slicing |

## How to regenerate

```
pip install build123d ocp-vscode
python "D:\CAD\Claude-Projects\VitaGrip\macros\vita_grip_b123d.py"
```

## How to view

```
# Terminal 1 — start viewer server
python -m ocp_vscode --port 3939 --axes --grid_xy --theme dark

# Browser — open http://localhost:3939

# Terminal 2 — send the part
python "D:\CAD\Claude-Projects\VitaGrip\macros\view_parts.py"
```

## Verification checklist before printing

- [ ] **Fit clearance (0.25 mm/side)** — verify against your printer's
  actual dimensional accuracy; tighten to 0.15-0.2 mm for a snugger grip
  or loosen to 0.3 mm+ if the first test print is too tight to install.
- [ ] **Side channel bite margins (3.0 mm front / 6.0 mm back)** —
  confirm these overlap enough of the Vita's bezel/rear-taper margins to
  resist the Vita sliding/popping out under normal handling, without
  colliding with any physical buttons, camera, or vents near the edges.
- [ ] **Corner tab placement** — cross-check against actual Vita
  photos/unit for the shoulder-button and speaker grille locations, so
  the tabs don't collide with any physical buttons or vents.
- [ ] **Handle ergonomics** — this is a judgement-based ergonomic shape
  (pixel-matched to reference photos, not derived from a hand-size
  dataset); a test print is the only way to confirm comfort and grip
  security for the intended user's hand size.
- [ ] **First print is a fit test, not a final part** — print once, dry
  fit an actual PCH-1000 (or accurate dummy) before committing to final
  material/infill choices.

This part is not load-bearing in the structural-safety-factor sense (no
static load beyond normal handheld gaming grip forces), so no separate
`structural_check.py` was created. If drop-impact or high infill/strength
concerns arise, consult the print-tolerance-expert agent conventions in
this repo before finalizing print settings.
