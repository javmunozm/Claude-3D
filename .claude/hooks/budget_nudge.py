"""PostToolUse hook: remind each subagent of its turn budget through
`additionalContext` (inserted next to the tool result as a system reminder).

The hard stop is the agent's `maxTurns` frontmatter field. It counts turns
(model responses), not tool calls: measured 2026-10-04, a probe with
`maxTurns: 3` made 4 parallel calls in one response and finished normally.
So this hook counts turns too, from the agent's own transcript:
- at 80 % of maxTurns: write the deliverable and handoff.md now;
- from maxTurns - 3, once per turn: write handoff.md and return now.

Fallback, when the agent has no maxTurns or its transcript cannot be found:
count tool calls against budgets.json (the warning, then the stop and every
5 calls after). Main-thread calls (no `agent_id` in the input) are ignored.

State: one small JSON per agent_id under <scratchpad_dir or %TEMP%>/budget_state/.
Test: test_hooks.py, next to this file. Source and history:
system_improvement/07_enforcement.md.
"""
import json
import re
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
AGENTS = HERE.parent / "agents"
PROJECTS = Path.home() / ".claude" / "projects"
DEFAULT = {"warn": 48, "stop": 60}


def load_budgets(path=HERE / "budgets.json"):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return {"default": DEFAULT}


def max_turns(agent_type, agents_dir=AGENTS):
    """The agent's maxTurns frontmatter field, or None."""
    try:
        text = (Path(agents_dir) / f"{agent_type}.md").read_text(encoding="utf-8")
    except (OSError, ValueError):
        return None
    head = re.match(r"---\s*\n(.*?)\n---", text, re.S)
    found = head and re.search(r"^maxTurns:\s*(\d+)\s*$", head.group(1), re.M)
    return int(found.group(1)) if found else None


def find_transcript(data, projects=PROJECTS):
    """The subagent's own transcript, <project>/<session>/subagents/agent-<agent_id>.jsonl, or None."""
    name = f"agent-{data['agent_id']}.jsonl"
    cands = []
    if data.get("transcript_path"):
        p = Path(data["transcript_path"])
        cands += [p, p.with_suffix("") / "subagents" / name, p.parent / "subagents" / name]
    if data.get("scratchpad_dir"):  # <temp>/claude/<project>/<session>/scratchpad
        s = Path(data["scratchpad_dir"]).parent
        cands.append(Path(projects) / s.parent.name / s.name / "subagents" / name)
    if data.get("session_id"):
        cands += sorted(Path(projects).glob(f"*/{data['session_id']}/subagents/{name}"))
    return next((c for c in cands if c.name == name and c.is_file()), None)


def count_turns(path, st):
    """Distinct assistant messages in the transcript, read from st['offset'] on (complete lines only)."""
    offset = st.get("offset", 0)
    with open(path, "rb") as f:
        f.seek(offset)
        chunk = f.read()
    end = chunk.rfind(b"\n") + 1
    recent, turns = st.get("recent", []), st.get("turns", 0)
    for raw in chunk[:end].splitlines():
        if b'"assistant"' not in raw:
            continue
        try:
            rec = json.loads(raw)
        except ValueError:
            continue
        if not isinstance(rec, dict):
            continue
        msg = rec.get("message") or {}
        if rec.get("type") != "assistant" or msg.get("model") == "<synthetic>":
            continue
        mid = msg.get("id") or rec.get("requestId") or rec.get("uuid")
        if mid not in recent:
            recent.append(mid)
            turns += 1
    st.update(offset=offset + end, turns=turns, recent=recent[-20:])
    return turns


def process(data, budgets, state_root=None, agents_dir=AGENTS, projects=PROJECTS):
    """Return the reminder text for this tool call, or None."""
    agent_id = data.get("agent_id")
    if not agent_id:
        return None
    agent_type = data.get("agent_type") or ""
    root = Path(state_root or data.get("scratchpad_dir") or tempfile.gettempdir()) / "budget_state"
    root.mkdir(parents=True, exist_ok=True)
    f = root / f"{agent_id}.json"
    try:
        st = json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        st = {}
    st.update(n=st.get("n", 0) + 1, agent_type=agent_type, t=time.time())
    limit = max_turns(agent_type, agents_dir)
    turns = None
    if limit:
        path = Path(st["transcript"]) if st.get("transcript") else find_transcript(data, projects)
        if path:
            try:
                turns = count_turns(path, st)
                st["transcript"] = str(path)
            except OSError:
                st.pop("transcript", None)
    msg = None
    if turns is not None:
        st["mode"] = "turns"
        warn, stop = int(0.8 * limit), max(limit - 3, int(0.8 * limit) + 1)
        if turns >= stop and st.get("stop_sent") != turns:
            st["stop_sent"] = turns
            msg = (f"Budget reached: turn {turns} of your {limit}-turn limit. Write handoff.md and return your "
                   f"report now. Do not start new work; a fresh agent will continue from the handoff.")
        elif warn <= turns < stop and not st.get("warn_sent"):
            st["warn_sent"] = turns
            msg = (f"Budget: this is turn {turns} of your {limit}-turn limit. Write your deliverable file and "
                   f"handoff.md now (done / not done / current files / next step), then finish only the current item.")
    else:
        st["mode"] = "calls"
        b = budgets.get(agent_type, budgets.get("default", DEFAULT))
        n, warn, stop = st["n"], int(b["warn"]), int(b["stop"])
        if n == warn:
            msg = (f"Budget: this is tool call {n} of a {stop}-call ceiling. Write your deliverable file and "
                   f"handoff.md now (done / not done / current files / next step), then finish only the current item.")
        elif n >= stop and (n - stop) % 5 == 0:
            msg = (f"Budget reached: tool call {n}, ceiling {stop}. Write handoff.md and return your report now. "
                   f"Do not start new work; a fresh agent will continue from the handoff.")
    f.write_text(json.dumps(st), encoding="utf-8")
    return msg


def main():
    try:
        # read bytes and decode as UTF-8: the Windows default for a piped stdin is the ANSI code page
        data = json.loads(sys.stdin.buffer.read().decode("utf-8", errors="replace"))
    except Exception:
        return 0
    msg = process(data, load_budgets())
    if msg:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": msg}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
