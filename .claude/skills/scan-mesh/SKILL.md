---
name: scan-mesh
description: Work on scan- or CT-derived meshes — repairing segmentation artefacts in reconstructed bone (sponge interiors, perforations, craters, terracing) without fusing joints or touching real anatomy, and the Blender sculpt round trip (prepare a mesh for hand-sculpting, import it back, detect whether sculpting happened, smooth without reopening fills). Measures and classifies every defect first, gates genus and volume together, writes a plan first, runs it once, reports. Use for any repair, smoothing, remesh or Blender handoff of a scanned or reconstructed mesh. Not for authoring new parts (cad-build) or tolerances (fdm-tolerance).
---

# scan-mesh

Two modes on the same kind of mesh:
- **REPAIR** — close holes that anatomy says should not be there, and leave
  every real space (joints, cortical boundaries, deformity) untouched
  (`reference/bone-repair.md`).
- **BLENDER** — prepare a mesh for the human sculptor, and gate what comes
  back (`reference/blender.md`).

**Better global numbers are not the goal.** On BrokeFeet, a seal radius of 8
gave a better sponge number (area/volume 0.353) and a strictly worse model,
every joint smoothed away; radius 5 collapsed the foot into one 98 cm³ mass.
Every defect in that project passed the numeric gates and was caught by
looking.

Three phases, always in this order: **PLAN → RUN → REPORT**. Nothing is
filled, smoothed, remeshed or exported before the plan is written and shown.

## 1. PLAN (measure, change nothing)

Read the project's README sections on rejected approaches first (for
BrokeFeet, `projects/BrokeFeet/README.md`, `v0/README.md`, `v2/README.md`):
most obvious ideas here were tested and failed for recorded reasons.

Measure the mesh as it is, then write the plan from `plan_template.md` (this
folder) to `projects/<Project>/work/plan_mesh.md` and show it in chat:
- **Baseline:** watertight, bodies, genus, volume, open edges, area/volume
  **per band** (not only global), and for a CT mesh the number of
  distinguishable bodies before bridging (the joint-preservation metric).
- **Every defect classified, with the number that decides it:** tunnel
  (raises genus), crater (surface pit, open or closed), terracing (sub-0.5 mm
  voxel steps), sponge interior, or **real** (joint space, cortical boundary,
  deformity: never modified). For CT, the intensity evidence from the
  de-identified panes.
- **The operation, localised:** per bone or per named region, never a global
  parameter. The method, and why the rejected ones are not it.
- **The predicted cost:** which joints are at risk, the body count and genus
  expected after, the volume change expected.
- **The gates, in order**, with their thresholds (below).
- For BLENDER: the transform (recentre only, 1 unit = 1 mm), Dyntopo detail,
  symmetry off, and what the sculptor should and should not touch.

## 2. RUN (the plan, once)

- Apply the operation to the named regions only.
- **Gates, together, not one at a time:**
  - watertight and body count (hard);
  - genus **and** volume read as a pair: **falling genus with rising volume
    is the fusion signature** (bones welded), not a repair;
  - bodies before bridging not reduced;
  - per-band area/volume, before and after;
  - the project's cross-validation (BrokeFeet: adduction and plantar RMS must
    not degrade, 1.34 / 0.30 mm);
  - for smoothing: inward travel along the vertex normal, at most 0.5 mm on
    any filled site;
  - for a sculpt import: the raw-triangle diff (count changed, max
    displacement, clustered sites).
- **Look at the renders** of the changed regions before reporting.
- **Nothing outside the plan** without a written amendment (at most one). A
  fill that would cross a joint or the coalition: stop and say so. **Two
  failures** on one region → leave it, report it with its numbers.

## 3. REPORT

In `work/mesh_report.md`, then in chat, at most 25 lines: the regions changed,
the evidence for each, the gate table before → after (per band), body count
before bridging, any joint you suspect narrowed, and what is not done. For
BLENDER, the files handed over (`.blend`, backup `.stl`, `TRANSFORM.json`),
the operator instructions, and on import the sculpted sites.

## Reference

| File | Holds |
|---|---|
| `reference/bone-repair.md` | Artefact vs anatomy table, the seal-radius cliff, closing and median filtering (rejected), where the damage is, how to work, reporting |
| `reference/blender.md` | The three measured failure modes (metre scaling, invisible sculpts, smoothing that reopens craters), the voxel-remesh table, prep and import steps, headless Blender, the handoff contents |

## Rules

- **No voxel remesh** of a mesh with thin interosseous tunnels or walls: at
  every pitch tested it closed 42–55 tunnels, and volume moved under 0.02 %.
  Genus is the gate. Ship original triangles; Dyntopo, or a masked remesh.
- No morphological closing (welded the midfoot into 66 cm³) and no median
  filtering (21 → 92–133 components) on the mask.
- Never conclude "unchanged" from vertex/face counts, bbox or centroid: a
  sculpt without Dyntopo changes none of them (30 448 triangles had moved,
  up to 7.13 mm). When the user says they sculpted, believe them and diff.
- Smooth only with the outward-normal clamp: plain Taubin reopened
  hand-filled craters (304 verts past 0.5 mm, worst −3.61 mm).
- Never scale a sculpt file to metres (Dyntopo silently did nothing).
- Real deformity is the point of a teaching model: never modify it.
- **Mesh gates must be rebuilt for the mesh they test:** voxel gates cannot
  run after meshing; a single-axis ray cast read a mortise 2.5× wrong.

## Session rules

- **Write as you go.** Each finished result goes into the deliverable when you
  have it. If the session must end mid-run, write `work/handoff.md`
  (`docs/templates/handoff.md`: done / not done / files / next step); the next
  session starts from the plan plus the handoff.
- **Two failures, then stop** that approach: report what failed, with its
  numbers, and what you would try next.
- **One scratch script, edited,** printing at most about 50 lines.
- **Images confirm, they do not search.** Measure numerically; look once at a
  cropped region.
- **Read only what you need.** Grep long docs and the README by section. Never
  `Glob` `**/*`.
- **Parallel calls.** Put independent reads and checks in one response.
- **Scripts and builds** run in the foreground with `timeout 300 python …` in
  the Bash tool (in PowerShell `timeout` is a different command). Anything over
  5 minutes is a defect to report, not something to wait out.
- **Shell.** One command per call, absolute paths, no `cd`, no `python -c`, no
  `sleep` loops; view files with Read / Glob / Grep. A hook denies the rest and
  says how to rewrite it.
