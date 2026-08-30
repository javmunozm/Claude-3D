# System

Environment, dependencies, and conventions shared by every project in this index.

## Toolchain

### Core — geometry authoring and viewing

| Component | Version | Purpose |
|-----------|---------|---------|
| Python | 3.13+ | Runs all geometry, verification, and viewer scripts |
| [build123d](https://github.com/gumyr/build123d) | 0.11.1 | Parametric CAD kernel — code-first geometry (no FreeCAD GUI) |
| [ocp-vscode](https://github.com/bernhard-42/vscode-ocp-cad-viewer) | 3.4.0 | Browser/VS-Code 3D viewer, driven from Python via a local server |

### Mesh processing

| Package | Version | Purpose |
|---------|---------|---------|
| [trimesh](https://trimesh.org/) | 4.12.2 | Mesh loading, topology checks, ray-casting, boolean operations |
| [manifold3d](https://github.com/elalish/manifold) | 3.5.2 | Guaranteed-manifold boolean operations and simplification |
| [pymeshfix](https://github.com/pyvista/pymeshfix) | 0.18.1 | Targeted mesh repair — fixes non-manifold edges and singularities without touching clean regions |
| [pymeshlab](https://pymeshlab.readthedocs.io/) | 2025.7 | Filter suite — Screened Poisson reconstruction, quadric decimation, curvature-aware smoothing (58 plugins) |

### Rendering and visualization

| Package | Version | Purpose |
|---------|---------|---------|
| [Blender](https://www.blender.org/) | 5.2.0 LTS | Headless rendering with correct occlusion and lighting; also used for BrokeFeet sculpt handoff |
| [pyvista](https://pyvista.org/) + [VTK](https://vtk.org/) | 0.48.4 / 9.6.2 | Offscreen rendering and interactive mesh inspection |
| matplotlib | 3.10.7 | Fallback renderer for `render_check.py` (painter-sorted, no z-buffer — see note below) |

### Image processing and measurement

| Package | Version | Purpose |
|---------|---------|---------|
| opencv (cv2) | 4.13.0 | Image analysis, edge detection, silhouette tracing |
| Pillow | 12.2.0 | Image I/O for reference comparison and render output |
| numpy | 2.3.2 | Array operations throughout the pipeline |
| scipy | 1.16.1 | Morphological operations, interpolation, signal processing |
| scikit-image | 0.26.0 | Segmentation, labeling, connected components (BrokeFeet pipeline) |

### CAD interchange

| Package | Version | Purpose |
|---------|---------|---------|
| [ezdxf](https://ezdxf.mozman.at/) | 1.4.4 | DXF read/write — build123d uses this for `import_dxf` and `ExportDXF` |
| svgpathtools | — | SVG path parsing — build123d uses this for `import_svg` |
| shapely | 2.1.2 | 2D computational geometry (polygon operations, offset curves) |

### Medical imaging (BrokeFeet project)

| Package | Version | Purpose |
|---------|---------|---------|
| [pydicom](https://pydicom.github.io/) | 3.0.2 | Read DICOM files — real Hounsfield units and voxel spacing from headers |
| [SimpleITK](https://simpleitk.readthedocs.io/) | 2.5.6 | Image registration, resampling, and volumetric segmentation |

### Other

| Package | Version | Purpose |
|---------|---------|---------|
| networkx | 3.6 | Graph algorithms (used in segmentation analysis) |
| rtree | 1.4.1 | Spatial indexing for point/region queries |
| scikit-learn | 1.7.1 | Clustering (used for sculpt-change detection in Blender handoff) |

### External tools

| Tool | Location | Purpose |
|------|----------|---------|
| Blender | `E:\Blender\blender.exe` (on user PATH) | Headless STL rendering and sculpt handoff |
| OrcaSlicer | `C:\Program Files\OrcaSlicer` | STL → G-code for FDM printing |

### Install

Core packages:

```
pip install build123d ocp-vscode
```

Full toolchain (mesh processing + rendering + medical imaging):

```
pip install pymeshfix pyvista pydicom SimpleITK pymeshlab
```

There is no FreeCAD dependency anywhere in this index — projects were
originally scaffolded assuming FreeCAD but the actual workflow is pure
Python + build123d. Do not reintroduce `.FCStd` files or FreeCAD macro
patterns.

### Known issues

**build123d FontManager crash on Windows.** Version 0.11.1 scans system fonts
on import. A corrupt file (`C:\Windows\Fonts\mstmc.ttf` — 4 KB of garbage
data) crashes the `register_font` method with `TTLibError: Not a TrueType or
OpenType font`. The fix is a try/except wrapping the `TTFont()` / `TTCollection()`
call in `build123d/text.py:register_font`. This patch lives in the installed
package and must be reapplied after upgrading build123d, until upstream fixes it.

## Import capabilities

build123d 0.11.1 supports direct import of four geometry formats:

| Format | Function | Notes |
|--------|----------|-------|
| DXF | `import_dxf()` | Technical drawings and plans — carries true geometry, no scale inference needed |
| SVG | `import_svg()` | Vector graphics — path-based import |
| STEP | `import_step()` | CAD interchange — full B-rep solid import |
| STL | `import_stl()` | Triangle mesh — no topology, suitable for reference/comparison |

For plans and technical drawings, DXF/SVG import is the preferred path because
the file already carries true geometry with dimensions — no photograph
measurement or scale anchor is needed.

## Rendering: Blender vs. matplotlib

`render_check.py` currently uses matplotlib (`Poly3DCollection` with
`set_sort_zpos`). This is a **painter-sort renderer with no depth buffer** —
it produces flat single-color silhouettes with no shading. On concave or
organic geometry it can show incorrect occlusion.

Blender 5.2 headless renders the same STL in ~12 seconds with correct
occlusion, directional lighting, and depth. It is installed and on PATH.

When the Blender renderer is integrated into `render_check.py`, keep
matplotlib as an automatic fallback and **record which renderer produced
each image** — a weak render must not be mistaken for a strong one.

**Blender 5.2 specifics** (so these are not re-derived):

- Engine: `BLENDER_EEVEE` (not `BLENDER_EEVEE_NEXT` — that name raises an enum error)
- STL import: `bpy.ops.wm.stl_import()` (the 5.x API; `bpy.ops.import_mesh.stl` is legacy fallback)
- Camera: orthographic, fitted to bounding-box radius
- Lighting: two sun lights (a single front-on sun renders nearly flat)

```
blender --background --factory-startup --python render.py -- input.stl output.png
```

## File types

| Extension | Role |
|-----------|------|
| `.py` (in `macros/`) | Source of truth — parametric geometry definitions |
| `.step` | Generated CAD interchange format — import into any CAD tool |
| `.stl` | Generated mesh — feed directly to a slicer for 3D printing |
| `.dxf` | Technical drawing input — importable directly via `import_dxf` |
| `README.md` | Per-project goal, status, dimensions, and file index |

`.step`/`.stl` files are regenerated, not edited. Treat them like compiled
output — safe to delete and rebuild from the `.py` source at any time.

## Units and coordinate convention

- All dimensions in source scripts are in **millimeters**.
- Per-piece local origin is the center of the bottom face (floor level),
  with **+Z up**. Horizontal axis conventions (e.g. +X direction) are
  documented per-project since they depend on the physical object being
  modeled — see the project's own README.

## Directory layout

```
Claude-Projects/
├── CLAUDE.md              Root index — projects table + links to docs/
├── docs/                  Index-wide documentation (this folder)
│   ├── architecture.md    How a project's geometry/build pipeline fits together
│   ├── system.md          This file — environment, deps, conventions
│   ├── commands.md        Standard commands for building/viewing/checking
│   ├── projects.md        Index of all projects with description and status
│   └── versioning.md      Adding a version to a project without cluttering projects/
├── tools/                 Shared verification tooling
│   ├── render_check.py    Topology gate + shaded renders + reference comparison
│   ├── reconcile.py       Detects drift between structural checks and geometry
│   └── read_3mf.py        Read meshes from 3MF archives
├── references/            Reference images/specs per subject, with SOURCES.md
│   └── <subject>/         One folder per reference subject
└── projects/              All CAD projects live here
    └── <ProjectName>/
        ├── README.md      Project-specific goal, status, dimensions
        ├── macros/        build123d Python scripts
        └── *.step / *.stl Generated output
```

## Disk constraints

C: drive is nearly full (93%). Install large packages or external tools to
D: or E: where possible. Blender is on E:.

## Adding a project

1. Create `projects/<ProjectName>/` with a `macros/` subfolder and a `README.md`.
2. Follow the script pattern in [architecture.md](architecture.md).
3. Add a row to the Projects table in [projects.md](projects.md).
