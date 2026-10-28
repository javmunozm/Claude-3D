---
name: session-end
description: Close a work session on a project. Updates STATE.md and NEXT_SESSION.md, records the session's cost, lists uncommitted system files, and proposes memory updates for approval. Usage: /session-end <Project>
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
   - `python "D:/CAD/Claude-Projects/tools/token_audit/token_audit.py" agents <session-id prefix>`
   - `python "D:/CAD/Claude-Projects/tools/token_audit/cost.py" <session-id prefix>`

   Copy the list-price total and the peak context (main session, and any
   subagent still used) into STATE.md's Rounds table.
4. **Uncommitted files.** Run `git -C "D:/CAD/Claude-Projects" status --short`
   and list the uncommitted files in the tracked set:
   - `.claude/`, `tools/`, `docs/`, `CLAUDE.md`;
   - each project's `README.md`, `STATE.md` and `macros/**/*.py`.

   Do not commit. Ask the user.
5. **Memory.** List the memory entries that this session made stale, such as a
   project status line, and propose the exact new text. Write it only after the
   user approves (CORE DIRECTIVE 2).
6. **Report in at most 10 lines:**
   - what changed;
   - what is pending;
   - the cost of the session;
   - the decision needed next time.
