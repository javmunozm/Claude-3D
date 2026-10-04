# VitaGripPS5 v2: the case as B-rep (spike)

**Status: spike, not a printable case.** r16 (`../stl/VitaGripPS5_case_r16.stl`) stays the printable bake.

## Goal
Rebuild the VitaGripPS5 snap-in case as a CAD B-rep in build123d instead of r16's 69-stage mesh pipeline (user decision, 2026-10-04). This spike tests the hardest part first:
- the right handle;
- its junction to a simplified body;
- one lip;
- the flat top cut.

The half is then mirrored to the left.

## Representation
B-rep in build123d. Most of the form comes from the r16 bake:
- y-plane sections of r16, smoothed (`splprep`, 0.08 mm per point) and resampled to 72 points;
- lofted with `Solid.make_loft`.

The precise features are modelled from the r16 constants:
- the pocket oval (183.30 x 84.55, caps at x ±70);
- the finger and lip profile (r16's `finger_solid`);
- the pit (r16's `pit_solid`);
- the flat top at Z 11.40;
- the tip trim at y -68.0025.

## Method (stages in `macros/vgps5_v2/`)
| Stage | File | What it does |
|---|---|---|
| constants | `constants.py` | r16 values; stations; spike parameters |
| sections | `sections.py` | slices r16 at y-planes, keeps x >= 66.5. For y >= -11.5 it fills the pocket, pits and slots row by row (z >= -14), so they can be re-cut exactly. Sections with r16's flat top are extended above z 8 by the domed cap of r16's uncut section at y -46, moved up the handle-top slope (0.36) |
| shapes | `shapes.py` | spline section wires, loft, pocket cutter, the fillet try-ladder, single-solid check |
| parts | `parts/grip_end.py` | right grip end. The main loft runs y 61 to -70 and handle plus end wall are ONE loft (no handle/body junction edge). A low rear-corner loft runs y 59 to 76.5. r16's corner clip (plane through y 59.7 at the top, 4.1 mm z per mm y) cuts the rear; the top is trimmed at 11.4, the tip at -68.0025 and the tip edge is rolled |
| parts | `parts/plate.py` | simplified floor plate, x 0..68.5 (2 mm into the loft), y -11.2..78.55, z -13.3..-8.8; no window or camera hole |
| parts | `parts/lip.py` | right upper finger with lip at (90.61, 46.20), n (0.986, 0.164), and its pit |
| assemble | `assemble.py` | junction edges between the plate and the loft; mirror about x = 0 and union |
| checks | `checks.py` | topology, mirror deviation, handle deviation from r16 |

Main: `macros/vita_grip_ps5_v2.py`. Nothing runs at import.

## Build
```
timeout 300 python projects/VitaGripPS5/v2/macros/vita_grip_ps5_v2.py [--out-step P] [--out-stl P] [--results P] [--junction-brep P]
python projects/VitaGripPS5/v2/audit/spike/scripts/junction_search.py <half_pre.brep>
```
The build takes 80 s. The junction search runs each fillet attempt in its own subprocess: in-process, an OCC fillet at r 1 ended the build twice with no Python error.

## Files
- `step/VitaGripPS5_v2_spike.step`, `stl/VitaGripPS5_v2_spike.stl`: the spike part (both halves).
- `audit/spike/spike_results.json`: gate numbers from the build.
- `audit/spike/junction_search.log`: the junction search.
- `audit/spike/spike_report.md`: the report.
- `renders/`, `audit/spike/roi_handle_root.png`: renders.

## Spike results (build 4, 2026-10-04)
See `audit/spike/spike_report.md`. In short:
- watertight, 1 body;
- mirror deviation 3.4e-6 mm;
- tip roll 3 mm valid;
- **top roll valid only up to 1.5 mm** (3 mm fails);
- **plate/loft junction:** the bottom edge takes no fillet at all;
- handle RMS 0.12-0.28 mm from r16.

## Rejected approaches (spike)
- **Trapezoid extension of flat-topped sections.** The z 11.4 contour got plan corners of R 0.33-1.4 at the handle U-turn and the rear inner corner, and the top roll failed at 1 mm (build 1). With the trapezoid on body stations and the cap sweep on handle stations, the contour kinked at y -11..-12.6 (R 0.5; build 3).
- **Rear loft overlap section as an unscaled copy.** It met the main loft's end face near-tangentially at (±78, 61, -20.5). The solid was valid, but the STL had 10 open edges (build 3).
- **Junction fillet search in the build process.** At r 1 the process ended silently (builds 1 and 3).

## Verification checklist (open)
- The rear corner (y 59-77), the plate (no window or camera hole), the second lip and the lower fingers are simplified or absent. None of them is verified against r16.
- Pocket wall, floor and lip locks (STATE.md) are built from the constants but were **not measured** on the spike's export.
- No structural check: print-tolerance-expert has not seen this geometry.
