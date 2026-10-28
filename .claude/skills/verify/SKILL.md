---
name: verify
description: Run the five-gate geometry verification for a project part. Usage: /verify <Project>/stl/<Part>.stl [--reference <path>]
user-invocable: true
---

# Five-gate geometry verification

Run all five gates in order for the specified STL. Do not skip gates or report
the part as verified until every applicable gate has passed.

## Parse the argument

The user passes `<Project>/stl/<Part>.stl` — resolve it relative to `projects/`.
If the user passes just a project name, glob `projects/<Project>/stl/*.stl` (and
`projects/<Project>/v*/stl/*.stl` for versioned projects) and list the
available STLs; ask which one to verify. Renders go to the sibling `renders/`.

If `--reference <path>` is passed, use it for gate (e). Otherwise check
`sources/` for a directory matching the project subject and offer any
images found there.

## Gate sequence

### (a) Regenerate

Find the geometry script in `projects/<Project>/macros/` and run it:

```
python projects/<Project>/macros/<script>.py
```

Confirm the STL was written without error. If the script has no
`if __name__ == "__main__":` guard, warn — module-level exports fire on
import and silently overwrite files.

### (b) Topology gate

```
python tools/render_check.py projects/<Project>/stl/<Part>.stl
```

**Hard gates:** `body_count == 1` and `is_watertight`. If either fails, stop
and report the failure — do not proceed to rendering. If the part is
legitimately multi-piece, the user must pass `--expect-bodies N`.

### (c) Form render

```
python tools/render_views.py projects/<Project>/stl/<Part>.stl --views front back
```

`render_check.py`'s own images are flat, unlit silhouettes: they show the
outline and hide every cross-section and surface defect inside it. Judge form
on the lit views of `render_views.py`.

After rendering, **read each PNG** with the Read tool and describe in your
response what the render shows:
- Are spans that should be open actually open?
- Do curves read as curves?
- Is there unexpected geometry spanning areas that should be hollow?

If you cannot read images, hand the render paths to the user and ask them to
confirm: "Please open `<path>` and confirm the shape matches intent."

Never render wireframe. Never skip reading the render.

**A render answers only about the axes in its image plane.** Renders are
orthographic, but that does not make every view informative: an `iso` view
compresses depth so severely that a 40x35 mm volumetric handle read as a flat
slab during VitaGrip review — a wrong verdict that would have triggered a
rebuild of correct geometry. Choose the view that contains the axis in doubt
(`right`/`left` for depth, `front`/`back` for the X-Y silhouette), and when the
question is dimensional rather than visual, run the `form-audit` skill for
cross-sections instead of judging by eye.

### (d) Mating check (multi-piece or mating parts only)

Skip this gate if the part is standalone with no mating geometry.

For split or mating parts, load both STLs and compare numerically:
- Mating-axis bounds must coincide
- Tenon must land inside pocket with intended clearance
- Assembled stack must reach intended overall dimension

If one piece is already printed, its exported STL's actual bounds are the
constraint — not a constant in the script or a claim in the README.

### (e) Whole-form comparison (when a reference exists)

```
python tools/render_check.py projects/<Project>/stl/<Part>.stl --views front --reference <reference_path>
```

Read the `_vs_reference.png` and answer one question:

> **Is this the same object as the reference?**

Not "are the dimensions right." Is the **form** the same — proportion, mass
distribution, whether features swell or taper in the same direction.

**The silhouette-profile table is not evidence.** It compares outer bounds only;
on the known-bad VitaGrip part it showed near-perfect agreement while the images
were obviously different objects. Only the image is evidence.

If no reference exists, say so plainly rather than implying visual confirmation.

**Qualify the reference before comparing to it.** Run the QUALIFY stage of the `photo-to-vectors` skill (or
its mirror-IoU test) on the photo first. A photo shot down one axis is blind to
that axis: VitaGrip's `054-1.webp` scores 0.967 (on-axis, usable for X-Y) while
`020-1.webp` scores 0.562 (three-quarter, shape reference only). A view that
cannot see a feature is not evidence the feature is correct — record it as
"blind", never as "matches". Also confirm the photo shows the same object
variant as the model before treating a difference as a defect.

## Report format

After all gates, report:

```
Verification: projects/<Project>/stl/<Part>.stl
  (a) Regenerate:   PASS / FAIL
  (b) Topology:     PASS / FAIL  [body_count, watertight, volume]
  (c) Shaded render: PASS / FAIL  [what you observed]
  (d) Mating check:  PASS / FAIL / SKIPPED  [reason]
  (e) Reference:     PASS / FAIL / NO REFERENCE  [what you observed]

  VERDICT: ALL GATES PASS / FAILED AT GATE (x)
```
