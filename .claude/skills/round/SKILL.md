---
name: round
description: Run one bounded fix round on a project. A round is a register, the user's approval, a fix pass and a review, with numeric ceilings, handoff files and a cost line. Usage: /round <Project> status|register|fix|review
user-invocable: true
---

# One fix round

Read `projects/<Project>/STATE.md` first. Do not read the README, old reviews
or the macro whole in the main thread: Grep for the section you need. Briefs
come from `docs/templates/`; the cycle is in `docs/workflow.md`.

## status
Print these sections of STATE.md and stop:
- the open entries;
- the current preview and the current bake;
- the pending decisions;
- the last round's cost line.

## register
1. Brief form-auditor with `docs/templates/brief_review.md`, mode REGISTER. The
   brief carries:
   - ceilings: 45 turns (its `maxTurns`; the budget hook reminds it at turn 36
     and from turn 42), 0 builds, at most 4 images;
   - the paths of the user's marks, with their located coordinates;
   - the sweep command: `python tools/form_sweep.py <mesh> --regions
     projects/<Project>/audit/regions.json --out audit/r<NN>/sweep --tag r<NN>
     --baseline <the baseline in STATE.md>`;
   - the deliverable, `audit/r<NN>/register.md`, summary block first.
2. When it returns, read only the summary block.
3. Present to the user:
   - the entries, grouped by cause;
   - any conflicts;
   - how the marks were classified;
   - the method-change trigger line.
4. Ask the user to approve the entries and their priority.

## fix
This step needs the user's approval of the register.
1. Brief cad-designer with `docs/templates/brief_fix_pass.md`:
   - the approved entries, in priority order;
   - the locks;
   - ceilings: 60 turns (25 for a one-change pass), at most 4 builds, at most
     6 images.
2. If it returns at a ceiling with work left, launch a **new** cad-designer
   with the same brief plus "continue from `audit/r<NN>/handoff.md`". Never
   `SendMessage` the finished agent: a resumed agent keeps its whole history.
3. Rebuild once yourself and run the hard gates (STATE.md, Commands). Look at
   one region render of the main change (`tools/render_roi.py`).

## review
1. Brief form-auditor in mode REVIEW, from `docs/templates/brief_review.md`:
   - the baseline sweep named in STATE.md, the new preview and the entries;
   - ceilings: 45 turns, 1 build, at most 3 images.
2. Read the summary block only.
3. If the method-change trigger is met, say **METHOD REVIEW** and stop the
   cycle. The trigger: 3 or more new regression IDs (the auditor sorts
   `form_sweep.py`'s NEW/WORSE components into IDs), or a region in its third
   consecutive register. See `system_improvement/06_cad_method.md`.
4. Update STATE.md:
   - the open entries;
   - the preview path;
   - one line in Rounds, with the cost from the token audit (`/session-end`).
5. Present the result to the user.

## After a bake
With the user's approval of the bake: sweep the baked mesh into
`audit/r<NN>/sweep/` with `tools/form_sweep.py` (no `--baseline`), and name
that `sweep_r<NN>.json` as the baseline in STATE.md.

## Rules
- Every ceiling is a number. A brief without numbers is not sent.
- One region render per question. Full views once per round, for the user.
- Ask before:
  - starting a new round;
  - baking into `stl/`;
  - deleting anything;
  - committing;
  - editing `CLAUDE.md`, `docs/`, `.claude/` or memory.
