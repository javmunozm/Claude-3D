"""Measure token use in Claude Code transcripts (main sessions + subagents).

Reads the `usage` block of every assistant API response (deduplicated by
message id), the tool_use inputs, and the tool_result payloads.

Usage: python token_audit.py <section> [session-prefix ...]
  sections: sessions | agents | tools | big | reads | baseline | ctx
"""
import base64
import collections
import io
import json
import os
import struct
import sys

ROOT = r"C:\Users\javmu\.claude\projects\D--CAD-Claude-Projects"
SECTION = sys.argv[1] if len(sys.argv) > 1 else "sessions"
ONLY = sys.argv[2:]


def iter_lines(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception:
                continue


def png_size(b64):
    try:
        raw = base64.b64decode(b64[:200] + "=" * (-len(b64[:200]) % 4))
    except Exception:
        return None
    if raw[:8] == b"\x89PNG\r\n\x1a\n":
        w, h = struct.unpack(">II", raw[16:24])
        return w, h
    return None


def img_size(block):
    src = block.get("source") or {}
    data = src.get("data") or ""
    wh = png_size(data)
    if wh:
        return wh
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(base64.b64decode(data)))
        return im.size
    except Exception:
        return None


def short_input(name, inp):
    if not isinstance(inp, dict):
        return str(inp)[:120]
    if name in ("Read",):
        s = inp.get("file_path", "")
        if inp.get("offset") or inp.get("limit"):
            s += f" [off={inp.get('offset')} lim={inp.get('limit')}]"
        return s
    if name in ("Bash", "PowerShell"):
        return " ".join(str(inp.get("command", "")).split())[:160]
    if name in ("Grep",):
        return f"/{inp.get('pattern')}/ in {inp.get('path', '')} mode={inp.get('output_mode', '')}"
    if name in ("Glob",):
        return f"{inp.get('pattern')} in {inp.get('path', '')}"
    if name in ("Agent", "Task"):
        return f"{inp.get('subagent_type')}: {inp.get('description')} (prompt {len(str(inp.get('prompt', '')))} ch)"
    if name in ("Write", "Edit"):
        return inp.get("file_path", "")
    return json.dumps(inp)[:160]


class Transcript:
    def __init__(self, path, label, agent_type="main"):
        self.path = path
        self.label = label
        self.agent_type = agent_type
        self.calls = collections.OrderedDict()  # msg id -> dict
        self.tool_uses = {}  # id -> (name, input, call_index)
        self.results = []  # (tool_use_id, chars, images[(w,h)])
        self.user_images = []
        self.first_ts = None
        self.last_ts = None
        self.compactions = 0
        self._parse()

    def _parse(self):
        for o in iter_lines(self.path):
            ts = o.get("timestamp")
            if ts:
                self.first_ts = self.first_ts or ts
                self.last_ts = ts
            t = o.get("type")
            if o.get("isCompactSummary"):
                self.compactions += 1
            if t == "assistant":
                msg = o.get("message") or {}
                mid = msg.get("id") or o.get("requestId") or o.get("uuid")
                u = msg.get("usage")
                if u and mid not in self.calls:
                    cc = u.get("cache_creation") or {}
                    self.calls[mid] = dict(
                        inp=u.get("input_tokens", 0) or 0,
                        cw=u.get("cache_creation_input_tokens", 0) or 0,
                        cr=u.get("cache_read_input_tokens", 0) or 0,
                        out=u.get("output_tokens", 0) or 0,
                        cw5=cc.get("ephemeral_5m_input_tokens", 0) or 0,
                        cw1h=cc.get("ephemeral_1h_input_tokens", 0) or 0,
                        model=msg.get("model"),
                        ts=ts,
                    )
                elif u and mid in self.calls:
                    # streaming splits one response across lines; keep the max output
                    self.calls[mid]["out"] = max(self.calls[mid]["out"], u.get("output_tokens", 0) or 0)
                idx = list(self.calls.keys()).index(mid) if mid in self.calls else -1
                for b in msg.get("content") or []:
                    if isinstance(b, dict) and b.get("type") == "tool_use":
                        self.tool_uses[b["id"]] = (b.get("name"), b.get("input"), idx)
            elif t == "user":
                msg = o.get("message") or {}
                content = msg.get("content")
                if isinstance(content, list):
                    for b in content:
                        if not isinstance(b, dict):
                            continue
                        if b.get("type") == "tool_result":
                            c = b.get("content")
                            chars = 0
                            imgs = []
                            if isinstance(c, str):
                                chars = len(c)
                            elif isinstance(c, list):
                                for cc in c:
                                    if not isinstance(cc, dict):
                                        continue
                                    if cc.get("type") == "text":
                                        chars += len(cc.get("text", ""))
                                    elif cc.get("type") == "image":
                                        imgs.append(img_size(cc))
                            self.results.append((b.get("tool_use_id"), chars, imgs))
                        elif b.get("type") == "image":
                            self.user_images.append(img_size(b))

    # --- aggregates
    def totals(self):
        s = dict(inp=0, cw=0, cr=0, out=0, cw5=0, cw1h=0)
        for c in self.calls.values():
            for k in s:
                s[k] += c[k]
        s["n"] = len(self.calls)
        ctx = [c["inp"] + c["cw"] + c["cr"] for c in self.calls.values()]
        s["peak"] = max(ctx) if ctx else 0
        s["first_ctx"] = ctx[0] if ctx else 0
        s["mean_ctx"] = int(sum(ctx) / len(ctx)) if ctx else 0
        s["processed"] = sum(ctx)
        models = collections.Counter(c["model"] for c in self.calls.values())
        s["models"] = dict(models)
        return s


def load_session(sid):
    main = Transcript(os.path.join(ROOT, sid + ".jsonl"), sid[:8], "main")
    subs = []
    sdir = os.path.join(ROOT, sid, "subagents")
    if os.path.isdir(sdir):
        for fn in sorted(os.listdir(sdir)):
            if fn.endswith(".jsonl"):
                meta = {}
                mp = os.path.join(sdir, fn[:-6] + ".meta.json")
                if os.path.exists(mp):
                    try:
                        meta = json.load(open(mp, encoding="utf-8"))
                    except Exception:
                        pass
                tr = Transcript(os.path.join(sdir, fn), fn[6:14], meta.get("agentType", "?"))
                tr.description = meta.get("description", "")
                subs.append(tr)
    return main, subs


def sessions_list():
    out = []
    for name in os.listdir(ROOT):
        if name.endswith(".jsonl"):
            sid = name[:-6]
            if ONLY and not any(sid.startswith(p) for p in ONLY):
                continue
            out.append((os.path.getmtime(os.path.join(ROOT, name)), sid))
    out.sort()
    return [s for _, s in out]


def fmt(n):
    if n >= 1_000_000:
        return f"{n / 1e6:.2f}M"
    if n >= 1000:
        return f"{n / 1e3:.1f}k"
    return str(n)


def weighted(t):
    # input-price-equivalent: input 1x, 5m cache write 1.25x, 1h cache write 2x,
    # cache read 0.1x, output 5x (Anthropic list-price ratios)
    cw_other = t["cw"] - t["cw5"] - t["cw1h"]
    return t["inp"] + 1.25 * (t["cw5"] + cw_other) + 2.0 * t["cw1h"] + 0.1 * t["cr"] + 5 * t["out"]


def main():
    sids = sessions_list()
    if SECTION == "sessions":
        print(f"{'session':10} {'date':16} {'who':18} {'calls':>6} {'input':>8} {'c.write':>8} {'c.read':>9} {'output':>8} {'peakctx':>8} {'meanctx':>8} {'weighted':>9}")
        for sid in sids:
            main_t, subs = load_session(sid)
            rows = [("main", main_t)] + [(f"  {s.agent_type[:16]}", s) for s in subs]
            gt = collections.Counter()
            for who, tr in rows:
                t = tr.totals()
                if t["n"] == 0:
                    continue
                w = weighted(t)
                gt.update(dict(n=t["n"], inp=t["inp"], cw=t["cw"], cr=t["cr"], out=t["out"], w=int(w)))
                print(f"{sid[:8]:10} {(tr.first_ts or '')[:16]:16} {who:18} {t['n']:>6} {fmt(t['inp']):>8} {fmt(t['cw']):>8} {fmt(t['cr']):>9} {fmt(t['out']):>8} {fmt(t['peak']):>8} {fmt(t['mean_ctx']):>8} {fmt(int(w)):>9}")
            if len(rows) > 1:
                print(f"{sid[:8]:10} {'':16} {'== SESSION TOTAL':18} {gt['n']:>6} {fmt(gt['inp']):>8} {fmt(gt['cw']):>8} {fmt(gt['cr']):>9} {fmt(gt['out']):>8} {'':>8} {'':>8} {fmt(gt['w']):>9}")
            print("-" * 130)
    elif SECTION == "agents":
        for sid in sids:
            main_t, subs = load_session(sid)
            for s in subs:
                t = s.totals()
                n_img = sum(len(r[2]) for r in s.results)
                res_chars = sum(r[1] for r in s.results)
                tools = collections.Counter(v[0] for v in s.tool_uses.values())
                print(f"{sid[:8]} {s.label} {s.agent_type:22} calls={t['n']:4} out={fmt(t['out']):>7} cr={fmt(t['cr']):>8} cw={fmt(t['cw']):>7} first_ctx={fmt(t['first_ctx']):>6} peak={fmt(t['peak']):>6} w={fmt(int(weighted(t))):>7} imgs={n_img:3} res_chars={fmt(res_chars):>7} models={t['models']}")
                print(f"           desc: {getattr(s, 'description', '')}")
                print(f"           tools: {dict(tools.most_common(8))}")
    elif SECTION == "tools":
        agg = collections.defaultdict(lambda: collections.Counter())
        for sid in sids:
            main_t, subs = load_session(sid)
            for tr in [main_t] + subs:
                scope = "main" if tr.agent_type == "main" else "sub"
                for tid, chars, imgs in tr.results:
                    name = (tr.tool_uses.get(tid) or ("?",))[0]
                    a = agg[(scope, name)]
                    a["n"] += 1
                    a["chars"] += chars
                    a["imgs"] += len([i for i in imgs])
                    for wh in imgs:
                        if wh:
                            a["img_px_tok"] += int(wh[0] * wh[1] / 750)
        print(f"{'scope':5} {'tool':14} {'results':>8} {'chars':>9} {'~tok(ch/4)':>10} {'images':>7} {'~img tok':>9}")
        for (scope, name), a in sorted(agg.items(), key=lambda kv: -(kv[1]["chars"] / 4 + kv[1]["img_px_tok"])):
            print(f"{scope:5} {str(name)[:14]:14} {a['n']:>8} {fmt(a['chars']):>9} {fmt(a['chars'] // 4):>10} {a['imgs']:>7} {fmt(a['img_px_tok']):>9}")
    elif SECTION == "big":
        rows = []
        for sid in sids:
            main_t, subs = load_session(sid)
            for tr in [main_t] + subs:
                for tid, chars, imgs in tr.results:
                    name, inp, _ = tr.tool_uses.get(tid) or ("?", {}, -1)
                    rows.append((chars, sid[:8], tr.agent_type, name, short_input(name, inp), len(imgs)))
        rows.sort(reverse=True)
        for r in rows[:40]:
            print(f"{fmt(r[0]):>7} {r[1]} {r[2][:18]:18} {str(r[3])[:10]:10} imgs={r[5]} {r[4]}")
    elif SECTION == "reads":
        cnt = collections.Counter()
        chars = collections.Counter()
        for sid in sids:
            main_t, subs = load_session(sid)
            for tr in [main_t] + subs:
                res = {tid: (c, imgs) for tid, c, imgs in tr.results}
                for tid, (name, inp, _) in tr.tool_uses.items():
                    if name == "Read" and isinstance(inp, dict):
                        p = inp.get("file_path", "").replace("/", "\\").lower()
                        cnt[p] += 1
                        chars[p] += res.get(tid, (0, []))[0]
        print(f"{'reads':>5} {'chars':>8}  path")
        for p, n in cnt.most_common(45):
            print(f"{n:>5} {fmt(chars[p]):>8}  {p}")
    elif SECTION == "baseline":
        seen = collections.defaultdict(list)
        for sid in sids:
            main_t, subs = load_session(sid)
            for tr in [main_t] + subs:
                t = tr.totals()
                if t["n"]:
                    seen[tr.agent_type].append(t["first_ctx"])
        for k, v in sorted(seen.items()):
            print(f"{k:24} n={len(v):3} first-call context: min={fmt(min(v))} median={fmt(sorted(v)[len(v) // 2])} max={fmt(max(v))}")
    elif SECTION == "ctx":
        # context growth curve of each transcript (every Nth call)
        for sid in sids:
            main_t, subs = load_session(sid)
            for tr in [main_t] + subs:
                ctx = [c["inp"] + c["cw"] + c["cr"] for c in tr.calls.values()]
                if not ctx:
                    continue
                step = max(1, len(ctx) // 12)
                pts = " ".join(fmt(x) for x in ctx[::step])
                print(f"{sid[:8]} {tr.agent_type[:18]:18} n={len(ctx):4} compactions={tr.compactions} | {pts}")


if __name__ == "__main__":
    main()
