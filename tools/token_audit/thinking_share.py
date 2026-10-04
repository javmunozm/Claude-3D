"""Split each API call's output into visible tool-input/text vs the rest (thinking),
and test whether thinking stays in context.

For steps where almost nothing is added between call i and i+1:
  delta = ctx[i+1] - ctx[i] ~= retained part of out[i]
Compare delta with out[i] (all retained) and with the visible part only.

Usage: python thinking_share.py <jsonl> [<chars_per_token>]
"""
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
CPT = float(sys.argv[2]) if len(sys.argv) > 2 else 1.9
calls = []
cur = None
for o in iter_lines(path):
    t = o.get("type")
    if t == "assistant":
        msg = o.get("message") or {}
        u = msg.get("usage")
        if u and (cur is None or cur["id"] != msg.get("id")):
            cur = dict(id=msg.get("id"), ctx=u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("cache_read_input_tokens", 0),
                       out=u.get("output_tokens", 0), vis=0, added=0)
            calls.append(cur)
        elif u and cur is not None:
            cur["out"] = max(cur["out"], u.get("output_tokens", 0))
        for b in msg.get("content") or []:
            if isinstance(b, dict) and b.get("type") == "tool_use":
                cur["vis"] += len(json.dumps(b.get("input"), ensure_ascii=False))
            elif isinstance(b, dict) and b.get("type") == "text":
                cur["vis"] += len(b.get("text", ""))
    elif t in ("user", "attachment") and cur is not None:
        if t == "user":
            c = (o.get("message") or {}).get("content")
            if isinstance(c, list):
                for b in c:
                    if isinstance(b, dict) and b.get("type") == "tool_result":
                        x = b.get("content")
                        cur["added"] += len(x) if isinstance(x, str) else sum(len(y.get("text", "")) for y in (x or []) if isinstance(y, dict))
        else:
            cur["added"] += sum(len(r.get("content", "")) for r in (o.get("rendered") or []) if isinstance(r, dict))

tot_out = sum(c["out"] for c in calls)
tot_vis_tok = sum(c["vis"] for c in calls) / CPT
print(f"calls={len(calls)} total output tokens={tot_out:,}; visible tool-input+text ~{tot_vis_tok:,.0f} tok (at {CPT} ch/tok) -> non-visible (thinking) ~{tot_out - tot_vis_tok:,.0f} ({100 * (tot_out - tot_vis_tok) / tot_out:.0f} %)")
rows = []
for i in range(len(calls) - 1):
    a, b = calls[i], calls[i + 1]
    if a["added"] < 400 and a["out"] > 500:
        vis_tok = a["vis"] / CPT
        rows.append((b["ctx"] - a["ctx"], a["out"], vis_tok))
if rows:
    sd = sum(r[0] for r in rows)
    so = sum(r[1] for r in rows)
    sv = sum(r[2] for r in rows)
    print(f"quiet steps={len(rows)}: sum(delta)={sd:,}  sum(out)={so:,}  sum(visible)~{sv:,.0f}  -> delta/out={sd / so:.2f}, delta/visible={sd / max(sv, 1):.2f}")
    think_heavy = [r for r in rows if r[2] < 0.3 * r[1]]
    if think_heavy:
        sd2 = sum(r[0] for r in think_heavy)
        so2 = sum(r[1] for r in think_heavy)
        sv2 = sum(r[2] for r in think_heavy)
        print(f"  steps where visible < 30 % of output ({len(think_heavy)}): delta={sd2:,} out={so2:,} visible~{sv2:,.0f} -> delta/out={sd2 / so2:.2f}")
