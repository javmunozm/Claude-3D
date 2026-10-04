"""Review maxTurns per agent against the past runs, in turns and list-price dollars.

For each run: turns (API requests), list-price cost, cost per turn as it goes.
For each candidate limit M, with the turn-counting hook (warning at int(0.8*M),
return from max(M-3, warning+1)):
  untouched - the run ends before the warning
  warned    - the run ends after the warning, before the return reminder
  cut       - the run reaches the return reminder (it would have been told to stop)
  $ over    - list price the runs spent after turn M (what the hard stop removes;
              the continuation agent's own cost is not subtracted)
Run: python -B maxturns_review.py
"""
import glob
import json
import os
import statistics
import sys
from collections import defaultdict

sys.path.insert(0, "D:/CAD/Claude-Projects/tools/token_audit")
import token_audit as ta  # noqa: E402

PRICES = {  # $/MTok: input, output, cache read, 5m write, 1h write (03_token_economics.md)
    "claude-opus-5-5": (4.0, 20.0, 0.20, 5.0, 8.0),
    "claude-sonnet-5-5": (2.0, 10.0, 0.20, 2.5, 4.0),
    "claude-opus-5": (5.0, 25.0, 0.50, 6.25, 10.0),
    "claude-opus-4-8": (5.0, 25.0, 0.50, 6.25, 10.0),
    "claude-opus-4-7": (5.0, 25.0, 0.50, 6.25, 10.0),
    "claude-sonnet-5": (2.0, 10.0, 0.20, 2.5, 4.0),
}
CANDIDATES = {
    "cad-designer": (40, 48, 60, 75),
    "form-auditor": (35, 45, 55),
    "reference-analyst": (40, 47, 50),
    "perspective-checker": (15, 25, 30),
    "print-tolerance-expert": (30, 38),
    "vector-tracer": (40, 50),
    "accuracy-reviewer": (20, 35),
    "bone-morphologist": (40,),
    "blender-handoff": (40,),
}
unpriced = defaultdict(int)


def usd(c):
    p = PRICES.get(c["model"])
    if p is None:
        unpriced[c["model"]] += 1
        return 0.0
    other = c["cw"] - c["cw5"] - c["cw1h"]
    return (c["inp"] * p[0] + c["out"] * p[1] + c["cr"] * p[2] + (c["cw5"] + other) * p[3] + c["cw1h"] * p[4]) / 1e6


runs = defaultdict(list)
for path in sorted(glob.glob(os.path.join(ta.ROOT, "*", "subagents", "agent-*.jsonl"))):
    meta_path = path[:-len(".jsonl")] + ".meta.json"
    if not os.path.exists(meta_path):
        continue
    with open(meta_path, encoding="utf-8") as f:
        meta = json.load(f)
    atype = meta.get("agentType")
    if atype not in CANDIDATES:
        continue
    tr = ta.Transcript(path, os.path.basename(path)[6:14], atype)
    per_turn = [usd(c) for c in tr.calls.values()]
    cum, s = [], 0.0
    for x in per_turn:
        s += x
        cum.append(s)
    runs[atype].append({"session": path.split(os.sep)[-3][:8], "desc": meta.get("description", "")[:44],
                        "T": len(per_turn), "usd": s, "cum": cum, "per_turn": per_turn})

for atype, rs in sorted(runs.items()):
    rs.sort(key=lambda r: r["T"])
    print(f"\n== {atype}: {len(rs)} runs, ${sum(r['usd'] for r in rs):.2f} in all")
    for r in rs:
        print(f"   T={r['T']:3}  ${r['usd']:6.2f}  {r['session']}  {r['desc']}")
    for M in CANDIDATES[atype]:
        w, st = int(0.8 * M), max(M - 3, int(0.8 * M) + 1)
        untouched = sum(r["T"] <= w for r in rs)
        warned = sum(w < r["T"] <= st for r in rs)
        cut = sum(r["T"] > st for r in rs)
        over = sum(r["usd"] - r["cum"][M - 1] for r in rs if r["T"] > M)
        print(f"   M={M:3} (warn {w}, return {st}): untouched {untouched}, warned {warned}, cut {cut}; "
              f"${over:6.2f} spent after turn {M}")

print("\nCost of one turn, by turn number (median over the runs that reach it), cad-designer and form-auditor:")
for atype in ("cad-designer", "form-auditor"):
    rs = runs[atype]
    row = []
    for t in (1, 5, 10, 20, 30, 40, 50, 60, 80, 100, 150):
        vals = [r["per_turn"][t - 1] for r in rs if r["T"] >= t]
        if len(vals) >= 2:
            row.append(f"t{t} ${statistics.median(vals):.3f} (n={len(vals)})")
    print(f"   {atype}: " + "; ".join(row))
print("\nCumulative cost at turn 5 (a fresh agent's start-up), median: " + "; ".join(
    f"{a} ${statistics.median([r['cum'][4] for r in rs if r['T'] >= 5]):.2f}"
    for a, rs in sorted(runs.items()) if sum(r["T"] >= 5 for r in rs) >= 1))
print("\nSplitting at turn 60, within each designer run longer than 60 turns:")
print("  the tail (turns 61..T) as it was, against a fresh agent that repeats the run's own first T-60 turns")
tot_tail = tot_fresh = tot_run = 0.0
for r in sorted(runs["cad-designer"], key=lambda r: r["T"]):
    if r["T"] <= 60:
        continue
    tail = sum(r["per_turn"][60:])
    fresh = sum(r["per_turn"][:r["T"] - 60])
    early = statistics.mean(r["per_turn"][1:21])
    late = statistics.mean(r["per_turn"][-20:])
    tot_tail, tot_fresh, tot_run = tot_tail + tail, tot_fresh + fresh, tot_run + r["usd"]
    print(f"   T={r['T']:3} ${r['usd']:6.2f}: tail ${tail:5.2f} vs fresh ${fresh:5.2f} (saves ${tail - fresh:5.2f}); "
          f"mean turn cost, turns 2-21 ${early:.3f}, last 20 ${late:.3f}")
print(f"   all: runs ${tot_run:.2f}; tails ${tot_tail:.2f}; fresh ${tot_fresh:.2f}; "
      f"saving ${tot_tail - tot_fresh:.2f} = {100 * (tot_tail - tot_fresh) / tot_run:.0f}% of the runs' cost")
if unpriced:
    print("unpriced requests by model:", dict(unpriced))
