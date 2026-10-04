# VitaGripPS5

A grip **case** for the Sony PS Vita **PCH-1000** with DualSense-style handles.
The console snaps into it from the front and is held by four lips.

Built from scratch. It shares no code, no geometry and no measurements with
`projects/VitaGrip1000`.

## The brief (user, 2026-09-25) — start here

This is the instruction the rebuild works from. It replaces every earlier
statement of intent in this file; the sections below it are history.

**Why it exists.** The socket build treated a grip case as a scaled-up
controller. One uniform scale (x1.3779) got the handle spread, the slot and the
curvature right, and made everything else wrong: handles 38 % too fat, the body
**71.10 mm** thick (the 1:1 scan is 51.60) to hold a 19.3 mm console, and the
controller's own surface — thumbstick rings, shoulder buttons, cut scars —
carried into a part that should be a clean handle.

**Goal:** a PS Vita PCH-1000 grip case with DualSense-style handles. It is a
case, not a controller. The console snaps into the case from the front and is
held by it.

**Ground truth (use these, never photos, for any dimension):**
- DualSense: `derived/dualsense_*.stl`, true scale (120 mm tip-to-tip, user caliper).
- PS Vita: `stl/console_solid.stl` / spec 182 x 83.55 x 18.6 mm.
- Photos and drawings are for intent, shape and placement only. No dimension may
  be derived from them.

**Keep (verified correct in the socket model):** the console slot dimensions,
the separation between the handles, and the handles' curvature.

**Fix:**
- Handle size: handles keep the **real DualSense proportions**, not scaled x1.378.
- Thickness: 71.1 mm is wrong. Size the body to hold a 18.6 mm console, not to
  the scaled controller.
- Surface: no controller features. No thumbstick rings, face buttons, touchpad,
  or L1/L2/R1/R2 shapes. Cut faces are clean, smooth surfaces with no leftover
  marks.

**Back:** a back wall behind the console with the **99 x 41 mm rear touch panel
cut-out** (user's choice over the fully open centre the references show). The
references (`054-1.webp`, `lateralrearbackview.png`, `psvitarearbackside.webp`,
`BackView*.png`) show the back's overall form: the handles cup the console's
ends, and the top edge with the L/R buttons stays uncovered.

**Retention:**
- The case holds the console at its ends; each handle cups one rounded end.
- **4 lips, 2 on each handle:** one where the console's rounded end meets its
  top edge, one where it meets its bottom edge. Each overhangs the front bezel
  only — never the screen, sticks, buttons, speaker or shoulder buttons.
  Placement reference: `039-1.webp`, blue grip, for position only.
- **Insertion is from the front.** The console is pushed in screen-up; the lips
  deflect as it passes (lead-in on their top face), then snap back over the
  bezel. The back wall stops it.
- Material is **PETG**. Lip overhang, thickness, lead-in and handle-wall flex
  come from `print-tolerance-expert`. It must insert without yielding and still
  hold firmly.

**How the agents are used:** `perspective-checker` on each reference before it
is compared with a render; `print-tolerance-expert` for clearances, lips and
walls; `cad-designer` builds; `form-auditor` measures handle girth, thickness,
lip positions and leftover controller features against the DualSense and Vita
STLs; `/verify`, then a render the user looks at. No STL is baked without the
user's approval.

**Verification:** every item under *Fix*, *Back* and *Retention* is checked by a
measurement and by a render the user looks at. A passing number does not
overrule the picture. Snap-fit strength and insertion effort are unproven until
a test print.

### Brief amendments (user, 2026-09-25, after previews r1 and r2)

**The case is an oval around the Vita, and the handles hang from its ends.** The
user's markup is `renders/case_preview_r2/front__top.png` (drawn over the r2
render); the sketch is `renders/case_preview/psgripsketch.jpeg` (stored rotated
90 deg). Read from them:
- The outer edge follows the console's oval end from the top corner down, and
  carries on into the handle's outer edge without curving inward below the
  shoulder. r2 read as "a 60s TV on legs": the widened shoulders bulged out past
  the handles, so the handles looked recessed under the console.
- **It is an oval, not a straight line** (user, after r4). The markup line was
  read as "straight" and gated as straight within 2 mm; r4 held x = 95 for 90 mm
  and came out square. The pocket itself was also faceted — the convex hull of
  the voxel console mesh, with a flat ~30 mm end segment and chamfers. The
  pocket is to be a smooth oval; see `renders/case_preview_r4/plan_oval_compare.png`.
- The inner edge runs diagonally from the tip up to the console's bottom corner.
- **Lips: 2 per end, both on the rounded end arc** (one upper, one lower). The
  top-edge and bottom-corner fingers are removed.
- **The handle dictates the rounded exterior — in section, not only in plan.**
  r4 met "straight outer edge" with a flat vertical end wall (29 mm tall, square
  top edge, a 20 deg crease into the handle) and read as a box on legs again.
  Each end carries the handle's own rounded cross-section from the junction,
  around the end, to the top corner: one rounded lobe per end, continuous with
  the handle, no flat face, no crease.
- **Method (user, after r4): "you have a DualSense, just extend the middle of
  the control and you will have the curvature."** Split the 1:1 scan at x = 0,
  move each half out rigidly, fill the gap with the centre section. Measured
  (`scratchpad` survey, 2026-09-25): 26 mm/side with the Vita's face at Z 7 and
  its centre at Y -2.5 puts the 3 mm wall around both ends inside DualSense
  material except the Vita's two bottom corners (227 mm2 missing, in the gap
  between the handles; 2 mm2 at the top). Those are filled by a bar along the
  bottom edge, which the sketch's back view shows. Plot:
  `renders/case_preview_r4/extend_middle_fit.png`.
- **Extend the middle in X and Y** (user, after r5 — "almost great"). X only
  (r5) put the Vita over the handle roots: the handles hung 11 mm and it read
  as a frame with two blobs. Measured: 26 mm/side in X plus a 30 mm band
  inserted at 1:1 Y = 10 (inside the joined body), Vita face Z 10, Vita Y
  -9..75.5 → the handles hang their full 47 mm and only 123 mm2 of end wall is
  missing, at the ends of the top and bottom edges. Plot:
  `renders/case_preview_r5/extend_xy_fit.png`.
- **The Y extension is a stretch, not an inserted slice** (user, after r6). An
  inserted 30 mm band made each end straight for 32.5 mm (x 102.3) and left
  extrusion creases on the back; stretching the same zone keeps the end one
  continuous curve.
- **Keep r5's pocket and lips — "perfect"** (user).
- **Handles a bit bigger and at least 20 mm longer at the bottom** (user).
- **The back follows the DualSense's own contour** (user: r5's flat plate
  between two blobs "is not respecting the contour of the DualSense"). The
  extended controller's underside is the back; material is added only where
  it is thinner than the back wall, following the same curve.
- **No triggers or shoulder-button shapes** (the stretched L1/R1 knob of r2).
- The Vita's **L/R buttons** sit on the top edge at about |x| 58–85 mm
  (pixel-read from `Fixed_dimensions.webp`, +-2 mm, unverified); the case stays
  clear of them. Top corners end rounded at >= 3 mm wall.
- Fingers 15 mm wide with a 1.0 mm root fillet; retention is estimated weak
  (1.6–3.2 N from four fingers vs 2.6 N console weight) on a console mesh whose
  edge shape is not trustworthy; settle by test print.

### Round 7 (user markup on r6, 2026-09-26)

The user marked `renders/case_preview_r6/` (4 images, drawn over the renders):
"the x are things that shouldnt exist, those bumps and warps, also i added x
were the triggers of the dualsense were added ... those triggers are not
needed". Lines: the back of each lobe one curve from handle tip to top corner;
the plan outer edge one curve from the top corner into the handle; the
underside one arc in side view.

Measured on r6 before changing anything: the X'd bumps were the lobe swell
around the finger pits (back 3-4 mm deeper at |x| 88-95, Y 10-40); the X'd
corners were the DualSense triggers (|x| 70-80, Y 58-78, Z -29 against -20).

What r7 (`macros/build_case_ext.py`, preview `renders/case_preview_r7/`) does:
- **Y extension is a stretch** (1:1 Y -8..40 stretched by 30, C1 density).
- **Lobe swell kept but broad** (sigma 10, one-shot scaled bump): the pits
  still need it - without it the upper pits broke through the back (0.05 mm
  wall). Narrow (r6, sigma 3.5) it read as the two X'd bumps.
- **Plan warp**: each end swollen outward to the upper convex hull of its own
  plan outline (max shortfall 2.5 mm at Y ~10).
- **Back = one convex arc per X column** (lower convex hull of the scan
  underside, monotone above the pocket centre), faded out on slopes > 45 deg
  and near the plan edge; the required back (-12.5 under the ring) is a
  ceiling surface met by smooth-min.
- **Trigger zones replaced**: at the top corners (|x| > 55, Y > 52) the scan
  below the floor is removed and refilled by that arc, rolled up into the
  corner clip. The triggers are hooked paddles; cutting from below (runs 1-12)
  only reached their undersides.

Measured on r7 (profiles r6 -> r7): side silhouette monotone from the handle
belly -31.9 to -16.5 at Y 76 (r6: 2.6 mm step at Y -16, trigger dip to -29);
plan outer edge monotone, x at Y 20 102.8/103.5 -> 105.1/104.8 (L/R), no
waist - **but a straight taper over Y -8..44, not a bowed arc**. Gates:
watertight, 1 body, genus 2, back >= 3.70, pits >= 3.48 except the upper-left
pit at Z 13.3 (2.77 < 3.0, top 0.3 mm of the wall). Known and not fixed: a row
of 1-2 mm teeth at each top corner beyond the wall end, where the zone refill
meets the upper trigger paddle above the floor; faint wrinkles on the lobe
backs. Not yet seen by the user.

**form-auditor on r7 (same day) - DEFECTS FOUND**, beyond the builder's own
windows: a **crease across both lobe backs at Y 52.5-53.5** (|x| 58-100, 24-32
deg at |x| 64-79; r6 had none there) with a **basin at (+-79, 53)**, z -22.9 R
/ -21.1 L - Y 52 is where the trigger zone starts (`Y_TZ0`), so the zone
boundary is the likely source (not yet verified). The side-silhouette dip is
**0.89 mm** (Y 45-53, R only), not 0.6. A 0.6-1.0 mm hollow remains along the
lobe's outer edge (|x| 97-101, Y 19-42). Plan outline: a 1.5 / 2.0 mm step at
Y 63-64 and a 1 mm staircase to Y 70 at the corner; the Y -8..44 taper is
straight (bow 0.04-0.11 mm). The corner teeth are 0.74 R / 1.1 L mm at Y 60-70,
Z -9..-11 - r6 had the same depth there. Confirmed: r6 bumps gone (<= 0.2 mm at
|x| 88-96), trigger dips gone (<= 0.34 mm, was 7.7), r6 step at Y -16 gone,
handles unchanged. The audit found r7 not mirror-symmetric (9.4 mm max);
location not found. Scripts: session scratchpad `audit/a1-a12.py`.

### Round 8 (2026-09-26, user: "yes" to fixing the crease and the plan bow)

**Crease cause, measured:** between Y 36 and 52 the scan underside already
drops into the trigger (x 70: -17.8 -> -20.2) while the convex target stays
level; r7 only added material outside the trigger zone, so the back followed
the scan down and the zone (from Y 52) lifted it back - crease + basin.
**Fix:** removal outside the zone too (ends only, faded on slopes and near the
plan edge), as a cut to the same smooth underside, eased in over its first
0.5 mm (a hard switch cut exactly to flank chords - stepped hairlines).
Re-running form-auditor's own scripts on r8: turn across Y 52.5 at |x| 64-82
**<= 5.7 deg** (r7 24-32); side-silhouette dip **0.34 mm** (r7 0.89); crest
re-deepening 0.33 max; trigger zone and plan outline unchanged; gates as r7.
Unchanged: 10.6-11.4 deg turn at |x| 88-94 (r7 11-13), the 0.75-0.99 mm hollow
at |x| 97-101 Y 19-42, the corner teeth, the upper-left pit's 2.77 at Z 13.3.
Renders: `renders/case_preview_r8/`.

**Plan bow - the user's decision, not made.** The user's drawn lines on
`r6_front__top.png` bow 3.4 (L) / 3.8 (R) mm off their chord over ~99 mm,
peak ~36 % down from the top corner (pixel read on a perspective render, scale
from the 220.1 mm width - intent only). r8's outline over the same span already
bows 5.2 / 4.0 mm, but peaks 18 % down, at the upper pits (Y 44): a straight
taper and then the corner turn. An arc with the user's distribution either
adds width (the smallest parabola never inside r8's outline adds 9.4 L /
6.5 R mm at Y ~4) or removes it near Y 44, where the upper pit walls are at
their 3.48 mm limit.

What did not work, in order (all in r7's run log): cutting the triggers
before the fill (sealed voids); one dilating envelope for fill and back
requirement (spread 7 mm of fill back into the trigger zone); per-cell fill /
cut / ring formulas (terraces at every boundary); a slab over the whole plan
as a hidden sliver (poked out of the steep flank - serrations); a pit-bottom
ceiling (fill on the flank beside the upper pits - serrations).

### Round 9 (user markup on r8, 2026-09-30)

The user marked three r8 renders in GIMP: `renders/case_preview_r8/*.xcf`,
one layer each, painted straight onto the render. Flattened copies are saved
next to them as `*__markup.png`. There is no written note. The readings below
are the session's interpretation, matched by eye on perspective renders. **None
of the marks has been located in model coordinates yet.**

- **`r8_corner_back_R`** (right lobe meeting the bar, from below/behind): a
  smooth grid of section lines drawn over the whole lobe-to-bar transition, and
  the row of teeth along the lower lobe/bar edge painted out in blue. The
  original render shows the upper corner teeth, a curved scar across the middle
  of the flank and a vertical seam below the teeth, all inside the drawn grid.
  Read as: this region is one smooth surface, with no teeth, scar or seam.
- **`r8_back__iso`** (left lobe, from behind): the lobe is outlined along its
  crest and lower edge, with five evenly spaced cross-lines. The original has
  lumps on the upper back and wrinkles near the bar. A clean line is drawn over
  the serrated edge at the lobe's bottom end. Read as: one clean, even tube, and
  no serrated end edge.
- **`r8_front__iso`** (front): the V-notch where the right handle meets the
  pocket wall is painted out in blue, with a short line carrying the edge
  down. Read as: no notch. On the left handle, an outline plus two cross-lines
  and one long line. Read as "smooth, even sections". **Not confirmed**: it may
  instead ask for a shape change (outline or girth).

Probably the same as defects r8 already listed as not fixed (match by eye,
not measured): the corner teeth (Y 60-70, Z -9..-11), the wrinkles on the
lobe backs, the 0.75-0.99 mm hollow at |x| 97-101 Y 19-42, and the 10.6-11.4
deg turn at |x| 88-94. **New** (not in r8's list): the front junction V-notch,
the flank scar and the lower lobe/bar teeth.

**Round 9 was run as one cycle** (2026-09-30 to 10-01): one register, one fix
pass, one review. The scratchpad files are listed at the end of this section.
The user's decisions: fix all 7 cause groups, plan bow **option B** (remove
width near Y 44), left handle **kept as scanned** (it is 4-9 % smaller and
3 mm shorter than the right, the same as the DualSense scan).

Located by the first audit:
- **The 9.4 mm asymmetry** is a thin fin on the right side only (x 56-66,
  Y -13, floor up to Z 12). The user's blue V-notch on the front view and a white
  mark on the back view are both this fin. Cause (measured): `C_plan` was two
  boxes, and the fin was the strip left between them.
- **The seams and the flank scar** lie on the trigger-zone polygon's 1 mm cell
  boundaries.
- **The upper pit walls** thinned above Z 10.6, where the required box ended.

Fix pass (`build_case_ext.py`, docstring now says round 9; new `--dump`
option):
- one smooth bottom-opening outline;
- the pit's required box taken up to the lip top;
- the moderate underside offset applied as a vertex move;
- the edge fill faded in 1-5 mm inside the silhouette;
- a smooth trigger-zone contour that reaches the silhouette above Y1-1;
- the front cut rolled into the skin.

Runs that failed are recorded in macro comments.

Review: the same sweep and thresholds on r8 and r9.

| | Entries |
|---|---|
| Fixed | D4 (Y 53 turn), D5 (pit walls 2.67 / 2.97 -> 3.48 / 3.51), D7 (corner plan step), D9 (fin), D13 L |
| Improved | D1 (corner teeth 1.21 / 0.76 -> 0.85 / 0.59), D3 (edge hollow 1.12 -> 0.39), D6 (symmetry 8.94 -> 4.66), D10, D11, D12 L, D13 R, D17 |
| Worse | D2 (lobe lumps), D8 (bow 5.90 L at 26 % / 4.85 R at 21 %, against the requested 3.4 / 3.8 at 36 %), D12 R, D15, D16 (folds) |
| Unchanged | D18, an inboard-flank line inherited from the scan. Bend radius 3.2-4.6 mm; going under 8 deg needs about 14 mm, i.e. reshaping the handle (user's call) |
| New | D19-D21 (zone-boundary chains and folds), D22 (0.7 mm knife wedge at the bottom-opening junction: the new opening edge crosses the skin), D23 (corner refill ledge 2.3-2.7 mm, flat top at the floor Z; it is the user's "patched" look on `r9_corner_back_R`), D24 (serration along the bottom bar's lower edge), D25 (crease across the back at Y -3; back minimum 3.54), D26 (right lobe back non-convex 0.87) |

**User, after the r9 renders:** the corner looks patched, and the sharp
corners need filleting. Fillet room was measured as edge families D27-D32:

| Family | Fillet that fits |
|---|---|
| D27 corner clip | 1.4-1.8 mm |
| D28 bottom opening | 1.2 mm |
| D29 front-cut boundary | 2.9 mm |
| D30 top edge | 1.3 mm everywhere |
| D31 back/bar edges | 5.5 mm on 90 % of the length |
| D32 junctions | 1.6-3.0 mm |

No fillet fits at the folds and the wedge until those are fixed. L/R button
clearance is not modelled.

Hard gates: watertight, 1 body. Handles +22.00 mm, girth x1.100. Pocket, lips,
window and camera are within 0.007 mm of r8. Renders:
`renders/case_preview_r9/`.

Files are in `audit/r9/`: `register_r9.md`, `fix_report_r9.md`,
`review_r9.md`, the r8 and r9 preview STLs, the r8 macro
(`build_case_ext_r8.py`) and `scripts/`.

### Round 10 (fix pass on the r9 register, 2026-10-01 to 10-02)

The user approved all r9 cause groups and gave these decisions:
- Fillets D27 1.5, D28 1.2, D29 2.5, D30 1.3 and D31 1.9 mm. D32 was not
  selected.
- D3 yields to D8.
- D18 is kept as scanned.
- During the pass: the bottom opening ends at |x| 66.75 R / 68.75 L, which
  keeps 3 mm or more of wall. Reaching 70 would have left a 0.7-1.4 mm sheet
  where the handle front face is undercut.
- The plan-trim window stays at Y 46..52, and the L bow is accepted at 4.76
  (peak at y 53, 9 %). Widening the window to 50..57 gave L 3.96 at 28 % but
  dropped the L upper pit wall to 2.60.

The fix pass needed three designer runs. The two intermediate defects it
created were fixed, with their causes measured:
- **D33**, the L upper pit wall at 2.83. Bisected with `--dump` to the plan
  trim; its Y window now ramps out over 46..52.
- **D34**, genus 4. Located by a box-by-box genus comparison: two
  zero-thickness contacts on the floor plane, Z -8.80. One came from the trim
  moving vertices in Z, the other from the zone-clear top sitting exactly on
  the floor. Now the trim moves vertices horizontally only, and the clear stops
  0.05 above the floor.

**Fillets.** Only D29 is applied. A rolling-ball search over a refined mesh
hung at 4.1 GB in one run and grew to 1.45 M faces in another. Vertex
projection worked on D29, but on the other families it hit the face cap,
folded faces, or made 35 k degenerate faces. A per-family local
remesh-and-open/close method is proposed and has not been built.

Review (same r9 sweep code, run fresh on r9 and r10; `audit/r10/review_r10.md`):

| | Entries |
|---|---|
| Fixed | D4, D7, D9, D13, D20, D24 (0.70 -> 0.00), D26 (0.87 -> 0.15), D33, D34, D8 R (3.72 at 32 %); corner asymmetry 4.52 -> 1.90 |
| Accepted by user | D3, D8 L (4.76 at y 53), D18 |
| Improved | D10 (R 9.3), D11, D12, D17, D21, D23 |
| Worse | D1, D2, D16, D19 (all now read the D35 slit), D5 R, D15 R, D27, D32 |
| New | D35-D38, below |

New entries:
- **D35, the user's "patched" corner.** It is actually an open air slit
  0.5-0.9 mm wide and 7-12 mm deep across each lobe back, on the arc
  (±84,56.8) to (±98,55.8). Cause, measured: the zone clear stops at dpit
  4.50, but the refill is the body outline inset by `REFILL_IN` 0.5. The band
  between them is cleared and never refilled.
- **D36, folds on the outer flank.** 341 folded edges (r9 had 63) at
  |x| 102-105. Cause not verified.
- **D37, a groove beside the R upper pit.** The D29 fillet clamp guarded only
  Z 13.3, so the R pit wall is 1.41-0.34 at Z 13.45-13.6. This is the D5 R
  regression.
- **D38, a crease band on the lower outer flank** at |x| ~101, with a turn of
  17-27 deg. The plan trim is suspected, not verified.

Topology: watertight, 1 body, genus 2, 278.69 cm3, and 3 degenerate faces
(r9 had 20). The back minimum is 3.54 L. Renders:
`renders/case_preview_r10/`. Files: `audit/r10/` (`fix_report_r10.md`,
`review_r10.md`, the r9 macro, the r10 preview STL, `scripts/`, logs).

### Round 11 (2026-10-02)

The user saw the r10 corner as "puzzle pieces added to the main frame". The
corner had been cut out and a separately built block glued back in (see
`docs/lessons.md`, "Ten defect IDs were one glued-in patch"). Decisions:
- the corner becomes one continuous surface;
- no cropped face;
- the console sits closer to the surface.

**Lip sizing** (print-tolerance-expert, `audit/r11/lip_sizing_r11.md`):
- LIP_T 3.4 → **1.2**, bound by printability (6 layers at 0.2 mm). The
  console face is now 1.40 below the lip top, which sits at Z 11.40.
- **Snap retention is weak or unverified at any LIP_T.** It depends on the
  Vita's front-edge radius, which has not been measured, and the insertion
  safety factor is 2.0. The user's decision: judge it on a test print.

**Fix pass:**
- The clear and refill booleans are deleted. The corner is now the lobe cut
  to the target surface U, on a 0.25 mm local grid. There is no slit, and
  genus is 2.
- **D8 R:** the cause was measured. `PIT_REQ_TOP_Z` following the lip down
  shrank the lobe swell. It is now decoupled at 13.6, and R is back to 3.72
  at 32 %.
- **The corner end stayed a cliff about 20 mm tall.** The upper pit is only
  1.8-4.5 mm from the top-edge opening line, so there is no room to round it.

**Shoulder buttons** (reference-analyst, `audit/r11/shoulder_buttons_r11.md`):
- Measured on `sources/psvitaGrip/Vita 1000/psvitaManualJoin_decimated.stl`:
  L at x -54.2..-82.3, R at +53.8..+81.55, Z -1.5..5.0, all ±0.4.
- A 23 mm finger reaches 90-91 % of each button. Moving the opening line to
  make room for a rounding costs reach.

Review (`audit/r11/review_r11.md`):
- Fixed: D5, D35, D37.
- New:
  - D40, a ledge 1.43 mm below U at y 53;
  - D41, the cliff;
  - D42, a crease from a zone-weight fade over only 2 mm.

### Round 12 (2026-10-02)

The user's decisions:
- Do not cut the lobe back or move the opening line, because that makes
  jagged texture. **Fill instead**, outside the button and its finger
  envelope.
- **One flat cut at the latch top, Z 11.40, across the whole part, handles
  included.**
- Fillet the new edge with the largest radius that fits, up to 3 mm.

Fix pass:
- **The top cut is one height-field operation**, `top_cut()`, on a 0.25 mm
  grid. It replaces the front cut, its blend, the end roll and the top-edge
  opening prism. The rolled edge is a rolling-ball opening of that same
  field, not a separate fillet stage.
- **Max Z is 11.4000** (r11 had 16.11); the plane's Z spread is 0.0017.
- Achieved radius, measured on 243 sections normal to the edge: handles and
  flanks have a median of 3.2-3.9. It is about 1.05 at the lobe end and
  0.50-0.56 at the bottom-opening ends (D44).
- **Corner:** no fill fits outside the finger envelope, because the disc at
  the last pressable point already touches the lobe end. The end is a wall
  12-16 mm tall (20 at S), with a 6 mm foot fillet below Z -2.8.
- The upper pit walls are 3.10 / 3.24, a 0.10 margin.

Review (`audit/r12/review_r12.md`):

| | Entries |
|---|---|
| Fixed | D4, D13, D22, D26, D36 (folds 379 -> 91); D17 and D29 replaced by the flat top |
| Open | D39 (films: the rolling-ball opening lowers the floor and erases the film rim, measured), D40 residual crease 17-37 deg, D41 (the squared corner) |
| New | D43 knife-edge cusp at S (±87.3, 58.7, Z -4..0), cause not verified; D44 unrolled bottom-opening edges (C and the pocket are cut after `top_cut`, measured); D45 slivers at the R handle tip; D46 turn spike at the handle-root top front |
| Not defects | the nicks on the handle flank (scan texture, also in r11); the "serrated crest" (no period, at real outline corners) |

- Gates: watertight, 1 body, genus 2, 0 sealed voids, 1 degenerate face.
  Slit check: none enclosed; 108 of the 118 small gaps are open vertically.
- The handle girth gate (stations y -43 / -59 / -70) no longer covers the
  part the flat cut changed: the cut removes 3-6 % of the section area at
  y -16..-40.

### Round 13: finishing pass, BAKED (2026-10-02; superseded by r16 below)

The user: "r12 looks almost good enough", so the round was a finishing pass,
not a redesign. The r12 form is kept.
- A last macro stage, `finish()`, switched by `FINISH_ON`, makes the local
  fixes and a light smooth: travel at most 0.2 mm, median 0.008.
- `finish_locks()` holds these at zero travel: the pocket, lips and fingers,
  the flat top plane, the pit walls, the window and camera, the back
  underside under the pocket, and the bottom-bar edge strip.
- Fixed: the D45 slivers and the degenerate face. Folds went 91 → 37.
- A first version (`audit/r13/case_preview_r13_v1.stl`) failed two checks:
  the back at 3.486, and a 0.22 mm wobble on the bottom-bar edge. The last
  two locks fixed both.

Checks (form-auditor, `audit/r13/check_r13.md`, plus the quick-fix
re-check):
- Passing:
  - watertight, 1 body, genus 2, 0 degenerate faces, 0 sealed voids, 0
    enclosed slits;
  - pit walls 3.10 / 3.24 / 6.12 / 4.99;
  - max Z 11.4000; the console face 1.40 below the top;
  - pocket, lips, window and camera deviation 0.000;
  - handle girth x1.100, length +22.00 / +21.98.
- **Back under the pocket: 3.499 at (-65.0, -8.5) against 3.5.** This is
  r12's own value. **The user accepted it** (0.001 mm, far below print
  resolution).

Known artifacts left in, with sizes against 0.15-0.2 mm layers and a
0.4 mm nozzle:
- vertical ribbing at the lobe/bar edge near the corner (D48): 0.20-0.37 mm,
  likely faint ribs;
- a groove under the bottom bar at y -9.2: 0.13-0.48 deep, 1.6 wide (already
  in r12);
- floor films beyond the corners (D39): about 1.4 mm² per side, thinner
  than a layer;
- the cusp at S (D43): under 0.3 mm, will not print.

**Baked:** `stl/VitaGripPS5_case_r13.stl`, a copy of
`audit/r13/case_preview_r13.stl` (SHA-256 `56141b26…`). `render_check`
passes. The 2026-09-14 `stl/VitaGripPS5.stl` (the old socket-grip) was kept,
unchanged.

**Verify on the first print:**
- snap retention and insertion (`audit/r11/lip_sizing_r11.md`: unverified,
  insertion safety factor 2.0, and it depends on the Vita's front-edge
  radius);
- the shoulder-button reach;
- the lip clearance with the real console.

**Rear features** — from `sources/VitaGripPs5/ps_vita_1000_diagrama_completo_ovalado.svg`
/ `.png`, a diagram the user supplied (made with Claude web). Its `≈` values are
**estimates**, not measurements; the diagram says so itself:
- Rear touch panel **≈ 108 x 55 mm**, 16 mm from the top edge, 12.5 from the
  bottom, 37 from each end. Replaces the 99 x 41 window.
- Rear camera **≈ 8 mm** diameter, **≈ 7 mm** from the top edge, centred. It
  must stay uncovered.
- The diagram draws the ends as semicircles R 41.75; **the pocket does not use
  that**. Measured on `console_solid.stl`, the real end is fuller: half-width
  83.4 / 72.3 / 63.6 mm at 30 / 38 / 41 mm from centre, against 78.3 / 66.6 /
  57.1 for the semicircle. A semicircle pocket would not fit the console.

### Rounds 14-16: user markup on r13, handle trim, BAKED r16 (2026-10-02 to 10-03)

The user marked four r13 renders in GIMP (`renders/case_preview_r13/*.xcf`:
`front__top`, `back__iso`, `corner_back_R`, `corner_back_R_v1`) and said they
were errors, added "a cut that should appear on both sides of the handle", and
asked for a symmetry check. The marks were located by ray-casting through the
red pixels with cameras validated against the renders (silhouette IoU 0.997
and 0.990). **The cut** is a straight line across the left handle at y about
-68 in the top view. The user decided: **trim both handle tips flat at y = -68.**

- **r14** (`audit/r14/`): register by form-auditor, then a fix pass. Reviewed
  and **rejected as a bake**: a cut-start cliff on the R rim (D58), the
  accepted L rim wall altered up to 1.65 mm (D59), the bar roll covering 59 %
  of the edge with folds 37 -> 153 (D60/D61), slivers 307 -> 623 (D62).
- **r15** (`audit/r15/`): L restored, R rim built from the mirrored L. It left a
  lens-shaped scoop on the R flank (seen in the render) and 3 gates unmet.
- **r16** (`audit/r16/`): the R rim cut dropped (`RIM_CUT_ON = False`), scoop
  gone. Reviewed by form-auditor (`audit/r16/review/review_r16.md`):
  **ACCEPT WITH LISTED ARTIFACTS**, no blocking item.

**What r16 changes against r13** (form-auditor numbers):
- both handles end in a flat face at y -68.0025 with a 3.0 mm roll (caps
  289 / 455 mm2); the handle length gate is now +14.82 L / +11.83 R and the
  third girth station is at y -63.3 (D49, D55);
- D11 seam kink fixed; D40 ridge about halved (0.25 -> 0.12);
- back under the pocket: 3.4256 -> 3.5256 on a 0.05 mm window (D56);
- rear face ymax 78.745 -> 78.550;
- bar rear-bottom edge: a 0.5 mm bevel over about 94 % of |x| <= 66 (D51);
- mirror symmetry max 3.57 -> 2.54 mm, p99 2.66 -> 2.20;
- locks (pocket, lips, flat top Z 11.4000, pit walls, window, camera,
  bottom-bar strip) unchanged within 0.005 mm.

**Back thickness, correction to round 13:** the accepted "3.499 against 3.5" was
read on a coarse grid. On a 0.05 mm window r13 read **3.4256** at (-65.05,
-8.70). r16 reads 3.5256.

**Not fixed from the user's marks** (r13 state, left in on purpose):
- the R/L rim asymmetry (D52, M1a/M2d): R is wider by 0.3 mm at y 62 to 2.25 at
  y 70, z -10, the scan's own asymmetry;
- the rim ripple (D48): p-p over 0.2 mm for 4.6 mm on R, 2.9 on L;
- the rim top roll (D50), the R crease (D19/D16/D2, turn 25 deg).

Folds are 43 (r13 37) and slivers 422 (r13 307). Measured harmless: the 7 new
folds stand off at most 0.018 mm, the new slivers are zero-area needles in the
bevel band, and the 10 folds above 0.15 mm are r13's own. The `--no-bar` variant
(`audit/r16/case_preview_r16_nobar.stl`: 38 folds, 256 slivers) leaves the bar
edge sharp.

Artifacts left in (sizes against 0.15-0.2 mm layers and a 0.4 mm nozzle; the full
paste-ready table is in `audit/r16/review/review_r16.md`):

| Artifact | Where | Size |
|----------|-------|------|
| Rear-bottom bevel (D51) | bar rear, abs(x) <= 66 | 0.5 mm; steps 0.15 / 0.26 at x 56.0 (old 0.45 mm rear-face recess, D60) |
| Bevel taper ends | abs(x) 66-78 | lumps 0.15-0.2 |
| Rim top films (D39) | x 84-101, y 58-78 | 167 R / 156 L columns under 0.4 mm (r13 130 / 145): slightly worse |
| D40 remainder | underside y 52.6-54.3 | ridge 0.10-0.14 |
| Slit lips M1b3 / M2c | R (85.2, 58.9, -22.4) / L | moved 0.071 / 0.063 vs r13 |
| Unapproved vertex moves (D66) | about a dozen spots, e.g. (-104.8, 10.1, 10.4) | up to 0.226, 1-10 vertices each |
| Back minimum | front strip y -8.70, abs(x) 62-66 | 3.5255 (margin 0.026 over 3.5) |

Not swept in the r16 review: D38, the fillet families D27/D28/D31/D32, the
groove at y -9.2, D44's roll radius, the handle-tip render. The slice test was
in Z only: the README does not state a print orientation.

**Baked:** `stl/VitaGripPS5_case_r16.stl`, a byte copy of
`audit/r16/case_preview_r16.stl` (SHA-256 `4AAF87F7...12EF`). `render_check`
passes. `stl/VitaGripPS5_case_r13.stl` is kept (SHA-256 `56141B26...`), as is
the 2026-09-14 `stl/VitaGripPS5.stl`. Macro: `macros/build_case_ext.py`, docstring
"round 16" (switches `RIM_CUT_ON = False`, `BAR_CUT_ON`, flag `--no-bar`).
Rejected paths are in the macro comments and in `audit/r14/` to `audit/r16/`.

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

## Status (updated 2026-09-14)

**Rebuilding from the DualSense scan, in progress.** The grip shell is cut from
the watertight DualSense mesh (`derived/dualsense_stripped.stl`) by a socket
cutter derived from `console_solid.stl`, plus a rear touch panel window. All
placement lives in `macros/socket_placement.py` so the build, the overlay
render and the live viewer share one `pose()` (see `docs/lessons.md`, "the gate
must share the datum it tests").

**The working surface is the live pyvista window, not the STL.** Edit
`socket_placement.py`, and `tools/watch_model.py` repaints within ~1 s. Baking
an STL is a separate, explicit act that requires the user's approval — see
*Workflow* below.

**Measured 2026-09-14**, `build_socket_grip.py --no-write` at defaults
(`DEFAULT_Y=35.0`, `DEFAULT_SINK=17.0`, `DEFAULT_TILT=0.0`):

```
stripped grip  scaled 1.3779 -> 222.40 x 156.26 x 71.10 mm  vol 984.0 cm3
console        183.40 x 84.95 x 41.06 mm  (raw 182.70 x 19.30 x 84.25)
placed at      Y 35.00  Z 25.02  tilt 0.00 deg
window         99.0 x 41.0 mm at Y 28.60  removed 78.9 cm3 (12.06 %)
result         222.40 x 156.26 x 71.10 mm  vol 575.3 cm3
               watertight True  bodies 1  genus 4  faces 215948
               removed 408.7 cm3 (41.5 % of the grip)
```

### OPEN DEFECT — the seat wall is twisted

**Unresolved. This is where work stopped.** The seat's outboard wall is not
flat; the user identified it in the viewer and annotated it
(`sources/psvitaGrip/Error.png`). The cause is *not* established.

A prismatic cutter was tried and **reverted**: it improved every scalar (wall
vertical, cutter bottom spread 15.00 → 0.0000 mm, genus 4 → 1, seat floor
183.40 mm instead of 179.91) and the user reported the result as worse on
sight. The hull path is what is in the file. Do not re-apply the prism without
first establishing from a picture what is actually wrong. See `docs/lessons.md`,
"every scalar improved and the part got worse".

Known and measured, but **not** proven to be the defect the eye is objecting to:
the hull cutter is a barrel — width 179.91 at the seat floor, 183.40 at
mid-height, 181.69 above it, then a riser seam. The seat floor is therefore cut
*narrower than the console it must hold*.

### The rear touch panel window

Cut through the seat floor, opening the Vita's rear touch panel. Verified by
ray probe: 0 hits at five stations inside the window, 2 hits at four control
stations outside it (the controls are what make the zeros meaningful).

**Size is 99 x 41 mm ±6 mm — treat the tolerance as real.** The IGN
infographic (`Fixed_dimensions.webp`) draws a red annotation box around the
panel, 246 x 101 px. Six attempts to segment the panel tonally all disagreed,
so that box is the only usable read. Converting it to mm is the weak link: the
console's own width in that view reads 403–452 px by method, giving a panel
anywhere in 99–111 x 41–46 mm. **Cut at the low end deliberately** — a window
inside the true panel still exposes it; one outside it eats structure.

Position came from the FRONT view, whose screen rectangle gives a clean datum
the BACK view does not: the panel sits ~6 mm toward the console's **top** edge.
That direction is solid; the magnitude is soft (the same grid read the X centre
17 px inconsistently).

**Not sourced from `console_solid.stl`** — measured, it is a voxel-remeshed
envelope with no surface features (10667 mm² of +Y area in a single 1.25 mm
bin). **Not sourced from `BackDetailedView.jpg`** — that is the AI-generated
fake blueprint, 173 mm overall width for a 182 mm console.

### Workflow

1. **Launch the viewer**: `python tools\watch_model.py`. Requires a display.
2. **Edit** `socket_placement.py`. The window repaints automatically.
3. **`c`** toggles OVERLAY (operands: shell, red socket cutter, green window
   cage) ↔ CUT (the boolean result). Both are needed — a coherent overlay can
   still cut almost nothing.
4. **Restart the viewer after editing `watch_model.py` itself.** It is not on
   its own watch list, so changes to the *viewer* never trigger a repaint.
5. **Never write an STL without the user's explicit approval.** Use
   `--no-write`. The STL is a bake, not the working artefact.

**`VitaGripPS5.stl` on disk is stale** — 570.4 cm³, the hull cut with the
window centred at Y 35 before the offset was corrected. It does not match the
current scripts.

What is on disk and trustworthy:

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
