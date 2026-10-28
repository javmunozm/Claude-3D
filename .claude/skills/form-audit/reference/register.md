# Sweep, register and review

Moved from the form-auditor agent (2026-10-27); "brief" now reads "plan" (the
audit plan, which carries the user's questions and marks).


## One audit, one register, one review

An audit is not a search that ends at the first defect. You sweep the whole
part, record **every** defect in one register, and propose the fix for each.
The cad-build skill then fixes the whole register in one pass, and the review
covers the whole part once. Do not stop after one finding to fix it and then
audit again.

This is why (VitaGripPS5, rounds 7-9, 2026-09-26 to 09-30). The r7 audit only
checked the windows its brief named and the builder's own. It found six
defects. r8 fixed one of them, the crease. The re-check after r8 re-ran only
the crease scripts and listed the other five as "Unchanged". The user then
marked r8 by hand. Three of the marks (a V-notch at the front junction, a scar
across the flank, teeth along the lower lobe/bar edge) were in no list. No
audit had swept those regions.

### Sweep the whole part, not only the plan's questions

Answer the plan's specific questions first, then sweep everything. Split the
part into named regions: for example handles, end lobes, back, pocket,
junctions, and every free edge. Run the same checks on every region, in one
script:

- **Continuity**: the turn angle between neighbouring sections and between
  neighbouring face normals. A crease is a local spike, not a high average.
- **Bumps and hollows**: deviation from a smoothed copy of the same surface,
  such as a height field or a section series smoothed along its path. Report
  the depth and the extent.
- **Edges**: serration along every boundary and free edge. Measure the tooth
  height off a smoothed copy of the edge polyline.
- **Walls**: the minimum thickness in each region, measured on a section.
  Take a hard minimum (wall, back, pit wall) on a **0.5 mm grid or finer**,
  not 1 mm. On VitaGripPS5 r13 (2026-10-02), the designer's 1 mm grid read
  the back as 3.563. A 0.5 mm grid found 3.486 at (-65.0, -8.47), below the
  3.5 limit, in a column the coarse grid skipped.
- **Slits**: cast rays across every boolean outline and every zone boundary,
  and fail on any air gap inside the part. Watertight, body count and genus
  all pass an open slit. The VitaGripPS5 r10 corner had a slit 0.5-0.9 mm
  wide and 7-12 mm deep, and read watertight, 1 body and genus 2. Classify
  each gap as enclosed, open to the outside, or a skimming ray, before calling
  it a slit.
- **Symmetry**: the maximum deviation after mirroring, **and where it is**. A
  value with no location is not a finding.

Choose the thresholds from the part's intent, and state them in the report. A
region you did not sweep is listed as **unswept**, not omitted.

### The register

Write every defect into one table as you find it, in the deliverable file.
Entries keep their IDs (D1, D2, ...) from round to round. Never renumber them.

| Field | Content |
|-------|---------|
| ID | D1, D2, ... |
| Region / location | Region name and model coordinates (x, y, z ranges) |
| Measurement | The number that shows the defect, and the threshold |
| Source | `sweep`, `plan` (a question the user asked), or `user mark <file>` |
| Cause | `measured: ...` or `not verified` |
| Proposed fix | What to change in the macro: the constant, stage or function, and the direction |
| Interacts with | Other IDs that share a cause or constrain this fix |

- **Every user mark gets an entry.** If the user has marked up
  a render, locate each mark in model coordinates and measure it. A mark that
  measures as fine goes under *Not defects*, with its number.
- **Classify every mark,** with the number that decides it: geometry; a
  designed edge not rounded; tessellation or shading (sub-layer facet noise
  that the closeup renders draw as lines: 6 of the 12 r13 paths measured so);
  or not reproducible. The class counts go into the summary block.
- **Group by cause.** Defects that share a cause get one proposed fix, and
  each entry names it. Several defects can come from a single stage boundary.
  The r7 crease and basin were both the trigger-zone edge at Y 52.
- **Group by construction step, not only by location.** For each entry, name
  the macro stage or boolean that made it. When three or more entries lie on
  the outline of one boolean, report that boolean as the defect, and propose
  replacing the method rather than tuning its edges. On VitaGripPS5 (r7-r10)
  ten IDs (D1, D2, D11, D12, D16, D19, D20, D21, D23, D35) were the outline of
  one cut-out-and-glued-back corner patch. Four rounds tuned its edges, one
  constant at a time. See `docs/lessons.md`, "Ten defect IDs were one
  glued-in patch".
- **Say what the geometry physically is, in one plain sentence, before the
  numbers.** For example: "the corner is a separate block glued into a hole",
  or "this is an open slit, not a seam". The VitaGripPS5 reports gave turn
  angles per ID for four rounds, and nobody wrote that the corner was a patch
  until the user asked.
- **Flag conflicts.** If a fix for one entry would break another, say so in
  *Interacts with* (VitaGripPS5's plan bow against the upper pit walls at
  3.48 mm). The user decides those, not the audit.
- The audit proposes the fixes. It does not make them: fixing is a separate
  cad-build step, after the user approves the register.

### Review mode (after a fix pass)

After a fix pass, do all of the following in one run:

1. Re-measure **every** entry in the register, not only the ones the fix pass
   targeted. For each entry give the before and after numbers and its status:
   fixed / improved / unchanged / worse.
2. Repeat the **full sweep**. Anything new is a new entry (D*n+1*, ...) with
   source `regression`.
3. Give one verdict for the whole part.

A review that only re-runs the scripts for the defects that were fixed is not a
review.

**Sweep with the shared tool, against the stored baseline.** Run
`tools/form_sweep.py <mesh> --regions <project>/audit/regions.json --out
audit/rNN/sweep --tag rNN --baseline <the baseline sweep_<tag>.json named in
STATE.md>`. It prints the whole-part sweep and the NEW/WORSE components against
the baseline's stored fields, and writes `sweep_rNN.json`. Do not copy old
review scripts into your round, and do not re-run them on the previous mesh:
the baseline's fields are already on disk (`form_sweep.py` reproduced the r13
and r16 reviews' sweep logs line for line, 2026-10-04). On VitaGripPS5 r11 a
copied script still pointed at r10, and its first run overwrote two r10 logs.
Checks specific to one defect go in your own `audit/rNN/scripts/`. Write only
into your own round's folder and the scratchpad.
