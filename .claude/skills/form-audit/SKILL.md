---
name: form-audit
description: Measure the actual 3D form of a built mesh or solid — cross-sections, wall thickness, taper, volumetric vs flat, slits, symmetry — against the intended form. Modes QUESTION (one doubt), REGISTER (whole-part sweep into one defect register with a fix proposed per entry) and REVIEW (after a fix pass, re-measure every entry and re-sweep). Writes an audit plan first, runs it once, reports a verdict. Use after a fix pass, when a render "looks wrong" but gates pass, or before trusting any visual verdict about shape. Not for changing geometry (cad-build) or comparing to a photo (photo-to-vectors).
---

# form-audit

You measure what a mesh **actually is**, in numbers, so nobody has to guess
from a picture. You never change geometry here: the audit proposes fixes,
and fixing is a separate cad-build step after the user approves.

Three phases, always in this order: **PLAN → RUN → REPORT**. No measurement
script runs before the plan is written and shown to the user.

## Modes

| Mode | When | Builds | Images |
|---|---|---|---|
| QUESTION | One specific doubt ("are the handles flat?") | 0 | ≤ 2 |
| REGISTER | A whole-part audit, with the user's marks | 0 | ≤ 4 |
| REVIEW | After a fix pass, against the register and the baseline sweep | ≤ 1 | ≤ 3 |

## 1. PLAN (no measuring)

Read only `projects/<Project>/STATE.md`, the register rows involved (Grep by
ID), the user's marks and their located coordinates, and the macro constants
that define the intended values (Grep, not the whole macro).

Write the plan from `plan_template.md` (this folder) to
`projects/<Project>/audit/r<NN>/plan_audit.md` and show it in chat. It must
contain:
- **The axis convention and how it will be derived:** which known dimension
  each extent will be matched to (`reference/measuring.md`, step 1).
- **One row per question or mark:** where (region, model coordinates or the
  section plane) / the measurement that answers it (the table in
  `reference/measuring.md`, step 3) / the intended value from the constants /
  the threshold.
- **The sweep** (REGISTER, REVIEW): one `tools/form_sweep.py` command with the
  regions file, thresholds, and for REVIEW the baseline named in `STATE.md`.
  The regions it will not reach are listed as unswept now, not discovered later.
- **Extra checks:** at most 3, each named, with the function in the one
  scratch script that will run it.
- **Ceilings** from the mode table, and the deliverable path.
- **Done when:** the list of rows that must have a number for the verdict.

## 2. RUN (the plan, once)

- **Write the summary block first** (`docs/templates/review_summary.md`) and
  keep it current as each number comes in.
- Run the plan's rows in order: the sweep is one command, the extra checks are
  functions in one scratch script, edited, printing at most about 50 lines.
- **Nothing outside the plan.** A measurement not in the plan needs a written
  amendment in the plan file first (what, why, the number that forced it). At
  most one amendment per run; a second need means stop and report it as an
  open question.
- **Do not re-measure a row to refine it.** A row has its number when its
  sampling passes the traps in `reference/measuring.md` (window size, < 3
  vertices, filter box, extreme vs first station). Then it is done.
- **Two failures on one row** → report it as "not measured", with what
  failed, and go on.
- Measure, don't look: a render locates a feature worth measuring and is
  never the measurement (`reference/measuring.md`, step 4).

**REVIEW independence.** The review judges the mesh, not the reasoning that
built it. Re-measure every register entry from the mesh with the plan's own
checks; never copy a number from the fix report as review evidence. Prefer a
fresh session (`/clear`) for a review, so the fix pass's context is not in it.

## 3. REPORT

Write `audit/r<NN>/<question|register|review>.md` in the format of
`reference/report.md`: summary block first, then the axis convention, the
sections, the register, the fix proposal per cause group, *Not defects*, and
one verdict: FORM MATCHES INTENT / ACCEPT WITH LISTED ARTIFACTS / DEFECTS
FOUND / METHOD REVIEW / CANNOT ESTABLISH ORIENTATION.

In chat, show only the summary block (at most 30 lines).

**METHOD REVIEW** overrides the others when the fix pass created 3 or more
regression IDs, or a region is in its third consecutive register. The next
step is then a method decision for the user, not another fix pass.

## Reference (read the section you need)

| File | Holds |
|---|---|
| `reference/measuring.md` | Why renders mislead; axis convention; cross-section technique and its traps; which measurement answers which question; which view contains which axis |
| `reference/register.md` | The whole-part sweep checks, register fields and grouping rules, review mode, `form_sweep.py` usage |
| `reference/report.md` | The report template and what each verdict requires |

## Rules

- Don't report a visual impression as a finding: "not measured", never
  "appears to".
- Don't pass a part whose orientation you could not establish.
- Compare against the **intended** form (macro constants, README dimension
  table, stated goal), not a photo: photos go through photo-to-vectors.
- When a measurement contradicts the premise you were given, report the
  contradiction as the primary finding.
- The *Not defects* section is mandatory when something checked turned out
  fine, with its number.
- Write only into the round's own `audit/r<NN>/` folder and the scratchpad.

## Session rules

- **Write as you go.** Each finished number goes into the deliverable when you
  have it. If the session must end mid-run, write `audit/r<NN>/handoff.md`
  (`docs/templates/handoff.md`: done / not done / files / next step); the next
  session starts from the plan plus the handoff.
- **Two failures, then stop** that approach: report what failed, with its
  numbers, and what you would try next.
- **One scratch script, edited,** printing at most about 50 lines.
- **Images confirm, they do not search.** Measure numerically; look once at a
  cropped region.
- **Read only what you need.** Grep long docs and the README by section. Never
  `Glob` `**/*`.
- **Parallel calls.** Put independent reads and checks in one response.
- **The REVIEW build** runs in the foreground with `timeout 300 python …` in
  the Bash tool (in PowerShell `timeout` is a different command). A build over
  5 minutes is a defect to report, not something to wait out.
- **Shell.** One command per call, absolute paths, no `cd`, no `python -c`, no
  `sleep` loops; view files with Read / Glob / Grep. A hook denies the rest and
  says how to rewrite it.
