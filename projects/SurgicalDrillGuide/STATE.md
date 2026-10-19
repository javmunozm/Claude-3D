# SurgicalDrillGuide: STATE

Updated: 2026-10-18, by session 0a716d67 (round 8: rigid shoe + M6, Ø1.5 wire variant).

Keep this file under about 150 lines. Agents read it instead of the README. History, rejected approaches and narrative stay in the README.

## Current
- **Bake:** `stl/` + `step/` from the round 8 working tree (not committed yet), built and gated 2026-10-18. Nothing printed.
  - SHA-256 (first 16), Ø3.0: main_frame `ee79750524c0746a`, l_arm_slider `e9399f8bedb4cd8a`, handle `89315e535cfed6b2` (unchanged since r7), end_stop_pin `56da0372746aac68`, shoe `1c7b775d0c9c358a`.
  - Ø1.5 variant: main_frame_wire1p5 `90af336e6e79592d`, l_arm_slider_wire1p5 `194056fcc3d775f5`. Handle, pin and shoe are shared.
  - `hw_*.stl` = metal screw / jam stack / drive nut clearance bodies (not printed). Assemblies are written locked.
- **Backups:** r7 bake in `attempts/r8-rigid-pawl-2026-10-18/r7_bake_backup/`; first r8 build in `.../r8_build_backup/`.
- **Macro:** entry `macros/surgical_drill_guide.py` (`--wire 1.5` for the variant; build Ø3.0 first); stage package `macros/sdg_model/` (new `parts/shoe.py`); gates `macros/sdg_gates.py` (`--wire 1.5`); structural `docs/mechanism_sizing.py` (untracked; reconciles 155+ pairs, halts on drift).
- **Method:** B-rep in build123d, in-plane outlines from traced DXF rings. See the README.
- **Round 8 record:** `attempts/r8-rigid-pawl-2026-10-18/` — `sizing.md` (Parts 1–4, newest on top; Part 1 = concept A, rejected), `build_report.md`, `review.md`, `fix_report.md`.

## Mechanism (r8, user decisions 2026-10-18)
- Rack: sawtooth, 0° locking wall, 60° ramp, pitch 3.5, depth 1.5, land 0.902; 29 notches; `RACK_EXT` 11.1; pin at X −6.482 Y −3.796 (`PIN_TIP_WALL` 3.0). n_max 18, MID 9, MAX tip gap 77.472.
- Rigid printed **shoe**, 6 teeth, DIN 557 M6 square nut inside. M6 × 20 DIN 464 knurled screw from below at X 88.533 Z 5, axially captured in a 5.5 floor by washer DIN 125-A + DIN 557 jam nut + Loctite 243 (Ø14.6 bore). Turning drives the shoe up (lock) / down (release, travel 1.841).
- Assembly through a +Z window in the carriage side wall (X 76.784..100.282, Y −24.992..−10.565). Order in `sizing.md` Part 2.
- Carriage: `WRAP_WALL_Z` 4.0 (slab Z −4.3..14.3), `CARRIAGE_TOP_WALL` 4.4, `PIN_PROTRUDE` 4.3. Shoe `SHOE_HOLE_TOP_WALL` 1.8.
- Ø1.5 variant: `WIRE_D` 1.5, `BORE_D` 1.9, `REAM_D` 1.7; the C-tip pad is sized from the Ø3.0 bore (user decision), so the frame differs only in the bore.
- Removed: flexure, tab, pad, two-point stop, leg, beam and their constants.

## Open entries
| ID | Region (x, y, z) | Number vs threshold | Class | Status | Decision |
|----|------------------|---------------------|-------|--------|----------|
| R6-1..R6-4 | hook band outline / bar ramp corners | wave 1.11, R 7.32, corner 97.8°, sharp ramp | form | open | user: left as built (2026-10-17) |
| D4 / 8 | head ±X wall; hook band X mid / top | SF 2.71; 1.72 / 2.55 (Z loads 0.89 / 1.22) | strength | accepted (r6) | unchanged in r8, both variants |
| walls | carriage top 4.4 / −Z side 4.0 over the window, 500 N | SF 3.09 / 3.01 at the bound | strength | pass, marginal | — |
| 1C-i | shoe centre section, 500 N | SF 3.02 (Kt at the hole not applied) | strength | pass, marginal | user: flat wall 1.8 |
| shoe flat | shoe hole flat at Z 8.3 | 0.000 to the Ø6.6 clearance circle; 0.30 to the Ø6.0 shank | fit | open | measure on print |
| thread | drive nut engagement at lock | 2.102 under clamp, 1.682 at −0.42 length tol; < 1 thread if the tip chamfer ≈ 1 pitch | fit | open | measure the bought screw |
| back-off | tightening with a tooth tip on a ramp | jaw can back off up to 2.6 before seating | function | open | check on print |
| pin print | end_stop_pin 18.6 long | SF 3.92 lying / 2.54 standing | print | rule | print it lying |
| R8-1 | shoe section steps at the nut slot | 12.30 → 7.00 → 4.00 | form, designed | open | user: not fixed in r8 |
| R8-3 | slider −Z wall at the jam bore | 2.0 (was 1.5), SF 6.94 | thin wall | open | user: not fixed in r8 |
| R8-4..R8-11 | jam bore rim, block/floor, window top, pocket, channel ceiling, nut slot, tooth / notch roots | radius 0 | corner | open | user: not fixed in r8 |
| μ / fatigue | release and lock under use | untested | function | open | measure on print |
| CUT_MIN_M[1.5] | `mechanism_sizing.py` hook cut for Ø1.5 | measured on the pre-fix-2 STL | data | stale | re-measure next sizing run |

## Locks (must not move)
| Lock | Tolerance | Why |
|------|-----------|-----|
| Carriage end X 106.4755 above the floor underside | 0.0 | 2.0 clearance to frame material at X 108.475 (`COUPLING_CARRIAGE_CLEAR`, build raises) |
| Wire line Y 51.796, Z 5; C-tip bore teardrop (Ø3.4 / Ø1.9) | 0.0 | coaxiality gate |
| MAX tip gap ≥ 74.0 at a seated pose | build raises | user requirement |
| Coupling: lug 14×10, socket +0.20/side, snap engagement 0.700, slack 0.315 | gate | round 6 |
| Handle flat plane = head −X face (X 111.111, derived) | 0.0 | round 7 user decision |
| Concept B: 0° sawtooth, rigid shoe, M6 + metal nuts, +Z window | — | round 8 user decisions |

## Gates
- **Hard (both variants):** every STEP 1 valid solid; every printed STL watertight, 1 body, 0 sealed voids; interference 0.0 mm³ for all part and hardware pairs at MIN / MID / MAX (designed drive-nut contact 0.000011).
- **Locked pose:** every shoe tooth overlap 1.3268, gaps 0.100, wall angle 0°; controls −X 0.15 and +Y 0.05 must collide.
- **Released pose:** shoe −Y 1.8408, swept ±X one pitch: 0 mm², margin +0.514.
- **Assembly:** shoe through the window and jam stack through the bore, swept: 0 mm³.
- **Bore:** rays at wire r and reamed r hit nothing; control > drawn r hits. C-tip wall min 1.799 (Ø3.0) / 2.543 (Ø1.5).
- **Structural:** `docs/mechanism_sizing.py`, 25 N working, 500 N clamp, PETG assumed, SF 3; Kt mostly not applied.

## Commands
- **Build:** `python macros\surgical_drill_guide.py` then `python macros\surgical_drill_guide.py --wire 1.5` (about 8–11 s each).
- **Gates:** `python macros\sdg_gates.py` and `python macros\sdg_gates.py --wire 1.5` (about 30 s each).
- **Structural:** `python docs\mechanism_sizing.py`.
- **Region render:** `python tools/render_roi.py <stl> <out.png> --center X Y Z --size 40`.
- Use the venv `D:\CAD\Claude-Projects\.venv\Scripts\python.exe`; paths relative to `projects/SurgicalDrillGuide/`.

## Rounds
| Round | Date | Agents (tool calls) | Peak context | List price | Result |
|-------|------|---------------------|--------------|------------|--------|
| r6 commit | 2026-10-17 | main only | — | in session total | committed 3f08922 |
| r7 (all) | 2026-10-17 | 9 subagents | ≤ 220.5k | $31.73 session | committed 0838f9d |
| r8 sizing A | 2026-10-18 | print-tolerance-expert (16) | 171.2k | $2.47 | V tooth; user chose sawtooth instead |
| r8 sizing B | 2026-10-18 | print-tolerance-expert (12) | 230.0k | $4.43 | shoe + nut + jam; window needed |
| r8 build | 2026-10-18 | cad-designer (40) | 218.3k | $3.77 | built, all gates pass |
| r8 review | 2026-10-18 | form-auditor (18), print-tolerance-expert (19) | 121.2k / 176.4k | $1.42 / $1.98 | 12 rows; window wall FAIL |
| r8 fix + Ø1.5 | 2026-10-18 | cad-designer (32), print-tolerance-expert (16) | 159.4k / 115.6k | $2.42 / $1.10 | walls, R8-2, R8-12, variant; shoe 1C-i FAIL found |
| r8 fix 2 | 2026-10-18 | cad-designer (12) | 84.8k | $1.00 | shoe 1.8, Ø1.5 pad = Ø3.0; all pass |
| session total | 2026-10-18 | main + 8 subagents | — | $22.05 (main $3.46, subagents $18.59) | |

## Decisions pending for the user
- Commit round 8 (macros, gates, STATE, NEXT_SESSION; README not yet updated with the r8 narrative).
- After the first print: lock grip under a pull, release in ~2 turns, back-off while tightening, thread engagement with the bought screw, shoe flat vs screw.
- Whether to fix R8-1, R8-3..R8-11 (corners) in a later round.
- Material: PETG assumed; a stronger filament raises every SF proportionally (not computed).
