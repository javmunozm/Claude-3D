# Claude-Projects — CAD Project Index

CAD projects built with [build123d](https://github.com/gumyr/build123d) (Python
CAD) rather than FreeCAD. Each subfolder under `projects/` is one physical
object, with its own README.

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

## Verification

Geometry that runs and exports without error can still be physically wrong —
every defect found in this repo so far passed both of those tests. After any
geometry change run `python tools\render_check.py projects\<Project>\<Part>.stl
--views front` and **look at the render**; before trusting any structural
verdict, read its `tools/reconcile.py` block.

**A render is not a measurement.** Ask `form-auditor` for a number before
believing a picture, and `perspective-checker` before comparing a picture to a
photo — see [docs/agents.md](docs/agents.md).

## Documentation

| Doc | Covers |
|-----|--------|
| [docs/architecture.md](docs/architecture.md) | Repo structure, `sources/` vs `projects/`, geometry code → exports → verification → viewer, project conventions |
| [docs/agents.md](docs/agents.md) | The nine subagents, their handoff order, the `/verify` skill, and how to brief them |
| [docs/commands.md](docs/commands.md) | Standard commands: generate, view, verify, DXF/SVG import, mesh repair, Blender rendering, pyvista inspection, DICOM reading |
| [docs/system.md](docs/system.md) | Full toolchain — packages with versions, Blender setup, import capabilities, rendering, disk constraints, known issues |
| [docs/versioning.md](docs/versioning.md) | Nesting a second generation inside a project, the move procedure, the path constants it breaks, retiring a version |
| [docs/attempts.md](docs/attempts.md) | `attempts/` folders, and the record-then-delete procedure when the user rejects work |
| [docs/projects.md](docs/projects.md) | Index of all projects with description and status |
| [docs/lessons.md](docs/lessons.md) | Post-mortems with their numbers — one entry per incident, read by the agents each concerns |

## Two rules that cost this repo the most

- **A version is never a sibling folder.** Nest it as `projects/<Project>/v2/`.
  Never delete an old version as "the old one" — v2 here imports from
  `v0/macros/`. See [docs/versioning.md](docs/versioning.md).
- **Never delete an attempt on your own judgment.** Only an explicit rejection
  from the user triggers cleanup, and the lesson gets recorded in the project
  README before the folder goes. See [docs/attempts.md](docs/attempts.md).
