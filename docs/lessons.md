# Lessons

One entry per incident, with the numbers that make it checkable. Agents read
the sections relevant to them rather than carrying their own copy of the story
— a lesson refined here reaches every agent at once, and a lesson duplicated
into five prompts gets updated in four of them.

Each entry states **what happened**, **why nothing caught it**, and **how to
apply it**. An entry without a measured number is not an entry.

---

## In an assembly, the anchor is usually not the subject — and the subject may hide it

`sources/VitaGripPs5/054-1.webp` is not a photo of a grip. It is a photo of a
blue grip **holding** a black PS Vita: one silhouette, two physical objects.

The scale anchor belongs to the console (182 mm, a published PCH-1000 spec).
The subject being designed is the grip, whose size is unknown — that is the
whole reason it is being measured. So the anchor object and the subject object
are different objects, and **the grip wraps the console's lower corners**.

That makes the console's span depend on which row you read it at:

```
console exposed span   739 px  @ row 282   <- nothing covering it
console median span    514 px              <- grip wrapping the corners
                       30.4 % spread
```

`reference-analyst` says to "identify the known dimension and the two pixel
coordinates spanning it." Followed literally on an occluded anchor, that
instruction returns a number and no warning. Both spans are two pixel
coordinates spanning the console.

The build took a scale of 0.2635 mm/px. The exposed span gives 0.2463:

| | width | height |
|---|---|---|
| From the exposed 739 px anchor | **222.4 mm** | **112.3 mm** |
| Shipped in VitaGripPS5 | 237.9 mm | 119.8 mm |
| ratio | **1.0697** | **1.0668** |

`sources/psvitaGrip/SOURCES.md` already recorded the grip at **223.3 mm** from
`handle-back.jpg` and **222.6 mm** from `054-1.webp`, cross-validated at 0.3 %
agreement, against two independent anchors. The correct reading reproduces
those to 0.4 %. Those figures sat in the repo, in writing, the entire time —
**no tool reads `SOURCES.md`**.

**Two axes wrong by the same factor is one scale error, not two mistakes.**
1.0697 and 1.0668 agree to 0.3 %. The shape was right the whole time and every
row of `LOBE_PROFILE` is uniformly inflated. When two axes drift together,
suspect the anchor, not the geometry.

### Why nothing caught it

`profile_gate.py` exists specifically to catch shape errors a bounding box
misses, and it is a good gate. But it imports its reference from
`tools/extract_profile.py`, which is handed `--width 237.9` **on the command
line**. The gate and the build consume the same unverified anchor, so the gate
confirms the build agrees with itself.

This inverts the usual rule. A gate must share the build's *placement* — the
VitaGripPS5 `fit_check.py` failure was a gate that re-derived placement and so
tested a pose 30 mm from the built one. But a gate must **not** share the
build's *unverified inputs*: there, sharing is what blinds it.

Placement is derived and can drift. An anchor is asserted and can be wrong.
Import the first; verify the second independently.

### How to apply

- Before measuring, ask **how many objects are in this frame**, and which one
  carries the known dimension. In an assembly the anchor is usually the
  mass-produced part; the unknown is the thing being designed.
- An anchor span is only valid **where nothing covers it**. Take the maximum
  row span, not the bounding box and not the median — an occluder makes a span
  smaller, never larger.
- Machine-checkable: profile the anchor mask row by row and fail when max and
  median diverge (30.4 % here). When the anchor is occluded, require the
  exposed span to be acknowledged explicitly rather than inferred.
- Cross-check the subject against any independently known dimension, and treat
  **both axes off by the same factor** as a scale fault, not a shape fault.
- Read `SOURCES.md`. It held the contradicting figures before the part shipped.

---

## An explanation that was never tested against the mask

`projects/VitaGripPS5/README.md` explains the 237.9 mm figure this way: a first
pass returned 343.5 mm because the blue mask swallowed the product's soft
blue-grey drop shadow, and raising the saturation floor from S>110 to S>150
dropped the shadow and gave 237.9.

The first half is true and worth keeping — the S floor genuinely matters for
rejecting the shadow. The conclusion does not follow. Sweeping the floor:

```
S>110   grip span 905 px
S>150   grip span 903 px
S>180   grip span 899 px
S>200   grip span 895 px
```

**A 1.1 % change across the entire usable range.** Once the shadow is excluded
at all, the mask is stable, and no S floor produces 237.9 mm from this image.
The mask was never what set that number.

So the repo's most detailed account of where its central dimension came from
describes a real fix to a different problem, and attaches it to a number that
fix cannot produce. The 237.9 has no derivation anywhere in the repo — it is an
assertion that acquired a plausible history.

### Why nothing caught it

The explanation was never re-run. It was written once, from a real debugging
session, and thereafter cited rather than tested. A documented mechanism reads
as evidence, and prose in a README cannot fail a gate.

### How to apply

- A stated mechanism is a **claim**, and the repo's third core directive
  applies to it: no claims without testing. Re-run the sweep the explanation
  implies and check the number actually moves the way the story says.
- Be specific about what a fix fixed. "Raising S to 150 drops the shadow"
  is supported. "…and gives 237.9 mm" is a separate claim needing its own
  measurement.
- A tool that takes a dimension as an argument should **print that value and
  its stated source** in its output, so a hand-passed number cannot travel
  downstream looking measured. `extract_profile.py --width 237.9` currently
  reports the profile without ever naming where 237.9 came from.

---

## A gate can be wrong in the same ways a build can

`profile_gate.py` reported VitaGripPS5's lobe as deviating **29.0 mm** against
a 4.0 mm tolerance, and its palm section as circular. Both verdicts were
wrong. Measuring the same mesh a second way gave 7.8 mm, and **the
disagreement between two measurements of one unchanged part was the finding** —
not either number on its own.

Three faults, all the same mistake in different axes: taking the extent of a
slice as a property of the thing being measured.

| Fault | Reported | Actual |
|---|---|---|
| Slice contained the bridge bar, not just the lobe | +21.4 mm at depth 88 | **+1.1 mm** |
| Horizontal slice through a spine leaning 12.2° reads an ellipse | palm 47.5 mm deep → "circular" | **46.4 mm, correctly oval** |
| ±2 mm band reached past the part's own ends | 29.4 mm at depth 0 | **21.1 mm** |

Each had an internal tell available before any fix:

- **A width that leaps while the depth beside it stays smooth is not a shape
  change.** Rows 85–105 jumped in width with `built_Y_depth` continuous
  across the jump — the signature of a second body entering the slice.
- **A shape property that changes with slice height is a slicing artefact.**
  Ovality that moves when the band moves is measuring the cut, not the section.
- **A value that converges as the ruler narrows was a ruler problem.** Depth 0
  read 29.4 → 28.2 → 25.9 → 21.1 as the band went 2.0 → 0.25 mm.

One fault *was* real: `lobe_halfwidth()` clamped below the profile table's last
station, sweeping the final 3.66 mm at constant width — a blunt stub, not a
tip. Worth separating: the table stopping short of the part is a *data* limit,
and clamping is a defensible response to it, but clamping silently produced
geometry nobody chose. Constructing the tail explicitly, and labelling it
construction, is the honest version.

### How to apply

- **When a gate and a part disagree, measure the part a second way before
  believing either.** A gate is code with no gate on it.
- **Never take `ptp()` over a slice** that may contain more than one body.
  Split on gaps and measure the cluster you meant.
- **A section perpendicular to a leaning axis is not a horizontal slice.**
  Measure the lean from the mesh and divide it out, or slice on the real
  normal.
- **A sampling band is a ruler with thickness.** Clip it to the part, and
  sweep it — a number that moves as the band narrows is not yet a measurement.
- **After fixing a gate, re-run it against a known-bad part.** The fixed gate
  here still fails the old shipped part at 14.6 mm, which is what
  distinguishes a repair from a loosened tolerance. Without that check, "the
  gate passes now" is indistinguishable from having deleted the gate.

## Correct dimensions do not make a correct shape

The VitaGripPS5 grip was **rejected on 2026-09-08** — "the figure doesn't match
anything" — and its STL and build macros deleted. At that moment it passed
every dimensional gate it had:

- 222.42 x 47.84 x 112.89 mm against a 222.4 x 112.3 measured target
- lobe profile within **3.7 mm** at 41 stations (tol 4.0), RMS **1.4**
- palm section correctly oval, 50.2 x 46.5 vs a 50.8 x 46.7 reference

Those numbers cost a 6.5 % anchor correction and three separate measurement-bug
fixes in the gate. They were also **beside the point**. A table of widths plus
an aspect ratio does not constrain a shape: the part matched the reference at
every station it was asked about and still read as two lumps on a stick.

The root cause is one image. `psvitarearbackside.webp` is a 3/4 **CAD render**;
read as an orthographic side view it shows the bridge as a round bar, and that
became `R_BRIDGE = 9.5` and the swept-tube approach. The real print photo shows
a flat-bottomed **C-channel**. Every subsequent correction refined the
dimensions of a form that was never verified as the right form.

**Why the gates could not see it.** `profile_gate.py` samples width at
stations along one axis. Two very different solids satisfy the same width
table — that is exactly the failure the gate's own docstring describes for
bounding boxes ("a tube of constant diameter satisfies the same box"), one
level up. Adding stations makes the sampling finer; it does not make it a
shape comparison.

### How to apply

- **Verify the FORM before refining its dimensions.** Ask which reference the
  cross-section came from, and run `perspective-checker` on that image, before
  any measurement work. A dimension gate on a wrong shape produces a
  well-measured wrong shape.
- **A scalar table is not a shape.** When a reference exists as geometry — a
  scan, a mesh — compare geometry to geometry: cross-sections against
  cross-sections. Reducing a scan to per-station widths and rebuilding from
  those throws away the very thing that would have caught this.
- **Passing every gate is not evidence a part is right; it is evidence the
  gates do not cover the failure.** When gates pass and the part still looks
  wrong, the gates are the thing to doubt.

## Status of the VitaGripPS5 anchor

**Corrected 2026-09-08; the code that carried it was then deleted with the
rejected part.** The correction is recorded here because the NUMBER survives
and the rebuild must not re-derive it wrongly:

**`PX_SCALE = 182.0 / 739.0` = 0.246279 mm/px.** The grip in `054-1.webp` is
**222.4 x 112.3 mm**. Do not use 0.2635, and do not use 237.9 x 119.8.

What scaled, and what deliberately did not:

| | |
|---|---|
| Scaled by `ANCHOR_FIX` | `GRIP_W`, `GRIP_H`, `HW_PALM`, `HW_TIP`, every `LOBE_PROFILE` row (depths **and** widths), `PALM_DEPTH_MM` |
| Unchanged — spec, not photo | `CONSOLE_W/H/D` (182 / 83.55 / 18.6), and `END_RISE`, which is the console's height |
| Unchanged — ratios | `LOBE_ASPECT`, `LOBE_DEPTH_RATIO` — the factor cancels |
| Unchanged — physical/design | `FIT_CLEAR`, `WALL`, `CHAMFER`, `GRIP_MARGIN`, `R_BRIDGE` |
| **Re-solved, not scaled** | `X_INSET` 28.02 → **26.06** |

`X_INSET` is the one that could not simply be multiplied. It is solved
empirically against the built sweep (`width = intercept - 2 * X_INSET`), and
the intercept is itself a property of the built lobe, which just shrank: the
relation moved from 293.93 to **274.54**. Verified linear by perturbation —
`X_INSET = 30.00` built 214.54 mm against a predicted 214.54.

**A scale correction is not a global multiply.** Sort every constant into
photo-derived, spec, ratio, design choice, and empirically-solved first; only
the first group scales, and the last must be re-measured.

### It did not fix the part

Three gates still fail, and **all three predate the correction** — each was
measured on the previously shipped STL too:

| | shipped | rebuilt |
|---|---|---|
| open edges | 8 | **4** |
| console interference | 2.02 % | **2.32 %** |
| lobe profile max deviation | 42.0 mm | **29.0 mm** |

The rescale improved the mesh and the profile, and left interference slightly
worse — the grip shrank while the console, correctly, did not.

Worth stating plainly: **a correct anchor does not make a correct part.** The
remaining profile fault is localised (rows 0–82 track within ~1 mm; rows
85–105 read 50–56 mm where the reference tapers 35 → 22), and it is the
circular-cross-section defect the README already lists. Fixing the measurement
made that defect *legible* rather than hiding inside a 6.5 % global error.

---

## `is_watertight` is not solidity — a cutter passed it with fifty tunnels

`projects/VitaGripPS5/console_solid.stl` is the boolean operand that carves the
Vita's socket. It reports `is_watertight True`. Measured further:

```
genus 50  (Euler -98)     1954 boundary edges     bbox fill 57.3 %
```

A PS Vita is a near-rectangular slab; it should fill 85–90 % of its bounding
box. 57.3 % is the signature of a body shot through with holes. Every cut ever
made with this operand inherited them — a boolean dutifully carves each tunnel
into the socket's walls.

The tunnels came from `make_console_cutter.py`, which voxelises the source
mesh, fills it, and marching-cubes it back out. That is the failure already
recorded for BrokeFeet as *voxel remesh closes tunnels*, met again in a
different project because the remesh lives in a different file.

**The genus was blamed on the wrong mesh for most of a session.** The finished
part read genus 50, then 53, and it was attributed to the DualSense strip,
which also voxelises. A two-line bisect settled it:

| mesh | genus | bbox fill |
|------|-------|-----------|
| `dualsense_stripped.stl` | **0** | 39.8 % |
| `console_solid.stl` | **50** | 57.3 % |

The shell was clean the whole time.

The fix, for a *cutter* specifically, is its convex hull: genus 0, watertight,
86.5 % fill, and the identical 182.70 × 19.30 × 84.25 extents. A cutter defines
the void an object drops into, so erring convex errs toward clearance. Part
genus fell **53 → 3**. A hull is wrong for a visible part — it is 50.8 % larger
in volume, having filled the real console's concavities.

### Why nothing caught it

`is_watertight` answers "does every edge have exactly two faces", which a
tunnelled solid satisfies perfectly — a torus is watertight. Nothing in the
pipeline asked for genus, and the bbox-fill ratio that makes the defect obvious
in one number was not being computed anywhere.

### How to apply

- For any mesh used as a **boolean operand**, gate on `genus == 0` and
  `body_count == 1`, not on `is_watertight` alone.
- **Bbox fill is the cheap tell.** A part whose real shape is roughly prismatic
  should fill 85–90 % of its bounding box; anything near 50 % is hollow,
  tunnelled, or half-missing. One line, no topology needed.
- When a defect appears in a boolean's *result*, bisect the *operands* before
  theorising about the operation. Both inputs here voxelise; only one was
  guilty.

---

## A boolean union of coplanar tangent faces returns two bodies, not a failure

The Vita socket has to open through the shell's top surface, or the cut leaves a
sealed internal void — the defect this repo has already recorded twice
(*sealed cavity passes every gate*, *sealed void invisible to every solid-part
gate*). The fix is to extrude the cutter upward past the shell's crown so the
pocket becomes a through-pocket.

Built the obvious way — a riser box starting exactly at the cutter's top face —
the union reported success and returned **two disjoint solids**:

```
union result: bodies 2, genus -1
  piece 1   vol 269.4 cm3   Z  4.50 .. 24.50    (the console hull)
  piece 2   vol 328.0 cm3   Z 24.50 .. 45.55    (the riser)
```

They met face-to-face at Z 24.50 and never merged: coplanar tangent faces give
the engine no overlapping volume to fuse, so it keeps both. Used as a cutter,
two separate solids **leave a thin wall of shell material standing in the
seam** — a skin across the pocket that should not exist.

Dropping the riser's base 25 % of its height *inside* the hull makes the
overlap a real volume, and the union collapses to one body:

| | butted | overlapped |
|---|---|---|
| cutter bodies | **2** | **1** |
| cutter genus | −1 (degenerate) | **0** |
| rays reaching the seat floor | 6 of 63 | **58 of 63** |
| rays stalled at the seam | 57 | **0** |
| removed | 32.8 % | 33.5 % |

`genus -1` is itself impossible for a solid, and was the visible tell that the
result was degenerate rather than merely unmerged.

**The riser must also carry the subject's outline, not its bounding box.** A
box riser squares off what the Vita rounds: in plan the console's silhouette is
14227.6 mm² against a 15392.4 mm² bounding rectangle — 92.4 % — so a box
overcuts **1164.8 mm²**, all at the four rounded corners, leaving a rectangular
opening above a Vita-shaped seat. Extruding the hull's own XY silhouette keeps
the section constant through the opening: 14384.8 mm² at the seat, 14400.8 mm²
in the riser.

### Why nothing caught it

`is_watertight` was True, the bounding box was right, and the volume removed
*rose*. `body_count` was the one field that would have said so, and it was
being checked on the boolean's **result** but never on the cutter that produced
it. The user saw the wall in the viewer before any gate did.

### How to apply

- **Never butt two solids for a union.** Overlap them by a real volume; a
  shared plane is a tangency, not an intersection.
- `raise` on `body_count > 1` for a cutter, at the point of construction. The
  check now lives in `socket_placement.load_cutter` — a multi-body cutter can
  no longer reach a boolean silently.
- To prove a pocket is genuinely open, **cast rays down into it from above the
  part** and count how many reach the floor. Volume removed cannot distinguish
  an open pocket from a sealed void of the same shape.

---

## A callback that never fires is indistinguishable from a scene that never changes

`tools/watch_model.py` holds a window open, polls the files a model is built
from, and repaints when one changes — so an edit made in the shell shows up on
screen without anyone typing a command.

Its first version armed the refresh with pyvista's timer API. **It never fired
once.** The window opened, drew the startup pose, and sat there looking
entirely correct while **nine successive edits** to the placement — two Y
moves, three Z moves, a tilt and its revert — never reached the screen. Every
"it should repaint now" said during that stretch was wrong, and the user was
asked to judge geometry from a frozen display.

Measured directly, once suspected:

```
pl.add_timer_event(max_steps=100, duration=500, callback=tick)
    -> ticks fired: 0
pl.iren.add_observer('TimerEvent', cb)
  + iren.interactor.CreateRepeatingTimer(400)
    -> ticks fired: 0        (so it is not the pyvista wrapper)
```

This VTK build (9.6.2 / pyvista 0.48.4) does not dispatch timer events to the
interactor at all. What works is driving the loop by hand:
`show(interactive_update=True, auto_close=False)` returns instead of blocking,
and each `update()` call processes input and re-renders. Verified: 21
iterations in 6 s with a live actor swap mid-loop, then end-to-end — edit →
rebuild #2, revert → rebuild #3.

**A second bug hid inside the same feature.** `importlib.reload` alone reloads
unreliably, and it fails in the case that matters most — *undoing* an edit.
Python caches source mtimes at 1-second granularity, so a file changed and
restored inside the same second reloads to the first version: the window keeps
showing a change already reverted. Measured: sink 10.0 → 32.0 reloaded
correctly, 32.0 → 10.0 kept reporting 32.0. `importlib.invalidate_caches()`
before the reload fixes it.

### Why nothing caught it

Nothing was watching the watcher. The window rendered successfully, the process
stayed alive, the shell printed no error — and a stale, correct-looking render
is the most convincing possible failure. Two further launches then crashed on
callback signatures (`add_key_event` rejects any callback with a parameter
lacking a default, including `*args`), each caught only after the window died.

### How to apply

- **Prove the refresh mechanism fires before trusting anything drawn through
  it.** A three-line test — arm the callback, print a counter, assert it is
  non-zero — would have caught this before the first edit.
- Test a callback's *registration* where it is written, not after a window
  fails to open.
- When a viewer and a number disagree, suspect the viewer is stale before
  re-deriving the geometry.
- A live viewer must show its own liveness: this one now prints a **rebuild
  counter and timestamp** in the readout, so a frozen window is visibly frozen.

---

## The percentage rose while the pocket fell apart

Placement for the Vita socket was tuned across seven moves with no picture,
using the percentage of shell volume the cut removed as the signal — the only
one available before the overlay renderer existed. The percentage endorsed
poses that were visibly wrong:

| pose | removed | verts engaged | what the render showed |
|------|---------|---------------|------------------------|
| Y 20, sink 10, tilt 0 | 13.4 % | **16.9 %** | one solid slab |
| Y 35, sink 21, tilt −9.15 | **17.67 %** | 3.7 % | scattered disconnected patches |
| Y 35, sink 21, tilt 0 | — | 2.5 % | socket nearly gone |

The best-reading percentage in that table belongs to the worst pose. A volume
fraction **sums disconnected scraps exactly as happily as it sums one coherent
pocket**, so it cannot tell a socket from debris of the same total size.

The tilt that produced it was itself correctly measured — the shell's top face
falls dZ/dY = −0.1611, i.e. 9.15°, from 33.90 mm at the front to 20.26 mm at
the rear. Applied as a rigid rotation it still made the part worse, because the
shell's top is a dome falling in **both** directions, not an inclined plane:
across X it is a symmetric double hump, −80/0/+80 all reading 29.76 and ±40
both 33.07. A rigid body has one orientation; that surface needs a different
one at every point. The parallelism check said so before the render did — gap
spread 5.25 mm along Y at the best available rotation.

### Why nothing caught it

The gate was a scalar, and scalars were the only instrument.
`MIN_PLAUSIBLE_REMOVAL_PCT = 5.0` was written into the placement module during
this same session on the strength of those numbers, and it passes every pose in
the table including the two whose sockets do not exist.

Worse, the threshold was calibrated against comments that no longer reproduce:
`build_socket_grip.py` documents Y = −31 as removing **1.2 %**, and the same
pose now measures **8.8 %**. Treat that constant as provisional.

### How to apply

- **Look at the render before reporting a verdict.** Not after, and not instead
  of measuring — the numbers and the picture answer different questions, and a
  percentage cannot see topology.
- For "is this one pocket or several", measure **connectivity**, not volume:
  split the intersection and count bodies, or count vertices engaged.
- A correctly measured number applied to the wrong model is still wrong. The
  9.15° slope was right; a rigid rotation was the wrong thing to do with it.

---

## Every scalar improved and the part got worse

The Vita socket's seat wall showed as visibly twisted in the live viewer — the
user circled it in a screenshot. The cutter was a convex hull of
`console_solid.stl`, and measuring it explained the twist exactly:

```
Z  4.50  width 179.91  depth 81.71   <- seat floor, NARROWEST
Z 10.50  width 183.40  depth 84.95   <- widest, mid-height
Z 16.50  width 181.69  depth 83.99   <- pinching back in
Z 18.50  width 183.40  depth 84.95   <- riser seam, steps out again
```

A hull of a rounded slab is a **barrel**. The opening bulges 3.5 mm between the
floor and mid-height, pinches, then breaks at the riser seam, so the wall leans
and curves in plan. Worse, the seat floor came out **179.91 mm against a
182.70 mm console** — the cutter was narrowest exactly where the console is
widest, so the Vita could not have seated at all.

Replacing the hull with a straight extrusion of the console's plan silhouette
fixed every one of those numbers:

| | hull | prism |
|---|---|---|
| wall profile | 179.91 → 183.40 → 181.69 | one Z band, vertical |
| cutter bottom Z spread | 15.00 mm | **0.0000 mm** |
| part genus | 4 | **1** |
| seat floor in the twisted band | `19.50` (no hit) at X −90 | **4.50 flat** |
| seat floor width | 179.91 mm | **183.40 mm** |

**The user looked at it and said it was worse.** Not marginally — "somehow it
got worse", on sight, and work stopped.

### Why nothing caught it

Nothing was *wrong* with the measurements. The barrel was real, the prism did
remove it, and every gate that fired was accurate. The failure is upstream of
the gates: **the defect was identified by theorising from a picture, then
verified against the theory rather than against the picture.**

The twist was visible. Instead of establishing what the eye was actually
objecting to, the session measured the cutter, found a defect that could
plausibly produce a twist, fixed that defect, and confirmed the fix with probes
aimed at the same theory. Six ray-grids and a Z-sweep all agreed — with each
other, and with the hypothesis that generated them.

That is confirmation, not verification. A probe designed from a theory can only
report on that theory. The one instrument that had already proved decisive —
looking — was used to *start* the investigation and then never again until the
user reopened the viewer.

### How to apply

- **When a defect is found by eye, the fix is verified by eye.** A scalar may
  support the verdict; it may not replace it. This repo's own record is that
  looking found the tilt failure, the swept-tube rejection, and this twist —
  each time after numbers had endorsed the bad geometry.
- **A measurement derived from a hypothesis cannot test that hypothesis.** Ask
  what result would *falsify* the theory before running the probe. Six grids
  that can only confirm are worth less than one render that could refute.
- Improving every number in a table is not evidence of improvement. It is
  evidence that the table describes what was changed.
- **Ask what the user is pointing at before rebuilding what you think they
  mean.** "The surface is inclined and extends in Y" described the region; it
  was read as a cause. A single clarifying question, or a request for the
  annotated screenshot that eventually arrived, would have cost one turn.
