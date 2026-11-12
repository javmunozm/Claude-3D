"""Offline tests for the hook in this folder. Commands marked REAL were taken from
this repo's session transcripts (2026-09-22 .. 2026-10-03), with `python` rewritten
to the repo venv where the command is meant to pass (rule added 2026-11-11).

Run: "D:/Proyectos/Claude-3D/.venv/Scripts/python.exe" -B "D:/Proyectos/Claude-3D/.claude/hooks/test_hooks.py"
It also runs the hook as a subprocess with JSON on stdin, the way Claude Code calls it.

The subagent budget hook (budget_nudge.py, budgets.json) and its tests were archived
on 2026-11-11 in .claude/agents-archive/hooks/: it ignored the main thread, and the
work has run in the main thread since 2026-10-27.
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import shell_guard  # noqa: E402

PY = '"D:/Proyectos/Claude-3D/.venv/Scripts/python.exe"'
PYW = "D:\\Proyectos\\Claude-3D\\.venv\\Scripts\\python.exe"
BARE = "bare python (use the repo venv)"
PYC = "python -c / stdin code"

CASES = [
    # (tool, command, expected rules)  -- REAL = from transcripts
    ("Bash", "cd /d/Temp/claude/D--Proyectos-Claude-3D/8b688bc4/scratchpad/sdg/; python -c \"import sys,numpy as np,cv2; sys.path.insert(0,'ref')\"",
     {"cd", "chained commands", PYC, BARE}),                                                  # REAL (user pasted it)
    ("Bash", "sed -i \"s/^PT_PASSES = 2 /PT_PASSES = 0 /\" \"D:/Proyectos/Claude-3D/projects/VitaGripPS5/macros/build_case_ext.py\" && timeout 600 python \"D:/Proyectos/Claude-3D/projects/VitaGripPS5/macros/build_case_ext.py\" --out \"D:/Temp/x.stl\"",
     {"chained commands", BARE}),                                                             # REAL r10 designer
    ("Bash", "until grep -q \"^done\" \"D:/Proyectos/Claude-3D/projects/VitaGripPS5/audit/r15/build_v5.log\"; do sleep 5; done; grep -n \"D19\" \"D:/x.log\"",
     {"chained commands"}),                                                                   # REAL r15 designer
    ("Bash", "python -c \"import mapbox_earcut; print('earcut ok')\"", {PYC, BARE}),         # REAL r14 designer (13.2 min)
    ("Bash", "python - <<'EOF'\nimport re\np = 'D:/x.py'\nEOF", {"heredoc code", PYC, BARE}),  # REAL shape, r14
    ("Bash", "F=\"D:/CAD/x.py\"; S=\"D:/Temp/y\"", {"chained commands"}),                       # REAL r10 designer
    ("Bash", "cat \"D:/Proyectos/Claude-3D/CLAUDE.md\"", {"viewing files in the shell"}),
    ("Bash", "ls -la D:/Proyectos/Claude-3D/projects", {"viewing files in the shell"}),
    ("PowerShell", "Get-Content \"D:\\x.txt\" -TotalCount 6", {"viewing files in the shell"}),
    ("PowerShell", "timeout 300 python \"D:\\Temp\\probe.py\"",
     {"timeout in PowerShell (use the tool's timeout parameter, or the Bash tool)", BARE}),   # REAL
    ("Bash", "py -c \"print(1)\"", {PYC, BARE}),
    # the venv rule (2026-11-11: `python` on PATH is 3.14 without numpy)
    ("Bash", "python \"D:/Proyectos/Claude-3D/tools/render_check.py\" \"D:/x.stl\" --views front", {BARE}),
    ("Bash", "timeout 300 python -u \"D:/x.py\"", {BARE}),
    ("PowerShell", "python tools\\render_check.py projects\\X\\stl\\X.stl --views front", {BARE}),
    ("Bash", PY + " -c \"print(1)\"", {PYC}),                                                 # venv does not excuse -c
    ("Bash", "py -3.13 -m venv \"D:/Proyectos/Claude-3D/.venv\"", set()),                      # rebuilding the venv
    ("Bash", "git -C \"D:/Proyectos/Claude-3D\" commit -m \"python path fix\"", set()),        # the word inside quotes
    ("Bash", "git -C \"D:/Proyectos/Claude-3D\" log --oneline -- tools/python_helpers.py", set()),
    # allowed
    ("Bash", "timeout 900 " + PY + " -u \"D:/Proyectos/Claude-3D/projects/VitaGripPS5/macros/build_case_ext.py\" --out \"D:/Proyectos/Claude-3D/projects/VitaGripPS5/audit/r10/case_preview_r10.stl\"", set()),  # REAL
    ("PowerShell", PYW + " \"D:\\Temp\\claude\\x\\scratchpad\\token_audit.py\" agents 537be8a2 8be432e3", set()),  # REAL
    ("PowerShell", "& \"" + PYW + "\" \"D:\\x.py\"", set()),
    ("PowerShell", "git -C \"D:\\Proyectos\\Claude-3D\" log --reverse --format=\"%h %ad %s\" --date=iso -S\"## Shell commands\" -- .claude/agents/cad-designer.md", set()),  # REAL
    ("PowerShell", "Get-ChildItem -Path \"D:\\Proyectos\\Claude-3D\" -Force | Select-Object Mode, LastWriteTime, Length, Name | Format-Table -AutoSize", set()),  # REAL
    ("PowerShell", "$env:PYTHONPATH = 'D:\\Proyectos\\Claude-3D'; " + PYW + " \"D:\\x.py\"", set()),  # env assignment + one python
    ("PowerShell", "$env:SDG_OUT_DIR = 'D:\\Temp\\p'; & \"" + PYW + "\" \"D:\\x.py\"", set()),
    ("Bash", "echo \"a; b && c\"", set()),
    ("PowerShell", "git commit -m @'\nFirst line; still the message\nsecond line\n'@", set()),
    ("Bash", PY + " -X faulthandler \"D:/Proyectos/Claude-3D/projects/VitaGripPS5/audit/r10/scripts/ft10.py\" \"D:/x.stl\"", set()),  # REAL shape
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


def run_hook(payload):
    return subprocess.run([sys.executable, str(HERE / "shell_guard.py")], input=json.dumps(payload),
                          capture_output=True, text=True, timeout=60)


def test_subprocess():
    """Run the hook exactly as Claude Code would: JSON on stdin, JSON (or nothing) on stdout.
    No agent_id in the payload: the main thread is where the work runs."""
    bad = 0
    payload = {"hook_event_name": "PreToolUse", "tool_name": "Bash",
               "tool_input": {"command": "cd D:/x && python -c \"print(1)\""}}
    r = run_hook(payload)
    try:
        out = json.loads(r.stdout)
        ok = out["hookSpecificOutput"]["permissionDecision"] == "deny"
    except Exception:
        ok = False
    bad += not ok
    print(f"  {'ok  ' if ok else 'FAIL'} main-thread deny JSON: {r.stdout.strip()[:110]}")
    payload["tool_input"]["command"] = PY + " \"D:/x.py\""
    r = run_hook(payload)
    ok = r.stdout.strip() == "" and r.returncode == 0
    bad += not ok
    print(f"  {'ok  ' if ok else 'FAIL'} main-thread allow: no output, exit {r.returncode}")
    payload["tool_name"] = "Read"
    payload["tool_input"] = {"file_path": "D:/x.py"}
    r = run_hook(payload)
    ok = r.stdout.strip() == "" and r.returncode == 0
    bad += not ok
    print(f"  {'ok  ' if ok else 'FAIL'} other tools ignored: no output, exit {r.returncode}")
    return bad


if __name__ == "__main__":
    print("shell_guard.decide:")
    fails = test_shell_guard()
    print("as a subprocess:")
    fails += test_subprocess()
    print("ALL PASS" if fails == 0 else f"{fails} FAILED")
    sys.exit(1 if fails else 0)
