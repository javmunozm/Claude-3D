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

`projects/VitaGrip1000/macros/trace_console.py` is the worked example: it traces
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

## Skills

Invocable as slash commands:

| Skill | Use for |
|-------|---------|
| `/verify` | Five-gate geometry verification for a project part: regenerate → topology → shaded render → mating check → reference comparison |
