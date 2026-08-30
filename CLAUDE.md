# Claude-Projects — CAD Project Index

This directory indexes all CAD projects. Each subfolder is a separate project with its own README containing project info. Projects are built with [build123d](https://github.com/gumyr/build123d) (Python CAD) rather than FreeCAD.

## CORE DIRECTIVE

1. **Do what you are told.** Execute the task as given. Do not re-scope it, do not substitute a
   different task, do not refuse it because you predict it will find nothing. If it finds
   nothing, run it and report nothing.
2. **No changes without permission.** Propose first; edit only after the user approves. This
   covers production code, docs, and memory.
3. **No claims without testing.** Do not assert a result, a mechanism, or a null from reasoning
   alone. Measure it, or say you have not measured it.
4. **Do not fabricate tests to support a claim.** No test built to reach a conclusion already
   chosen, and no reporting of a test that was not actually run.

Methodology on this project is the user's call. Report what a run produced; do not gate the
user's decisions behind conditions of your own.

## Structure

```
Claude-Projects/
├── CLAUDE.md          ← this file (project index and conventions)
├── docs/              ← index-wide documentation (see below)
├── tools/             ← shared tooling (render_check, reconcile, read_3mf)
├── references/        ← reference images/specs per subject, with SOURCES.md
├── projects/          ← all CAD projects live here
│   ├── <ProjectName>/
│   │   ├── README.md      ← project info, goals, status, file locations
│   │   ├── macros/         ← build123d Python scripts that generate the geometry
│   │   └── *.step / *.stl  ← generated CAD output
│   └── ...
```

## Verification

Geometry that runs and exports without error can still be physically wrong —
every defect found in this repo so far passed both of those tests. After any
geometry change run `python tools\render_check.py projects\<Project>\<Part>.stl
--views front` and **look at the render**; before trusting any structural
verdict, read its `tools/reconcile.py` block. See
[docs/commands.md](docs/commands.md).

For mesh repair and inspection, see the pymeshfix, pymeshlab, and pyvista
commands in [docs/commands.md](docs/commands.md). For the full toolchain
and package versions, see [docs/system.md](docs/system.md).

## Documentation

| Doc | Covers |
|-----|--------|
| [docs/architecture.md](docs/architecture.md) | How a project's geometry code, exported files, verification, and viewer fit together |
| [docs/system.md](docs/system.md) | Full toolchain — all packages with versions, Blender setup, import capabilities, rendering options, disk constraints, known issues |
| [docs/commands.md](docs/commands.md) | Standard commands: generate, view, verify, DXF/SVG import, mesh repair, Blender rendering, pyvista inspection, DICOM reading |
| [docs/projects.md](docs/projects.md) | Index of all projects with description and status |
| [docs/versioning.md](docs/versioning.md) | Adding a version to a project without cluttering `projects/` — nesting rule, move procedure, the path constants it breaks |

## Agents

Project-level subagents in `.claude/agents/`, tailored to this repo's build123d/FDM-printing workflow:

| Agent | Use for |
|-------|---------|
| `reference-analyst` | Turning reference photos/specs into a dimensioned measurement table with per-value confidence |
| `cad-designer` | Authoring/revising build123d geometry scripts, part fit and assembly |
| `print-tolerance-expert` | Fit clearances, structural sizing (stress/buckling/safety factor), print settings |
| `bone-morphologist` | Repairing CT-derived skeletal meshes — porous or perforated bone that is a segmentation artefact, not anatomy |
| `blender-handoff` | Preparing meshes for Blender sculpting and importing sculpted results back — prep scripts, sculpt detection, smoothing gates |

Typical flow for a photo-driven part: `reference-analyst` (measure) →
`cad-designer` (build + verify) → `print-tolerance-expert` (tolerances,
structural check). Each hands off explicitly rather than re-deriving the
previous stage's numbers.

For a scan-derived part, `bone-morphologist` sits before `cad-designer`: it
repairs the reconstructed mesh, then the builder turns it into a printable
model. Give it the parameters already swept and the approaches already
rejected — see BrokeFeet's README — or it will re-walk them.

When a mesh needs hand-sculpting in Blender, `blender-handoff` sits between
`bone-morphologist` (or `cad-designer`) and the human sculptor: it prepares
the mesh, writes the `.blend` file, and gates what comes back. See
BrokeFeet's `v2/blender/` directory for the established workflow.

**Brief agents to report negative results.** In this repo the most useful
agent output has been a measured "this does not work, and here is why", plus
corrections to the task premise. An agent that only reports success will hand
back a better metric attached to a worse model — see BrokeFeet's
`area/volume` vs `genus` history.

## Skills

Project-level skills in `.claude/skills/`, invocable as slash commands:

| Skill | Use for |
|-------|---------|
| `/verify` | Run the five-gate geometry verification for a project part: regenerate → topology → shaded render → mating check → reference comparison |

## Conventions

- Each project lives in its own named subfolder under `projects/`.
- Every project folder must have a `README.md` with at minimum: project goal, current status, and location of the generated `.step` / `.stl` files.
- Geometry is authored as Python scripts under `projects/<ProjectName>/macros/` using build123d, and run to regenerate `.step` / `.stl` output — there are no `.FCStd` files.
- Viewing/inspection uses `ocp-vscode` (`python -m ocp_vscode`), not the FreeCAD GUI.
- `references/` and `tools/` stay at the repo root, shared across all projects — not nested under `projects/`.

### One project = one physical object

**A version is never a sibling folder.** `BrokeFeet/` and `BrokeFeetV1/` were
one clubfoot model split across two top-level folders; the result was a
duplicated 46 MB of byte-identical STLs, two READMEs each claiming to be ready,
and no single place saying which file to slice.

When a project gains a second generation, nest it:

```
projects/<Project>/
├── README.md     ← which version ships, what each holds, shared clinical scope
├── v0/           ← README.md, macros/, its own exports
└── v2/           ← README.md, macros/, its own exports
```

The root `README.md` is a **navigation layer**, not a summary: which version
ships and which file to slice, what each version owns, and which versions still
depend on each other. Version folders are named for what they ship, and gaps are
fine (`v0` + `v2` with no `v1` is correct when the v1 work shipped as v2).

See [docs/versioning.md](docs/versioning.md) for the full procedure — including
the path constants that nesting breaks and how to verify the move.

**Never delete an old version as "the old one" without checking imports.** v2
here imports directly from `v0/macros/` and does not run without it.

## Projects

See [docs/projects.md](docs/projects.md) for the full list of projects with description and status.
