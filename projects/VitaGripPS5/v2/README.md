# VitaGripPS5 v2: the case as B-rep (spike)

**Status: pass 1d done in part, 2026-10-05; not a printable case.** r16 (`../stl/VitaGripPS5_case_r16.stl`) stays the printable bake.

Pass 1d (`audit/p1d/fix_report.md`; outputs `step/` and `stl/VitaGripPS5_v2_p1d.*`; valid, watertight, 1 body):
- **One loft again, rear face to tip:** there is no seam at y -13.5 (no B-rep edge; STL max 9.47° there, no folds). Every guided split-loft variant failed in the full build; see the report.
- **Root transition 15 mm** (y -13.5..-28.5, user choice 14-16). Inner flank 0.92 / 1.23 mm per mm at z 5 / 8.
- **Open:**
  - **The ring lines are still visible,** at y -13 and y -27/-28. They are not the seam: they stay with one loft. Suspected cause, not measured: station noise across close stations.
  - Plate-front round; S5.
- Body y >= -12 is unchanged from p1c (max 0.07). Handle vs r16 moved +16: middle RMS 0.07-0.09, max 0.47; tip RMS 0.12-0.15, max 0.53.

Pass 1c (`audit/p1c/fix_report.md`; outputs `step/` and `stl/VitaGripPS5_v2_p1c.*`; valid, watertight, 1 body):
- **Two lofts:**
  - body/corner: rear face to y -13.5;
  - handle: y -13.5 to the tip.
  They meet on one shared section (identical caps, exact fuse). Open: the seam is a crease, median 16-18°, max 48-51°, against 8°. Three seam methods were tried; see the report.
- **Handle 16 mm shorter (user request):**
  - Tip plane at y -52.0025; root (-14.48) to tip 37.5 mm.
  - r16's stations from y -39.5 to the tip are moved +16 mm, unchanged: middle and tip vs moved r16, RMS <= 0.15, max <= 0.53.
  - y -13.5..-23.5 morphs from r16's root into the moved handle. r16's 16 mm root flare is compressed into 10 mm there, which leaves a pinched waist on the inner side of the root (flank slope up to 1.86 mm/mm).
- **Rear corner:** the wall-end fin is gone (outer lean -0.1); the rim crest has a 2 mm round.
- **Still open:** the plate-front round (no edge takes r 1), and S5 (11.5°, now in the morph).
- **The body at y -12..55 is unchanged from p1b:** max 0.19.

Pass 1b (`audit/p1b/fix_report.md`; outputs `step/` and `stl/VitaGripPS5_v2_p1b.*`; valid, watertight, 1 body):
- **Rear corner:** now part of the one grip-end loft (tip to rear face, y 78.55). Its top is one cutter with the rounds built in: 3 mm top round, 1:20 wall at 25° in plan, 6.5 mm foot, flat at the floor. It was fitted to r16 (RMS 1.10). The rear slab, the second loft and the y 61 step are gone. Open: a fin at the wall's outer end (155.7° at (96, 64, 0)), and the rim crest is sharp (its fillet fails). The fix for both breaks three other booleans through the global loft (builds 2-3).
- **U-turn:** top from a 3D ball opening (r 3) of the height field; handle edges over 30° 3 → 0; a soft ripple remains.
- **S5:** 14.88° → 12.9°. **Regression:** the plate-front 1 mm fillet no longer builds.
- **Handle vs r16, top-round band excluded:** RMS 0.08-0.15, max 0.52-1.54 (limit 0.3 / 2.0). Band included: root 0.327.

Pass 1 (`audit/p1/fix_report.md`; outputs `step/` and `stl/VitaGripPS5_v2_p1.*`):
- **Top round:** 3 mm, built into the sections on the flanks (B-rep median 3.02). At the handle U-turn (y ≈ -42) it left a transverse crease: 3 STL edges over 30°, open as N2.
- **Plate:** built into the grip end. Plate boxes plus a lofted blend; the old concave step is now a 15° crossing. The front edges carry a 1 mm round.
- **S5:** unchanged (14.88°).
- **Handle vs r16:** root rms 0.326 (over the 0.3 working limit, from the 3 mm inner round); middle 0.088-0.114; tip 0.12-0.15.

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
| parts | `parts/plate.py` | pass 1, floor plate with no window or camera hole: boxes x 0..60 (z -13.3..-8.8) and x 0..67.5 (z -12..-8.8) for y -11.2..61, rear box x 0..68.5 for y 61..78.55, plus a lofted blend (y -11.2..61): flat at -13.3 to x 61, then a cubic crossing the grip underside at x 69 at 15° |
| parts | `parts/lip.py` | right upper finger with lip at (90.61, 46.20), n (0.986, 0.164), and its pit |
| assemble | `assemble.py` | junction edges between the plate and the loft; mirror about x = 0 and union |
| checks | `checks.py` | topology, mirror deviation, handle deviation from r16 |

Main: `macros/vita_grip_ps5_v2.py`. Nothing runs at import.

## Build
```
timeout 300 python projects/VitaGripPS5/v2/macros/vita_grip_ps5_v2.py [--out-step P] [--out-stl P] [--results P] [--half-brep P] [--no-gates] [--sections-only] [--grip-only]
python projects/VitaGripPS5/v2/audit/p1/scripts/p1_post.py
```
Pass 1 build:
- 19 s to export, 68 s with the gates.
- Defaults write `step/VitaGripPS5_v2_p1.step`, `stl/VitaGripPS5_v2_p1.stl` and `audit/p1/p1_results.json`.
- `--half-brep` writes the half before the lip. `p1_post.py` reads that file (path set in the script) for fillet trials, one subprocess each: in-process, an OCC fillet at r 1 ended the spike build twice with no Python error.

Pass-1 stage changes:
- `sections.py`: `round_top`, `apex_clip`, `resample_aligned` (graded spacing), `blend_profile`.
- `parts/plate.py`: plate boxes and the blend loft.
- `checks.py`: `edge_creases`, `round_radii`, `handle_smoothness`.

Pass 1 replaced the spike's main; the spike's code is at commit `bcdb801`. The spike outputs (`*_v2_spike.*`) are still on disk, unchanged.

## Fitted surface along y (pass fit, 2026-10-05)
The main's defaults now write `step|stl/VitaGripPS5_v2_fit.*` and `audit/fit/fit_results.json` (178.6 s with the gates).

**What it does.** Up to p1d the loft passed exactly through every r16 station. Each station is smoothed on its own, so
each one keeps 0.01-0.18 mm of noise. Between stations 0.5-1.5 mm apart that noise became the ring lines (measured
in `audit/fit/fix_report.md`, step 1). `sections.fit_along_y` now runs before the single loft:
- for every matched point index, a cubic smoothing spline along y through that index's (x, z) over all stations
  (`make_smoothing_spline`, weights = each station's share of the y span, lam = h^4);
- the stations between `FIT_Y0` and `FIT_Y_TIP` are replaced by evenly spaced ones;
- the smoothing fades in and out with smoothstep ramps, so it leaves no kink against the stations kept as they are.

**Constants** (`constants.py`):

| Constant | Value | Meaning |
|---|---|---|
| `FIT_ALONG_Y` | True | off = the p1d stations, exact interpolation |
| `FIT_Y0` | -3 | stations y >= -3 are not changed (body y >= 5 vs p1d: max 0.062 mm) |
| `FIT_RAMP` | 5 | the smoothing is fully on from y -8 |
| `FIT_Y_TIP`, `FIT_TIP_RAMP` | -45, 6 | fully on down to y -39; the stations at y <= -45 (tip roll, extrapolation) are not changed |
| `FIT_SPACING` | 1.5 | 27 new stations replace 24 |
| `FIT_SMOOTH` | 2.0 mm (h) | residual to the old stations: median 0.25, max 0.73 mm (in the top round band) |

**Tried and failed** (grip-only trials):

| Variant | Result |
|---|---|
| h 1.5 | rim crest fillet fails at r 2, 1.5 and 1 |
| h 2.5 | tip fillet only valid at r 1; the tip moves 0.77 mm |
| spacing 1.0 | valid, but the tip zone gets worse (z -20: 3.85° over the reference at y -45) |
| spacing 2.0 | rim crest fails, tip r 3 fails, grip + blend invalid |
| `FIT_Y_TIP` -48 | the loft fails |

On the fitted loft the plate-front fillet attempt (r 1) crashed the process (segfault). It had never succeeded (p1c, p1d), so `FRONT_R` is now 0.

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
- p1d, G1 seam between two lofts (`audit/p1d/fix_report.md`):
  - Spline guide stations at -13.5 +- g: the body loft's top cut returns nothing. This happened at every g (0.02-0.2), at max degree 3 / 5 / 8, and with centripetal parametrisation.
  - A handle guide along the body's own end tangent: the trimmed handle was invalid. That tangent is up to 74° off the chords.
  - No guide at T 15: the pieces do not fuse.
- p1c, seam between two lofts:
  - Overlapping lofts trimmed at the station plane y -13.5: crease max 66°, STL folds 179°. Fragile: the fuse gave 2 solids without the fillets, and some trims returned nothing.
  - Overlapping lofts cut at -13.25, between stations: a micro-step, 30 seam edges at 80-97°.
  - A -14 station on the handle side: the trimmed handle loft was invalid.
  Details: `audit/p1c/fix_report.md`.
- **Trapezoid extension of flat-topped sections.** The z 11.4 contour got plan corners of R 0.33-1.4 at the handle U-turn and the rear inner corner, and the top roll failed at 1 mm (build 1). With the trapezoid on body stations and the cap sweep on handle stations, the contour kinked at y -11..-12.6 (R 0.5; build 3).
- **Rear loft overlap section as an unscaled copy.** It met the main loft's end face near-tangentially at (±78, 61, -20.5). The solid was valid, but the STL had 10 open edges (build 3).
- **Junction fillet search in the build process.** At r 1 the process ended silently (builds 1 and 3).
- **Pass 1, blend crossing at 10° (x 68.5):** the union left a zero-volume sliver at y 56-57. 15° at x 69 fuses cleanly.
- **Pass 1, uniform-parameter loops with ungraded segment spacing** (up to 9× jumps on the dome stations): the tip round failed at 3/2/1.
- **Pass 1, extra stations at y -37 and -39.5:** the main loft blew up (volume 1.4e8).
- **Pass 1, flat at TOP_Z + 0.01:** loft ringing of about 0.04 left two dimple islands in the flat top. 0.03 leaves none.

## Verification checklist (open)
- The rear corner (y 59-77), the plate (no window or camera hole), the second lip and the lower fingers are simplified or absent. None of them is verified against r16.
- Pocket wall, floor and lip locks (STATE.md) are built from the constants but were **not measured** on the spike's export.
- No structural check: print-tolerance-expert has not seen this geometry.
