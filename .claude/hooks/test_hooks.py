"""Offline tests for the hooks in this folder (shell_guard.py, git_state.py). Commands marked REAL were taken from
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
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import git_state  # noqa: E402
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
    # PowerShell hashtable literals: `;` separates entries, not commands (both blocked on 2026-11-11)
    ("PowerShell", "Get-Volume | Where-Object DriveLetter | Select-Object DriveLetter, @{n='SizeGB';e={[math]::Round($_.Size/1GB,1)}}, @{n='FreeGB';e={[math]::Round($_.SizeRemaining/1GB,1)}} | Format-Table -AutoSize", set()),  # REAL
    ("PowerShell", "Get-Disk | Select-Object Number, @{n='SizeGB';e={[math]::Round($_.Size/1GB,0)}} | Format-Table -AutoSize", set()),  # REAL
    ("PowerShell", "Get-Volume | Select-Object @{n='a';e={1}}; Get-Disk", {"chained commands"}),   # a second command after it
    ("PowerShell", "Get-Partition | ForEach-Object { $d = Get-Disk -Number $_.DiskNumber; $d.FriendlyName }", {"chained commands"}),  # statements in a script block
    ("Bash", "echo @{a=1;b=2}", {"chained commands"}),                                         # Bash has no hashtable literal
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


def check(ok, text):
    print(f"  {'ok  ' if ok else 'FAIL'} {text}")
    return 0 if ok else 1


def git(cwd, *args):
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args],
                          cwd=str(cwd), capture_output=True, text=True, timeout=60)


def test_git_state():
    """parse and message on fixed text, then a real clone of a bare repository: commit, push, commit."""
    bad = 0
    sample = ("# branch.oid abc\n# branch.head main\n# branch.upstream origin/main\n# branch.ab +2 -0\n"
              "1 .M N... 100644 100644 100644 a b docs/x.md\n2 R. N... 100644 100644 100644 a b R100 new.py\told.py\n? requirements.txt\n")
    st = git_state.parse_status(sample)
    bad += check(st == {"branch": "main", "upstream": "origin/main", "ahead": 2, "behind": 0, "changed": 2, "untracked": 1},
                 f"parse_status: {st}")
    m = git_state.message("SessionStart", st) or ""
    bad += check("2 commit(s)" in m and "3 file(s)" in m, f"SessionStart text: {m[:90]!r}")
    clean = dict(st, ahead=0, changed=0, untracked=0)
    bad += check(git_state.message("SessionStart", clean) is None, "SessionStart, clean and pushed: nothing")
    bad += check("Push now" in (git_state.message("PostToolUse", st, 'git -C "D:/x y" commit -m "a"') or ""),
                 "PostToolUse after `git -C <path> commit`, 2 ahead: reminder")
    bad += check(git_state.message("PostToolUse", clean, "git commit -m a") is None, "PostToolUse after a commit that is already pushed: nothing")
    for cmd in ("git status", "git log --grep commit", "git -C D:/x push origin main", 'echo "git commit"x'):
        bad += check(git_state.message("PostToolUse", st, cmd) is None, f"PostToolUse after {cmd!r}: nothing")
    for cmd in ("git commit -m x", "git -c user.name=a commit --amend", "timeout 60 git --no-pager commit -q -m x"):
        bad += check(bool(git_state.COMMIT.search(cmd)), f"commit recognised in {cmd!r}")

    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        git(d, "init", "-q", "--bare", "remote.git")
        git(d, "clone", "-q", "remote.git", "work")
        w = d / "work"
        (w / "a.txt").write_text("1", encoding="utf-8")
        git(w, "add", "a.txt")
        git(w, "commit", "-q", "-m", "one")
        s1 = git_state.read_state(w)
        t1 = git_state.unpushed_text(s1) if s1 else None
        bad += check(bool(t1), f"clone with one commit, never pushed: {t1!r}")
        git(w, "push", "-q", "-u", "origin", "HEAD")
        s2 = git_state.read_state(w)
        bad += check(s2 is not None and s2["ahead"] == 0 and git_state.message("SessionStart", s2) is None, f"after push: ahead {s2 and s2['ahead']}, nothing to say")
        (w / "a.txt").write_text("2", encoding="utf-8")
        (w / "b.txt").write_text("new", encoding="utf-8")
        s3 = git_state.read_state(w)
        bad += check(s3 is not None and (s3["changed"], s3["untracked"]) == (1, 1), f"one edit, one new file: changed {s3 and s3['changed']}, untracked {s3 and s3['untracked']}")
        git(w, "commit", "-q", "-am", "two")
        s4 = git_state.read_state(w)
        bad += check(s4 is not None and s4["ahead"] == 1, f"second commit, not pushed: ahead {s4 and s4['ahead']}")
    # as Claude Code runs it, against this repository: valid JSON or nothing, exit 0
    for payload in ({"hook_event_name": "SessionStart", "source": "startup"},
                    {"hook_event_name": "PostToolUse", "tool_name": "Bash", "tool_input": {"command": "git status"}}):
        r = subprocess.run([sys.executable, str(HERE / "git_state.py")], input=json.dumps(payload), capture_output=True, text=True, timeout=60)
        try:
            ok = r.returncode == 0 and (r.stdout.strip() == "" or "hookSpecificOutput" in json.loads(r.stdout))
        except ValueError:
            ok = False
        bad += check(ok, f"git_state subprocess, {payload['hook_event_name']}: exit {r.returncode}, {r.stdout.strip()[:100] or 'no output'}")
    return bad


if __name__ == "__main__":
    print("shell_guard.decide:")
    fails = test_shell_guard()
    print("as a subprocess:")
    fails += test_subprocess()
    print("git_state:")
    fails += test_git_state()
    print("ALL PASS" if fails == 0 else f"{fails} FAILED")
    sys.exit(1 if fails else 0)
