# Versioning a project

How to add a second (or third) generation to an existing project without
cluttering `projects/` — and how to consolidate one that has already sprawled.

## The rule

**One project = one physical object = one folder under `projects/`.** Versions
are subfolders inside it. A version is never a sibling of the project.

```
projects/<Project>/
├── README.md     ← navigation: which version ships, which file to slice
├── v0/           ← README.md, macros/, its own stl/, step/, renders/
└── v2/           ← README.md, macros/, its own stl/, step/, renders/
```

(BrokeFeet, the first nested project, predates the `stl/`/`step/`/`renders/`
convention and is finished. It is exempt: see architecture.md.)

### Why

`BrokeFeet/` and `BrokeFeetV1/` were one clubfoot model in two top-level
folders. That cost:

- **46 MB of byte-identical duplication** — `BrokeFeet_axial_raw.stl` and
  `BrokeFeetV1_baseline.stl` were the same bytes, as were two sculpt exports.
- **Ambiguous shipping state** — both READMEs described themselves as ready;
  nothing at the top said which STL to slice.
- **A lying name** — `BrokeFeetV1/` contained V1 *and* V2 files, and shipped a
  file called `BrokeFeetV2_pinned2.stl`.
- **An invisible dependency** — the V1 scripts import from `BrokeFeet/macros/`,
  so "delete the old folder" would have broken the shipping model.

### Retiring a version

**Never delete an old version as "the old one" without checking imports.**
BrokeFeet's `v2/` imports directly from `v0/macros/` and does not run without
it. Run the dependency check in step 1 below before removing anything.

For discarding a single attempt rather than a whole version, see
[attempts.md](attempts.md).

### Naming

Version folders are named for **what they ship**, not when they started. Gaps
are correct: BrokeFeet has `v0/` and `v2/` and no `v1/`, because the V1 rebuild
and the V2 sculpt/pin work happened in one folder and ship as V2. Inventing a
`v1/` to fill the gap would re-create the original problem.

## Procedure

### 1. Establish the dependency direction first

Before moving anything, find out whether the versions are independent.

```
grep -rn --include=*.py "sys.path\|parents\[\|Path(__file__)" projects/<Project>*/macros/
grep -rn --include=*.py "<OtherVersion>" projects/<Project>*/macros/
```

`-r` on the folder, not `macros/*.py`: a split project keeps its stages in
`macros/<pkg>/` (architecture.md, "Parametric model pattern"), and a
`macros/*.py` glob misses them.

If one version imports from the other, it is an **upstream dependency**, not
dead weight. Record that in the root README so nobody deletes it.

### 2. Check what git tracks

```
git ls-files projects/<Project>/ | wc -l
grep <Project> .gitignore
```

Also read `.gitattributes` if it exists (LFS?).

Only each project's `README.md` and `macros/**/*.py` are tracked (see
architecture.md, "What the repo tracks"); everything else in a project is a
plain filesystem move. Use `git mv` for the tracked files so history follows.

### 3. Move

```
mkdir projects/<Project>_new
mv projects/<Project>    projects/<Project>_new/v0
mv projects/<Project>V1  projects/<Project>_new/v2
mv projects/<Project>_new projects/<Project>
```

**Windows note:** the final rename of a directory created moments earlier can
fail with *Access denied* even with no process holding a handle — and it fails
for **any** target name, so it is the source directory that is locked, not a
name collision. Recover by creating the final directory and moving the children
into it (child moves work):

```powershell
New-Item -ItemType Directory projects\<Project>
Move-Item projects\<Project>_new\v0 projects\<Project>\v0
Move-Item projects\<Project>_new\v2 projects\<Project>\v2
Remove-Item projects\<Project>_new
```

### 4. Fix the path constants nesting breaks

This is the step that silently breaks everything, because the scripts still run
— they just read from the wrong directory or fail to import.

**a. Repo-root anchors gain one level; project anchors do not.** Nesting
inserts `<vN>/` between the project and `macros/`, so every `parents[N]`
that reaches the **repo root** needs N + 1. An anchor that reaches the file's
own project folder (`parents[1]` from `macros/x.py`, `parents[2]` from
`macros/<pkg>/x.py`) now reaches the version folder, which is right, because
outputs belong to the version. Leave those alone.

| File | Repo root, flat project | Repo root, nested (`<vN>/`) |
|---|---|---|
| `macros/x.py` | `parents[3]` | `parents[4]` |
| `macros/<pkg>/x.py` | `parents[4]` | `parents[5]` |
| `macros/<pkg>/parts/x.py` | `parents[5]` | `parents[6]` |

Do **not** use a blanket `sed` on `parents[...]`. The same number means the
repo root in one file and the project folder in another (e.g.
`SurgicalDrillGuide/macros/sdg_model/constants.py` uses `parents[2]` for the
project folder). Anchors also come in other forms (`HERE.parents[2]` with
`HERE` = the macros folder, `.parent.parent`, nested `os.path.dirname`), and
they live outside `macros/` too (e.g. `SurgicalDrillGuide/docs/mechanism_sizing.py`).
Edit each repo-root anchor by hand. Then list every anchor in the project:
save this as a `.py` in the scratchpad and run it with
`python "<abs path>" "<abs path to projects/<Project>>"`:

```python
import re, sys
from pathlib import Path

proj = Path(sys.argv[1]).resolve()
anchor = re.compile(r"parents\[\d+\]|\.parent\.parent|os\.path\.dirname\(")
direct = re.compile(r"Path\(__file__\)\.resolve\(\)\.parents\[(\d+)\]")
n = 0
for f in sorted(proj.rglob("*.py")):
    if "attempts" in f.parts or "__pycache__" in f.parts:
        continue
    for i, line in enumerate(f.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
        if not anchor.search(line):
            continue
        n += 1
        m = direct.search(line)
        if m:
            d = f.resolve().parents[int(m.group(1))]
            kind = ("repo root" if (d / "sources").is_dir() and (d / "projects").is_dir()
                    else "project/version" if (d / "macros").is_dir() else "NEITHER")
        else:
            kind = "CHECK BY HAND"
        print(f"{kind:16s} {f.relative_to(proj)}:{i}  {line.strip()[:90]}")
print(f"{n} anchor line(s) under {proj}" if n else f"NO anchor lines found under {proj}: wrong path?")
```

The script resolves only the unambiguous form,
`Path(__file__).resolve().parents[N]`. That line must read `repo root` or
`project/version`, and be the folder the variable's name says it is;
`NEITHER` is broken. Every other form prints as `CHECK BY HAND`: trace it
yourself, and don't treat it as a pass. Many are harmless (a script adding
its own folder to `sys.path`). The last line always gives the count. "NO
anchor lines found" means the path argument is wrong, not that the project
is clean. Tested 2026-09-25 on VitaGripPS5, BedLifter, SurgicalDrillGuide
and VitaGrip-hori: every anchor form in them was listed.

**b. Sibling references become nested ones.** `HERE.parent.parent / "BrokeFeet"
/ "macros"` must become `HERE.parent.parent / "v0" / "macros"`. Catch every
spelling (`HERE.parent.parent`, `ROOT.parent`, `REPO / ...`).

**c. Purge `__pycache__`.** Stale caches from the old layout shadow the moved
modules:

```
find projects/<Project> -name __pycache__ -type d -exec rm -rf {} +
```

### 5. Update the paths outside the project

```
grep -rln "<OldFolderName>" --include=*.md --include=*.py --include=*.json .
```

- `.gitignore` — the `projects/` allowlist uses `**`, so it needs no edit for a
  new version level. Check with `git status` that nothing outside
  `README.md` / `macros/**/*.py` shows up.
- `docs/projects.md` — collapse the version rows into **one project row**.
- `CLAUDE.md` and `.claude/agents/*.md` — fix *path* references. Leave
  historical narrative alone: "the first BrokeFeetV1 handoff scaled to metres"
  is a true statement about the past and should not be rewritten.
- Data files (e.g. `TRANSFORM.json`) — a `"source"` naming a **file** that still
  exists needs no edit; only directory paths change.

### 6. Verify by running, not by reading

The move is proven when a cross-version import actually resolves. Save this as
a `.py` in the scratchpad (never `python -c`) and run it:

```python
import sys
from pathlib import Path
HERE = Path(r"<abs path to projects/<Project>/v2/macros>")
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / "v0" / "macros"))
import <upstream_module> as m
print("imported from:", m.__file__)
print("refs dir exists:", m.<SOME_DIR>.is_dir())
```

Then confirm ignores still bite (`git status --porcelain --ignored | grep -c '^!!'`)
and that `git status` shows the move rather than a mass deletion.

## The root README

The project root `README.md` is a **navigation layer, not a summary**. It carries:

- **Which file to slice** — one filename, unambiguous.
- **A version table** — what each holds, which ships, which is still an upstream
  dependency.
- **Scope/safety statements** that apply to every version (for BrokeFeet, the
  clinical-scope warning).
- **Pointers into each version's README** by topic.

It must **not** condense the version READMEs. In this repo those documents are
archives of *measured negative results* — rejected discriminators, rejected
fills, rejected smoothing — and that record is the thing that stops a future
session re-walking work already quantified. Consolidating a project means
**re-filing those documents, never rewriting them.**
