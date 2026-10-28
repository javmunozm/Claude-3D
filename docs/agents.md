# Skills (formerly agents)

Since 2026-10-27 the work runs in the **main session through skills** in
`.claude/skills/`, not through subagents. The nine subagents were archived in
`.claude/agents-archive/` (its README maps each one to its skill and says how to
restore one). Reason: Anthropic's guidance that a single agent loading skills on
demand beats a fleet of specialists on quality, cost and handoff loss; and in
this repo, subagents iterated out of sight instead of planning first.

Each skill's `description:` is loaded automatically and says when to use it.
This document covers what the descriptions cannot: the shape every skill
shares, the order they run in, and the lessons behind them.

## The skills

| Skill | Use for | Replaces |
|-------|---------|----------|
| `photo-to-vectors` | Reference images → qualified, anchored measurements and traced, reviewed SVG/DXF | perspective-checker, reference-analyst, vector-tracer, accuracy-reviewer |
| `cad-build` | Any geometry or macro change, including a fix pass on a register | cad-designer |
| `form-audit` | The real 3D form of a built mesh: QUESTION, REGISTER, REVIEW | form-auditor |
| `fdm-tolerance` | Clearances, structural sizing, print settings, with inputs reconciled | print-tolerance-expert |
| `scan-mesh` | Repairing scan/CT meshes; the Blender sculpt round trip | bone-morphologist, blender-handoff |
| `/verify` | Five-gate geometry verification of a part | — |
| `/round` | One bounded fix round: register → approval → fix → review | — |
| `/session-end` | Close a session: STATE.md, NEXT_SESSION.md, cost, memory proposals | — |

A skill is a folder, `.claude/skills/<name>/SKILL.md`. A bare
`.claude/skills/<name>.md` file is not loaded: `/verify` sat at
`.claude/skills/verify.md` and never appeared in the skill list until it was
moved (2026-09-24). Long material lives in the skill's `reference/` files and
is read by section, only when needed.

## Plan → run → report

Every working skill has the same three phases, in this order:

1. **Plan.** Nothing is measured, built or edited yet. The plan is written from
   the skill's `plan_template.md` into the project (`work/` or `audit/r<NN>/`)
   and shown in chat. It names the inputs, every step, the check that proves
   each step, and the ceilings as numbers. A field the plan cannot fill, or a
   contradiction with `STATE.md`, goes under *Questions before RUN*; the run
   starts only when that section says none.
2. **Run.** The plan, once. A step that is not in the plan needs a written
   amendment first (what, why, the number that forced it), at most one. Two
   failures on one step: leave it, report it with its numbers. No re-measuring
   to refine a number.
3. **Report.** A file in the project, and a short summary in chat, with the
   plain sentence first and the numbers after.

Why: the agent runs that iterated instead of planning. Of 29 form-auditor runs,
12 broke their own "one scratch script" rule (up to 9 scripts) and 11 wrote
nothing to their deliverable until 85 % of the run had passed; the r15
designer pass wrote 23 scripts in 298 tool calls (`tools/token_audit/
agent_behavior_check.py runs`, measured 2026-10-27).

**Ceilings stay numbers.** From the 2026-09-24 budget rules: of 36 agent runs,
the 19 briefs that named a number had a median of 42 tool calls and $1.76 mean
list price; the 17 without one had a median of 71 and $5.78. The same holds for
a plan: a plan without numeric ceilings is not run.

## The reference chain

For a photo-driven part:

```
photo-to-vectors   QUALIFY → MEASURE → TRACE → REVIEW
      ▼
cad-build          plan (with the arithmetic) → build → five gates
      ▼
form-audit         does the built form match the intent?
      ▼
fdm-tolerance      clearances, structural check (inputs reconciled)
```

Each stage consumes the previous stage's files (`docs/MEASUREMENTS.md`,
`vectors/`) rather than re-deriving its numbers.

### The vector stage is the one that gets skipped

TRACE and REVIEW are easy to walk past: a measurement table *feels* like enough
to start modelling, and build123d's primitives are right there. Both VitaGrip
projects skipped them.

- `VitaGrip-hori` traced a full `vectors/` set, then abandoned it when the
  approach changed. The files are still there, and its README has to explain why.
- `VitaGrip1000`'s first pass went straight from pixel measurements to
  `Rectangle(182, 83.55)` for a console whose outline is **not** a rectangle —
  it tapers ~40 mm at each end. The pocket cut 1232 mm² (8.8 %) more than the
  console occupies. Every topology gate passed; the user caught it by looking at
  the reference image.

The rule that would have caught both: **if a project has a `vectors/` folder,
some macro must `import_dxf()` from it.** A vectors folder nothing imports means
the stage was performed and then discarded — which is indistinguishable, from
the outside, from the stage having worked.

**That rule is necessary but not sufficient.** VitaGrip1000's first pass
*passed* it and was still wrong: it traced the **console** — the part the grip
fits *around* — imported that DXF, and then built the grip's own handles from
eyeballed photo pixels lofted through hand-typed stations. A hand-set
`HANDLE_RAKE = 5.9` deg came out of the build as **1.6 deg**, against a sketch
asking for a pronounced hook. Nothing caught it, because nothing was traced to
compare against.

**The part being designed must itself be traced. Importing a vector of a
mating part does not satisfy the stage.** Ask: *which curve in `vectors/`
is the shape I am authoring?* If the answer names only the thing it mounts
to, the stage has not run.

The same failure recurs inside a single script. VitaGrip1000's rebuild traced
the handle's depth from the drawing's side view, then **invented** its width as
`34 + 6*f` — and produced straight tapered slabs that passed every topology
gate. The front view had the real taper (13.5 → 39.9 mm) the whole time. A
traced contour for one axis does not license a guessed number for another.

`projects/VitaGrip1000/v0/macros/trace_console.py` (also in `v2/`) is the worked example: it traces
four orthographic views, gates each against its annotated dimension, checks the
rings are simple, and reports the protrusions the silhouette cannot show.
`vita_grip.py` then imports its DXF in `console_profile()`.

**For a scan-derived part**, `scan-mesh` (REPAIR) runs before `cad-build`: it
repairs the reconstructed mesh, then the builder turns it into a printable
model. Its plan starts from the parameters already swept and the approaches
already rejected — see BrokeFeet's README — or it re-walks them.

**When a mesh needs hand-sculpting**, `scan-mesh` (BLENDER) sits between the
pipeline and the human sculptor: it prepares the mesh, writes the `.blend`
file, and gates what comes back. See BrokeFeet's `v2/blender/` directory.

## A render is not a measurement

`form-audit` and the QUALIFY stage of `photo-to-vectors` both exist because of
one VitaGrip incident. An `iso` render was read as showing "flat slab handles";
direct measurement showed 40x35 mm volumetric handles matching their design
constants. The visual verdict was wrong, and acting on it would have rebuilt
correct geometry.

Switching that render to orthographic moved its silhouette aspect by 0.2% — the
projection was never the problem, the **viewing angle** was.

Run `form-audit` for a number before believing a picture, and QUALIFY a photo
before comparing a picture to it.

## Render a region, not the part

Numbers first. When a picture is still needed, draw only the region in question:

```
python tools/render_roi.py <stl> <out.png> --center X Y Z --size 40 [--views top under_a iso_a] [--ref <previous.stl>] [--px 400]
```

It clips the mesh to a box, renders 2-3 fixed angles onto one small sheet, and
prints the face count and bounds beside it. `--ref` adds a second row with the
previous bake, so a change reads side by side. Views: top, under, front, back,
left, right, iso_a, iso_b, under_a, under_b (`under_*` look from below and
behind, the corner views the user marks).

- **One sheet per question**, not a render after every build. Full views once
  per round, at the end: `render_check.py --views front` for the gate.
- **Drawing is not what costs.** Timed 2026-10-03 on a 137k-face part: one
  closeup 1.5 s, `render_check` 14 s, one macro build about 165 s. The cost is
  run length and context: VitaGripPS5 r14 designer 260 tool calls / 505k
  tokens, r15 designer 298 calls / 522k tokens / about 9 h wall-clock, r16
  designer (one switch, short brief) 36 calls / 114k tokens. Images were about
  4 % of the cost of the largest run (measured 2026-10-03).

## Report negative results

In this repo the most useful output has been a measured "this does not work,
and here is why", plus corrections to the task premise. Work aimed only at
success hands back a better metric attached to a worse model — see BrokeFeet's
`area/volume` vs `genus` history. Every skill's report has room for both.

## Rebuild only what changed

Since 2026-10-27, `tools/stage_cache.py` keys each part on its builder's
arguments, the source and constants of the modules it uses, and its input
files. An unchanged part loads from a cache and its files are not rewritten.
SurgicalDrillGuide is the reference: a one-constant change to the slider
rebuilt the slider only and wrote 5 of 16 files (it used to write all 16).
Previews go to a preview folder, never `stl/`. See
`projects/SurgicalDrillGuide/work/build_report.md`.

## Fix rounds: one register, one pass, one review

From VitaGripPS5, rounds 7-9 (2026-09-26 to 09-30). Each audit checked only
the windows its brief named. Each round fixed one defect and re-checked only
that one. The r7 audit found six defects. r8 fixed the crease and carried the
other five as "unchanged". The user's markup on r8 then found three more
(a junction notch, a flank scar, teeth along an edge) that no audit had swept.

The cycle (`/round`) is:

```
form-audit  REGISTER  sweep the whole part → one defect register, a fix proposed per entry
      ▼
user        approves the fixes (or picks, where entries conflict)
      ▼
cad-build   fixes every approved entry in one pass, reports per entry
      ▼
form-audit  REVIEW (fresh session): re-measures every entry + repeats the full sweep, one verdict
```

- The register keeps its IDs (D1, D2, ...) across rounds, so each entry's
  history can be read in one place.
- User markup goes into the audit plan. Every mark becomes an entry, located
  in model coordinates.
- Do not run a pass per defect, and do not re-audit between fixes. If the
  review leaves entries open, the next round is the same cycle, with the open
  entries plus any regressions.
- Inside an approved build the user's approval covers the fix pass. Conflicts
  that the audit flags still go to the user.
- **Plan the fix pass in priority order, with a fallback:** "if a ceiling is
  reached, stop at a valid mesh with P1-P2 done, and report the rest as not
  done". Every VitaGripPS5 pass from r10 to r12 ran out of budget, and needed
  one or two resumes.
- **Before reporting a pass to the user, look at the key render.** Twice the
  designer's "done" came with a corner the user would reject on sight.
- **The review judges the mesh, not the reasoning that built it:** it runs in a
  fresh session and copies no number from the fix report.
- **When rounds keep producing new defects on the same outline, stop tuning
  and replace the method** (`docs/lessons.md`, "Ten defect IDs were one
  glued-in patch"). **The trigger, as numbers:** a fix pass that creates 3 or
  more regression IDs, or a region in its third consecutive register, makes
  the review's verdict **METHOD REVIEW**: the next step is a method decision
  for the user, not another fix pass. Six of the eight VitaGripPS5 passes from
  r9 to r16 met the first condition, and nothing stopped the cycle.
- **A bake is a byte-identical copy of a checked preview into `stl/`,** made
  with the user's approval. Never overwrite an existing STL without asking:
  `stl/VitaGripPS5.stl` was an older design. Back up only the files the bake
  replaces.

## Testing the skills

`.claude/evals/skills_eval.md` holds 14 past incidents as requests, with the
inputs still on disk and objective pass lines. Run each case twice in a fresh
session, and after any edit to a skill. If a skill scores worse than the agent
it replaced, restore the agent from `.claude/agents-archive/`.

The subagent-era sections of this document (briefing fields, ceilings by role,
handoff and resume) are in git history before 2026-10-27.
