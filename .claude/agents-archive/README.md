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

**The hooks are inactive.** `.claude/hooks/budget_nudge.py`, `shell_guard.py` and `budgets.json` only act on subagent
calls, and no `settings.json` (user or project) registers them (checked 2026-11-11). Restoring an agent with its turn
budget also means adding them back under `hooks` in `.claude/settings.json`.
