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
