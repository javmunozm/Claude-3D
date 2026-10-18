# SurgicalDrillGuide: STATE

Updated: 2026-10-17, by session cc8d490f (rounds 6 commit + round 7).

Keep this file under about 150 lines. Agents read it instead of the README. History, rejected approaches and narrative stay in the README.

## Current
- **Bake:** `stl/` from commit 0838f9d (round 7), regenerated and gated before the commit. SHA-256 (first 16): main_frame `8e5b4cd04bbeaaeb`, l_arm_slider `ce1a95f7e00a5cff`, handle `89315e535cfed6b2`, end_stop_pin `82377a3a9da18c99`. STEP in `step/`. Ready to print; nothing printed yet.
- **Working preview:** none (the bake is current).
- **Macro:** entry `macros/surgical_drill_guide.py` (full build ~11 s, writes `stl/` and `step/`); stage package `macros/sdg_model/`; gates `macros/sdg_gates.py`; structural check `docs/mechanism_sizing.py` (not tracked; reconciles strictly against the macro and halts on drift).
- **Method:** B-rep in build123d, in-plane outlines imported from traced DXF rings. See the README.
- **Coupons:** `attempts/r7-ratchet-2026-10-17/coupon/` predate the root and stop fixes; not a reference.

## Open entries
| ID | Region (x, y, z) | Number vs threshold | Class | Status | Decision |
|----|------------------|---------------------|-------|--------|----------|
| R6-1..R6-4 | hook band outline / bar ramp corners | wave 1.11, R 7.32, corner 97.8°, sharp ramp | form | open | user: left as built (2026-10-17) |
| 1a | flexure at the stop | SF 2.69 nominal; 1.64–1.81 with Kt | strength | accepted | user: variant B for a firmer release |
| 1a' | flexure root, 25 N on the pad | SF 1.60 (Kt) | strength | accepted | user: stop is only a travel limit |
| 1a'' | flexure → block square corner X 90.82 | SF 1.73 (Kt 2.0) | strength | accepted | same |
| 1h leg | stop leg junction with the floor (2.5 wide), X 103.975–106.475, Y −12.065 | SF 1.27 (−X, r 1) / 1.21 (+X square); holds ~11 N on the pad at SF 3 | strength | accepted | user 2026-10-17: working load goes through the teeth |
| 1d | ratchet click | 22.3 MPa with Kt vs untested 10.6 fatigue est. | fatigue | open | measure on print |
| 2p | flat locking contact | CAD 1.184; ~0.426 after assumed print rounding vs 0.45 | print | open | measure on print |
| pin | pin → collar at MAX | 0.118 (within FDM error); if it binds, MAX 22 teeth, tip gap 71.67 | fit | open | measure on print |
| D4 / 8 | head ±X wall; hook band X mid / Z | 2.71; 1.72 / 0.89 | strength | accepted (r6) | Z loads accepted |

## Locks (must not move)
| Lock | Tolerance | Why |
|------|-----------|-----|
| Carriage end X 106.4755 above the floor underside | 0.0 | 2.0 clearance to frame material at X 108.475 (`COUPLING_CARRIAGE_CLEAR`, build raises) |
| Wire line Y 51.796, Z 5; C-tip bore Ø3.4 teardrop | 0.0 | coaxiality gate |
| MAX tip gap ≥ 74.0 at a seated pose | build raises | user requirement |
| Coupling: lug 14×10, socket +0.20/side, snap engagement 0.700, slack 0.315 | gate | round 6 |
| Flexure t 1.759, stop gaps 1.30 / 2.77 | gate | round 7 user decision (variant B) |
| Handle flat plane = head −X face (X 111.111, derived) | 0.0 | round 7 user decision |

## Gates
- **Hard:** every STEP 1 valid solid; every part STL watertight, 1 body, 0 sealed voids; interference 0.0 mm³ for all pairs at MIN / MID / MAX; lift check (pawl lowered 1.30, moved −X one pitch) 0 mm² with colliding controls; tooth overlap 1.1697 and seat gap 0.100 for every tooth at every pose.
- **Structural:** `docs/mechanism_sizing.py`, 25 N, PETG assumed, SF 3; Kt values are assumed chart readings.

## Commands
- **Build:** `python "D:\CAD\Claude-Projects\projects\SurgicalDrillGuide\macros\surgical_drill_guide.py"` (about 11 s; `--part <name>` for one part, does not rewrite assemblies).
- **Gates:** `python "D:\CAD\Claude-Projects\projects\SurgicalDrillGuide\macros\sdg_gates.py"` (about 30 s).
- **Structural:** `python "D:\CAD\Claude-Projects\projects\SurgicalDrillGuide\docs\mechanism_sizing.py"`.
- **Region render:** `python tools/render_roi.py <stl> <out.png> --center X Y Z --size 40`.
- Use the venv `D:\CAD\Claude-Projects\.venv\Scripts\python.exe`.

## Rounds
| Round | Date | Agents (tool calls) | Peak context | List price | Result |
|-------|------|---------------------|--------------|------------|--------|
| r6 commit | 2026-10-17 | main only (verify + README) | — | in session total | committed 3f08922 |
| r7 sizing | 2026-10-17 | print-tolerance-expert (30) | 220.5k | $3.84 | pitch 2.6 / depth 1.4 / 4 teeth; 5 teeth fail; 5 N → SF 2.69 |
| r7 coupons | 2026-10-17 | cad-designer (30) | 184.6k | $3.10 | coupons A/B built; user judged fit in the slicer, chose B |
| r7 build | 2026-10-17 | cad-designer (47), form-auditor (24), print-tolerance-expert (30) | 203.5k / 142.9k / 172.8k | $3.77 / $2.59 / $2.50 | built; D1 root V, D2 pad, 1h stops |
| r7 fix | 2026-10-17 | cad-designer (38), print-tolerance-expert (21) | 131.7k / 169.2k | $2.62 / $1.95 | root fillet, beam 2.84, pad 90.32; leg blocked |
| r7 reinforce | 2026-10-17 | cad-designer (36), print-tolerance-expert (18) | 142.1k / 129.5k | $2.50 / $1.73 | beam 3.62, leg 4.0 below floor (junction still 2.5); committed 0838f9d |
| session total | 2026-10-17 | main + 9 subagents | — | $31.73 (main $7.13, subagents $24.60) | |

## Decisions pending for the user
- After the first print: report tooth grip, release force, pin → collar gap at MAX, and any flexure cracking; decide whether to revisit the flexure (thickness / Kt) or the stop leg.
- Material: PETG is assumed; a stronger filament raises every SF proportionally (not computed).
