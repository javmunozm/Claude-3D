# Versioning a project

How to add a second (or third) generation to an existing project without
cluttering `projects/` — and how to consolidate one that has already sprawled.

## The rule

**One project = one physical object = one folder under `projects/`.** Versions
are subfolders inside it. A version is never a sibling of the project.

```
projects/<Project>/
├── README.md     ← navigation: which version ships, which file to slice
├── v0/           ← README.md, macros/, its own .stl/.step
└── v2/           ← README.md, macros/, its own .stl/.step
```

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

### Naming

Version folders are named for **what they ship**, not when they started. Gaps
are correct: BrokeFeet has `v0/` and `v2/` and no `v1/`, because the V1 rebuild
and the V2 sculpt/pin work happened in one folder and ship as V2. Inventing a
`v1/` to fill the gap would re-create the original problem.

## Procedure

### 1. Establish the dependency direction first

Before moving anything, find out whether the versions are independent.

```
grep -rn "sys.path\|parents\[\|Path(__file__)" projects/<Project>*/macros/*.py
grep -rn "<OtherVersion>" projects/<Project>*/macros/*.py
```

If one version imports from the other, it is an **upstream dependency**, not
dead weight. Record that in the root README so nobody deletes it.

### 2. Check what git tracks

```
git ls-files projects/<Project>/ | wc -l
cat .gitattributes 2>/dev/null   # LFS?
grep <Project> .gitignore
```

Large exports are usually gitignored here, so moving them is a plain filesystem
operation with no history cost. If they *are* tracked, use `git mv` so history
follows.

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

**a. Repo-root depth gains one level.** A macro at
`projects/<P>/<vN>/macros/x.py` reaches the repo root at `parents[4]`, not
`parents[2]`:

```
sed -i 's|parents\[2\]|parents[4]|' projects/<Project>/v*/macros/*.py
```

Verify against a real directory rather than trusting the arithmetic:

```
python -c "
from pathlib import Path; import re
for f in sorted(Path('projects/<Project>').rglob('macros/*.py')):
    m = re.search(r'parents\[(\d+)\]', f.read_text(encoding='utf-8', errors='ignore'))
    if m:
        root = f.resolve().parents[int(m.group(1))]
        print(('OK  ' if (root/'references').is_dir() else 'FAIL'), f, '->', root)
"
```

Run that from the **repo root** — a relative `rglob` from inside the project
matches nothing and prints a vacuous pass.

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

- `.gitignore` — every ignore path gains the version level, or large exports
  start getting committed.
- `docs/projects.md` — collapse the version rows into **one project row**.
- `CLAUDE.md` and `.claude/agents/*.md` — fix *path* references. Leave
  historical narrative alone: "the first BrokeFeetV1 handoff scaled to metres"
  is a true statement about the past and should not be rewritten.
- Data files (e.g. `TRANSFORM.json`) — a `"source"` naming a **file** that still
  exists needs no edit; only directory paths change.

### 6. Verify by running, not by reading

The move is proven when a cross-version import actually resolves:

```
python -c "
import sys; from pathlib import Path
HERE = Path('projects/<Project>/v2/macros').resolve()
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent.parent/'v0'/'macros'))
import <upstream_module> as m
print('imported from:', m.__file__)
print('refs dir exists:', m.<SOME_DIR>.is_dir())
"
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
