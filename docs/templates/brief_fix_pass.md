<!-- Agent-era template, not used since 2026-10-27: a fix pass is now planned with
     .claude/skills/cad-build/plan_template.md. Kept for restoring the cad-designer agent. -->
# Brief: <Project> r<NN> fix pass (cad-designer)

<!-- Fill every <...>. A brief with an empty ceiling is not sent (docs/agents.md, "Briefing agents"). -->

## Ceilings
- Turns: hard stop <60> (agent `maxTurns`; lower it here if the task is small).
- The budget hook reminds you at turn <48> (80 % of `maxTurns`) and from turn <57> (`maxTurns` − 3). A lower turn ceiling set here is yours to watch.
- Builds: at most <4>. If a build takes over 5 minutes, report it and stop building.
- Images: at most <6>, region renders only (`tools/render_roi.py`).
- At about 80 % of any ceiling: write `audit/r<NN>/handoff.md` (template `docs/templates/handoff.md`) and return.

## Read (and nothing else whole)
- `projects/<Project>/STATE.md`: sections Open entries, Locks, Gates, Commands.
- `audit/r<NN>/register.md`: the summary block, plus the rows of the approved IDs (find them with Grep).
- The stage modules that own those entries: <list paths>.

## Do, in this order
1. <ID(s)>: <cause group>. <Approved fix, with its size>.
2. <ID(s)>: ...

If the budget runs short, stop at the last state that passes the hard gates, with items 1–<k> done.

## Do not touch
- Locks: <list, with tolerances>.
- Other rounds' folders, and `stl/` (a bake is the orchestrator's job, with the user's approval).

## Deliver (write as you go, not at the end)
- `audit/r<NN>/fix_report.md`:
  - first, one plain sentence per changed region ("the corner is one surface; its end is a 14 mm wall");
  - then one row per entry: ID | change | before → after | status (fixed / partial / not attempted, and why).
- `audit/r<NN>/case_preview_r<NN>.stl` and its build log.
- `audit/r<NN>/handoff.md`, if you stop early.

## Report back (at most 25 lines)
- The plain sentences per region.
- The entry table.
- The hard-gate results.
- What is not done, and why.
- Tool calls used (harness count).
