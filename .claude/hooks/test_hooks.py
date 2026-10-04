"""Offline tests for the hooks in this folder. Commands marked REAL were taken from
this repo's session transcripts (2026-09-22 .. 2026-10-03).

Run: python -B "D:/CAD/Claude-Projects/.claude/hooks/test_hooks.py"
It also runs both hooks as subprocesses with JSON on stdin, the way Claude Code calls them.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import budget_nudge  # noqa: E402
import shell_guard  # noqa: E402

CASES = [
    # (tool, command, expected rules)  -- REAL = from transcripts
    ("Bash", "cd /d/Temp/claude/D--CAD-Claude-Projects/8b688bc4/scratchpad/sdg/; python -c \"import sys,numpy as np,cv2; sys.path.insert(0,'ref')\"",
     {"cd", "chained commands", "python -c / stdin code"}),                                   # REAL (user pasted it)
    ("Bash", "sed -i \"s/^PT_PASSES = 2 /PT_PASSES = 0 /\" \"D:/CAD/Claude-Projects/projects/VitaGripPS5/macros/build_case_ext.py\" && timeout 600 python \"D:/CAD/Claude-Projects/projects/VitaGripPS5/macros/build_case_ext.py\" --out \"D:/Temp/x.stl\"",
     {"chained commands"}),                                                                   # REAL r10 designer
    ("Bash", "until grep -q \"^done\" \"D:/CAD/Claude-Projects/projects/VitaGripPS5/audit/r15/build_v5.log\"; do sleep 5; done; grep -n \"D19\" \"D:/x.log\"",
     {"chained commands"}),                                                                   # REAL r15 designer
    ("Bash", "python -c \"import mapbox_earcut; print('earcut ok')\"", {"python -c / stdin code"}),  # REAL r14 designer (13.2 min)
    ("Bash", "python - <<'EOF'\nimport re\np = 'D:/x.py'\nEOF", {"heredoc code", "python -c / stdin code"}),  # REAL shape, r14
    ("Bash", "F=\"D:/CAD/x.py\"; S=\"D:/Temp/y\"", {"chained commands"}),                       # REAL r10 designer
    ("Bash", "cat \"D:/CAD/Claude-Projects/CLAUDE.md\"", {"viewing files in the shell"}),
    ("Bash", "ls -la D:/CAD/Claude-Projects/projects", {"viewing files in the shell"}),
    ("PowerShell", "Get-Content \"D:\\x.txt\" -TotalCount 6", {"viewing files in the shell"}),
    ("PowerShell", "timeout 300 python \"D:\\Temp\\probe.py\"", {"timeout in PowerShell (use the tool's timeout parameter, or the Bash tool)"}),  # REAL, this session
    ("Bash", "py -c \"print(1)\"", {"python -c / stdin code"}),
    # allowed
    ("Bash", "timeout 900 python -u \"D:/CAD/Claude-Projects/projects/VitaGripPS5/macros/build_case_ext.py\" --out \"D:/CAD/Claude-Projects/projects/VitaGripPS5/audit/r10/case_preview_r10.stl\"", set()),  # REAL
    ("PowerShell", "python \"D:\\Temp\\claude\\x\\scratchpad\\token_audit.py\" agents 537be8a2 8be432e3", set()),  # REAL, this session
    ("PowerShell", "git -C \"D:\\CAD\\Claude-Projects\" log --reverse --format=\"%h %ad %s\" --date=iso -S\"## Shell commands\" -- .claude/agents/cad-designer.md", set()),  # REAL
    ("PowerShell", "Get-ChildItem -Path \"D:\\CAD\\Claude-Projects\" -Force | Select-Object Mode, LastWriteTime, Length, Name | Format-Table -AutoSize", set()),  # REAL
    ("PowerShell", "$env:PYTHONPATH = 'D:\\CAD\\Claude-Projects'; python \"D:\\x.py\"", set()),  # allowed by settings.local.json
    ("Bash", "echo \"a; b && c\"", set()),
    ("PowerShell", "git commit -m @'\nFirst line; still the message\nsecond line\n'@", set()),
    ("Bash", "python -X faulthandler \"D:/CAD/Claude-Projects/projects/VitaGripPS5/audit/r10/scripts/ft10.py\" \"D:/x.stl\"", set()),  # REAL shape
    ("Bash", "taskkill //PID 35708 //F", set()),                                              # REAL
]


def test_shell_guard():
    bad = 0
    for tool, cmd, expected in CASES:
        got = set(shell_guard.decide(cmd, tool))
        ok = got == expected
        bad += not ok
        print(f"  {'ok  ' if ok else 'FAIL'} {tool:10} {cmd[:70]!r:74} -> {sorted(got)}" + ("" if ok else f"  expected {sorted(expected)}"))
    return bad


def test_budget_nudge():
    """The tool-call fallback: no agent definition, so no maxTurns."""
    bad = 0
    budgets = {"cad-designer": {"warn": 3, "stop": 5}, "default": {"warn": 2, "stop": 4}}
    with tempfile.TemporaryDirectory() as d:
        no_agents = Path(d) / "no_agents"
        msgs = {}
        for i in range(1, 12):
            m = budget_nudge.process({"agent_id": "a1", "agent_type": "cad-designer"}, budgets, d, no_agents)
            if m:
                msgs[i] = m.split(":")[0]
        expected = {3: "Budget", 5: "Budget reached", 10: "Budget reached"}
        ok = msgs == expected
        bad += not ok
        print(f"  {'ok  ' if ok else 'FAIL'} fallback, cad-designer warn 3 / stop 5 over 11 calls -> reminders at {sorted(msgs)}" + ("" if ok else f" expected {sorted(expected)}"))
        m = budget_nudge.process({"agent_type": "cad-designer"}, budgets, d, no_agents)  # main thread: no agent_id
        ok = m is None
        bad += not ok
        print(f"  {'ok  ' if ok else 'FAIL'} main-thread call ignored")
        m1 = [budget_nudge.process({"agent_id": "b2", "agent_type": "unknown-agent"}, budgets, d, no_agents) for _ in range(2)]
        ok = m1[0] is None and m1[1] is not None
        bad += not ok
        print(f"  {'ok  ' if ok else 'FAIL'} unknown agent type falls back to 'default' (warn at 2)")
    return bad


def append(path, rec):
    with open(path, "ab") as f:
        f.write((json.dumps(rec) + "\n").encode("utf-8"))


def tool_turn(path, turn, calls):
    """One model response with `calls` parallel tool calls, logged the way Claude Code logs it:
    one assistant record per tool_use (same message id), each followed by its tool result."""
    for k in range(calls):
        append(path, {"type": "assistant", "message": {"id": f"msg_{turn}", "model": "m", "content": [
            {"type": "tool_use", "id": f"tu_{turn}_{k}", "name": "Read", "input": {}}]}})
        append(path, {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": f"tu_{turn}_{k}"}]}})
        yield


def test_turn_counting():
    """maxTurns counts model responses, so the hook counts them too: parallel calls share a turn."""
    bad = 0
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        agents = d / "agents"
        agents.mkdir()
        (agents / "probe.md").write_bytes(b"---\r\nname: probe\r\nmaxTurns: 10\r\neffort: low\r\n---\r\nbody\r\n")
        ok = budget_nudge.max_turns("probe", agents) == 10 and budget_nudge.max_turns("missing", agents) is None
        bad += not ok
        print(f"  {'ok  ' if ok else 'FAIL'} maxTurns read from CRLF frontmatter; a missing definition gives None")

        # 10 turns of 2 parallel calls; maxTurns 10 -> warning at turn 8, stop at turns 9 and 10, once per turn
        sub = d / "proj" / "sess" / "subagents"
        sub.mkdir(parents=True)
        payload = {"agent_id": "t1", "agent_type": "probe", "transcript_path": str(d / "proj" / "sess.jsonl")}
        got = {}
        for turn in range(1, 11):
            for _ in tool_turn(sub / "agent-t1.jsonl", turn, 2):
                m = budget_nudge.process(payload, {}, d / "state", agents)
                if m:
                    got.setdefault(turn, []).append(m.split(":")[0])
        expected = {8: ["Budget"], 9: ["Budget reached"], 10: ["Budget reached"]}
        st = json.loads((d / "state" / "budget_state" / "t1.json").read_text(encoding="utf-8"))
        ok = got == expected and st["turns"] == 10 and st["n"] == 20 and st["mode"] == "turns"
        bad += not ok
        print(f"  {'ok  ' if ok else 'FAIL'} 10 turns x 2 parallel calls, maxTurns 10 -> reminders {got}; "
              f"state turns {st['turns']}, calls {st['n']}, mode {st['mode']}" + ("" if ok else f"  expected {expected}"))

        # an unfinished last line is not counted until it is complete
        tr = d / "agent-t2.jsonl"
        a = json.dumps({"type": "assistant", "message": {"id": "msg_a", "content": []}}) + "\n"
        b = json.dumps({"type": "assistant", "message": {"id": "msg_b", "content": []}}) + "\n"
        tr.write_bytes((a + b[:25]).encode("utf-8"))
        st = {}
        first = budget_nudge.count_turns(tr, st)
        tr.write_bytes((a + b).encode("utf-8"))
        second = budget_nudge.count_turns(tr, st)
        ok = (first, second) == (1, 2)
        bad += not ok
        print(f"  {'ok  ' if ok else 'FAIL'} unfinished last line: counted {first}, then {second} once complete")

        # the transcript is found from transcript_path, from scratchpad_dir, or from session_id
        projects = d / "projects"
        for sess, aid in (("s3", "t3"), ("s4", "t4")):
            (projects / "proj" / sess / "subagents").mkdir(parents=True)
            (projects / "proj" / sess / "subagents" / f"agent-{aid}.jsonl").write_bytes(a.encode("utf-8"))
        via_scratch = budget_nudge.find_transcript(
            {"agent_id": "t3", "scratchpad_dir": str(d / "tmp" / "claude" / "proj" / "s3" / "scratchpad")}, projects)
        via_session = budget_nudge.find_transcript({"agent_id": "t4", "session_id": "s4"}, projects)
        missing = budget_nudge.find_transcript({"agent_id": "t9", "session_id": "s4"}, projects)
        ok = (via_scratch is not None and via_scratch.parent.parent.name == "s3"
              and via_session is not None and via_session.parent.parent.name == "s4" and missing is None)
        bad += not ok
        print(f"  {'ok  ' if ok else 'FAIL'} transcript found from scratchpad_dir and from session_id; none for an unknown agent")
    return bad


def test_subprocess():
    """Run the hooks exactly as Claude Code would: JSON on stdin, JSON (or nothing) on stdout."""
    bad = 0
    payload = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "agent_id": "x", "agent_type": "cad-designer",
               "tool_input": {"command": "cd D:/x && python -c \"print(1)\""}}
    r = subprocess.run([sys.executable, str(HERE / "shell_guard.py")], input=json.dumps(payload), capture_output=True, text=True, timeout=60)
    try:
        out = json.loads(r.stdout)
        ok = out["hookSpecificOutput"]["permissionDecision"] == "deny"
    except Exception:
        ok = False
    bad += not ok
    print(f"  {'ok  ' if ok else 'FAIL'} shell_guard subprocess deny JSON: {r.stdout.strip()[:110]}")
    payload["tool_input"]["command"] = "python \"D:/x.py\""
    r = subprocess.run([sys.executable, str(HERE / "shell_guard.py")], input=json.dumps(payload), capture_output=True, text=True, timeout=60)
    ok = r.stdout.strip() == "" and r.returncode == 0
    bad += not ok
    print(f"  {'ok  ' if ok else 'FAIL'} shell_guard subprocess allow: no output, exit {r.returncode}")
    warn = budget_nudge.load_budgets()["perspective-checker"]["warn"]
    with tempfile.TemporaryDirectory() as d:
        p = {"hook_event_name": "PostToolUse", "tool_name": "Read", "agent_id": "sub1", "agent_type": "perspective-checker", "scratchpad_dir": d}
        outs = [subprocess.run([sys.executable, str(HERE / "budget_nudge.py")], input=json.dumps(p), capture_output=True, text=True, timeout=60).stdout.strip()
                for _ in range(warn)]
        ok = outs[warn - 1] != "" and all(o == "" for o in outs[:warn - 1]) and json.loads(outs[warn - 1])["hookSpecificOutput"]["hookEventName"] == "PostToolUse"
        bad += not ok
        print(f"  {'ok  ' if ok else 'FAIL'} budget_nudge subprocess, no transcript: first reminder at call {next((i + 1 for i, o in enumerate(outs) if o), None)} (fallback, budgets.json warn {warn})")
    # turn mode, with the real perspective-checker definition and UTF-8 input that the ANSI code page cannot decode
    limit = budget_nudge.max_turns("perspective-checker")
    if limit is None:
        print("  skip budget_nudge subprocess, turns: perspective-checker has no maxTurns")
        return bad
    warn_turn = int(0.8 * limit)
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        sub = d / "proj" / "sess" / "subagents"
        sub.mkdir(parents=True)
        for turn in range(1, warn_turn + 1):
            for _ in tool_turn(sub / "agent-sub2.jsonl", turn, 1):
                pass
        p = {"hook_event_name": "PostToolUse", "tool_name": "Read", "agent_id": "sub2", "agent_type": "perspective-checker",
             "transcript_path": str(d / "proj" / "sess.jsonl"), "scratchpad_dir": str(d),
             "tool_response": "Ángulo — cara de 37,5 Ð"}
        r = subprocess.run([sys.executable, str(HERE / "budget_nudge.py")], input=json.dumps(p, ensure_ascii=False).encode("utf-8"),
                           capture_output=True, timeout=60)
        out = r.stdout.decode("utf-8").strip()
        try:
            text = json.loads(out)["hookSpecificOutput"]["additionalContext"]
            ok = f"turn {warn_turn} of your {limit}-turn limit" in text
        except Exception:
            ok, text = False, out or r.stderr.decode("utf-8", "replace")[-200:]
        bad += not ok
        print(f"  {'ok  ' if ok else 'FAIL'} budget_nudge subprocess, {warn_turn} turns in the transcript, UTF-8 input: {text[:80]!r}")
    return bad


if __name__ == "__main__":
    print("shell_guard.decide:")
    fails = test_shell_guard()
    print("budget_nudge.process:")
    fails += test_budget_nudge()
    print("budget_nudge turn counting:")
    fails += test_turn_counting()
    print("as subprocesses:")
    fails += test_subprocess()
    print("ALL PASS" if fails == 0 else f"{fails} FAILED")
    sys.exit(1 if fails else 0)
