# Agents and skills

Delegation surfaces for this repo: project-level subagents in `.claude/agents/`
and skills in `.claude/skills/`, both tailored to the build123d/FDM-printing
workflow.

Each agent's own `description:` frontmatter is loaded automatically and states
when to use it and what it is *not* for. This document covers what that
frontmatter cannot: the order they hand off in, and the lessons that made
several of them exist.

## The agents

| Agent | Use for |
|-------|---------|
| `reference-analyst` | Turning reference photos/specs into a dimensioned measurement table with per-value confidence |
| `cad-designer` | Authoring/revising build123d geometry scripts, part fit and assembly |
| `print-tolerance-expert` | Fit clearances, structural sizing (stress/buckling/safety factor), print settings |
| `bone-morphologist` | Repairing CT-derived skeletal meshes — porous or perforated bone that is a segmentation artefact, not anatomy |
| `blender-handoff` | Preparing meshes for Blender sculpting and importing sculpted results back — prep scripts, sculpt detection, smoothing gates |
| `vector-tracer` | Generating SVG/DXF vector files from reference images using vtracer/cv2+scipy pipeline |
| `accuracy-reviewer` | Evaluating accuracy of generated vector files against reference images and known dimensions |
| `form-auditor` | Auditing the real 3D form of a built mesh — cross-sections, taper, volumetric vs flat, built-vs-intended |
| `perspective-checker` | Deciding whether a photo and a render are comparable at all — on-axis test, which axes a view can and cannot measure |

## Handoff order

Typical flow for a photo-driven part:

```
perspective-checker  (is this photo usable, and for which axes?)
      ▼
reference-analyst    (measure)
      ▼
vector-tracer        (vectorize reference views)
      ▼
accuracy-reviewer    (verify the vectors)
      ▼
cad-designer         (build + verify)
      ▼
form-auditor         (does the built form match intent?)
      ▼
print-tolerance-expert  (tolerances, structural check)
```

Each stage hands off explicitly rather than re-deriving the previous stage's
numbers.

### The vector stage is the one that gets skipped

`vector-tracer` and `accuracy-reviewer` are easy to walk past: a measurement
table *feels* like enough to start modelling, and build123d's primitives are
right there. Both VitaGrip projects skipped them.

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

**For a scan-derived part**, `bone-morphologist` sits before `cad-designer`: it
repairs the reconstructed mesh, then the builder turns it into a printable
model. Give it the parameters already swept and the approaches already
rejected — see BrokeFeet's README — or it will re-walk them.

**When a mesh needs hand-sculpting**, `blender-handoff` sits between
`bone-morphologist` (or `cad-designer`) and the human sculptor: it prepares the
mesh, writes the `.blend` file, and gates what comes back. See BrokeFeet's
`v2/blender/` directory for the established workflow.

## A render is not a measurement

`form-auditor` and `perspective-checker` both exist because of one VitaGrip
incident. An `iso` render was read as showing "flat slab handles"; direct
measurement showed 40x35 mm volumetric handles matching their design constants.
The visual verdict was wrong, and acting on it would have rebuilt correct
geometry.

Switching that render to orthographic moved its silhouette aspect by 0.2% — the
projection was never the problem, the **viewing angle** was.

Ask `form-auditor` for a number before believing a picture, and
`perspective-checker` before comparing a picture to a photo.

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
  agent length and context: VitaGripPS5 r14 designer 260 tool calls / 505k
  tokens, r15 designer 298 calls / 522k tokens / about 9 h wall-clock, r16
  designer (one switch, short brief) 36 calls / 114k tokens. Images were about
  4 % of the cost of the largest run (`system_improvement/03_token_economics.md`).
- **Every fix-pass brief states a ceiling in builds and in tool calls** (the
  r14-r16 briefs named "stop at a valid mesh" but no call ceiling). Suggested:
  4 builds, and the harness-count ceiling from "Briefing agents" below. At the
  ceiling the agent stops at its last valid mesh and reports what is not done.

## Brief agents to report negative results

In this repo the most useful agent output has been a measured "this does not
work, and here is why", plus corrections to the task premise. An agent briefed
only to succeed will hand back a better metric attached to a worse model — see
BrokeFeet's `area/volume` vs `genus` history.

## Briefing agents: budget, deliverable, fresh fix rounds

From the 2026-09-23 audit of 17 runs:

- **Every brief carries a budget** ("about N tool calls, stop at M") and names
  the file the results go in. The four SurgicalDrillGuide v2 runs briefed with
  no budget took 94–169 calls and 8–24M tokens each. The ones briefed with a
  budget took 9–25 calls.
- **Put the facts the agent needs in the brief**, with pointers to sections,
  so it does not have to read whole docs to find them.
- **A fix round goes to a new agent with a short brief**: what changed, what to
  fix, which files. Do not send it to the finished agent with `SendMessage`.
  That agent carries its whole history: cad-designer's two fix rounds started
  from a 318k context and ended at 474k, while a new agent starts at about 20k.
- **Budget from the harness count, with margin** (SurgicalDrillGuide, 2026-09-24).
  Agents undercount their own calls by up to about 25 %: 24 against 30, 34
  against 44, 33 against 38. The last run overran its hard stop. Set the hard
  stop at the true ceiling and expect about 80 % of it to be used.
- **After an agent reports a build, re-run the build and gates yourself** before
  the next agent relies on the files. The pipeline takes about 1 minute. On
  round 4 this caught a macro edited after its exports were written.
- Every agent definition has a `## Budget and stopping` section (write as you
  go, two failures then stop, one scratch script, limited image reads).
- **Ceilings are enforced** (2026-10-04). Each agent's frontmatter sets
  `maxTurns`, the hard stop, and `effort: high`. `maxTurns` counts turns (model
  responses), not tool calls. The hook `.claude/hooks/budget_nudge.py` counts
  each agent's turns from its transcript: at 80 % of `maxTurns` it asks for the
  deliverable and `handoff.md`, and from `maxTurns − 3` it asks the agent to
  return. Without a `maxTurns` or a transcript it falls back to the tool-call
  counts in `.claude/hooks/budgets.json`. The hook
  `.claude/hooks/shell_guard.py` denies commands that break the shell rules,
  with the reason.

Measured on the 36 agent runs made after the budget rules were committed
(2026-09-24): the 19 briefs that named a number had a median of 42 tool calls
and $1.76 mean list price; the 17 without one had a median of 71 and $5.78.
Details: `system_improvement/02_briefing.md`.

### Required fields

Templates: `docs/templates/brief_fix_pass.md`, `brief_review.md`,
`handoff.md`, `review_summary.md`. A brief with an empty field is not sent.

1. **Task.** One paragraph, including what the result is for.
2. **Inputs, by path.** The facts the agent needs go in the brief itself. Point
   to sections, not to whole documents.
3. **Deliverable.** The file path. Written as the agent goes, with the summary
   block first.
4. **Ceilings, as numbers:** turns (the agent's `maxTurns`, or lower; the hook
   reminds at 80 % of `maxTurns` and from `maxTurns − 3`, so a lower number is
   the agent's to watch); builds; images.
5. **Priority list,** with a fallback: "stop at the last state that passes the
   hard gates, with items 1–k done".
6. **Stop rule.** At about 80 % of a ceiling, write `handoff.md` and return.
7. **What not to touch.** Locks, other rounds' folders, `stl/`.
8. **Report format.** A plain sentence per changed region first, then the
   numbers. Negative results and corrections to the premise are wanted. Tool
   calls by the harness count.

### Ceilings by role

A **turn** is one model response, which can carry several tool calls (the r9
designer made 51 turns and 109 tool calls). Parallel calls in one response
share one API request (measured 2026-10-04), so they do not use up the budget.
Each limit sits above the longest past run whose brief set a number
(`agent_behavior_check.py runs`), so bounded work finishes; every run a limit
would have cut had no number in its brief (reviewed 2026-10-04).

| Role | Turns (hard) | Builds | Images | Basis (turns / tool calls, list price) |
|---|---|---|---|---|
| cad-designer, fix pass | 60 | 4 | 6 | r9 pass 51 / 109 ($5.12); SurgicalDrillGuide r4 40 / 63 ($2.64), r5 27 / 38 ($1.08) |
| cad-designer, one change | 25 (set in the brief) | 2 | 2 | r16 18 / 36 ($0.62) |
| form-auditor, register | 45 | 0 | 4 | r9 28 / 46 ($1.80); r14 35 / 66 ($2.73) |
| form-auditor, review | 45 | 1 | 3 | r9 32 / 49 ($2.54); unbounded r10–r16 reviews 38–54 / 63–78 |
| reference-analyst | 45 | 0 | 8 | no run with a numeric brief; r11 shoulder buttons 37 / 53 ($1.62), which a limit of 40 would warn on turn 32 |
| perspective-checker | 25 | 0 | 8 | VitaGripPS5 classification 9 / 14 ($0.44) |
| print-tolerance-expert | 30 | 0 | 0 | 7–36 / 11–42 |
| vector-tracer | 50 | 0 | 8 | one unbounded run: 83 / 168 ($8.09) |
| accuracy-reviewer | 35 | 0 | 8 | re-review 14 / 17 ($1.03) |
| bone-morphologist, blender-handoff | 40 | — | 6 | no runs in the transcripts |

**If a task cannot fit, split it.** Late turns cost more than early ones,
because every call re-sends the growing context. In the seven designer runs
over 60 turns, splitting each at turn 60 would have saved $16 of $90 (18 %;
$0.17 to $5.14 per run). A fresh agent's first 5 turns cost about $0.30.

### Handoff and resume

- An agent that stops early writes `handoff.md` (`docs/templates/handoff.md`):
  why it stopped, tool calls used, what is done and verified, what is not and
  why, the current files and whether they pass the hard gates, the next step.
- A fresh agent gets the same brief plus "continue from `<path>/handoff.md`".
- `SendMessage` is only for answering a question from an agent that is still
  running. After a usage-limit stop, start a new agent from the handoff.

## Fix rounds: one register, one pass, one review

From VitaGripPS5, rounds 7-9 (2026-09-26 to 09-30). Each audit checked only
the windows its brief named. Each round fixed one defect and re-checked only
that one. The r7 audit found six defects. r8 fixed the crease and carried the
other five as "unchanged". The user's markup on r8 then found three more
(a junction notch, a flank scar, teeth along an edge) that no audit had swept.

The cycle is:

```
form-auditor   sweep the whole part → one defect register, a fix proposed per entry
      ▼
user           approves the fixes (or picks, where entries conflict)
      ▼
cad-designer   fixes every approved entry in one pass, reports per entry
      ▼
form-auditor   review mode: re-measures every entry + repeats the full sweep, one verdict
```

- The register keeps its IDs (D1, D2, ...) across rounds, so each entry's
  history can be read in one place.
- User markup goes into the auditor's brief. Every mark becomes an entry,
  located in model coordinates.
- Do not launch an agent per defect, and do not re-audit between fixes. If the
  review leaves entries open, the next round is the same cycle, with the open
  entries plus any regressions.
- Inside an approved build the user's approval covers the fix pass. Conflicts
  that the auditor flags still go to the user.
- **Brief the fix pass in priority order, with a fallback:** "if the budget
  runs short, stop at a valid mesh with P1-P2 done, and report the rest as
  not done". Every VitaGripPS5 pass from r10 to r12 ran out of budget, and
  needed one or two resumes.
- **Before reporting a pass to the user, the orchestrator looks at the key
  render itself.** Twice the designer's "done" came with a corner the user
  would reject on sight.
- **A whole-part review copies the previous scripts into its own
  `audit/rNN/` and retargets every path before the first run.** In r11 a
  stale path overwrote two r10 logs.
- **When rounds keep producing new defects on the same outline, stop tuning
  and replace the method** (`docs/lessons.md`, "Ten defect IDs were one
  glued-in patch"). **The trigger, as numbers:** a fix pass that creates 3 or
  more regression IDs, or a region in its third consecutive register, makes
  the review's verdict **METHOD REVIEW**: the next step is a method decision
  for the user, not another fix pass. Six of the eight VitaGripPS5 passes from
  r9 to r16 met the first condition, and nothing stopped the cycle.
- **A bake is a byte-identical copy of a checked preview into `stl/`,** made
  by the orchestrator with the user's approval. Never overwrite an existing
  STL without asking: `stl/VitaGripPS5.stl` was an older design.

## Skills

Invocable as slash commands. Each skill is a folder,
`.claude/skills/<name>/SKILL.md`. A bare `.claude/skills/<name>.md` file is
not loaded: `/verify` sat at `.claude/skills/verify.md` and never appeared in
the skill list until it was moved (2026-09-24).

| Skill | Use for |
|-------|---------|
| `/verify` | Five-gate geometry verification for a project part: regenerate → topology → form render → mating check → reference comparison |
| `/round` | One bounded fix round from the project's `STATE.md`: `status`, `register`, `fix`, `review`, with the brief templates, numeric ceilings, handoffs and the method-change trigger (`docs/workflow.md`) |
| `/session-end` | Close a session on a project: update `STATE.md` and `NEXT_SESSION.md`, record the cost, list uncommitted system files, propose memory edits for approval |
