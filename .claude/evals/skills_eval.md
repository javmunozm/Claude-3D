# Skills eval: past incidents replayed

Written 2026-10-27 for the agents → skills migration. Each case is a request that once went wrong in this repo,
with the inputs still on disk and the result that would have caught the defect. Use it to compare a skill against
the agent it replaces, and to re-check a skill after any edit.

**How to run a case.** Start a fresh session (`/clear`). Paste the case's *Request* as written. Score against
*Pass* only; the *Trap* is for the scorer, not the prompt. Run each case **twice**: the Anthropic migration guide
saw a break in one of two runs only. Record both runs in the score sheet at the end.

**What counts.** A case passes when every *Pass* line holds in the run's plan or report. A run that reaches the right
number by a method the *Pass* forbids fails. "Plan" means the written plan (plan → run → report), before any
measurement or edit. Numbers carry their tolerance; a measurement that disagrees with an expected value marked
*(expected)* is a finding to report, not a fail, as long as the method lines hold.

Cases that change files (E10, E12) are marked **writes**: run them on a scratch copy or revert afterwards.

---

## photo-to-vectors

### E01 — the anchor is occluded
- **Request:** "Measure the PS Vita grip's width and height from `sources/VitaGripPs5/054-1.webp`, using the PS Vita (182 mm wide) as the scale."
- **Inputs:** `sources/VitaGripPs5/054-1.webp`, `sources/psvitaGrip/SOURCES.md`
- **Trap:** the grip wraps the console's lower corners; the median console span (514 px) is 30.4 % short of the exposed span (739 px). The old build took 0.2635 mm/px and shipped 237.9 × 119.8.
- **Pass:**
  1. The plan names two objects in the frame and says which one carries the 182 mm.
  2. The anchor is the maximum exposed row span (739 px ± 3), with the max-vs-median spread reported.
  3. Scale 0.2463 mm/px ± 0.5 %; grip 222.4 × 112.3 mm ± 1 %.
  4. It reads `SOURCES.md` and cross-checks against 223.3 / 222.6 mm there.
- **Source:** `docs/lessons.md`, "In an assembly, the anchor is usually not the subject".

### E02 — a 3/4 render read as a side view
- **Request:** "Take the bridge cross-section of the grip from this side view: `sources/VitaGripPs5/psvitarearbackside.webp`."
- **Inputs:** `sources/VitaGripPs5/psvitarearbackside.webp`
- **Trap:** it is a 3/4 CAD render. Read as orthographic it gave a round bar (`R_BRIDGE = 9.5`); the real print is a flat-bottomed C-channel.
- **Pass:**
  1. The image is classified before any measurement: not orthographic, not on-axis, a render.
  2. No cross-section dimension is taken from it; the report says which axes it cannot measure.
  3. It asks for, or names, a view that can show the section.
- **Source:** `docs/lessons.md`, "Correct dimensions do not make a correct shape"; memory "Perspective render is not a side view".

### E03 — which photo can measure X–Y
- **Request:** "Can I take X–Y dimensions from `sources/psvitaGrip/054-1.webp` and from `sources/psvitaGrip/020-1.webp`?"
- **Inputs:** `sources/psvitaGrip/054-1.webp`, `sources/psvitaGrip/020-1.webp`
- **Trap:** 020-1 is three-quarter and looks usable.
- **Pass:**
  1. An on-axis test with a number per image (mirror IoU: 054-1 ≈ 0.967, 020-1 ≈ 0.562, ± 0.02 *(expected)*).
  2. Verdict: 054-1 usable for X–Y; 020-1 shape reference only, "blind" on the axes it compresses.
- **Source:** `.claude/skills/verify/SKILL.md`, gate (e).

### E04 — a stated mechanism that was never re-run
- **Request:** "The VitaGripPS5 README says raising the mask's saturation floor from S>110 to S>150 gave the 237.9 mm grip width. Confirm it."
- **Inputs:** `sources/VitaGripPs5/054-1.webp`, `projects/VitaGripPS5/README.md`
- **Trap:** the README's story is plausible and the first half is true.
- **Pass:**
  1. It runs the sweep: S 110 / 150 / 180 / 200 → grip span 905 / 903 / 899 / 895 px (± 3 px *(expected)*).
  2. Conclusion: a 1.1 % change; no S floor produces 237.9 mm. The claim is reported as unsupported.
- **Source:** `docs/lessons.md`, "An explanation that was never tested against the mask".

### E05 — trace the part being designed, not only its mate
- **Request:** "Start a console pocket and the two handles for VitaGrip1000 from its reference drawing." (Plan only: stop after the plan.)
- **Inputs:** `projects/VitaGrip1000/v2/macros/trace_console.py`, `projects/VitaGrip1000/v2/macros/trace_grip.py`
- **Trap:** the first pass used `Rectangle(182, 83.55)` for a console that tapers about 40 mm at each end (overcut 1232 mm², 8.8 %), and later invented the handle width as `34 + 6*f`.
- **Pass:**
  1. The plan traces the console outline (not a rectangle) and the handles themselves, in every view that shows them.
  2. Every authored width/depth comes from a traced curve; none is a formula without a source.
  3. The vectors are checked against annotated dimensions before any geometry.
- **Source:** `docs/agents.md`, "The vector stage is the one that gets skipped".

---

## form-audit

### E06 — an open slit that passes topology
- **Request:** "Audit the rear corners of `projects/VitaGripPS5/audit/r10/case_preview_r10.stl`. Topology gates pass."
- **Inputs:** `projects/VitaGripPS5/audit/r10/case_preview_r10.stl`
- **Trap:** watertight, 1 body, genus 2 — and an open air slit 0.5–0.9 mm wide, 7–12 mm deep across each lobe back.
- **Pass:**
  1. The plan includes rays across boolean outlines / zone boundaries, written before running.
  2. The slit is found with width and depth in the stated range, and classified (open to the outside).
  3. One plain sentence: the corner is a block glued into a cut; entries on that outline are grouped as one boolean (replace the step).
- **Source:** `docs/lessons.md`, "Ten defect IDs were one glued-in patch".

### E07 — a watertight cutter full of tunnels
- **Request:** "Is `projects/VitaGripPS5/stl/console_solid.stl` fit to use as the socket cutter?"
- **Inputs:** `projects/VitaGripPS5/stl/console_solid.stl`
- **Trap:** `is_watertight` is True.
- **Pass:**
  1. Genus 50 and bbox fill 57.3 % (± 0.5) are reported; verdict: not fit.
  2. It names a fix for a cutter (convex hull or prism of the plan silhouette) and says the hull is wrong for a visible part.
- **Source:** `docs/lessons.md`, "`is_watertight` is not solidity".

### E08 — a wall measured on a section
- **Request:** "How thick is the wall between the end-stop pin hole and the rack's free end on `projects/SurgicalDrillGuide/stl/SurgicalDrillGuide_main_frame.stl`?"
- **Inputs:** `projects/SurgicalDrillGuide/stl/SurgicalDrillGuide_main_frame.stl`, `projects/SurgicalDrillGuide/macros/sdg_model/constants.py`
- **Trap:** a filter box read 0.56 mm too thick, ending on the wrong face.
- **Pass:**
  1. A planar section through the hole axis, the plane named; the witness point on the far surface printed.
  2. Value compared with `PIN_TIP_WALL` 3.0 *(expected)*; a disagreement is reported as a finding.
  3. Sampled toward the edge until the value stops changing.
- **Source:** `docs/lessons.md`, "A filter box read a wall 0.56 mm thicker".

---

## cad-build

### E09 — the arithmetic says it cannot seat
- **Request:** "On SurgicalDrillGuide, make the handle's Ø16 core seat against the head's Ø16.85 mouth." (Plan only.)
- **Inputs:** `projects/SurgicalDrillGuide/STATE.md`
- **Trap:** round 4 existed only because a Ø16 core cannot bear on a Ø16.85 mouth.
- **Pass:**
  1. The plan's arithmetic shows a 0.425 mm radial gap and no bearing surface, before any edit or build.
  2. Builds used: 0. The plan ends in a question or a proposed seat, not a build.
- **Source:** `.claude/skills/cad-build/reference/gates.md`, "Before you build: run the arithmetic".

### E10 — change one part, touch nothing else (**writes**)
- **Request:** "Set `CARRIAGE_FLOOR` to 2.6 on SurgicalDrillGuide and show me." Revert afterwards.
- **Inputs:** `projects/SurgicalDrillGuide/macros/surgical_drill_guide.py`, `tools/stage_cache.py`
- **Trap:** the old pipeline rewrote all 16 files and wrote straight into `stl/`.
- **Pass:**
  1. The build goes to a preview folder (`SDG_OUT_DIR`), not `stl/`; `stl/` mtimes unchanged.
  2. The build's line reads `rebuilt ['l_arm_slider']`; 5 of 16 files written.
  3. Gates run on the preview, report included.
- **Source:** `projects/SurgicalDrillGuide/work/build_report.md`.

---

## fdm-tolerance

### E11 — a marginal wall under load
- **Request:** "Is the 1.8 mm wall over the SurgicalDrillGuide shoe's screw hole strong enough at the 500 N clamp?"
- **Inputs:** `projects/SurgicalDrillGuide/STATE.md`, `projects/SurgicalDrillGuide/docs/mechanism_sizing.py`
- **Trap:** the pass is marginal and its Kt is not applied. The 3.02 is the r8 figure in `STATE.md`; `mechanism_sizing.py` already carries r9 changes (`SHOE_ROOF` 6.0, a roof hole), so the r9 number may differ — a run should notice and say which design it checked.
- **Pass:**
  1. It runs `mechanism_sizing.py` (or reproduces its row) and reports SF ≈ 3.02 *(expected)* at 500 N, PETG assumed.
  2. It states that Kt at the hole is not applied, and what SF would be with a stated Kt.
  3. Any fix is material (thicker wall, fillet, material); never "add supports" or "cut the part" as a fix.
- **Source:** `STATE.md` row 1C-i; memory "Supports are the slicer's job".

### E12 — a placeholder clearance (**writes** if approved)
- **Request:** "`SHOE_CLEAR_X` is still a PLACEHOLDER at 0.20. Set it."
- **Inputs:** `projects/SurgicalDrillGuide/macros/sdg_model/constants.py`
- **Trap:** inventing a number, or changing it without reconciling the checks that use it.
- **Pass:**
  1. The value comes with its basis (printer, material, orientation of the mating faces) and a test coupon or measurement to confirm it.
  2. It lists what the change touches (`parameters.py` pocket → slider and shoe rebuild) and re-runs the sizing reconcile.
  3. It asks before editing the constant.
- **Source:** `constants.py:141`; `docs/agents.md`, roles of print-tolerance-expert.

---

## scan-mesh

### E13 — a falling genus that means fused bones
- **Request:** "The BrokeFeet hindfoot still has holes. Repair `projects/BrokeFeet/v2/stl/BrokeFeetV2_pinned2.stl`." (Plan only.)
- **Inputs:** `projects/BrokeFeet/v2/stl/BrokeFeetV2_pinned2.stl`, `projects/BrokeFeet/v2/README.md`
- **Trap:** voxel remesh is a recorded negative; a lower genus with a higher volume means joints welded, not holes fixed.
- **Pass:**
  1. The plan measures first: genus, open edges, bodies, volume; and classifies each defect (tunnel, crater, terracing) with its number.
  2. Genus and volume are gated together: falling genus with rising volume fails as fusion.
  3. It does not propose a voxel remesh, citing the README's measured negative.
- **Source:** `projects/BrokeFeet/v2/README.md` lines 85–90, 377–384; memory "Tunnels not cavities", "Craters vs tunnels".

### E14 — did the sculpt change anything
- **Request:** "Did the Blender sculpt change the mesh? Compare `projects/BrokeFeet/v2/blender/BrokeFeetV2_sculpt.stl` with `projects/BrokeFeet/v2/stl/BrokeFeetV2_pinned2.stl`."
- **Inputs:** `projects/BrokeFeet/v2/blender/BrokeFeetV2_sculpt.stl`, `projects/BrokeFeet/v2/stl/BrokeFeetV2_pinned2.stl`
- **Trap:** without Dyntopo, vertex/face counts, bbox and centroid stay identical after a sculpt.
- **Pass:**
  1. It compares raw vertex positions (per-vertex displacement: count moved, max, p99), not counts or bbox.
  2. It states where the change is (region or coordinates) if any.
- **Source:** memory "Sculpt invisible to counts".

---

## Score sheet

| Case | Skill | Run 1 | Run 2 | Tool calls (1 / 2) | Notes |
|------|-------|-------|-------|--------------------|-------|
| E01 | photo-to-vectors | | | | |
| E02 | photo-to-vectors | | | | |
| E03 | photo-to-vectors | | | | |
| E04 | photo-to-vectors | | | | |
| E05 | photo-to-vectors | | | | |
| E06 | form-audit | | | | |
| E07 | form-audit | | | | |
| E08 | form-audit | | | | |
| E09 | cad-build | | | | |
| E10 | cad-build | | | | |
| E11 | fdm-tolerance | | | | |
| E12 | fdm-tolerance | | | | |
| E13 | scan-mesh | | | | |
| E14 | scan-mesh | | | | |

## Field use (real passes run with the skills, not eval cases)

| Date | Project / pass | Skill | User's verdict | Measured | Notes |
|------|----------------|-------|----------------|----------|-------|
| 2026-10-27 | VitaGripPS5 v2 / cove (A1, A2) | cad-build | "it's WAY faster than before"; "ok, its working" (A2) | Build to export 61–65 s per run; full macro gates 437 s more (499 s total, background) | User, from memory: under the agents a build alone took about 5 min, with form-auditor running in the background and agents messaging each other (not measured here; STATE.md gave 70–150 s for the latch macro). Two user corrections were needed: build 1 left a thin fin past the wall (→ A1), A1 cut the strip too short (→ A2). A2 went one amendment over the skill's ceiling, by the user's choice. The arithmetic step caught a wrong option of mine ("step around the slot" = 0.04 mm edge) before any build. |
