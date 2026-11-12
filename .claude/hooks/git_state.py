"""SessionStart / PostToolUse hook: say when work exists only on this disk.

A commit is not saved until it is pushed. On 2026-11-11 the disk was formatted and two
weeks of commits that had never been pushed were lost. The rule ("an approved commit is
pushed in the same step", CLAUDE.md) used to live only in text; this hook states the
facts at the two moments they matter:

  SessionStart                 commits not on origin, and uncommitted files in the tracked set
  PostToolUse (Bash/PowerShell) after a `git commit`: the commits still not on origin

It prints nothing when there is nothing to say. It never blocks and never runs a git
command that changes anything (`git status` only; no fetch).

Input: the hook JSON on stdin. Output: hookSpecificOutput.additionalContext for the
model, and for SessionStart a systemMessage for the user. Registered in
.claude/settings.json. Test: test_hooks.py, next to this file.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
# `commit` as git's subcommand, after any global options (`-C <path>`, `-c k=v`, `--no-pager`): not `git log --grep commit`
COMMIT = re.compile(r"(^|[\s;&|(])git(\.exe)?((\s+-[Cc]\s+(\"[^\"]*\"|'[^']*'|\S+))|(\s+--?[\w-]+(=\S+)?))*\s+commit(\s|$)", re.I)


def parse_status(text):
    """`git status --porcelain=v2 --branch` -> dict(branch, upstream, ahead, behind, changed, untracked)."""
    st = {"branch": None, "upstream": None, "ahead": None, "behind": None, "changed": 0, "untracked": 0}
    for line in text.splitlines():
        if line.startswith("# branch.head "):
            st["branch"] = line.split(" ", 2)[2]
        elif line.startswith("# branch.upstream "):
            st["upstream"] = line.split(" ", 2)[2]
        elif line.startswith("# branch.ab "):
            m = re.search(r"\+(\d+) -(\d+)", line)
            if m:
                st["ahead"], st["behind"] = int(m.group(1)), int(m.group(2))
        elif line[:2] in ("1 ", "2 ", "u "):
            st["changed"] += 1
        elif line.startswith("? "):
            st["untracked"] += 1
    return st


def read_state(repo=REPO):
    try:
        r = subprocess.run(["git", "-C", str(repo), "status", "--porcelain=v2", "--branch"],
                           capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return parse_status(r.stdout) if r.returncode == 0 else None


def unpushed_text(st):
    """The sentence about commits that are not on the remote, or None."""
    if st["upstream"] is None:
        return f"branch `{st['branch']}` has no upstream: none of its commits is on a remote"
    if st["ahead"] is None:  # an upstream is configured but that ref does not exist: nothing was ever pushed
        return f"`{st['upstream']}` does not exist yet: no commit of `{st['branch']}` is on the remote"
    if st["ahead"]:
        return f"{st['ahead']} commit(s) on `{st['branch']}` are not on `{st['upstream']}`"
    return None


def message(event, st, command=""):
    """The text for this event, or None when there is nothing to say."""
    if st is None:
        return None
    ahead = unpushed_text(st)
    if event == "PostToolUse":
        if not COMMIT.search(command or "") or not ahead:
            return None
        return (f"Not pushed: {ahead}. CLAUDE.md: an approved commit is pushed to origin in the same step. "
                f"Push now and report the result, unless the user said not to.")
    parts = []
    if ahead:
        parts.append(ahead + " (they exist only on this disk)")
    n = st["changed"] + st["untracked"]
    if n:
        parts.append(f"{n} file(s) in the tracked set are uncommitted ({st['changed']} changed, {st['untracked']} new)")
    if not parts:
        return None
    return "Claude-3D git state: " + "; ".join(parts) + ". Tell the user in the first reply, and ask before committing."


def main():
    try:
        data = json.loads(sys.stdin.buffer.read().decode("utf-8", errors="replace") or "{}")
    except ValueError:
        return 0
    event = data.get("hook_event_name") or "SessionStart"
    command = str((data.get("tool_input") or {}).get("command", ""))
    if event == "PostToolUse" and not COMMIT.search(command):
        return 0  # the common case: no git call at all
    msg = message(event, read_state(), command)
    if msg:
        out = {"hookSpecificOutput": {"hookEventName": event, "additionalContext": msg}}
        if event == "SessionStart":
            out["systemMessage"] = msg.split(". Tell the user")[0]
        print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
