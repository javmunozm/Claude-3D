"""Calibrate tokens per char from consecutive API calls.

For each API call i -> i+1: delta = ctx[i+1] - ctx[i]. That delta holds the
output of call i that stays in context, plus everything added before call i+1
(tool results, attachments). Prints, per step type, delta - out[i] vs the chars
added, so the ratio is measured on this repo's own content.

Usage: python calibrate.py <jsonl>
"""
import collections
import json
import sys


def iter_lines(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    yield json.loads(line)
                except Exception:
                    pass


path = sys.argv[1]
calls = []  # dict(ctx, out, added_chars, kinds, sig_chars, tooluse_chars)
cur = None
names = {}
for o in iter_lines(path):
    t = o.get("type")
    if t == "assistant":
        msg = o.get("message") or {}
        u = msg.get("usage")
        mid = msg.get("id")
        if u and (cur is None or cur["id"] != mid):
            cur = dict(id=mid, ctx=u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("cache_read_input_tokens", 0),
                       out=u.get("output_tokens", 0), added=0, kinds=collections.Counter(), sig=0, tu=0, imgs=0)
            calls.append(cur)
        elif u and cur is not None:
            cur["out"] = max(cur["out"], u.get("output_tokens", 0))
        for b in msg.get("content") or []:
            if isinstance(b, dict):
                if b.get("type") == "thinking":
                    cur["sig"] += len(b.get("signature", "") or "")
                elif b.get("type") == "tool_use":
                    names[b.get("id")] = b.get("name")
                    cur["tu"] += len(json.dumps(b.get("input"), ensure_ascii=False))
                elif b.get("type") == "text":
                    cur["tu"] += len(b.get("text", ""))
    elif t == "user" and cur is not None:
        content = (o.get("message") or {}).get("content")
        if isinstance(content, list):
            for b in content:
                if isinstance(b, dict) and b.get("type") == "tool_result":
                    c = b.get("content")
                    n = len(c) if isinstance(c, str) else sum(len(x.get("text", "")) for x in (c or []) if isinstance(x, dict) and x.get("type") == "text")
                    if isinstance(c, list):
                        cur["imgs"] += sum(1 for x in c if isinstance(x, dict) and x.get("type") == "image")
                    cur["added"] += n
                    cur["kinds"][names.get(b.get("tool_use_id"), "?")] += n
    elif t == "attachment" and cur is not None:
        n = sum(len(r.get("content", "")) for r in (o.get("rendered") or []) if isinstance(r, dict))
        cur["added"] += n
        cur["kinds"]["attachment"] += n

# out[i] includes thinking; does thinking stay? test: regress delta on (out, added chars)
rows = []
for i in range(len(calls) - 1):
    a, b = calls[i], calls[i + 1]
    d = b["ctx"] - a["ctx"]
    rows.append((d, a["out"], a["added"], a["tu"], a["sig"], a["imgs"], dict(a["kinds"])))

# 1) steps with tiny tool results: delta ~= retained output
small = [(d, out, tu, sig) for d, out, add, tu, sig, im, k in rows if add < 300 and im == 0 and out > 300]
if small:
    sd = sum(r[0] for r in small)
    so = sum(r[1] for r in small)
    print(f"steps with <300 chars added ({len(small)}): sum(delta)={sd:,} sum(out)={so:,} -> retained/out = {sd / so:.2f}")
    sig = sum(r[3] for r in small)
    print(f"   signature chars in those steps: {sig:,}  (sig chars per output token {sig / so:.2f})")

# 2) steps dominated by one Read result
for kind in ("Read", "Bash", "attachment"):
    sel = [(d - out, add) for d, out, add, tu, sig, im, k in rows if im == 0 and add > 3000 and k.get(kind, 0) > 0.9 * add]
    sel = [(x, y) for x, y in sel if x > 0]
    if sel:
        print(f"{kind}-dominated steps ({len(sel)}): chars/token = {sum(y for x, y in sel) / sum(x for x, y in sel):.2f}  (delta minus out[i])")

# 3) where did the context go (sum of deltas by bucket)
tot_out = sum(r[1] for r in rows)
tot_delta = sum(r[0] for r in rows)
print(f"sum(delta)={tot_delta:,}  sum(out)={tot_out:,}  first={calls[0]['ctx']:,} last={calls[-1]['ctx']:,}")
# largest single growth steps
rows_i = sorted(enumerate(rows), key=lambda x: -x[1][0])[:8]
for i, (d, out, add, tu, sig, im, k) in rows_i:
    print(f"  step {i}: delta={d:,} out={out:,} added_chars={add:,} imgs={im} kinds={k}")
