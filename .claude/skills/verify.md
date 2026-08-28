---
name: verify
description: Run the five-gate geometry verification for a project part. Usage: /verify <Project>/<Part>.stl [--reference <path>]
user_invocable: true
---

# Five-gate geometry verification

Run all five gates in order for the specified STL. Do not skip gates or report
the part as verified until every applicable gate has passed.

## Parse the argument

The user passes `<Project>/<Part>.stl` — resolve it relative to `projects/`.
If the user passes just a project name, glob `projects/<Project>/*.stl` and
list the available STLs; ask which one to verify.

If `--reference <path>` is passed, use it for gate (e). Otherwise check
`references/` for a directory matching the project subject and offer any
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
python tools/render_check.py projects/<Project>/<Part>.stl
```

**Hard gates:** `body_count == 1` and `is_watertight`. If either fails, stop
and report the failure — do not proceed to rendering. If the part is
legitimately multi-piece, the user must pass `--expect-bodies N`.

### (c) Shaded render

```
python tools/render_check.py projects/<Project>/<Part>.stl --views front back
```

After rendering, **read each PNG** with the Read tool and describe in your
response what the render shows:
- Are spans that should be open actually open?
- Do curves read as curves?
- Is there unexpected geometry spanning areas that should be hollow?

If you cannot read images, hand the render paths to the user and ask them to
confirm: "Please open `<path>` and confirm the shape matches intent."

Never render wireframe. Never skip reading the render.

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
python tools/render_check.py projects/<Project>/<Part>.stl --views front --reference <reference_path>
```

Read the `_vs_reference.png` and answer one question:

> **Is this the same object as the reference?**

Not "are the dimensions right." Is the **form** the same — proportion, mass
distribution, whether features swell or taper in the same direction.

**The silhouette-profile table is not evidence.** It compares outer bounds only;
on the known-bad VitaGrip part it showed near-perfect agreement while the images
were obviously different objects. Only the image is evidence.

If no reference exists, say so plainly rather than implying visual confirmation.

## Report format

After all gates, report:

```
Verification: projects/<Project>/<Part>.stl
  (a) Regenerate:   PASS / FAIL
  (b) Topology:     PASS / FAIL  [body_count, watertight, volume]
  (c) Shaded render: PASS / FAIL  [what you observed]
  (d) Mating check:  PASS / FAIL / SKIPPED  [reason]
  (e) Reference:     PASS / FAIL / NO REFERENCE  [what you observed]

  VERDICT: ALL GATES PASS / FAILED AT GATE (x)
```
