---
name: session-end
description: Close a work session on a project. Updates STATE.md and NEXT_SESSION.md, records the session's cost, lists uncommitted files and unpushed commits, and proposes memory updates for approval. Usage: /session-end <Project>
user-invocable: true
---

# Session end

1. **Update `projects/<Project>/STATE.md`** (template `docs/templates/STATE.md`):
   - the current bake and preview, and the baseline sweep;
   - the open entries;
   - the locks and gates, if they changed;
   - the pending decisions;
   - one line per round run this session.
2. **Rewrite `NEXT_SESSION.md`** as a human summary of at most 60 lines. It
   points to STATE.md for detail, and ends with the first decision the user has
   to make next time.
3. **Cost.** Run the token audit for this session:
   - `"D:/Proyectos/Claude-3D/.venv/Scripts/python.exe" "D:/Proyectos/Claude-3D/tools/token_audit/token_audit.py" sessions <session-id prefix>`
   - `"D:/Proyectos/Claude-3D/.venv/Scripts/python.exe" "D:/Proyectos/Claude-3D/tools/token_audit/cost.py" <session-id prefix>`

   If `cost.py` prints `UNPRICED`, the model has no row in its `PRICES` table:
   report the cost as unknown, never as $0.00.

   Copy the list-price total and the main session's peak context (`peakctx`)
   into STATE.md's Rounds table.
4. **Uncommitted and unpushed.** Run `git -C "D:/Proyectos/Claude-3D" status --short --branch`
   and report both:
   - the uncommitted files in the tracked set (`.claude/`, `tools/`, `docs/`,
     `CLAUDE.md`, `requirements.txt`, and per project the allowlist in
     `.gitignore`: README, STATE, NEXT_SESSION, `macros/**/*.py`, `vectors/`,
     `docs/`, the audit records);
   - the commits not on `origin` (the `[ahead N]` on the first line).

   Do not commit without asking. When the user approves, commit **and push**
   in the same step, and report the push result. A session never ends with
   `[ahead N]` unreported: on 2026-11-11 two weeks of local-only commits were
   lost with the disk.
5. **Memory.** List the memory entries that this session made stale, such as a
   project status line, and propose the exact new text. Write it only after the
   user approves (CORE DIRECTIVE 2).
6. **Report in at most 10 lines:**
   - what changed;
   - what is pending;
   - the cost of the session;
   - the decision needed next time.
