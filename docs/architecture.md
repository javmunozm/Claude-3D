# Architecture

How a CAD project in this index is put together, from geometry code to printable output.

## Layer overview

```
references/            Reference images, specs, DXF/SVG drawings
      │
      │  (DXF/SVG: import_dxf / import_svg — true geometry, no scale needed)
      │  (photos:  measure → anchor → trace — scale from known dimension)
      ▼
macros/*.py            Python source — parametric geometry, built with build123d
      │  run with `python`
      ▼
*.step / *.stl          Generated CAD output, written to the project's root folder
      │
      ├─► render_check.py   topology + shaded renders (matplotlib or Blender)
      ├─► pymeshfix         mesh repair if topology gate fails
      ├─► pyvista           interactive inspection / offscreen renders
      ├─► ocp-vscode        interactive 3D viewer (browser or VS Code panel)
      └─► slicer            STL → G-code for 3D printing (OrcaSlicer)
```

Nothing in a project folder is hand-edited CAD data. The `.step` and `.stl`
files are build artifacts — regenerate them by re-running the script that
produced them, the same way you'd rebuild any compiled output. If a part
needs to change, edit the Python source, not the exported files.

## Parametric model pattern

Each project's core script (e.g. `projects/BedLifter/macros/bed_lifter_b123d.py`) follows
the same shape:

1. **Constants block** — real-world measurements (lengths, diameters, angles)
   as named variables at module scope, in millimeters. This is the only part
   of the file that should change when the physical object being modeled
   changes.
2. **Derived geometry** — values computed from the constants (angles via
   `math.asin`/`math.cos`, solved offsets, etc.), kept separate from raw
   inputs so the trigonometry isn't duplicated at each use site.
3. **Builder functions** — pure functions that take dimensions as arguments
   and return a build123d shape (e.g. `build_lifter(...)`, `make_lifter_split(...)`).
   These don't reference the module-level constants directly, so they're
   reusable for variant parts.
5. **Generate step** — module-level calls at the bottom of the file that
   invoke the builders with the project's actual constants and call
   `export_step` / `export_stl` to write output next to the project folder.

Splitting a part for printing (e.g. `HeadLifter_Lower` / `HeadLifter_Upper`)
is handled as a boolean cut into two halves plus a tenon/pocket joint,
rather than as two independently authored parts — this keeps the joint
geometry (tenon dimensions, clearance) derived from one shared definition
instead of duplicated across files.

## Verification layer

Structural sanity checks (e.g. `structural_check.py`) are standalone —
no build123d or CAD dependency, just `math`. They take the same dimensions
used in the geometry script (copied, not imported) and check stress/buckling
against material allowables at a fixed safety factor. This is deliberately
decoupled from the geometry builder so a check can be run without a CAD
environment installed.

The cost of that decoupling is **drift**: copied values fall out of step with
the geometry silently, since both scripts keep running perfectly on their own.
This has happened here — BedLifter's check validated a 9.332° design while the
geometry built 8.850°, alongside a collar diameter overstated more than 2×,
and still printed `ALL CHECKS PASS`.

So the decoupling stays, but the drift is made detectable: a check declares
the geometry values it assumes and `tools/reconcile.py` compares them against
the geometry module's real ones, grading each mismatch by whether it errs
conservatively. Non-conservative mismatches abort before any verdict prints.
If build123d isn't installed the reconciliation warns and skips, preserving
the run-anywhere property — but then the verdict must be reported as having
unverified inputs.

## Verification layer — geometry

`tools/render_check.py` gates the exported mesh itself: `body_count`,
watertightness, winding consistency, positive volume, bounding box, plus
shaded renders from standard cameras. It exists because dimensional
correctness does not imply shape correctness — see
[commands.md](commands.md) for the failures that motivated it and the
workflow that catches them.

## Mesh repair layer

When a mesh fails the topology gate (non-manifold edges, non-watertight),
two repair tools are available before re-running the gate:

- **pymeshfix** — targeted repair that fixes singularities and
  self-intersections without modifying clean regions. Preferred for meshes
  with isolated defects (e.g. VitaGrip's 2 non-manifold edges out of
  225,000).
- **pymeshlab** — heavier filter suite (Screened Poisson, quadric
  decimation, curvature-aware smoothing) for meshes needing more
  intervention.
- **manifold3d** — re-booleans a mesh into a guaranteed-manifold solid.
  Already used in BrokeFeet for STEP export.

See [commands.md](commands.md#repair-non-manifold-meshes) for usage.

## Viewer layer

`view_parts.py`-style scripts import the builder functions from the
geometry script (so the viewer never has stale geometry) and push shapes
to a running `ocp-vscode` server over its `show()` API. The server and the
script that sends geometry are separate processes — see [commands.md](commands.md).

## Adding a new project

A new project folder should follow this same layered structure: a
`macros/` (or equivalent) folder with a constants → derived → builder →
generate script, optional `structural_check.py`-style verification, and a
`README.md` describing the physical goal. See [system.md](system.md) for
the required environment and [commands.md](commands.md) for the standard
commands every project should support.
