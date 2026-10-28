# Workflow

*In force from 2026-10-04; agents replaced by skills on 2026-10-27
(`docs/agents.md`). Numbers come from the transcripts of 29 sessions and 60
agent runs, measured 2026-10-03 (`tools/token_audit/`).*

## Roles

| Who | Owns | Does not |
|---|---|---|
| **User** | goals, approvals, visual judgment, physical tests | — |
| **Main session** (one agent, loading skills) | the plan of every step, shown before it runs; the work itself, through the skills; the round cycle; bakes on approval; `STATE.md` / `NEXT_SESSION.md`; the cost line | read the whole README, macro or old reviews; run a step without a plan; decide a method change, bake or commit without the user |

The user approves:
- a new build or round;
- a method change;
- a bake;
- deleting anything;
- commits;
- edits to `CLAUDE.md`, `docs/`, `.claude/`, skills, settings or memory.

The main session's rules are `CLAUDE.md`, this document, `docs/agents.md`, the
skills in `.claude/skills/` (each with its plan template) and the memory.

## A session

1. **Start.** Begin a fresh session (or `/clear`). Read
   `projects/<Project>/STATE.md` (if a project has none yet, its
   `NEXT_SESSION.md`) and nothing else whole. Say the plan in three
   lines, and ask if it starts a build or a round.
2. **During.**
   - One round at a time.
   - Every step runs from a written plan with numeric ceilings.
   - Read summary blocks, not whole reports.
   - Images only when a number cannot answer, as one region sheet per question
     (`tools/render_roi.py`).
3. **End.** Run `/session-end <Project>`. It updates `STATE.md` and
   `NEXT_SESSION.md`, records the cost, lists the uncommitted system files, and
   proposes memory edits for approval.
4. **A usage limit stops a run.** The plan, the report written so far and
   `handoff.md` on disk let a fresh session continue from where it stopped.

Why a fresh session per round: in r10–r13 the main thread rewrote its cache
after waiting 89–127 minutes for fix passes, which cost 29 % of the main
thread's spend. Rewrites after the user was away cost another 16 %. A small
context makes both cheap.

## A project, start to finish

1. **Intake.** The user's brief goes into the README section "The brief": goal,
   ground truth, what to keep, what to fix, and the constraints.
2. **References.** `photo-to-vectors`: QUALIFY, then MEASURE; TRACE and REVIEW
   whenever an outline matters (a pocket, a profile, the part being designed).
3. **Method gate (new).** Choose the representation before any geometry, and
   record the choice in the README (`docs/cad_method.md`):
   - B-rep in build123d by default;
   - a mesh pipeline only when the part *is* a scan or a sculpt (BrokeFeet).
4. **Build.** `cad-build`, from its plan with ceilings. Stage modules
   (`docs/architecture.md`) with a stage cache (`tools/stage_cache.py`), so a
   change rebuilds only the parts it touches and a build stays under 5 minutes.
5. **Verify.**
   - The hard gates (`/verify` a–b) and one region render.
   - A `form-audit` REGISTER of the whole part.
   - Review renders for the user (`tools/render_views.py`, at the cameras in `STATE.md`).
6. **Fix rounds.** The bounded cycle below, until the user accepts.
7. **Bake.** A byte copy of a checked preview into `stl/`, with the user's
   approval. Then prune the macro (`docs/architecture.md`, "At a bake").
8. **Print and measure.** Record the results in the README. A new round only if
   the print shows a problem, and only after asking.
9. **New generation.** Nested as `v2/` (`docs/versioning.md`).

## The fix-round cycle

```
user marks + sweep
   ▼
form-audit  REGISTER  plan first; marks classified; grouped by construction step
   ▼
user        approves entries and priorities; decides on METHOD REVIEW if triggered
   ▼
cad-build   FIX PASS  plan first; ≤ 4 builds; preview folder, only changed parts rebuilt; handoff.md if cut short
   ▼
main        hard gates; one region render of the main change
   ▼
form-audit  REVIEW    fresh session; sweep tool + baseline.json; summary block; regression count
   ▼
main        STATE.md + cost line; summary block to the user
```

Rules:
- **One round** = one register, one approval, one fix pass and one review.
- **Ceilings are numbers in the plan.** The case for this, from the agent era:
  of 36 runs made after the budget rules existed, the 19 whose brief named a
  number had a median of 42 tool calls and cost $1.76 on average. The 17
  without one had a median of 71 and cost $5.78.
- **The review runs in a fresh session** and re-measures from the mesh; it
  copies no number from the fix report.
- **The method-change trigger.** If a pass creates 3 or more regression IDs, or
  the same region appears in 3 consecutive registers, the next step is a method
  review for the user, not another fix pass. Six of the eight VitaGripPS5 passes
  from r9 to r16 met the first condition, and nothing stopped the cycle.
- **Sub-layer findings** (under 0.1 mm) that the user did not mark are
  reported, not registered.

## Giving feedback on renders

- **Draw on the review renders.** These are the lit views from the cameras
  listed in `STATE.md`. Save the `.xcf` and a flattened `.png` in
  `renders/case_preview_r<NN>/`.
- **Add one short note per image** ("bump here", "should be one surface", "cut
  on both sides"). In r9 the marks had no written note. The README records the
  readings as "the session's interpretation, matched by eye", and one of them as
  "not confirmed".
- **The main session locates each mark** by ray-casting through the render's
  camera. That method works: the r13 cameras were validated at silhouette IoU
  0.997 and 0.990.
- **form-audit classifies each mark** with the number that decides it. On
  r13, 6 of the 12 marked paths measured as sub-layer facet noise. They are real
  facet edges of the scan mesh, so no render setting hides them (tested
  2026-10-04 with `tools/render_review.py`); the measurement decides.

## Commits

The repo tracks the system and each project's skeleton:
- `.claude/`, `tools/`, `docs/`, `CLAUDE.md`;
- each project's `README.md`, `macros/**/*.py`, and the proposed `STATE.md`.

It never tracks outputs (`docs/architecture.md`, "What the repo tracks"). Ask
before every commit.
