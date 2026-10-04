"""Static check of the agent definitions, the /verify skill, CLAUDE.md and docs/.

Reports: size, frontmatter, sections, duplicated sections across agents,
path references that do not exist, agent cross-references, and tool flags that
the named tool's argparse does not define.

Usage: python agent_static_check.py
"""
import collections
import hashlib
import re
from pathlib import Path

ROOT = Path(r"D:\CAD\Claude-Projects")
AGENTS = sorted((ROOT / ".claude" / "agents").glob("*.md"))
OTHER = [ROOT / "CLAUDE.md", ROOT / ".claude" / "skills" / "verify" / "SKILL.md"] + sorted((ROOT / "docs").glob("*.md"))
AGENT_NAMES = {p.stem for p in AGENTS}

# ---- argparse flags per tool
tool_flags = {}
for t in (ROOT / "tools").glob("*.py"):
    src = t.read_text(encoding="utf-8", errors="ignore")
    tool_flags[t.name] = set(re.findall(r"add_argument\(\s*[\"'](--[\w-]+)", src))


def frontmatter(text):
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    fm = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                fm[k.strip()] = v.strip()
    return fm


def sections(text):
    out = collections.OrderedDict()
    cur = "_preamble"
    buf = []
    for line in text.splitlines():
        if line.startswith("## "):
            out[cur] = "\n".join(buf)
            cur = line[3:].strip()
            buf = []
        else:
            buf.append(line)
    out[cur] = "\n".join(buf)
    return out


PATH_RE = re.compile(r"`([^`\n]+)`")


def path_candidates(text):
    for m in PATH_RE.finditer(text):
        s = m.group(1).strip()
        # take the first token that looks like a path (commands contain paths)
        for tok in re.split(r"\s+", s):
            tok = tok.strip("\"'(),;:")
            if not tok or "<" in tok or "*" in tok or "{" in tok or tok.startswith(("http", "--", "-")):
                continue
            if ("/" in tok or "\\" in tok) and (re.search(r"\.\w{1,5}$", tok) or tok.endswith(("/", "\\"))):
                yield tok


def exists(tok):
    p = tok.replace("\\", "/").lstrip("./")
    if re.match(r"^[A-Za-z]:/", p):
        return Path(p).exists(), p
    for base in (ROOT, ROOT / "projects"):
        if (base / p).exists():
            return True, p
    return False, p


print("=" * 100)
print("AGENTS")
dup = collections.defaultdict(list)
for a in AGENTS:
    text = a.read_text(encoding="utf-8")
    fm = frontmatter(text)
    secs = sections(text)
    for name, body in secs.items():
        h = hashlib.md5(body.strip().encode()).hexdigest()[:8]
        dup[(name, h)].append(a.stem)
    desc = fm.get("description", "")
    xrefs = set(re.findall(r"see ([a-z-]+)", desc)) | set(re.findall(r"\(see ([a-z-]+)\)", text))
    bad_x = sorted(x for x in xrefs if x not in AGENT_NAMES and x not in {"below", "above", "the", "docs"})
    print(f"\n{a.stem}: {len(text):,} chars, {text.count(chr(10)) + 1} lines; model={fm.get('model')}; tools={fm.get('tools')}")
    print(f"   description {len(desc)} chars; PROACTIVELY={'PROACTIVELY' in desc}; sections: {', '.join(k for k in secs if k != '_preamble')}")
    if bad_x:
        print(f"   cross-refs to unknown agents: {bad_x}")

print("\nSections whose text is identical in several agents:")
for (name, h), who in sorted(dup.items(), key=lambda kv: -len(kv[1])):
    if len(who) > 1:
        print(f"   '{name}' identical in {len(who)} agents: {', '.join(who)}")

print("=" * 100)
print("PATH REFERENCES THAT DO NOT EXIST (agents, skill, CLAUDE.md, docs)")
for f in AGENTS + OTHER:
    text = f.read_text(encoding="utf-8")
    missing = []
    for tok in sorted(set(path_candidates(text))):
        ok, norm = exists(tok)
        if not ok:
            missing.append(tok)
    if missing:
        print(f"\n{f.relative_to(ROOT)}: {len(missing)} missing")
        for m in missing:
            print(f"   {m}")

print("=" * 100)
print("TOOL FLAGS MENTIONED vs ARGPARSE")
for f in AGENTS + OTHER:
    text = f.read_text(encoding="utf-8")
    for line in text.splitlines():
        for tool, flags in tool_flags.items():
            if tool in line:
                for fl in re.findall(r"(--[\w-]+)", line):
                    if flags and fl not in flags:
                        print(f"   {f.relative_to(ROOT)}: '{fl}' not an option of tools/{tool} (has {sorted(flags)})")
