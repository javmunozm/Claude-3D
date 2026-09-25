# Architecture

How a CAD project in this index is put together, from geometry code to printable output.

## Repository structure

```
Claude-Projects/
├── CLAUDE.md          ← project index, CORE DIRECTIVE, doc pointers
├── docs/              ← index-wide documentation
├── tools/             ← shared tooling (render_check, render_views, reconcile, mesh_to_step, …; full list in system.md)
├── sources/           ← input material per subject: photos, specs, scans, SOURCES.md
├── projects/          ← all CAD projects live here
│   ├── <ProjectName>/
│   │   ├── README.md      ← project info, goals, status, file locations
│   │   ├── macros/        ← build123d Python scripts that generate the geometry
│   │   ├── vectors/       ← generated SVG / DXF traced from sources/
│   │   ├── attempts/      ← rejected work, not committed (see attempts.md)
│   │   ├── stl/           ← generated meshes (.stl, and .3mf where written)
│   │   ├── step/          ← generated STEP solids
│   │   └── renders/       ← generated PNGs (render_check / render_views default here)
│   └── ...
```

`sources/` and `tools/` stay at the repo root, shared across all projects —
never nested under `projects/`.

### sources/ holds inputs, projects/ holds outputs

Anything a script *reads* and never regenerates (photos, specs, DICOM panes,
downloaded STLs) lives in `sources/<subject>/`. Anything a script *writes* —
meshes, SVG, DXF — lives under the project that generated it, **never back in
`sources/`**.

When a project gains a second generation it nests as `v0/`, `v2/` … inside the
project folder rather than becoming a sibling — see [versioning.md](versioning.md).

## Layer overview

```
sources/            Input images, specs, scans (read-only inputs)
      │
      │  (DXF/SVG: import_dxf / import_svg — true geometry, no scale needed)
      │  (photos:  vectorize → scale → SVG/DXF — see pipeline below)
      ▼
macros/*.py            Python source — parametric geometry, built with build123d
      │  run with `python`
      ▼
vectors/*.svg,*.dxf     Generated vector output, written to the project's vectors/ folder
      │
stl/*.stl, step/*.step  Generated CAD output, written to the project's stl/ and step/ folders
      │
      ├─► render_check.py   topology + shaded renders (matplotlib or Blender)
      ├─► pymeshfix         mesh repair if topology gate fails
      ├─► pyvista           interactive inspection / offscreen renders
      ├─► ocp-vscode        interactive 3D viewer (browser or VS Code panel)
      └─► slicer            STL → G-code for 3D printing (OrcaSlicer)
```

## Vectorization pipeline

When a project starts from a reference photograph rather than a DXF/SVG
drawing, the image must be vectorized before it can enter the CAD pipeline.

```
reference photo (.jpg/.png/.webp)
      │
      ├─► vtracer (Rust-based raster→SVG, good for clean images)
      │   OR
      ├─► cv2 + scipy (threshold → contour → spline smooth, better for noisy images)
      │
      ▼
raw SVG (traced outlines in pixel coordinates)
      │
      ├─► scale calibration (known dimension → px/mm)
      ├─► svgpathtools (parse, clean, filter paths)
      │
      ▼
clean SVG (mm units, smooth curves, features labeled)
      │
      ├─► svgpathtools + ezdxf (SVG paths → DXF polylines)
      │
      ▼
DXF (importable by build123d via import_dxf)
```

The `vector-tracer` agent runs this pipeline; the `accuracy-reviewer` agent
verifies the output against the source image and known dimensions. See
[commands.md](commands.md#vectorize-a-reference-image) for the specific
commands.

Nothing in a project folder is hand-edited CAD data. The `.step` and `.stl`
files are build artifacts — regenerate them by re-running the script that
produced them, the same way you'd rebuild any compiled output. If a part
needs to change, edit the Python source, not the exported files.

## Parametric model pattern

A project's geometry is built in stages, and **each stage is its own `.py`**
inside a package under `macros/` (`macros/<pkg>/`), with one short main in
`macros/` that calls them in order. Nobody should
have to read or edit a 1000-line file to change one part: fixing a handle means
opening the handle's file and nothing else.

1. **Constants** (`constants.py`) — real-world measurements (lengths,
   diameters, angles) as named values in millimeters. This is the only file
   that changes when the physical object being modeled changes.
2. **Inputs and derived values** (e.g. `rings.py`) — traced vectors read
   from `vectors/`, and values computed from them and the constants (angles,
   solved offsets), so the trigonometry isn't repeated at each use site.
3. **Shape helpers** (e.g. `shapes.py`) — small generic functions (extrude a
   face, a box, a teardrop bore, a cone) that the part builders share.
   Project-specific profiles that several parts need (a thread, a ratchet
   tooth) get their own file (e.g. `mechanisms.py`).
4. **Parameter bundles** (e.g. `parameters.py`) — the constants and derived
   values grouped into the dicts each builder takes, plus the build-time
   arithmetic checks that stop the build before any slow geometry.
5. **Part builders** (`parts/<part>.py`, one file per part) — pure functions
   that take dimensions as arguments and return a build123d shape. They don't
   read module-level constants directly, so they're reusable for variant
   parts.
6. **Main** (`<project>.py`, in `macros/`, outside the package) — calls the
   stages in order, assembles, validates, exports to `stl/` and `step/`, and
   can build a single part on request. It holds no geometry of its own.

Rules:

- **The stage package has a name unique to the project** (e.g.
  `SurgicalDrillGuide/macros/sdg_model/`), and imports inside it are relative
  (`from .constants import ...`). Never put the stage files loose in
  `macros/`. Python caches a module by its bare name, so two projects' loose
  `constants.py` collide in one process. Measured 2026-09-25: the second
  project silently got the first project's `T_Z`, and in the other load
  order it raised an `ImportError`. Count `parents[...]` from the file's
  real depth. A file directly in the package (`macros/<pkg>/x.py`) reaches
  the project folder at `parents[2]`. A file in a subpackage
  (`macros/<pkg>/parts/x.py`) reaches it at `parents[3]`.
- **Stage files only define things.** Nothing runs at import, so any stage
  can be imported, tested or rebuilt alone. Only the main has an
  `if __name__ == "__main__":` block.
- **Share across projects only what is already reused (YAGNI).** A helper
  stays in its project until a second project needs it; then it moves to a
  shared module. No speculative library, no framework.
- **Applied when a project is next reworked** (decided 2026-09-24). Existing
  single-file macros stay as they are until then.
  `projects/SurgicalDrillGuide/macros/` is the first project split this way
  (2026-09-25; exports and gate logs byte-identical before and after): the
  reference for the **file layout**. It does not yet meet item 5 (part builders): its part
  builders still import some constants and call `ring_face()` directly.
  Moving those into arguments is still to do.

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

## Project conventions

- Each project lives in its own named subfolder under `projects/`.
- Every project folder must have a `README.md` with at minimum: project goal,
  current status, and the location of the generated `.step` / `.stl` files.
- Generated files never sit in the project (or version) root: meshes go to
  `stl/`, STEP to `step/`, PNGs to `renders/`. Macros create the folder before
  writing, because `.gitignore` excludes some `stl/` and `step/` folders and a
  fresh clone does not have them. Workflow folders keep their own contents
  (`blender/`, `derived/`, `holes/`, `work/`, `vectors/`).
- **BrokeFeet is exempt.** It is one of the earliest projects, it is
  finished, and it keeps its own structure: for example
  `v2/BrokeFeetV2_pinned2.3mf` sits at the version root. Do not restructure
  it, and do not report its layout as a defect.
- Geometry is authored as Python scripts under `projects/<Project>/macros/`
  using build123d, and run to regenerate `.step` / `.stl` output — there are no
  `.FCStd` files.
- Viewing/inspection uses `ocp-vscode` (`python -m ocp_vscode`), not the
  FreeCAD GUI.

## Adding a new project

A new project folder should follow this same layered structure: a
`macros/` folder holding a project-named package with one `.py` per stage
(constants → derived → shape helpers → parameters → one file per part) and a
main beside it, see [Parametric model pattern](#parametric-model-pattern),
optional `structural_check.py`-style verification, and a `README.md`
describing the physical goal. See [system.md](system.md) for
the required environment and [commands.md](commands.md) for the standard
commands every project should support.
