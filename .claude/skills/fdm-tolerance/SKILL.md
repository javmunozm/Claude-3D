---
name: fdm-tolerance
description: The numbers that go into an FDM-printed part — fit clearances between mating parts, wall thickness, structural sizing (stress, bending, shear, buckling, bearing, safety factor), print orientation, infill and layer settings — and whether a design is dimensionally and structurally sound. Reconciles every input against the geometry before any verdict. Writes a plan first, runs it once, reports PASS/FAIL per check. Use whenever a clearance is chosen, a load-bearing part is sized or re-checked after a change, or a "dimensions to verify before printing" list is filled. Not for building the geometry (cad-build).
---

# fdm-tolerance

You determine the numbers a printed part needs and whether the design holds
them. You don't edit geometry: you propose the dimension change, and the
cad-build skill makes it, after the user approves.

**A check is only worth what its inputs are worth.** A BedLifter check printed
`ALL CHECKS PASS` for a design that no longer existed (tilt 9.332° vs 8.850°,
collar Ø50 vs a built Ø22.5), and the README cited it. Reconciling inputs is
part of running the check (`reference/sizing.md`).

Three phases, always in this order: **PLAN → RUN → REPORT**. No check runs
before the plan is written and shown.

## 1. PLAN (no calculating)

Read the project's `STATE.md` (Gates, Open entries, Locks), the existing check
script (for SurgicalDrillGuide `docs/mechanism_sizing.py`), and the README's
conventions (safety factor, material, load assumptions): Grep by section.
Treat the README as a claim, not a source.

Write the plan from `plan_template.md` (this folder) to
`projects/<Project>/work/plan_sizing.md` and show it in chat. It must say:
- **The question** in one sentence, and the verdict it will produce.
- **Load cases, named:** each load, its value, and its path ("500 N clamp,
  all on the shoe's centre section"), with the worst case stated.
- **Inputs and their reconcile pairs:** every geometry-derived number the
  check consumes, the name it has in the geometry module, and its direction
  (`higher-is-conservative`, `lower-is-conservative`, `neutral`).
- **Allowables:** material, value, source, the safety factor, and the
  anisotropy assumption (layer lines: about 50–70 % in the worst axis).
- **Stress concentrations:** where a Kt applies, and whether the check applies
  it. A check that skips Kt says so in its verdict.
- **For a clearance:** the fit type, the printer class, the orientation of the
  mating faces, the confidence of each input dimension (a photo-derived
  dimension cannot anchor a tight fit: it needs Specified), and the coupon or
  measurement that will confirm it.
- **What a change would touch:** for a proposed constant, which parameters and
  parts it feeds (for SurgicalDrillGuide, the build's `rebuilt` line shows it).

## 2. RUN (the plan, once)

- Reconcile first (`tools/reconcile.py`, `strict=True`); its output prints
  above any PASS/FAIL. Unreconciled inputs make the verdict **unverified**,
  and it is reported that way.
- Run the existing check script, or extend it in the same pattern (pure math,
  no CAD import, docstring revision kept current). One check per load-bearing
  feature: axial, bending, shear, buckling, bearing.
- **Drift found** → fix the check's inputs to match the geometry, re-run, and
  report both verdicts, before and after.
- **Nothing outside the plan** without a written amendment (at most one).
  **Two failures** on one check → report it as not computed, with why.

## 3. REPORT

In `work/sizing_report.md`, then in chat, at most 25 lines:
1. The verdict per check, `[PASS]` / `[FAIL]` against
   `strength / safety factor`, with SF as a number and the Kt note.
2. The reconcile result (pairs checked, drift found).
3. For a FAIL or a marginal PASS: the specific dimension change (constant,
   from → to), and what it touches. Not "make it bigger".
4. New unverified assumptions, added to the README's "dimensions to verify
   before printing".

## Reference

| File | Holds |
|---|---|
| `reference/sizing.md` | The stale-check incident, the reconcile rules, the domains (fit tolerances, structural sizing, print settings) with this repo's defaults and allowables, how to work |

## Rules

- **Supports and cuts are the slicer's job, never a fix.** Don't flag
  printability as a defect, and don't propose supports, splitting the part or
  print-orientation tricks to rescue a weak or unprintable feature: thicken,
  fillet or change the material instead.
- Don't assert a design is safe without running the numbers; show the
  calculation or the script.
- Don't report PASS from a check whose inputs you haven't reconciled.
- Flag datasheet allowables as optimistic for FDM, especially across layers.
- State the reasoning behind every clearance (printer accuracy, material,
  load case), not only the number. Holes print undersized, bosses oversized.
- Ask before editing any constant, even a PLACEHOLDER.

## Session rules

- **Write as you go.** Each finished result goes into the deliverable when you
  have it. If the session must end mid-run, write `work/handoff.md`
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
- **Scripts and builds** run in the foreground with `timeout 300 python …` in
  the Bash tool (in PowerShell `timeout` is a different command). Anything over
  5 minutes is a defect to report, not something to wait out.
- **Shell.** One command per call, absolute paths, no `cd`, no `python -c`, no
  `sleep` loops; view files with Read / Glob / Grep. A hook denies the rest and
  says how to rewrite it.
