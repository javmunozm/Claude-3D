# Workflow

*In force from 2026-10-04 (Phase 1 of `system_improvement/09_implementation_plan.md`).
Numbers come from the transcripts of 29 sessions and 60 agent runs, measured
2026-10-03. Parts marked "Phase 3" or "Phase 4" (`STATE.md`, the skills, the
sweep tool, review renders) are not built yet.*

## Roles

| Who | Owns | Does not |
|---|---|---|
| **User** | goals, approvals, visual judgment, physical tests | — |
| **Orchestrator** (the main session) | briefs, the round cycle, reading summaries, presenting decisions, bakes on approval, `STATE.md` / `NEXT_SESSION.md`, the cost line | read the whole README, macro or old reviews; geometry work beyond a small check; resume finished agents |
| **Agents** | one bounded task per brief; a deliverable written as they go; a handoff file before their ceiling | decide method, bake, commit, ask the user |

The user approves:
- a new build or round;
- a method change;
- a bake;
- deleting anything;
- commits;
- edits to `CLAUDE.md`, `docs/`, `.claude/`, skills, settings or memory.

The orchestrator has no definition file today. Its rules are spread over
`CLAUDE.md`, `docs/agents.md` and the memory. This document, the brief
templates (`docs/templates/`) and the `/round` skill (Phase 3; drafted in
`system_improvement/drafts/skills/round/`) are its definition.

## A session

1. **Start.** Begin a fresh session (or `/clear`). Read
   `projects/<Project>/STATE.md` (Phase 3; until it exists, the project's
   `NEXT_SESSION.md`) and nothing else whole. Say the plan in three
   lines, and ask if it starts a build or a round.
2. **During.**
   - One round at a time.
   - Agents run under numeric ceilings.
   - The orchestrator reads summary blocks, not whole reports.
   - Images only when a number cannot answer, as one region sheet per question
     (`tools/render_roi.py`).
3. **End.** Run `/session-end <Project>` (Phase 3; drafted in
   `system_improvement/drafts/skills/session-end/`). It updates `STATE.md` and
   `NEXT_SESSION.md`, records the cost, lists the uncommitted system files, and
   proposes memory edits for approval.
4. **A usage limit stops a run.** The deliverable and `handoff.md` on disk let
   a fresh agent continue. Do not resume the stopped agent: a resumed agent
   keeps its whole history, as the Claude Code docs state.

Why a fresh session per round: in r10–r13 the main thread rewrote its cache
after waiting 89–127 minutes for fix passes, which cost 29 % of the main
thread's spend. Rewrites after the user was away cost another 16 %. A small
context makes both cheap.

## A project, start to finish

1. **Intake.** The user's brief goes into the README section "The brief": goal,
   ground truth, what to keep, what to fix, and the constraints.
2. **References.** perspective-checker, then reference-analyst. Add
   vector-tracer and accuracy-reviewer when an outline matters (a pocket, a
   profile).
3. **Method gate (new).** Choose the representation before any geometry, and
   record the choice in the README (`system_improvement/06_cad_method.md`):
   - B-rep in build123d by default;
   - a mesh pipeline only when the part *is* a scan or a sculpt (BrokeFeet).
4. **Build.** cad-designer, from a brief with ceilings. Stage modules
   (`docs/architecture.md`) with a stage cache, so that a build stays under
   5 minutes.
5. **Verify.**
   - The hard gates (`/verify` a–b) and one region render.
   - A form-auditor register of the whole part.
   - Review renders for the user (`system_improvement/05_verification.md`).
6. **Fix rounds.** The bounded cycle below, until the user accepts.
7. **Bake.** A byte copy of a checked preview into `stl/`, with the user's
   approval. Then prune the macro (`system_improvement/04_project_state.md`).
8. **Print and measure.** Record the results in the README. A new round only if
   the print shows a problem, and only after asking.
9. **New generation.** Nested as `v2/` (`docs/versioning.md`).

## The fix-round cycle

```
user marks + sweep
   ▼
form-auditor  REGISTER  45 turns; marks classified; grouped by construction step
   ▼
user          approves entries and priorities; decides on METHOD REVIEW if triggered
   ▼
cad-designer  FIX PASS  60 turns per agent; handoff.md; a NEW agent continues if needed
   ▼
orchestrator  one rebuild + hard gates itself; one region render of the main change
   ▼
form-auditor  REVIEW    sweep tool + baseline.json; summary block; regression count
   ▼
orchestrator  STATE.md + cost line; summary block to the user
```

Rules:
- **One round** = one register, one approval, one fix pass (one or more fresh
  agents) and one review.
- **Ceilings are numbers in the brief**, and `maxTurns` in the agent
  frontmatter enforces them. The case for this: of 36 runs made after the budget
  rules existed, the 19 whose brief named a number had a median of 42 tool calls
  and cost $1.76 on average. The 17 without one had a median of 71 and cost
  $5.78.
- **Never resume a finished agent.** There were 6 such resumes in r10–r16.
- **The method-change trigger.** If a pass creates 3 or more regression IDs, or
  the same region appears in 3 consecutive registers, the next step is a method
  review for the user, not another fix pass. Six of the eight VitaGripPS5 passes
  from r9 to r16 met the first condition, and nothing stopped the cycle.
- **Sub-layer findings** (under 0.1 mm) that the user did not mark are
  reported, not registered.

## Giving feedback on renders

- **Draw on the review renders.** These are smooth-shaded and zebra views from
  the cameras listed in `STATE.md`. Save the `.xcf` and a flattened `.png` in
  `renders/case_preview_r<NN>/`.
- **Add one short note per image** ("bump here", "should be one surface", "cut
  on both sides"). In r9 the marks had no written note. The README records the
  readings as "the session's interpretation, matched by eye", and one of them as
  "not confirmed".
- **The orchestrator locates each mark** by ray-casting through the render's
  camera. That method works: the r13 cameras were validated at silhouette IoU
  0.997 and 0.990.
- **form-auditor classifies each mark** with the number that decides it. On
  r13, 6 of the 12 marked paths measured as sub-layer facet noise, which says
  the review renders themselves need fixing (`system_improvement/05_verification.md`).

## Commits

The repo tracks the system and each project's skeleton:
- `.claude/`, `tools/`, `docs/`, `CLAUDE.md`;
- each project's `README.md`, `macros/**/*.py`, and the proposed `STATE.md`.

It never tracks outputs (`docs/architecture.md`, "What the repo tracks"). Ask
before every commit.
