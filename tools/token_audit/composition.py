"""What fills a transcript's context: chars by category, plus a measured
chars-per-token calibration from consecutive-call context deltas.

Usage: python composition.py <path-to-jsonl> [<path> ...]
"""
import base64
import collections
import io
import json
import struct
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


def img_wh(block):
    data = (block.get("source") or {}).get("data") or ""
    try:
        raw = base64.b64decode(data[:200] + "=" * (-len(data[:200]) % 4))
        if raw[:8] == b"\x89PNG\r\n\x1a\n":
            return struct.unpack(">II", raw[16:24])
    except Exception:
        pass
    try:
        from PIL import Image
        return Image.open(io.BytesIO(base64.b64decode(data))).size
    except Exception:
        return None


def analyze(path):
    cat = collections.Counter()
    n_items = collections.Counter()
    imgs = []
    calls = collections.OrderedDict()
    tool_names = {}
    # per-call content added after that call (for delta calibration)
    events = []  # (kind, key, chars) in file order, with call boundaries
    for o in iter_lines(path):
        t = o.get("type")
        if t == "assistant":
            msg = o.get("message") or {}
            mid = msg.get("id")
            u = msg.get("usage")
            if u and mid not in calls:
                calls[mid] = u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("cache_read_input_tokens", 0)
                events.append(("CALL", mid, calls[mid]))
            for b in msg.get("content") or []:
                if not isinstance(b, dict):
                    continue
                bt = b.get("type")
                if bt == "thinking":
                    c = len(b.get("thinking", "") or "")
                    cat["asst.thinking(text)"] += c
                    cat["asst.thinking(signature)"] += len(b.get("signature", "") or "")
                    n_items["asst.thinking(text)"] += 1
                elif bt == "redacted_thinking":
                    cat["asst.redacted_thinking"] += len(b.get("data", "") or "")
                elif bt == "text":
                    cat["asst.text"] += len(b.get("text", ""))
                    n_items["asst.text"] += 1
                elif bt == "tool_use":
                    name = b.get("name")
                    tool_names[b.get("id")] = name
                    c = len(json.dumps(b.get("input"), ensure_ascii=False))
                    cat[f"asst.tool_use:{name}"] += c
                    n_items[f"asst.tool_use:{name}"] += 1
                    events.append(("ADD", f"tool_use:{name}", c))
        elif t == "user":
            msg = o.get("message") or {}
            content = msg.get("content")
            if isinstance(content, str):
                cat["user.text"] += len(content)
                n_items["user.text"] += 1
                continue
            for b in content or []:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "tool_result":
                    name = tool_names.get(b.get("tool_use_id"), "?")
                    c = b.get("content")
                    chars = 0
                    if isinstance(c, str):
                        chars = len(c)
                    elif isinstance(c, list):
                        for cc in c:
                            if isinstance(cc, dict) and cc.get("type") == "text":
                                chars += len(cc.get("text", ""))
                            elif isinstance(cc, dict) and cc.get("type") == "image":
                                wh = img_wh(cc)
                                imgs.append((name, wh))
                                events.append(("IMG", name, wh))
                    cat[f"result:{name}"] += chars
                    n_items[f"result:{name}"] += 1
                    events.append(("ADD", f"result:{name}", chars))
                elif b.get("type") == "text":
                    cat["user.text_block"] += len(b.get("text", ""))
                    n_items["user.text_block"] += 1
                    events.append(("ADD", "user.text_block", len(b.get("text", ""))))
                elif b.get("type") == "image":
                    imgs.append(("user", img_wh(b)))
        elif t == "attachment":
            a = o.get("attachment") or {}
            rendered = o.get("rendered") or []
            c = sum(len(r.get("content", "")) for r in rendered if isinstance(r, dict))
            cat[f"attachment:{a.get('type')}"] += c
            n_items[f"attachment:{a.get('type')}"] += 1
            events.append(("ADD", f"attachment:{a.get('type')}", c))
        elif t == "system":
            cat["system-line"] += len(json.dumps(o.get("content", "")))
    return cat, n_items, imgs, calls, events


for path in sys.argv[1:]:
    cat, n_items, imgs, calls, events = analyze(path)
    ctx = list(calls.values())
    print("=" * 90)
    print(path.split("\\")[-1], f"calls={len(ctx)} first_ctx={ctx[0] if ctx else 0} last_ctx={ctx[-1] if ctx else 0}")
    total = sum(v for k, v in cat.items() if "signature" not in k)
    for k, v in cat.most_common():
        print(f"  {k:34} {v:>10,d} chars  ({n_items.get(k, 0)} items)  ~{v / 3.6 / 1000:6.1f}k tok @3.6")
    print(f"  {'TOTAL (excl. signatures)':34} {total:>10,d} chars ~{total / 3.6 / 1000:.1f}k tok")
    # images
    by = collections.Counter()
    tok = collections.Counter()
    for name, wh in imgs:
        by[name] += 1
        if wh:
            tok[name] += int(wh[0] * wh[1] / 750)
    for name in by:
        sizes = collections.Counter(wh for n, wh in imgs if n == name)
        print(f"  images via {name}: {by[name]}  sum(w*h/750)={tok[name]:,d}  sizes={dict(sizes.most_common(4))}")
    # calibration: context growth between consecutive calls vs chars added between them
    seg_chars = 0
    seg_imgs = 0
    pairs = []
    prev = None
    for ev in events:
        if ev[0] == "CALL":
            if prev is not None:
                pairs.append((ev[2] - prev, seg_chars, seg_imgs))
            prev = ev[2]
            seg_chars = 0
            seg_imgs = 0
        elif ev[0] == "ADD":
            seg_chars += ev[2]
        elif ev[0] == "IMG":
            seg_imgs += 1
    textonly = [(d, c) for d, c, i in pairs if i == 0 and c > 4000 and d > 0]
    if textonly:
        ratio = sum(c for d, c in textonly) / sum(d for d, c in textonly)
        print(f"  calibration: {len(textonly)} text-only steps with >4k chars: chars/token(delta incl. output) = {ratio:.2f}")
    imgsteps = [(d, c, i) for d, c, i in pairs if i > 0]
    if imgsteps:
        print("  image steps (ctx delta, text chars, n_images):", [(d, c, i) for d, c, i in imgsteps[:12]])
