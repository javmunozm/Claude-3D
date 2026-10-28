# Fixing a defect register

Moved from the cad-designer agent (2026-10-27); "brief" now reads "plan", and
the review is the form-audit skill's step, not a separate agent.


## Fixing a defect register

When the user has approved a form-audit register, fix every approved entry in
**one pass**. Do not return after the first fix, and do not ask for
an audit between entries. On VitaGripPS5 (rounds 7-8) one defect was fixed per
round. The other entries were carried as "unchanged", and new defects went
unnoticed in regions nobody re-swept.

- **Work by cause group.** Entries that share a cause get one change. Do not
  make a separate change for each symptom.
- **Check each entry as you go** with the auditor's own scripts, if the
  register names them. Run the full five gates once, at the end.
- **The two-failures rule applies per entry.** If an entry fails twice, leave it
  open with its numbers and the reason, and go on to the next entry. Do not
  stop the whole pass.
- **Report a row for every entry**: the ID, what changed in the macro, the
  before and after numbers, and the status (fixed / partial / not attempted, and
  why). Keep the register's IDs. Anything new you notice gets a new ID.
- **Do not declare the register closed.** The closing review is a separate
  step, run with the form-audit skill from its own plan, in one run over the
  whole part. The fix pass's own entry checks are not the review.
- **Work in the plan's priority order, and keep a valid mesh on disk.**
  Every VitaGripPS5 fix pass from r10 to r12 ran out of budget before it
  finished, and the r12 pass was cut off mid-edit by a usage limit. Finish
  the top-priority items to a mesh that passes the hard gates (watertight,
  1 body, the expected genus, walls at the minimum) before starting the next
  item. If the budget runs short, stop at the last valid mesh and write the
  report: what is done and what is not.
- **Open the report with one plain sentence per changed region** saying what
  the geometry physically is now ("the corner is one piece; its end is a
  14 mm wall"), before the numbers.
- **Take hard minima on a 0.5 mm grid or finer.** A 1 mm grid skipped the
  VitaGripPS5 r13 back column that read 3.486 against 3.5.
- **Never write into a project's `stl/` during a pass.** A bake is a byte copy
  of a checked preview, made only with the user's approval.
- **Macro hygiene.** A failed approach goes into the README's "Rejected
  approaches" (what was tried, and the measured reason it failed), not into
  macro comments: 36 % of the VitaGripPS5 macro was comments and docstrings.
  At every bake, delete the switches and stages the bake does not use.
