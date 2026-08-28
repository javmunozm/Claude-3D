# Commands

Standard commands for working with any project in this index. Examples use
`BedLifter`; substitute the project folder name.

## Setup (once per environment)

```
pip install build123d ocp-vscode
```

## Generate / regenerate CAD output

Run the project's geometry script directly with Python. This (re)writes the
`.step` and `.stl` files into the project's root folder.

```
python "D:\CAD\Claude-Projects\projects\BedLifter\macros\bed_lifter_b123d.py"
```

Run this any time the constants or builder logic in the script change —
the exported files are not hand-maintained.

## View parts in 3D

Two terminals: one runs the viewer server, the other pushes geometry to it.

```
# Terminal 1 — start the viewer server (leave running)
python -m ocp_vscode --port 3939 --axes --grid_xy --theme dark

# Browser — open http://localhost:3939
# (or use the OCP CAD Viewer panel in VS Code instead of a browser)

# Terminal 2 — build parts and send them to the viewer
python "D:\CAD\Claude-Projects\projects\BedLifter\macros\view_parts.py"
```

Re-run the Terminal 2 script after any geometry change to refresh the view;
the server in Terminal 1 does not need to be restarted.

## Verify geometry (required after every geometry change)

A script that runs without error, and exports files without error, can still
produce a physically wrong part. Every geometry defect found in this repo so
far passed both of those tests — a solid slab across a span that should have
been open, an export of two disconnected bodies, and two halves of a split
part regenerated against different split planes. Bounding-box checks and
wireframe views missed all three; a **shaded** render caught them.

```
# Topology gate only (fast, no rendering)
python tools\render_check.py projects\VitaGrip\VitaGrip.stl

# Topology gate + shaded renders from standard cameras
python tools\render_check.py projects\VitaGrip\VitaGrip.stl --views front back
```

`body_count == 1` and `is_watertight` are hard gates — failing either means
the part is not printable, however correct its dimensions. Pass
`--expect-bodies N` only for parts that are deliberately multi-piece.

Renders are written next to the STL. **Open them and look.** A render nobody
inspects is worse than no render, because it creates false confidence. Never
render wireframe — it hides exactly the bugs this catches.

### Compare against a reference photo (required when a reference exists)

```
python tools\render_check.py projects\VitaGrip\VitaGrip.stl --views front ^
    --reference references\psvitaGrip\054-1.webp
```

This writes `<Part>_vs_reference.png` — the render beside the photo. **Open it
and answer one question: is this the same object?** Not "are the dimensions
right", not "did each feature come out as intended" — is the *form* the same.

This gate exists because VitaGrip went through four revisions in which every
local check passed (span open, one body, band thick) and the result still
looked nothing like the reference: a thin flat bracket against a fat
controller grip, with handle horns tapering to a 13 mm point where the
reference horns swell to a ~53 mm teardrop. Correct parts do not compose into
a correct whole.

The command also prints a silhouette-profile table. **Treat it as a hint, not
a verdict.** It compares each row's outer width, so a hollow frame and a solid
body of the same outline score identically — on the known-bad VitaGrip part it
showed near-perfect agreement. Only the image is evidence.

For multi-piece or mating parts, also compare the mating faces numerically:
load both STLs, check that the mating-axis bounds coincide with the intended
clearance, and confirm the assembled stack reaches the intended overall
dimension. Where one piece is already printed, its exported STL — not a
constant in the script or a claim in a README — is the constraint.

## Run structural / verification checks

Project-specific, dependency-free scripts that validate the design against
material and load assumptions. No CAD environment required.

```
python "D:\CAD\Claude-Projects\projects\BedLifter\macros\structural_check.py"
```

Look for `[PASS]` / `[FAIL]` per check in the output, and an overall
verdict line at the end.

**Read the reconciliation block first.** These checks are deliberately
decoupled from the geometry scripts (see [architecture.md](architecture.md))
so they run without a CAD environment — which means their inputs are copied
by hand and can drift. `tools/reconcile.py` compares a check's assumed values
against the geometry module's real ones and grades each mismatch by whether
it errs conservatively:

```
  [OK      ] tilt angle (deg)    check=8.85   geometry=8.85   (ANGLE_DEG)
  [CRITICAL] head collar dia     check=50     geometry=22.5   (WHEEL_TOP_R)
             -> deviation is NOT conservative
```

A `CRITICAL` row means the check may be validating a design that doesn't
exist, in the unsafe direction — a PASS verdict below it means nothing until
the inputs are corrected. This is not hypothetical: BedLifter's check ran for
some time against a 9.332° design while the geometry built 8.850°, with a
collar diameter overstated more than 2×, and reported `ALL CHECKS PASS`.

## Adding a new command to a project

If a project introduces a new standard script (e.g. an assembly checker or
a BOM export), document its invocation here and cross-reference it from
the project's own `README.md`.
