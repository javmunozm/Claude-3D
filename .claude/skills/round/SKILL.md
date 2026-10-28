---
name: round
description: Run one bounded fix round on a project. A round is a register, the user's approval, a fix pass and a review, each run in the main session with its skill (form-audit, cad-build), plan first, with numeric ceilings, a report file and a cost line. Usage: /round <Project> status|register|fix|review
user-invocable: true
---

# One fix round

Read `projects/<Project>/STATE.md` first. Do not read the README, old reviews
or the macro whole: Grep for the section you need. The cycle is in
`docs/workflow.md`. Every step below is **plan → run → report**: the step's
plan is written and shown before anything is measured, built or edited.

## status
Print these sections of STATE.md and stop:
- the open entries;
- the current preview and the current bake;
- the pending decisions;
- the last round's cost line.

## register
1. Run the **form-audit** skill in mode REGISTER. Its plan carries:
   - the user's marks, with their located coordinates;
   - the sweep command: `python tools/form_sweep.py <mesh> --regions
     projects/<Project>/audit/regions.json --out audit/r<NN>/sweep --tag r<NN>
     --baseline <the baseline in STATE.md>`;
   - ceilings: 0 builds, at most 4 images;
   - the deliverable, `audit/r<NN>/register.md`, summary block first.
2. Present to the user, from the summary block:
   - the entries, grouped by cause (and by construction step);
   - any conflicts;
   - how the marks were classified;
   - the method-change trigger line.
3. Ask the user to approve the entries and their priority.

## fix
This step needs the user's approval of the register.
1. Run the **cad-build** skill for a fix pass. Its plan
   (`audit/r<NN>/plan_build.md`) carries:
   - the approved entries, in priority order, one row per cause group, each
     with the check that proves it;
   - the locks;
   - ceilings: at most 4 builds (2 for a one-change pass), at most 6 images;
   - the fallback: stop at the last state that passes the hard gates.
2. Build into a preview folder, never `stl/`. Report the build's
   `rebuilt / from cache / written` line.
3. Run the hard gates (STATE.md, Commands) and look at one region render of
   the main change (`tools/render_roi.py`) before reporting.
4. If the session must end mid-pass, write `audit/r<NN>/handoff.md`; the next
   session continues from the plan plus the handoff.

## review
1. **Start a fresh session (`/clear`)** so the review judges the mesh, not the
   reasoning that built it.
2. Run the **form-audit** skill in mode REVIEW: the baseline sweep named in
   STATE.md, the new preview and the register; ceilings 1 build, at most
   3 images. Every entry is re-measured from the mesh; no number is copied
   from the fix report.
3. If the method-change trigger is met, say **METHOD REVIEW** and stop the
   cycle. The trigger: 3 or more new regression IDs (sorted from
   `form_sweep.py`'s NEW/WORSE components), or a region in its third
   consecutive register. See `docs/cad_method.md`.
4. Update STATE.md:
   - the open entries;
   - the preview path;
   - one line in Rounds, with the cost from the token audit (`/session-end`).
5. Present the summary block to the user.

## After a bake
With the user's approval of the bake: back up only the `stl/` files the bake
replaces, copy the checked preview in, sweep the baked mesh into
`audit/r<NN>/sweep/` with `tools/form_sweep.py` (no `--baseline`), and name
that `sweep_r<NN>.json` as the baseline in STATE.md.

## Rules
- Every ceiling is a number, written in the step's plan.
- One region render per question. Full views once per round, for the user.
- Ask before:
  - starting a new round;
  - baking into `stl/`;
  - deleting anything;
  - committing;
  - editing `CLAUDE.md`, `docs/`, `.claude/` or memory.
