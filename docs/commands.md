# Commands

Standard commands for working with any project in this index. Examples use
`BedLifter`; substitute the project folder name.

## Setup (once per environment)

```
pip install build123d ocp-vscode
pip install pymeshfix pyvista pydicom SimpleITK pymeshlab
```

See [system.md](system.md) for the full package list and versions.

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
python tools\render_check.py projects\BedLifter\MiddleLifter.stl

# Topology gate + shaded renders from standard cameras
python tools\render_check.py projects\BedLifter\MiddleLifter.stl --views front back
```

`body_count == 1` and `is_watertight` are hard gates — failing either means
the part is not printable, however correct its dimensions. Pass
`--expect-bodies N` only for parts that are deliberately multi-piece.

Renders are written next to the STL. **Open them and look.** A render nobody
inspects is worse than no render, because it creates false confidence. Never
render wireframe — it hides exactly the bugs this catches.

### Compare against a reference photo (required when a reference exists)

```
python tools\render_check.py projects\BedLifter\MiddleLifter.stl --views front ^
    --reference sources\psvitaGrip\054-1.webp
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

## Import geometry from DXF or SVG

build123d 0.11.1 imports DXF and SVG files directly. For plans, technical
drawings, and CAD exports, this is the preferred path — the file already
carries true geometry with no scale inference needed.

```python
from build123d import import_dxf, import_svg, extrude

# DXF — technical drawing → extruded solid
sketch = import_dxf("drawing.dxf")
part = extrude(sketch, amount=10)

# SVG — vector graphic → sketch
sketch = import_svg("outline.svg")
```

For scanned plans or hand sketches, use the vectorization pipeline below.

## Vectorize a reference image

Turn a raster reference image into SVG/DXF geometry suitable for build123d
import. Two approaches available:

### vtracer (preferred for clean images)

```python
import vtracer

vtracer.convert_image_to_svg_py(
    "sources/subject/photo.jpg",
    "sources/subject/svg/photo.svg",
    colormode="binary",       # "binary" for silhouettes, "color" for photos
    filter_speckle=4,         # remove noise (pixels)
    corner_threshold=60,      # preserve sharp corners
    mode="spline",            # cubic Bezier output
    path_precision=3,
)
```

### cv2 + scipy (for noisy images or when vtracer picks up too much)

```python
import cv2
import numpy as np
from scipy.interpolate import splprep, splev

img = cv2.imread("photo.jpg", cv2.IMREAD_GRAYSCALE)
mask = (img < 228).astype(np.uint8) * 255
kern = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kern)  # remove watermarks

contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
body = max(contours, key=cv2.contourArea)

# Smooth with B-spline
pts = body.reshape(-1, 2).astype(float)
tck, u = splprep([pts[:, 0], pts[:, 1]], s=cv2.arcLength(body, True) * 0.8, per=True, k=3)
x, y = splev(np.linspace(0, 1, 400), tck)
```

### SVG→DXF conversion (no Inkscape needed)

```python
import svgpathtools
import ezdxf
import numpy as np

paths, _ = svgpathtools.svg2paths("outline.svg")
doc = ezdxf.new()
msp = doc.modelspace()

for path in paths:
    points = [(path.point(t).real, path.point(t).imag) for t in np.linspace(0, 1, 200)]
    msp.add_lwpolyline(points, dxfattribs={"layer": "BODY"})

doc.saveas("outline.dxf")
```

See the `vector-tracer` and `accuracy-reviewer` agents for the full workflow.

## Repair non-manifold meshes

pymeshfix repairs singularities, self-intersections, and degenerate elements
while leaving clean regions untouched.

```python
import pymeshfix
import pyvista as pv

mesh = pv.read("projects/BedLifter/MiddleLifter.stl")
fixer = pymeshfix.MeshFix(mesh)
fixer.repair(verbose=True)
fixer.mesh.save("projects/BedLifter/MiddleLifter_repaired.stl")
```

Use this for meshes that fail the watertight gate due to non-manifold edges
or pinch points (e.g. VitaGrip's 2 bad edges out of 225,000). For meshes
with actual holes, use `trimesh.repair.fill_holes()` or `manifold3d` instead.

pymeshlab offers heavier filters when pymeshfix is not enough:

```python
import pymeshlab
ms = pymeshlab.MeshSet()
ms.load_new_mesh("input.stl")
ms.meshing_repair_non_manifold_edges()
ms.meshing_repair_non_manifold_vertices()
ms.save_current_mesh("output.stl")
```

## Render with Blender (headless)

Blender 5.2 produces renders with correct occlusion, directional lighting,
and depth — unlike the matplotlib fallback in `render_check.py`.

```
blender --background --factory-startup --python render_script.py -- input.stl output.png
```

See [system.md](system.md#rendering-blender-vs-matplotlib) for the Blender 5.2
specifics (engine name, STL import API, camera/lighting setup).

## Inspect meshes with pyvista

pyvista provides interactive 3D inspection and offscreen rendering. Useful
for debugging mesh issues before running the full verification gate.

```python
import pyvista as pv

mesh = pv.read("projects/BedLifter/MiddleLifter.stl")
print(f"Points: {mesh.n_points}, Faces: {mesh.n_faces}")
print(f"Bounds: {mesh.bounds}")
print(f"Volume: {mesh.volume:.2f} mm³")

# Non-manifold edge check
edges = mesh.extract_feature_edges(
    boundary_edges=True, non_manifold_edges=True,
    feature_edges=False, manifold_edges=False
)
print(f"Boundary edges: {edges.n_cells}")

# Interactive plot (if display available)
mesh.plot()

# Offscreen render
plotter = pv.Plotter(off_screen=True)
plotter.add_mesh(mesh, color="lightblue")
plotter.screenshot("output.png")
```

## Live-watch a model while editing it (VitaGripPS5)

`tools/watch_model.py` holds a pyvista window open, polls the placement
module and its input meshes for changes, and rebuilds + repaints
automatically — no manual re-run between edits. It is specific to
VitaGripPS5's socket cut: it imports `socket_placement.pose()` /
`load_cutter()` directly, so what is on screen is guaranteed to be the same
geometry the builder would produce, not a second implementation that can
drift from it (see [docs/lessons.md](lessons.md), "the gate must share the
datum it tests").

```
python tools\watch_model.py                       # opens on the boolean CUT result
python tools\watch_model.py --mode overlay         # shows operands: body + cutter + intersection
python tools\watch_model.py --y -31 --sink 30      # start from a specific pose
python tools\watch_model.py --interval 0.5         # poll faster
```

Requires a display (headless: use `render_overlay.py` for a static PNG
instead). Press `c` to toggle overlay/cut, `r` to force a rebuild, close the
window to quit. It never writes an STL — baking the result to a file is a
separate, explicit step (`build_socket_grip.py`), and on VitaGripPS5 it needs
the user's approval each time.

**It does not watch itself.** `WATCH` lists `socket_placement.py`,
`build_socket_grip.py`, `strip_dualsense.py` and the two input meshes — not
`watch_model.py`. Editing the *viewer* (colours, what it draws, the readout)
changes nothing on screen until the process is restarted, and the window keeps
rendering the old code while looking perfectly alive. Kill and relaunch after
touching it.

In OVERLAY mode the VitaGripPS5 scene draws three things: the shell opaque, the
socket cutter translucent red with an edge cage, and the rear touch panel
window as a **green cage** (a buried translucent solid is invisible — VTK
resolves transparency by depth order and submerged geometry loses). CUT mode
applies both differences in the builder's own order.

The heads-up text reports percentage of grip volume removed, whether the
socket has a floor, and the live placement numbers — because a coherent-
looking overlay can still cut almost nothing, and only the `cut` mode shows
that. Its refresh is a manual `pl.update()` loop, not a pyvista timer
callback: an earlier version armed `add_timer_event` and it silently never
fired, leaving the window frozen on the startup pose through nine
successive edits (see [docs/lessons.md](lessons.md), "a callback that never
fires is indistinguishable from a scene that never changes").

## Read DICOM studies (BrokeFeet project)

pydicom and SimpleITK replace the 8-bit brightness thresholds with real
Hounsfield units (~200–300 HU for bone) and recover true voxel spacing
from DICOM headers.

```python
import pydicom
import SimpleITK as sitk

# Read a DICOM series from a directory
reader = sitk.ImageSeriesReader()
dicom_names = reader.GetGDCMSeriesFileNames("path/to/dicom/")
reader.SetFileNames(dicom_names)
image = reader.Execute()

# Voxel spacing from headers (no on-screen ruler needed)
spacing = image.GetSpacing()  # (x, y, z) in mm
print(f"Voxel spacing: {spacing}")

# Threshold on Hounsfield units
bone = sitk.BinaryThreshold(image, lowerThreshold=200, upperThreshold=3000)
```

This directly addresses BrokeFeet's hardest problem: the void/joint
separation whose best brightness threshold scored Youden J = 0.002. HU is a
physical quantity; screen grey is not.

## Adding a new command to a project

If a project introduces a new standard script (e.g. an assembly checker or
a BOM export), document its invocation here and cross-reference it from
the project's own `README.md`.
