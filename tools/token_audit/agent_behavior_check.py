"""Measure every subagent run against the rules in its own definition.

Per run: tool calls (default stop 60), images read (limit ~10), shell-rule
violations (cd, &&/||/; chains, python -c, heredoc code, cat/head/ls to view
files), new .py scripts written (rule: one scratch script), when the first
deliverable (.md) write happened (rule: write as you go), resumes via
SendMessage, whether the launching brief named a numeric budget, list price.

Usage: python agent_behavior_check.py [runs|summary]
"""
import collections
import json
import os
import re
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import token_audit as ta  # noqa: E402

MODE = sys.argv[1] if len(sys.argv) > 1 else "summary"
PRICES = {
    "claude-opus-5-5": (4.0, 20.0, 0.20, 5.0, 8.0),
    "claude-sonnet-5-5": (2.0, 10.0, 0.20, 2.5, 4.0),
    "claude-opus-5": (5.0, 25.0, 0.50, 6.25, 10.0),
    "claude-sonnet-5": (2.0, 10.0, 0.20, 2.5, 4.0),
}
BUDGET_RE = re.compile(r"(?i)(\b\d+\s*(?:tool\s*)?calls\b|hard stop\s*~?\d+|\bceiling\s*(?:of\s*)?~?\d+|\bat most\s*~?\d+\s*(?:tool\s*)?calls)")
RULES_FROM = "2026-09-24T17:55"  # commit 44ce899 added 'Budget and stopping' + 'Shell commands' to every agent


def usd(tr):
    s = 0.0
    for c in tr.calls.values():
        p = PRICES.get(c["model"])
        if not p:
            continue
        other = c["cw"] - c["cw5"] - c["cw1h"]
        s += (c["inp"] * p[0] + c["out"] * p[1] + c["cr"] * p[2] + (c["cw5"] + other) * p[3] + c["cw1h"] * p[4]) / 1e6
    return s


def shell_violations(cmd):
    v = []
    c = cmd.strip()
    if re.search(r"(^|[;&|]\s*)cd\s", c):
        v.append("cd")
    if "&&" in c or "||" in c:
        v.append("chain")
    elif re.search(r";\s*\S", c) and "<<" not in c and "python -c" not in c:
        v.append("chain")
    if re.search(r"python[0-9.]*\s+-c\b", c):
        v.append("python -c")
    if "<<" in c:
        v.append("heredoc")
    if re.match(r"(cat|head|tail|ls|type)\s", c):
        v.append("view-in-shell")
    return v


def main_links(sid):
    """toolUseId -> brief prompt, and agent id -> number of SendMessage resumes."""
    path = os.path.join(ta.ROOT, sid + ".jsonl")
    briefs, resumes = {}, collections.Counter()
    for o in ta.iter_lines(path):
        if o.get("type") != "assistant":
            continue
        for b in (o.get("message") or {}).get("content") or []:
            if isinstance(b, dict) and b.get("type") == "tool_use":
                inp = b.get("input") or {}
                if b.get("name") in ("Agent", "Task"):
                    briefs[b.get("id")] = str(inp.get("prompt", ""))
                elif b.get("name") == "SendMessage":
                    resumes[str(inp.get("to", ""))] += 1
    return briefs, resumes


rows = []
for sid in ta.sessions_list():
    main_t, subs = ta.load_session(sid)
    if not subs:
        continue
    briefs, resumes = main_links(sid)
    sdir = os.path.join(ta.ROOT, sid, "subagents")
    for s in subs:
        agent_id = os.path.basename(s.path)[6:-6]
        meta = {}
        mp = s.path[:-6] + ".meta.json"
        if os.path.exists(mp):
            meta = json.load(open(mp, encoding="utf-8"))
        brief = briefs.get(meta.get("toolUseId"), "")
        ordered = sorted(s.tool_uses.values(), key=lambda x: x[2])
        n_tools = len(ordered)
        n_imgs = sum(len(r[2]) for r in s.results)
        viol = collections.Counter()
        n_shell = 0
        py_written = set()
        first_md = None
        for i, (name, inp, _) in enumerate(ordered):
            if not isinstance(inp, dict):
                continue
            if name in ("Bash", "PowerShell"):
                n_shell += 1
                for v in shell_violations(str(inp.get("command", ""))):
                    viol[v] += 1
            elif name == "Write":
                fp = str(inp.get("file_path", ""))
                if fp.endswith(".py"):
                    py_written.add(fp.lower())
                if fp.endswith(".md") and first_md is None:
                    first_md = i
            elif name == "Edit":
                fp = str(inp.get("file_path", ""))
                if fp.endswith(".md") and first_md is None:
                    first_md = i
        t = s.totals()
        rows.append(dict(
            ruled=(s.first_ts or "") >= RULES_FROM,
            sid=sid[:8], agent=s.agent_type, desc=getattr(s, "description", "")[:44], calls=t["n"], tools=n_tools,
            imgs=n_imgs, shell=n_shell, viol=dict(viol), scripts=len(py_written),
            first_md=(None if first_md is None else round(first_md / max(n_tools, 1), 2)),
            resumes=resumes.get(agent_id, 0), budget=bool(BUDGET_RE.search(brief)), brief_len=len(brief),
            usd=usd(s), model=",".join(sorted(m for m in t["models"] if m and not m.startswith("<"))),
        ))

if MODE == "runs":
    for r in rows:
        print(f"{r['sid']} {r['agent'][:20]:20} {r['desc']:44} tools={r['tools']:3} imgs={r['imgs']:2} scripts={r['scripts']:2} "
              f"firstMD={r['first_md']} resumes={r['resumes']} budget={'Y' if r['budget'] else '-'} ${r['usd']:.2f} viol={r['viol']}")
    sys.exit()

if MODE == "ruled":
    rows = [r for r in rows if r["ruled"]]
    print(f"RUNS STARTED AFTER THE RULES WERE COMMITTED ({RULES_FROM} UTC): {len(rows)}")
by = collections.defaultdict(list)
for r in rows:
    by[r["agent"]].append(r)
print(f"{'agent':22} {'runs':>4} {'$total':>8} {'tools med/max':>13} {'>60':>5} {'imgs med/max':>12} {'>10':>4} {'scripts med/max':>15} {'viol/run':>8} {'MD late':>7} {'resumed':>7} {'budget':>6}")
for agent, rs in sorted(by.items(), key=lambda kv: -sum(r["usd"] for r in kv[1])):
    tools = [r["tools"] for r in rs]
    imgs = [r["imgs"] for r in rs]
    scr = [r["scripts"] for r in rs]
    viol = [sum(r["viol"].values()) for r in rs]
    late = sum(1 for r in rs if r["first_md"] is None or r["first_md"] > 0.8)
    print(f"{agent[:22]:22} {len(rs):>4} {sum(r['usd'] for r in rs):>8.2f} {statistics.median(tools):>6.0f}/{max(tools):<6} "
          f"{sum(1 for x in tools if x > 60):>5} {statistics.median(imgs):>5.0f}/{max(imgs):<6} {sum(1 for x in imgs if x > 10):>4} "
          f"{statistics.median(scr):>7.0f}/{max(scr):<7} {statistics.mean(viol):>8.1f} {late:>7} {sum(1 for r in rs if r['resumes']):>7} "
          f"{sum(1 for r in rs if r['budget']):>3}/{len(rs):<2}")

allv = collections.Counter()
for r in rows:
    allv.update(r["viol"])
print("\nshell-rule violations, all runs:", dict(allv), " shell commands total:", sum(r["shell"] for r in rows))
b = [r for r in rows if r["budget"]]
nb = [r for r in rows if not r["budget"]]
if b and nb:
    print(f"briefs WITH a numeric budget: {len(b)} runs, tool calls median {statistics.median([r['tools'] for r in b]):.0f}, max {max(r['tools'] for r in b)}, "
          f"mean ${statistics.mean([r['usd'] for r in b]):.2f}")
    print(f"briefs WITHOUT:               {len(nb)} runs, tool calls median {statistics.median([r['tools'] for r in nb]):.0f}, max {max(r['tools'] for r in nb)}, "
          f"mean ${statistics.mean([r['usd'] for r in nb]):.2f}")
