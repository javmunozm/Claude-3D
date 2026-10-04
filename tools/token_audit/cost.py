"""API list-price equivalent (USD) of each transcript, using per-model prices.

A relative-cost proxy only: claude.ai plans are not billed per token.
Usage: python cost.py [session-prefix ...]
"""
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import token_audit as ta  # noqa: E402

# $/MTok: input, output, cache read, 5m write (1.25x input), 1h write (2x input)
PRICES = {
    "claude-opus-5-5": (4.0, 20.0, 0.20, 5.0, 8.0),
    "claude-sonnet-5-5": (2.0, 10.0, 0.20, 2.5, 4.0),
    "claude-opus-5": (5.0, 25.0, 0.50, 6.25, 10.0),
    "claude-opus-4-8": (5.0, 25.0, 0.50, 6.25, 10.0),
    "claude-opus-4-7": (5.0, 25.0, 0.50, 6.25, 10.0),
    "claude-sonnet-5": (2.0, 10.0, 0.20, 2.5, 4.0),
}
seen_unknown = collections.Counter()


def call_usd(c):
    p = PRICES.get(c["model"])
    if p is None:
        seen_unknown[c["model"]] += 1
        return 0.0
    cw_other = c["cw"] - c["cw5"] - c["cw1h"]
    return (c["inp"] * p[0] + c["out"] * p[1] + c["cr"] * p[2] + (c["cw5"] + cw_other) * p[3] + c["cw1h"] * p[4]) / 1e6


def tr_usd(tr):
    return sum(call_usd(c) for c in tr.calls.values())


ta.ONLY = sys.argv[1:]
grand = 0.0
for sid in ta.sessions_list():
    main_t, subs = ta.load_session(sid)
    m = tr_usd(main_t)
    s = sum(tr_usd(x) for x in subs)
    grand += m + s
    models = collections.Counter(c["model"] for c in main_t.calls.values())
    print(f"{sid[:8]} {(main_t.first_ts or '')[:10]} main ${m:7.2f}  subagents ${s:7.2f}  total ${m + s:7.2f}   main model {dict(models.most_common(2))}")
    for x in subs:
        t = x.totals()
        print(f"           {x.agent_type[:22]:22} {getattr(x, 'description', '')[:38]:38} calls={t['n']:4} ${tr_usd(x):7.2f}")
print(f"ALL ${grand:.2f}")
if seen_unknown:
    print("unpriced calls by model:", dict(seen_unknown))
