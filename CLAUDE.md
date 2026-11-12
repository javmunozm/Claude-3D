# Claude-Projects — CAD Project Index

CAD projects built with [build123d](https://github.com/gumyr/build123d) (Python
CAD) rather than FreeCAD. Each subfolder under `projects/` is one physical
object, with its own README.

## CORE DIRECTIVE

1. **Do what you are told.** Execute the task as given. Do not re-scope it, do not substitute a
   different task, do not refuse it because you predict it will find nothing. If it finds
   nothing, run it and report nothing.
2. **No changes without permission — except inside an approved build.** Propose first; edit
   only after the user approves. This covers production code, docs, and memory.
   Once the user approves a build or rebuild, its stages run without further prompts:
   measurements, vectors, macros, exports, renders, and that project's own docs.
   Still ask before: starting a new build, changing repo-wide files (`CLAUDE.md`, `docs/`,
   `.claude/` (skills, hooks, settings), memory), deleting anything, or committing.
   **An approved commit is pushed to `origin` in the same step.** A commit that exists only
   on this disk is not saved.
3. **No claims without testing.** Do not assert a result, a mechanism, or a null from reasoning
   alone. Measure it, or say you have not measured it.
4. **Do not fabricate tests to support a claim.** No test built to reach a conclusion already
   chosen, and no reporting of a test that was not actually run.

Methodology on this project is the user's call. Report what a run produced; do not gate the
user's decisions behind conditions of your own.

## Verification

Geometry that runs and exports without error can still be physically wrong —
every defect found in this repo so far passed both of those tests. After any
geometry change run `python tools\render_check.py <stl> --views front` (the
topology gate; its images are flat silhouettes), then
`python tools\render_views.py <same stl> --views front back` and **look at the
lit render**; before trusting any structural verdict, read its
`tools/reconcile.py` block.

**`python` always means the repo venv,** `D:\Proyectos\Claude-3D\.venv\Scripts\python.exe`
(`requirements.txt`). The `python` on PATH has none of the packages; a hook
(`.claude/hooks/shell_guard.py`, registered in `.claude/settings.json`) denies it.
`python tools\selftest.py` checks the whole toolchain in under two minutes.

**A render is not a measurement.** Run the `form-audit` skill for a number
before believing a picture, and the QUALIFY stage of `photo-to-vectors` before
comparing a picture to a photo — see [docs/agents.md](docs/agents.md).

## Documentation

| Doc | Covers |
|-----|--------|
| [docs/architecture.md](docs/architecture.md) | Repo structure, `sources/` vs `projects/`, geometry code → exports → verification → viewer, project conventions |
| [docs/agents.md](docs/agents.md) | The skills (plan → run → report), the reference chain, the fix-round cycle, the eval set; the subagents they replaced |
| [docs/commands.md](docs/commands.md) | Standard commands: generate, view, verify, DXF/SVG import, mesh repair, Blender rendering, pyvista inspection, DICOM reading |
| [docs/system.md](docs/system.md) | Full toolchain — packages with versions, Blender setup, import capabilities, rendering, disk constraints, known issues |
| [docs/versioning.md](docs/versioning.md) | Nesting a second generation inside a project, the move procedure, the path constants it breaks, retiring a version |
| [docs/attempts.md](docs/attempts.md) | `attempts/` folders, and the record-then-delete procedure when the user rejects work |
| [docs/projects.md](docs/projects.md) | Index of all projects with description and status |
| [docs/workflow.md](docs/workflow.md) | Roles, a session, a project from intake to print, the bounded fix-round cycle, feedback on renders |
| [docs/cad_method.md](docs/cad_method.md) | B-rep by default; bringing a scanned shape into B-rep; CAD tools compared; the stage cache |
| [docs/lessons.md](docs/lessons.md) | Post-mortems with their numbers — one entry per incident, read by the agents each concerns |

Work runs in the main session through skills (`.claude/skills/`): each writes a
plan with numeric ceilings, shows it, runs it once and reports — see
`docs/workflow.md`. The nine subagents were archived on 2026-10-27
(`.claude/agents-archive/`); skills are tested with `.claude/evals/skills_eval.md`.

## The rules that cost this repo the most

- **A version is never a sibling folder.** Nest it as `projects/<Project>/v2/`.
  Never delete an old version as "the old one" — a v2 can import from
  `v0/macros/` (BrokeFeet's did). See [docs/versioning.md](docs/versioning.md).
- **Never delete an attempt on your own judgment.** Only an explicit rejection
  from the user triggers cleanup, and the lesson gets recorded in the project
  README before the folder goes. See [docs/attempts.md](docs/attempts.md).
- **A commit is not saved until it is pushed.** On 2026-11-11 the disk was formatted
  and two weeks of commits that had never been pushed were lost, together with
  every untracked source, export and audit record. Push with every approved
  commit; a hook (`.claude/hooks/git_state.py`) states what is still local at
  session start and after each commit, and `/session-end` reports it.
  `sources/` is not in git: it needs its own copy off this machine.
- **No disk tools without a warning and a backup.** Never recommend, install or
  run a partitioning, boot or firmware tool, or anything that needs a reboot to
  apply, before saying plainly that it can make the machine unbootable and
  checking that the work is pushed and `sources/` is copied **off this
  machine**. On 2026-11-11 Claude recommended MiniTool Partition to merge
  unallocated space into existing partitions; by the user's account it
  corrupted both disks it touched (`C:` and the second disk, `RespaldoD`) and
  the system had to be formatted. A second disk in the same machine is not a
  backup.
