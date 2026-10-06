# VitaGripPS5: STATE

Updated: 2026-10-05 by `/session-end` (session 49ca6a61: system improvement,
then the v2 B-rep spike and passes 1–1d).

Keep this file under about 150 lines. Agents read it instead of the README. History, rejected approaches and narrative stay in the README.

## Current
- **Bake:** `stl/VitaGripPS5_case_r16.stl` (SHA-256 `4AAF87F76AA7D209BA65E94D897353BE9EDAB277F8B6BDF9FD2477FDEFAE12EF`), a byte copy of `audit/r16/case_preview_r16.stl`. Review: `audit/r16/review/review_r16.md`, **ACCEPT WITH LISTED ARTIFACTS**.
- **Kept on purpose:** `stl/VitaGripPS5_case_r13.stl` (the previous bake, SHA-256 `56141B26...`) and `stl/VitaGripPS5.stl` (the 2026-09-14 socket grip, not this case).
- **Working preview:** none for r16. **v2 (B-rep) work in progress:** `v2/stl/VitaGripPS5_v2_edge.stl` (pass "edge" on top of pass 2 + s8 `2cbbd85`; reviewed ACCEPT WITH LISTED ARTIFACTS, committed 2026-10-06). Next: the finishing passes, "Decisions pending" item 5. See "v2" below.
- **Macro:** `macros/build_case_ext.py`, one file of 216.9 KB, docstring "round 16". Switches `FINISH_ON`, `RIM_CUT_ON = False`, `BAR_CUT_ON`, `D19_ON = False`; flag `--no-bar`. Over 60 KB: split it into stage modules before its next change (`docs/architecture.md`).
- **Method:** r16 is a mesh pipeline on the DualSense scan (numpy and trimesh), not B-rep; fillets cannot be made on it. **The user decided on 2026-10-04 to rebuild the case as a CAD (B-rep) design** in `v2/` (`docs/versioning.md`); a spike runs first (`v2/audit/spike/spike_report.md`). r16 stays the printable bake until a v2 replaces it.
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
| Pit walls, Z 0..10.2 (r16: L 3.97..3.38, R 3.99..3.43; **v2, re-based 2026-10-05:** upper 3.95–4.93, lower 7.71–9.50) | 0.01 | wall thickness |
| Window and camera hole (+2 mm each) (**v2:** exact at r16's constants, window 110 x 57.05 R 3.5, y 3.00..60.05; camera D 12 at (0, 68.05); r16's mesh sits 0.0075 / 0.0054 inside) | 0.005 | the console's rear window and camera |
| Bottom-bar strip, abs(x) < 62, y -12..-8.5 (**v2:** its own flat plate as in pass 2, 0.8–1.3 mm more material than r16) | 0.005 | |
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

## v2 (B-rep rebuild in `v2/`, build123d)
Build: `python projects/VitaGripPS5/v2/macros/vita_grip_ps5_v2.py` (about 20 s to export, about 70–150 s with its gates). Reports: `v2/audit/<pass>/fix_report.md`.

- **Built:** one grip end lofted from smoothed r16 sections (y-planes), mirrored exactly (max 3e-6 mm); flat top Z 11.40 with a 3 mm round built into the sections (flanks median 3.0); tip 3 mm round; 3D rolling-ball top at the U-turn; floor plate blended into the grips; rear corner part of the grip loft (no fin, rim 2 mm round); one upper lip per side with pit and 1 mm slots. Export `tolerance=0.002, angular_tolerance=0.05`.
- **Handle 16 mm shorter (user, 2026-10-04):** 16 mm removed right below the console body, the rest moved +16 in y; tip at y -52.0025, root-to-tip 37.5 mm (DualSense 1:1: 38.7 L / 41.7 R); 15 mm morph from the root flare into the moved handle (inner flank 0.92–1.23 mm per mm, r16 about 0.9).
- **Fitted handle surface (pass "fit", 2026-10-05, method change):** the loft no longer passes exactly through r16's sections. A smoothing spline per matched point along y (h 2.0 mm), stations every 1.5 mm from y -3 to -45, ramps at both ends (`FIT_ALONG_Y` and `FIT_*` in `constants.py`; off = p1d). Cause measured first: p1d's station slopes swung 0.17–0.56 between stations 0.5–1.5 mm apart, r16's about 0.05.
- **Measured (review `v2/audit/fit/review.md`, ACCEPT WITH LISTED ARTIFACTS, 0 regressions vs p1d):** ring lines gone (turn at y -9 / -13 / -27 at most 3.98°, bump 0.002–0.004 mm; p1d up to 22.3°); handle vs r16 moved +16 RMS 0.065–0.15, max 0.54; body y >= 5 within 0.060 of p1d, pocket walls, lip, pit and bar strip 0.0000; top round min 2.74 (S1 fixed); S5 6.44° (fixed); p1d's 0.002 mm knife-edge sliver at (66.5, -9.0, -7.3) gone, thinnest ramp wall 4.52. Left matches right to 0.0000.
- **Plate front (passes "front" + "corner", 2026-10-05; review `v2/audit/corner/review.md`):** the convex bottom edge is an r 1 round (B-rep face f92, x 64–68 median 1.005, min 0.989), cut into the lone blend loft before the fuse, ramping from 0 at x 62.25 (`FRONT_ROUND*`, `parts/plate.front_round_cutter`). The concave plate-front / grip corner is an r 1.005 rolling-ball web fused in before the plate fuse (`CORNER_ROUND`, `parts/plate.corner_round_web`); corner box max 26.2° (fit 108.3°). Switch off = the previous pass, byte-identical. Hard gates pass: no voids or slits (sky test), plate-front wall 4.46, locks 0.0000, everything else re-meshed only. Accepted by the user: the 0.047 mm end step at x 62.0–62.25 and the web's radius dip (min 0.32 at (67.57, -11.2, -12.92), +0.002..+0.005 mm from an ideal r 1).
- **Pass 2 (2026-10-05; review `v2/audit/p2/review.md`):** per side a lower finger/lip/pit (the upper one mirrored about y 33.275, at (90.61, 20.35), n (0.986, -0.164); +0.004 / +0.040 from r16 R), rear window 110 x 57.05 R 3.5 (y 3.00..60.05), camera hole D 12 at (0, 68.05), bottom opening (nothing above the floor inside |x| 66.75, flat closed end; r16 R value used on both sides). Switches `LOWER_LIP_ON`, `WINDOW_ON`, `CAMERA_ON`, `BOTTOM_OPEN_ON`; all off = pass corner, byte-identical. Hard gates: 1 body, watertight, genus 2, back min 4.50, no voids/slits (sky test), lips within 0.0002 of r16 on all four. 229.65 cm3.
- **Locks vs r16, first check (pass 2 review):** pocket wall = geometry (S9); window / camera outlines = r16's mesh is 0.0075 / 0.0054 inside its own constants, v2 exact; bottom-bar strip up to 1.29 = v2's simplified flat plate (more material); upper pit walls 3.95–4.93 (r16 3.43–3.99) = v2's rear corner 0.5–1.2 further out; lower pit walls match at z 0–5, +0.64 at z 10.2 (3 mm top round). Window–camera bridge 2.000 (r16 2.002).
- **Open:**
  - **S8 FIXED (pass s8, 2026-10-05, review `v2/audit/s8/review.md`, ACCEPT WITH LISTED ARTIFACTS, 0 regressions):** `OPEN_X_END` 67.4; wall >= 3.0 everywhere from the end face to x 72, min 3.2862 at (±67.41, z -8.79) (x-section method 3.196, r16 3.296); new gate `gates_p2.end_wall_y` (proven on p2: 1.432 / 2.258); its top-round exclusion (z > 8.4) verified sound (90° plan corner, disk test). Open from it: the end face / grip edge turns 21–35° (B-rep 20.7–34.1, convex, 23.1 mm long, z -8.80..9.34; p2 10–22°; r16 had a 1.2 mm fillet there). **The user chose on 2026-10-06 to round it. Done in pass "edge"** (review `v2/audit/edge/review.md`, ACCEPT WITH LISTED ARTIFACTS, 0 regressions vs s8): `OPEN_END_R` 1.2 (0 = s8, byte-identical), a B-rep fillet right after the opening cut; radius 1.1987–1.2000, tangent to the end face and grip (max 0.002°), ends square on the floor and the pocket wall y -9; box facet turn max 7.16° (s8 35.4°); end wall 3.1429 (x-section 3.140); change vs s8 outside the box 0.0065; p2's 0.011 at (67.786, -16.101, 6.035) is re-meshing (same exact surface in all three STEPs). G1: `end_wall_y`'s band rule now excludes on erosion only; the review proposes adding `|t_x|` < 0.5. **The user chose (2026-10-06) to fix it in the plate-edges pass.** History: the wall in front of the bottom opening's closed end, x 66.75–67.28, z -8.8..-5, measured in y at fixed x (r16's `OPEN_WALL` rule, 3.15): 1.43 at the end face, 2.26 at x 67 (r16 3.29). Not a pass-2 regression: at the floor the front face moved 1.02 mm in pass "fit" (p1d -12.29 → fit -11.27); the fit review's 4.52 used a different wall method and missed it. Options (review): (a) `OPEN_X_END` 66.75 → 67.4 (r16's rule; shaves <= 0.2 off the inner flank's top round); (b) keep the fit smoothing off the root's front face (reopens the fit loft; the S7 web sits on that face); (c) a local pad on the front face.
  - **S9 (ACCEPTED by the user 2026-10-05 as a listed artifact):** rear-corner pocket wall, x 87.2–88.4, y 55.4–59, z -6..8: up to 0.024 mm of material inside r16's pocket outline (lock 0.005). Real, sub-layer, already in corner.
  - **S7 (new; METHOD REVIEW by the third-register rule; ACCEPTED by the user 2026-10-05 as a listed artifact):** the round's and the web's boundary edges are not tangent: f92/f95 (round / underside, x 65.8–69.2) 10.4° median, 12.25° max, 0.023 mm deep; f91/f92 (web / round) 15.9°, 0.038 mm; f92/f225 (round end into the grip, 0.44 mm long, x 69.4–69.5) 21–27°, about 0.1 mm. The web meets both faces at 5.72° by design (`cross` 0.005). Fix proposed by the review: place the cutter arc's end point tangent to the underside (a method change in the cutter, not a constant).
  - Sub-layer, reported only: 3 cells of 8.4–8.9° on the flat-top tangent edge in the morph (bumps <= 0.039); bend y -29..-30 1.45° / 0.007; tip stations 3.83° / 0.013.
  - `checks.outer_flank_turn` reads false fails at z 3.5–5 near the U-turn and tip: the fixed-z plane skims the top round there (review: fixed-z 13.3° / 0.469 mm, along the normal 2.02° / 0.006). Use the review's polar probe (`v2/audit/fit/scripts/fit_review.py`) until the check is fixed.
  - Pass 1d is one loft (`SINGLE_LOFT = True`); the split (the user's option 1) is kept behind the switch.
  - Not run this round: slit / sealed-void ray tests (rear band and corner moved <= 0.0215 vs p1d), S4 chord error.
  - Not done: strength check of the fingers, lower ones included (print-tolerance-expert); tangency of pass 2's cut edges; S4 chord error.

## Rounds
List price of the agent runs only (the orchestrator is not included); measured 2026-10-04 with `tools/token_audit/maxturns_review.py`. Rounds r10-r16 with the orchestrator: $118.14.

| Round | Date | Agents (tool calls) | List price | Result |
|-------|------|---------------------|------------|--------|
| r10 | 2026-10-01..02 | designer 168, review 72 | $18.98 | fix pass on the r9 register |
| r11 | 2026-10-02 | designer 117, review 63, reference-analyst 53, print-tolerance-expert 42 | $13.88 | fix pass; shoulder buttons located; lips sized |
| r12 | 2026-10-02 | designer 71, review 63 | $10.95 | fix pass |
| r13 | 2026-10-02 | designer 123, short check 78 | $10.51 | finishing pass, baked (superseded by r16) |
| r14 | 2026-10-02..03 | register 66, designer 260, review 65 | $21.16 | rejected as a bake: R rim cliff, L wall altered |
| r15 | 2026-10-03 | designer 298 | $18.12 | lens scoop on the R flank, 3 gates unmet |
| r16 | 2026-10-03 | designer 36, review 75 | $3.79 | baked, ACCEPT WITH LISTED ARTIFACTS |
| v2 spike | 2026-10-04 | designer 10 (usage-limit stop) + 36, review 21 | $6.57 | go; ACCEPT WITH LISTED ARTIFACTS (`bcdb801`) |
| v2 p1 / 1b | 2026-10-04 | designer 20 (stop) + 39, 47 | $11.01 | 3 mm round, plate blend, one-piece corner (`285ad15`) |
| v2 p1c / 1d | 2026-10-04..05 | designer 50, 46 | $6.31 | handle -16 mm, waist fixed, ring lines open (`6cf587f`) |
| v2 fit | 2026-10-05 | designer 75, review (usage-limit stop) + 42 | at `/session-end` | fitted surface; rings gone; ACCEPT WITH LISTED ARTIFACTS (`f5b81d8`) |
| v2 front + corner | 2026-10-05 | designer 60 + 37 (front), 52 (corner), review (usage-limit stop) + 26 | at `/session-end` | plate-front r 1 round + concave corner web; S2 fixed, S7 new and accepted (`7d796cc`) |
| v2 p2 | 2026-10-05 | designer 98, review 46 | at `/session-end` | lower latches, window, camera hole, bottom opening; S8 wall fails (from pass fit), S9; METHOD REVIEW (committed with s8, 2026-10-06) |
| v2 s8 | 2026-10-05 | designer 39, review 33 | at `/session-end` | opening end 67.4, wall 3.286, end-wall gate; ACCEPT WITH LISTED ARTIFACTS (committed with p2, 2026-10-06) |
| v2 edge | 2026-10-06 | designer 47, review 28 | at `/session-end` | closed-end edge r 1.2 (B-rep fillet); wall 3.143; ACCEPT WITH LISTED ARTIFACTS (committed 2026-10-06) |

Session 49ca6a61 total, orchestrator included: $85.10 list (main $61.04, agents $24.06).

## Decisions pending for the user
1. **The first print.** Check: snap retention and insertion (insertion safety factor 2.0; `audit/r11/lip_sizing_r11.md`); shoulder-button reach with a real finger (model ii 91 %, model i 77-80 %); the console's fit in the pocket and the lip clearance (CLEAR_Z 0.2); the handle ends at y -68 in the hand.
2. **Print orientation:** the README does not state one; the r16 slice test was in Z only.
3. **S8:** done. The user chose (a), `OPEN_X_END` 66.75 → 67.4 (2026-10-05); pass "s8" ran it. Locks re-based on v2 and S9 accepted (same date).
4. **Pass 2 + s8** committed 2026-10-06 (the user's choice). The closed-end edge: the user chose to round it (2026-10-06); pass "edge" did it (reviewed, committed 2026-10-06).
5. **Finishing passes (user, 2026-10-06; the design is "almost finished"):**
   - **Latches:** finger x2 (root 1.8 → 3.6, tip 0.9 → 1.8) and hook overhang +1 (1.5 → 2.5), for better grip. **Sized first** (user's choice) by print-tolerance-expert, `v2/audit/latch/sizing.md`, then built. Scaled from r11's model (not measured), the requested size gives about 27 MPa root stress on insertion (SF about 0.5 against 14 MPa interlayer; r11 SF 2.0). This replaces the "Lips and fingers" and "Pit walls" locks once built.
   - **Pocket contour:** r 1.0 round on the top edge where the console goes in (Z 11.4, inside the grips); 0.4 mm of straight wall stays above the console face (Z 10.0). After the latch pass (the pits interrupt the contour).
   - **Plate edges:** full half-round (r 2.25 top and bottom, a bull-nose on the 4.5 mm plate) on the front edge y -11.2 and the top-bridge edge y 78.55, running into the grips. This replaces the "Bottom-bar strip" lock and meets the S7 front round / corner web at x 62–69.
   - Order: edge (done) → plate edges → latches (after sizing) → pocket contour; each pass reviewed before the next.
5. Handle tolerance against r16: working limit RMS 0.3 / max 2.0 mm, round band excluded (set by the orchestrator; confirm or change). The user chose the 3 mm round everywhere and the 15 mm root transition.
6. Any structural check that hard-codes the old tip (-75.18 / -78.15), the +22 mm handle length or the 34 mm girth station must be re-reconciled before it is trusted.
7. Archiving `audit/r9`..`r15` to `audit/archive/` (it needs your approval).