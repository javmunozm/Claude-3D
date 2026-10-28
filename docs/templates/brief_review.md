<!-- Agent-era template, not used since 2026-10-27: an audit is now planned with
     .claude/skills/form-audit/plan_template.md. Kept for restoring the form-auditor agent. -->
# Brief: <Project> r<NN> <REGISTER | REVIEW> (form-auditor)

## Ceilings
- Turns: hard stop <45> (agent `maxTurns`).
- The budget hook reminds you at turn <36> (80 % of `maxTurns`) and from turn <42> (`maxTurns` − 3).
- Builds: <0 for a register | 1 for a review>.
- Images: at most <4>.
- Write the summary block (`docs/templates/review_summary.md`) first, and keep it current as you go.

## Read
- `projects/<Project>/STATE.md`.
- User marks: `renders/case_preview_r<NN>/<files>`. Their located coordinates: <file>.
- REVIEW only: the baseline, `audit/r<MM>/baseline.json`, and the fix report's summary sentences.

## Run
- The whole-part sweep:

  ```
  python tools/form_sweep.py <mesh> --regions projects/<Project>/audit/regions.json --out audit/r<NN>/sweep.json [--baseline audit/r<MM>/baseline.json]
  ```

  (Until `form_sweep.py` exists: copy the previous round's sweep script into `audit/r<NN>/scripts/`, retarget its paths, and check that it reproduces the previous numbers.)
- Then measure each user mark and each entry: one script, edited. It prints at most about 50 lines.

## Rules for the register
- **Classify every user mark** with the number that decides it:
  - geometry defect;
  - designed edge not yet rounded;
  - tessellation / shading;
  - not reproducible.
- **Group entries by the construction step that made them.** Three or more entries on one step's outline make one entry: "replace the step".
- **Report sub-layer findings (under 0.1 mm) without registering them,** unless the user marked them.
- **State the method-change trigger** in the summary: three or more regressions from the last pass, or one region in its third consecutive register.

## Deliver
- `audit/r<NN>/<register|review>.md`, with the summary block first.
- `audit/r<NN>/sweep.json`.
- REVIEW only: `audit/r<NN>/baseline.json`, if this mesh is the one the user will judge.

## Report back
The summary block, at most 30 lines.
