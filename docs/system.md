# System

Environment, dependencies, and conventions shared by every project in this index.

## Toolchain

| Component | Purpose |
|-----------|---------|
| Python 3.10+ | Runs all geometry, verification, and viewer scripts |
| [build123d](https://github.com/gumyr/build123d) | Parametric CAD kernel — code-first geometry (no FreeCAD GUI) |
| [ocp-vscode](https://github.com/bernhard-42/vscode-ocp-cad-viewer) | Browser/VS-Code 3D viewer, driven from Python via a local server |

Install once per environment:

```
pip install build123d ocp-vscode
```

There is no FreeCAD dependency anywhere in this index — projects were
originally scaffolded assuming FreeCAD but the actual workflow is pure
Python + build123d. Do not reintroduce `.FCStd` files or FreeCAD macro
patterns.

## File types

| Extension | Role |
|-----------|------|
| `.py` (in `macros/`) | Source of truth — parametric geometry definitions |
| `.step` | Generated CAD interchange format — import into any CAD tool |
| `.stl` | Generated mesh — feed directly to a slicer for 3D printing |
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
│   └── projects.md        Index of all projects with description and status
├── tools/                 Shared verification tooling
│   ├── render_check.py    Topology gate + shaded renders + reference comparison
│   └── reconcile.py       Detects drift between structural checks and geometry
├── references/            Reference images/specs per subject, with SOURCES.md
│   └── <subject>/         One folder per reference subject
└── projects/              All CAD projects live here
    └── <ProjectName>/
        ├── README.md      Project-specific goal, status, dimensions
        ├── macros/        build123d Python scripts
        └── *.step / *.stl Generated output
```

## Adding a project

1. Create `projects/<ProjectName>/` with a `macros/` subfolder and a `README.md`.
2. Follow the script pattern in [architecture.md](architecture.md).
3. Add a row to the Projects table in [projects.md](projects.md).
