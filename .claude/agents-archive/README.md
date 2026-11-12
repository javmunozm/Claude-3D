# Archived subagents (2026-10-27)

These nine subagent definitions were replaced by skills, following Anthropic's "when to fold subagents into your main
agent loop" guidance and the user's decision of 2026-10-27. Claude Code does not load this folder.

| Agent | Now |
|-------|-----|
| cad-designer | `.claude/skills/cad-build/` |
| form-auditor | `.claude/skills/form-audit/` |
| perspective-checker, reference-analyst, vector-tracer, accuracy-reviewer | `.claude/skills/photo-to-vectors/` (stages QUALIFY, MEASURE, TRACE, REVIEW) |
| print-tolerance-expert | `.claude/skills/fdm-tolerance/` |
| bone-morphologist, blender-handoff | `.claude/skills/scan-mesh/` (modes REPAIR, BLENDER) |

Each skill's `reference/` files hold these agents' method sections verbatim (minus the subagent budget mechanics);
the coverage check of 2026-10-27 found every number, path and rule present except the turn-limit mechanics.

**To restore an agent** (for example if `.claude/evals/skills_eval.md` shows a skill doing worse than the agent it
replaced): move its file back to `.claude/agents/`. The budget hook and `budgets.json` still know every agent by name.

**The budget hook is archived here** (`hooks/budget_nudge.py`, `hooks/budgets.json`, moved 2026-11-11). It acts only
on subagent calls: it returns nothing for the main thread, where the work has run since 2026-10-27. Restoring an
agent with its turn budget means moving both files back to `.claude/hooks/`, registering `budget_nudge.py` as a
`PostToolUse` hook in `.claude/settings.json`, and restoring its tests from git (`git show 197a6a3:.claude/hooks/test_hooks.py`).

`shell_guard.py` is **not** archived: it stays in `.claude/hooks/`, registered in `.claude/settings.json`, and applies
to the main thread.
