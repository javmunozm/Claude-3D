"""PreToolUse hook: enforce the repo's shell rules before a command can stall on a
permission prompt. Registered in .claude/settings.json (tracked).

Rules (every skill's "Shell." session rule, CLAUDE.md "Verification"):
  - Python is the repo venv, never the bare `python` / `py` on PATH (the system
    interpreter has none of the packages; measured 2026-11-11: `import numpy` fails)
  - never `cd`; every path absolute
  - one command per call: no `;`, `&&`, `||` and no multi-line command lists
  - never `python -c`; no heredoc code fed to an interpreter
  - view files with Read / Grep / Glob, not cat / head / tail / ls / Get-Content

Input: the hook JSON on stdin (tool_name, tool_input.command, ...).
Output: for a violating Bash/PowerShell command, a PreToolUse "deny" decision
whose reason tells the model how to rewrite the command. Otherwise nothing
(the normal permission flow applies). Test: test_hooks.py, next to this file.
"""
import json
import os
import re
import sys

# Measured on the transcripts after the rules were committed (2026-09-24): the main
# thread broke them on 50 % of its commands, subagents on 16 %. Set the environment
# variable SHELL_GUARD_MAIN=0 to apply the guard to subagents only. Since 2026-10-27 the work
# runs in the main thread (skills), so the default must stay on.
APPLY_TO_MAIN = os.environ.get("SHELL_GUARD_MAIN", "1") != "0"

VIEW = re.compile(r"^\s*(cat|head|tail|less|more|type|ls|Get-Content|gc)(\s|$)", re.I)
CD = re.compile(r"^\s*(cd|chdir|Set-Location|sl|pushd)(\s|$)", re.I)
PY_C = re.compile(r"(^|[\s/\\\"'])(python3?|py)(\.exe)?[\"']?(\s+-[A-Za-z]+(\s+\S+)?)*?\s+-c(\s|$)", re.I)
HEREDOC_CODE = re.compile(r"(python3?|py|bash|sh|node|pwsh)(\.exe)?\b[^|\n]*<<-?\s*['\"]?\w+", re.I)
PY_STDIN = re.compile(r"(^|[\s/\\\"'])(python3?|py)(\.exe)?[\"']?\s+-(\s|$)", re.I)
VENV_PY = "D:/Proyectos/Claude-3D/.venv/Scripts/python.exe"
BARE_PY = re.compile(r"(^|[\s|&;(])(python3?|py)(\.exe)?(?=\s|$)", re.I)
QUOTED = re.compile(r"\"[^\"]*\"|'[^']*'")
MAKE_VENV = re.compile(r"\s-m\s+venv(\s|$)", re.I)
ANY_PY = re.compile(r"^\s*(&\s*)?[\"']?[^\s\"']*python(\.exe)?[\"']?(\s|$)", re.I)
ENV_ASSIGN = re.compile(r"^\s*\$env:[A-Za-z_][A-Za-z0-9_]*\s*=\s*.+$", re.I)

FIX = ("Rewrite it as ONE command with absolute paths. For Python, Write the code to a .py file "
       "and run `\"" + VENV_PY + "\" \"<absolute path>.py\"` (in PowerShell prefix it with `& `). "
       "View files with Read, find them with Glob, search them with Grep.")


def split_top_level(cmd, hashtables=False):
    """Split a command on ; && || and newlines that sit outside quotes.

    With `hashtables` (PowerShell), a `;` inside a hashtable literal `@{ ... }` separates
    its entries, not commands: `Select-Object Name, @{n='GB';e={$_.Size/1GB}}` is one
    pipeline (it was blocked as "chained commands" twice on 2026-11-11). A script block
    `{ a; b }` outside a hashtable is still split: that is two statements.
    """
    segs, buf, q, i, depth = [], [], None, 0, 0
    while i < len(cmd):
        ch = cmd[i]
        if q:
            buf.append(ch)
            if ch == q:
                q = None
        elif ch in "'\"":
            q = ch
            buf.append(ch)
        elif hashtables and not depth and cmd.startswith("@{", i):
            depth = 1
            buf.append("@{")
            i += 1
        elif depth:
            depth += (ch == "{") - (ch == "}")
            buf.append(ch)
        elif cmd.startswith("&&", i) or cmd.startswith("||", i):
            segs.append("".join(buf))
            buf = []
            i += 1
        elif ch in ";\n":
            segs.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
        i += 1
    segs.append("".join(buf))
    return [s for s in segs if s.strip()]


def decide(command, tool="Bash"):
    """Return the list of rules a command breaks (empty list = allowed)."""
    cmd = command.strip()
    rules = []
    if tool == "PowerShell" and re.match(r"^\s*timeout(\.exe)?\s", cmd, re.I):
        # measured 2026-10-03: in PowerShell `timeout` is the Windows wait command, the run fails
        rules.append("timeout in PowerShell (use the tool's timeout parameter, or the Bash tool)")
    heredoc = bool(HEREDOC_CODE.search(cmd))
    if heredoc:
        rules.append("heredoc code")
        segs = [cmd]  # the heredoc body is not a command list
    else:
        segs = split_top_level(cmd, hashtables=(tool == "PowerShell"))
    if len(segs) > 1:
        # the one allowed pair: `$env:X = ...; <python> ...`
        if not (len(segs) == 2 and ENV_ASSIGN.match(segs[0]) and ANY_PY.match(segs[1])):
            rules.append("chained commands")
    for s in segs:
        if CD.match(s):
            rules.append("cd")
        if VIEW.match(s):
            rules.append("viewing files in the shell")
    if PY_C.search(cmd) or PY_STDIN.search(cmd):
        rules.append("python -c / stdin code")
    unquoted = QUOTED.sub('""', cmd)
    if BARE_PY.search(unquoted) and not MAKE_VENV.search(unquoted):
        rules.append("bare python (use the repo venv)")
    return sorted(set(rules))


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    if data.get("tool_name") not in ("Bash", "PowerShell"):
        return 0
    if not data.get("agent_id") and not APPLY_TO_MAIN:
        return 0
    command = str((data.get("tool_input") or {}).get("command", ""))
    rules = decide(command, data.get("tool_name"))
    if rules:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": "Blocked by the repo shell rules (" + ", ".join(rules) + "). " + FIX,
        }}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
