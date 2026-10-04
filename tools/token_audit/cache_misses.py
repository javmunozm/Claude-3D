"""Find cache rebuilds: API calls whose cache_creation is a large share of the
context, with the idle gap since the previous call and the TTL split.

Usage: python cache_misses.py <jsonl> [<jsonl> ...]
"""
import datetime as dt
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


def ts(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


for path in sys.argv[1:]:
    seen = set()
    calls = []
    for o in iter_lines(path):
        if o.get("type") != "assistant":
            continue
        msg = o.get("message") or {}
        u = msg.get("usage")
        mid = msg.get("id")
        if not u or mid in seen:
            continue
        seen.add(mid)
        cc = u.get("cache_creation") or {}
        calls.append(dict(t=ts(o["timestamp"]), cw=u.get("cache_creation_input_tokens", 0), cr=u.get("cache_read_input_tokens", 0),
                          inp=u.get("input_tokens", 0), cw5=cc.get("ephemeral_5m_input_tokens", 0), cw1h=cc.get("ephemeral_1h_input_tokens", 0)))
    tot_cw = sum(c["cw"] for c in calls)
    tot5 = sum(c["cw5"] for c in calls)
    tot1h = sum(c["cw1h"] for c in calls)
    big = []
    for i, c in enumerate(calls):
        ctx = c["cw"] + c["cr"] + c["inp"]
        if i and c["cw"] > 20000 and c["cw"] > 0.4 * ctx:
            gap = (c["t"] - calls[i - 1]["t"]).total_seconds() / 60
            big.append((i, gap, c["cw"], ctx))
    print(f"{path.split(chr(92))[-1][:40]:40} calls={len(calls)} cache_write={tot_cw:,} (5m={tot5:,} 1h={tot1h:,}) rebuilds(>40% of ctx)={len(big)} rebuilt_tokens={sum(b[2] for b in big):,}")
    for i, gap, cw, ctx in big[:15]:
        print(f"     call {i:4}: idle {gap:7.1f} min before it, cache_write={cw:,} of ctx {ctx:,}")
