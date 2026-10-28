---
name: cad-build
description: Build or change build123d geometry in this repo — a new part, a change to a project macro, or a fix pass on an approved form-audit register. Writes a build plan first (changes, arithmetic, the gate that proves each change, numeric ceilings), shows it, then carries it out once and reports against it. Use whenever geometry or a macro changes. Not for measuring a built part's form (form-audit) or for strength and clearance numbers (fdm-tolerance).
---

# cad-build

You build parametric geometry with **build123d** (never FreeCAD). The script
layout and project conventions are in `docs/architecture.md`, packages and
known issues in `docs/system.md`: Grep them for the section you need.

Three phases, always in this order: **PLAN → RUN → REPORT**. No edit and no
build happens before the plan is written and shown to the user.

## 1. PLAN (no edits, no builds)

Read only what the plan needs: the project's `STATE.md` (sections Open
entries, Locks, Gates, Commands), the register rows being fixed (Grep by ID),
and the stage modules that own them. Never read a whole README, macro or old
review.

Write the plan from `plan_template.md` (this folder) to
`projects/<Project>/audit/r<NN>/plan_build.md` (outside a round:
`projects/<Project>/work/plan_build.md`) and show it in chat. Every field is
filled; a field you cannot fill is a question for the user, not a guess.

The plan must contain:
- **The arithmetic, done.** The load path and every clearance the change
  touches, computed from the constants. Run
  `projects/<Project>/docs/mechanism_sizing.py` or the project's equivalent
  with the proposed constants if it exists. Round 4 of
  SurgicalDrillGuide existed only because a Ø16 core could not bear on a
  Ø16.85 mouth, which the constants already said (`reference/gates.md`).
- **One row per change:** register ID(s) / file and function / constant from →
  to / the measurable effect expected / the check that proves it, with its
  threshold. Entries that share a cause are one change.
- **Ceilings as numbers:** builds (default 4; one-change pass 2), images
  (default 6; one-change pass 2), one scratch script.
- **Order and fallback:** priority order, and "if a ceiling is reached, stop
  at the last state that passes the hard gates with items 1–k done".
- **Not touched:** locks with tolerances, `stl/`, other rounds' folders.

## 2. RUN (the plan, once)

- Do the rows in order. After each, run only that row's check, and record the
  before → after number in the report as you go.
- **Nothing outside the plan.** A step that is not in the plan needs a written
  amendment in the plan file first (what, why, with the number that forced
  it). At most one amendment per pass; a second need means stop and report.
- **Two failures on one row** → leave it open with its numbers and reason, and
  go to the next row. Do not stop the pass.
- **Builds** count against the ceiling. Run them in the foreground with
  `timeout 300 python …` (Bash tool). A build over 5 minutes is a defect to
  report, not to wait out.
- **Rebuild only what changed.** A macro built on `tools/stage_cache.py`
  (SurgicalDrillGuide is the reference) rebuilds and rewrites only the parts
  whose inputs changed, and prints `rebuilt / from cache / written`: put that
  line in the report. A macro without it gets it at its next round (the same
  pattern: key each part, export only on a new key).
- **Previews never go into `stl/`.** Build into a preview folder
  (`SDG_OUT_DIR`, or the macro's `--out`). Before a bake overwrites `stl/`,
  back up only the files the bake replaces, not the whole folder.
- Check each new solid with `is_valid` and a 2D section before any export.
  Booleans fuse only where solids overlap (`reference/modeling.md`).
- At the end, run the **five gates** once (`reference/gates.md`, or `/verify`).
  Do not edit the script after the final export.

## 3. REPORT

Write `audit/r<NN>/fix_report.md` (or `work/build_report.md`), then show in
chat, at most 25 lines:
1. One plain sentence per changed region saying what the geometry physically
   is now ("the corner is one piece; its end is a 14 mm wall").
2. One row per plan row: ID | change | before → after | fixed / partial / not
   attempted, and why.
3. The five gate results, as numbers.
4. What is not done, and why. Builds and images used against the ceilings,
   and any amendment.

The closing review of a register is a separate step with the **form-audit**
skill, never this pass's own checks. If the session ends mid-pass, write
`audit/r<NN>/handoff.md` (`docs/templates/handoff.md`); the next session starts
from the plan plus the handoff.

## Reference (read the section you need)

| File | Holds |
|---|---|
| `reference/gates.md` | The arithmetic rule and the five gates (a)–(e), with the incidents behind each |
| `reference/modeling.md` | Representation choice, script layout, booleans, cut-then-refill, height fields, organic forms, mesh pipelines, when to stop tweaking |
| `reference/fix-register.md` | Rules for a fix pass on a register |
| `reference/failures.md` | Why "it built without error" proves nothing; writing about physical state |

## Rules

- Don't introduce FreeCAD, `.FCStd` files, or GUI workflows.
- Don't hand-edit `.step`/`.stl`: change the Python source and regenerate.
- Don't invent physical dimensions (hardware, loads, clearances): ask the user,
  or record them as unverified in the README's verification checklist.
- Don't declare geometry correct on a successful run, a bounding box, a
  wireframe or a silhouette-profile table. Only the five gates count, and gate
  (e) needs the comparison image actually looked at.
- If a whole-form comparison fails twice on the same aspect, stop tuning:
  re-measure and report the structural change it implies.
- Strength, safety factor and material questions go to the fdm-tolerance skill.
  A changed dimension that a structural check uses must be said explicitly.
- Never write a README claim about the physical world you have not verified
  ("printed", "unchanged", "test-fitted"). Attribute user claims.
- A failed approach goes into the README's "Rejected approaches", not into
  macro comments.
## Session rules

- **Write as you go.** Each finished row goes into the report when it is done.
- **Two failures, then stop** that approach: report what failed, with its
  numbers, and what you would try next.
- **One scratch script, edited,** printing at most about 50 lines. Not one
  file per question.
- **Images confirm, they do not search.** Measure first, then one region
  render (`tools/render_roi.py`).
- **Read only what you need.** Grep long docs and the README by section; read
  `STATE.md`, not old reviews or the whole macro. Never `Glob` `**/*`.
- **Parallel calls.** Put independent reads and checks in one response.
- **A build over 5 minutes is fixed with a stage cache** (`docs/cad_method.md`,
  "A stage cache"), not waited out: in the VitaGripPS5 r10 run the re-billing
  after 10-minute builds was 40 % of the cost.
- **Shell.** One command per call, absolute paths, no `cd`, no `python -c`, no
  `sleep` loops; view files with Read / Glob / Grep. A hook denies the rest and
  says how to rewrite it.
