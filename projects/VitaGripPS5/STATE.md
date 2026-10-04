# VitaGripPS5: STATE

Updated: 2026-10-04, by the system-improvement session (Phase 3a), from
`NEXT_SESSION.md`, the README section "Rounds 14-16" and
`audit/r16/review/review_r16.md`.

Keep this file under about 150 lines. Agents read it instead of the README. History, rejected approaches and narrative stay in the README.

## Current
- **Bake:** `stl/VitaGripPS5_case_r16.stl` (SHA-256 `4AAF87F76AA7D209BA65E94D897353BE9EDAB277F8B6BDF9FD2477FDEFAE12EF`), a byte copy of `audit/r16/case_preview_r16.stl`. Review: `audit/r16/review/review_r16.md`, **ACCEPT WITH LISTED ARTIFACTS**.
- **Kept on purpose:** `stl/VitaGripPS5_case_r13.stl` (the previous bake, SHA-256 `56141B26...`) and `stl/VitaGripPS5.stl` (the 2026-09-14 socket grip, not this case).
- **Working preview:** none; the bake is current.
- **Macro:** `macros/build_case_ext.py`, one file of 216.9 KB, docstring "round 16". Switches `FINISH_ON`, `RIM_CUT_ON = False`, `BAR_CUT_ON`, `D19_ON = False`; flag `--no-bar`. Over 60 KB: split it into stage modules before its next change (`docs/architecture.md`).
- **Method:** a mesh pipeline on the DualSense scan (numpy and trimesh), not B-rep. Fillets cannot be made on this mesh. Whether to rebuild as B-rep (v2) is decided after the print.
- **The part:** X width 220.08; Y fore-aft from the handle tips at -68.0025 to the rear at +78.550; Z up, pocket floor -8.80, flat top 11.40. 137 216 faces, watertight, 1 body, genus 2, volume 266 520.9 mm3.

## Open entries
From the r16 register; IDs kept across rounds. Thresholds: turn 8 deg, bump 0.3, tooth 0.3, wall 3.0, back 3.5, symmetry 1.0 mm, folds >= 150 deg; layer 0.15-0.2, nozzle 0.4.

| ID | Region (x, y, z) | Number vs threshold | Class | Status | Decision |
|----|------------------|---------------------|-------|--------|----------|
| D48 | R rim, x 84-110, y 60-76, z -10.5..-11.5 | outline p-p > 0.2 over 4.6 mm (L 2.9), max 0.40 / 0.48 | user mark M1a/M2d | unchanged | left in; needs a new rim method |
| D52 | corner rim R vs L, y 64-72 | R - L +0.93..+1.70 at z -11.5; +2.25 at y 70, z -10 | user mark | not fixed | left in (scan asymmetry); fix only if the user asks for symmetry |
| D50 | rim top crest, x 80-97, y 66-76 | crest turn median 92 R / 96 L; r about 0.5-0.9 | user mark | not fixed | left in |
| D19/D16/D2 | R lobe crease (84.5, 58.5) | turn 25.0 deg against 8 | brief | unchanged | left in; smoothing moved the slit lip 0.339, so `D19_ON = False` |
| D51 | bar rear-bottom edge, abs(x) <= 66 | 0.5 mm bevel over 94-97 %; end kinks 37 / 52 deg | user mark M1c | improved | accepted (bar-roll-ON variant) |
| D60 | rear-face jog, x 56.2-66.4 | steps 0.15 / 0.26 at x 56.0 | brief | improved | left in (about 2-3 layers) |
| D39 | rim top films, x 84-101, y 58-78 | 167 R / 156 L columns under 0.4 mm | sweep | slightly worse than r13 | left in (the slicer drops them) |
| D40 | underside, y 52.6-54.3 | ridge 0.10-0.14 | carried | under a layer | left in |
| D44 | bottom-opening edges | not rolled (r 0.5) | carried | sharp edge | left in |
| D64 | bevel taper ends, abs(x) 66-78 | lumps 0.15-0.2 | regression r16 | open, sub-layer | accept (thicker by 0.1-0.2) |
| D65 | D40 L zone (-62.7, 53.6, -15.1) | ridge 0.10; micro-creases under 0.1 high | regression r16 | open, sub-nozzle | accept |
| D66 | about a dozen spots, e.g. (-104.8, 10.1, 10.4) | vertex moves up to 0.226 | regression r16 | open, <= 1 layer | accept, or cap the collapse travel at 0.1 |
| D61/D62 | bevel band | folds 43, slivers 422 | sweep | measured harmless | none |
| D43, D46, D53, D54, D38, D25, D28, D30, D31 | carried from r12-r13 | see `audit/r12/review_r12.md` | carried | unchanged | left in |

Not swept in r16: D38, the fillet families D27/D28/D31/D32, the groove at y -9.2, D44's roll radius, the handle-tip render. Accepted by the user: the squared corner wall (D41); D3, D8 L (about 4.75), D18; the left handle as scanned; the bottom-opening ends at 66.75 / 68.75.

**Do not retry without a new method:** a cut of the rim (r14's prism cut left a cliff and altered the L wall) or a mirror of it (r15's mirrored-L rim left a lens-shaped scoop on the R flank).

## Locks (must not move)
| Lock | Tolerance | Why |
|------|-----------|-----|
| Flat top, Z 11.4000 | 0.0024 | the top plane the console sits 1.40 below |
| Pocket walls and floor (z -8.80) | 0.005 walls, < 0.02 floor | the console's fit |
| Lips and fingers, lip u at Z 9.30 / 9.47 / 9.80 / 10.20 / 11.00 = -0.00 / -1.49 / -1.30 / -1.06 / -0.60 | 0.005 | snap retention (`audit/r11/lip_sizing_r11.md`) |
| Pit walls, Z 0..10.2 (L 3.97..3.38, R 3.99..3.43) | 0.01 | wall thickness |
| Window and camera hole (+2 mm each) | 0.005 | the console's rear window and camera |
| Bottom-bar strip, abs(x) < 62, y -12..-8.5 | 0.005 | |
| Handle girth, y -20..-63.3 | 0.3 mm2 per section | hand fit |
| Handle tips: flat face at y -68.0025, 3.0 mm roll | as built | the user's trim, 2026-10-02 |

## Gates
- **Hard:**
  - watertight, winding consistent, 1 body, genus 2;
  - back >= 3.5 mm on a 0.05 mm window (r16: 3.5256 at (-65.05, -8.70)); walls >= 3.0;
  - max z 11.4000;
  - no sealed voids and no enclosed slits (ray tests over the rear band and the rim corners).
- **Surface bar,** agreed with the user on 2026-10-04:
  - on surfaces meant to be smooth: turn under 8° between neighbouring 0.5 mm sections, bump under 0.3 mm against a smoothed copy, edge tooth under 0.3 mm;
  - anything under 0.1 mm (below a print layer) is reported, not registered, unless the user marks it;
  - every user mark is classified by measurement (geometry / designed edge not rounded / tessellation / not reproducible), not by how a render looks. Measured 2026-10-04: on this scan mesh no render separates tessellation marks from real defects (`tools/render_review.py` on r13: M1d and M2b still render above D50 L, D48 L, D51 R), because the marks are real facet edges under 0.11 mm.
- **Review cameras** (agreed 2026-10-04): R corner, position (190, 150, -90), target (90, 65, -12), fov 30 (silhouette IoU 0.997); its L mirror, (-190, 150, -90) -> (-90, 65, -12); back__iso, `render_views.py` iso of the copy turned 180 deg about X (IoU 0.990); front top, `render_views.py` top.

## Commands
- **Build** (about 165 s): `timeout 600 python "D:/CAD/Claude-Projects/projects/VitaGripPS5/macros/build_case_ext.py" --out <path>.stl`. `--out` may not point into `stl/`.
- **Gates:** `python "D:/CAD/Claude-Projects/projects/VitaGripPS5/audit/r15/scripts/check15.py" <stl> [<baseline stl> | -] [heavy]`, then `python D:/CAD/Claude-Projects/tools/render_check.py <stl> --views front`.
- **Sweep** (about 8 s for r16; measured 2026-10-04): `python D:/CAD/Claude-Projects/tools/form_sweep.py <stl> --regions "D:/CAD/Claude-Projects/projects/VitaGripPS5/audit/regions.json" --out <audit/rNN/sweep> --tag rNN --baseline "D:/CAD/Claude-Projects/projects/VitaGripPS5/audit/r16/sweep/sweep_r16.json"`.
  - **Baseline:** `audit/r16/sweep/sweep_r16.json`, the sweep of the baked r16 mesh. It reproduces the r16 review's `sweep_r16.log` line for line.
  - `audit/regions.json` comes from `macros/export_sweep_regions.py`; re-export it after any change to the pocket, fingers, pits, window or camera hole.
  - Checks specific to one defect stay in the round's own `scripts/`; `audit/r16/review/scripts/` holds the last ones (rim, roll, films, slits).
- **Region render:** `python D:/CAD/Claude-Projects/tools/render_roi.py <stl> <out.png> --center X Y Z --size 40`.
- **Corner closeups:** `python <audit/r9/closeup.py> <stl> <png> 90 65 -12 190 150 -90` (R); `-90 65 -12 -190 150 -90` (L).
- **Locating a user mark:** ray-cast through the red pixels with the render's camera, after validating the camera by silhouette IoU. Use VTK's OBBTree: the pure-Python trimesh ray backend runs out of memory on large batches.

## Rounds
List price of the agent runs only (the orchestrator is not included); measured 2026-10-04 with `system_improvement/drafts/tools/maxturns_review.py`. Rounds r10-r16 with the orchestrator: $118.14.

| Round | Date | Agents (tool calls) | List price | Result |
|-------|------|---------------------|------------|--------|
| r10 | 2026-10-01..02 | designer 168, review 72 | $18.98 | fix pass on the r9 register |
| r11 | 2026-10-02 | designer 117, review 63, reference-analyst 53, print-tolerance-expert 42 | $13.88 | fix pass; shoulder buttons located; lips sized |
| r12 | 2026-10-02 | designer 71, review 63 | $10.95 | fix pass |
| r13 | 2026-10-02 | designer 123, short check 78 | $10.51 | finishing pass, baked (superseded by r16) |
| r14 | 2026-10-02..03 | register 66, designer 260, review 65 | $21.16 | rejected as a bake: R rim cliff, L wall altered |
| r15 | 2026-10-03 | designer 298 | $18.12 | lens scoop on the R flank, 3 gates unmet |
| r16 | 2026-10-03 | designer 36, review 75 | $3.79 | baked, ACCEPT WITH LISTED ARTIFACTS |

## Decisions pending for the user
1. **The first print.** Check: snap retention and insertion (insertion safety factor 2.0; `audit/r11/lip_sizing_r11.md`); shoulder-button reach with a real finger (model ii 91 %, model i 77-80 %); the console's fit in the pocket and the lip clearance (CLEAR_Z 0.2); the handle ends at y -68 in the hand.
2. **Print orientation:** the README does not state one; the r16 slice test was in Z only.
3. **After the print:** keep r16 and fix only what the print shows, or approve the B-rep v2 spike (`system_improvement/06_cad_method.md`).
4. Any structural check that hard-codes the old tip (-75.18 / -78.15), the +22 mm handle length or the 34 mm girth station must be re-reconciled before it is trusted.
5. Archiving `audit/r9`..`r15` to `audit/archive/` (it needs your approval).