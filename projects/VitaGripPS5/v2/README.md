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

**Pass front (S2, 2026-10-05, outputs `*_front.*`, not baked).** The plate front's bottom edge is rounded by a cutter cut
from the lone blend loft before any fuse (`parts/plate.py: front_round_cutter`), not by a fillet. `FRONT_ROUND = 1.0`
(0 = pass fit) ramps by smoothstep from `FRONT_ROUND_X0 = 62` over `FRONT_ROUND_RAMP = 2`; sections start at
X0 + `FRONT_ROUND_START = 0.25` (r 0.047, a 0.047 mm end step there); the underside line is a secant; the arc is drawn
at r (1 + `FRONT_ROUND_CROSS = 0.005`); past the arc the cutter runs to 0.1 L under the real underside. Measured: r 0.989-1.013
at x 64-69 (B-rep); details in `audit/front/fix_report.md`.

**Pass corner (2026-10-05, outputs `*_corner.*`, not baked).** The concave plate-front / grip junction (x 66.9-68.5 on
y -11.2, z -8.8..-13.07, then along the front round to (69.4, -10.6, -13.7)) has an r 1 rolling-ball round. It is a lone web solid
(`parts/plate.py: corner_round_web`), lofted through ball-centre sections solved against the lone blend and grip end and
fused into the half, not a fillet. `CORNER_ROUND = 1.0` (0 = pass front: the hash is identical); its end sinks into the
material over `CORNER_ROUND_SINK`; the web is trimmed at the floor plane. Open: the web's B-rep radius dips locally to 0.32 where the plate
front turns into the front round (median 1.005); details in `audit/corner/fix_report.md`.

**Pass latch (2026-10-06, outputs `*_latch.*`, not baked).** `LATCH_X2 = True` doubles the 4 snap fingers (root 3.6 / tip 1.8, root fillet r 2.0; lip line, overhang 1.5, lead 30, gap 2.5, ROOT_Z unchanged); the extra thickness and the pit face (u 4.3 -> 6.1) go outward. False = pass plate, STL byte-identical (SHA-256 `293FD06B…7E33`); `--latch-x2 0|1` overrides. Must be printed on its side (interlayer SF 1.01). Details: `audit/latch/fix_report.md`. Review `audit/latch/review.md`: ACCEPT WITH LISTED ARTIFACTS; S10 (slot-side root fillet cut short, sharp slot-wall foot; `audit/latch/root_check.md`: in-layer SF 3.25 for the fillet, 1.77–3.25 with the foot) and S11 (0.065 mm facets in the latch profiles) accepted by the user, 2026-10-06; the slot is to be checked on the print.

**Pass plate (2026-10-06, outputs `*_plate.*`, not baked).** The plate's front (y -11.2) and rear (y 78.55) edges are
half-rounds, `PLATE_NOSE_R = 2.25` (0 = pass edge, STL byte-identical, SHA-256 `71A8050F…5A91D`, re-hashed run 3).
Bottom edges and the front top: variable-radius OCC fillets on the lone plate before the fuse (`parts/plate.nose_fillet`).
Top edges: r 2.24 to x 58, then down to r 0.5 at x 66 (rear) and 0.15 at x 65.5 (front), so a small notch stays where
each round meets the grip (build 2's laws; run 3 fell back to them). Details and gates: `audit/plate/fix_report.md`.
Rejected (run 3), carrying the round on along the grip:
- rear: one fillet on the fused half (`parts/plate.nose_post_fillet`, kept, off with `PLATE_NOSE["post"] = {}`), r 2.24
  -> 1.0 along the grip's rear edge -> 0.3 at the blend end face x 70.5. B-rep valid, STL watertight, but folded facets
  where the round turns under the grip end: 479 edges up to 179.7 deg at (±72, 78, -12) (build 3).
- front: the corner web's top edge leaves the plate edge at a 5.7 deg kink, so the contour stops there; adding it as a
  second contour builds an invalid solid (r 1.0 to the end, and tapered to 0.3).

## Pass 2 (2026-10-05): lower latches, window, camera hole, bottom opening
r16's remaining features, each an exact B-rep feature behind its own switch in `constants.py`. With
`--off all` the build reproduces pass corner's STL byte for byte (SHA-256 `7391D824…9AA05A`, measured).
Defaults now write `step/VitaGripPS5_v2_p2.step`, `stl/VitaGripPS5_v2_p2.stl`, `audit/p2/p2_results.json`.

| Switch | Feature | Constants |
|--------|---------|-----------|
| `LOWER_LIP_ON` | lower finger + lip + pit per side, the upper one's mirror about YC 33.275 (r16's rule `y_lo = 2 YC - y_up`); same `lip.py` profiles | `FINGER_P_LO` (90.61, 20.35), `FINGER_N_LO` (0.986, -0.164) |
| `WINDOW_ON` | rear window through the floor plate, 110 x 57.05, R 3.5, x 0, y 3.00..60.05 | `WINDOW_W`, `WIN_Y0`, `WIN_Y1`, `WINDOW_R` (derived as r16 from `CLEAR_Y`, `PANEL_*`, `WINDOW_GROW`) |
| `CAMERA_ON` | camera hole D 12 at (0, 68.05) through the plate | `CAMERA_HOLE_D`, `CAMERA_Y` |
| `BOTTOM_OPEN_ON` | nothing above the floor (z >= -8.8) in front of the pocket for abs(x) < `OPEN_X_END` (p2: 66.75, r16's right-side end; pass s8 2026-10-05: **67.4**, user's option (a) for S8, r16's OPEN_WALL rule; the y-wall in front of the end is now >= 3.286, was 1.43; new permanent gate `gates_p2.end_wall_y`, wall in y at fixed x, x `OPEN_X_END`..72, z -8.8..11.4, both sides; it reproduces 1.43 / 2.26 on p2; `audit/s8/fix_report.md`) | `OPEN_X_END`, `OPEN_Y_LO` |
| `OPEN_END_R` | pass edge 2026-10-06 (user: "Round it"): the closed end's edge to the grip (23.1 mm, z -8.80..9.34) is an r 1.2 B-rep fillet, applied on the half right after the opening cut (`try_fillet`, fallback 1.0); radius median 1.1999, min 1.1987; facet turn in the end box max 7.16° (s8 35.4°); `end_wall_y` min 3.1429 (s8 3.2862); its top-round band now excludes a chord only by the erosion test (<= 2.2 at r 1.5), still reads 1.432 / 2.258 on p2; 0 = s8, byte-identical; `audit/edge/fix_report.md` | `OPEN_END_R`, `OPEN_END_R_FALLBACK` |
| `PLATE_NOSE_R` | pass plate 2026-10-06 (user: full half-round on the plate's front and top-bridge edges), **left at 0 = pass edge** (SHA proven before the continuation's edits; not re-hashed since). With `--plate-nose-r 2.25`, both edges get variable-radius fillets on the lone plate (`nose_fillet`): r 2.24 top and bottom (a 0.02 flat at the tip) to x 58, then fading per `PLATE_NOSE` laws into the grip. Front and rear build valid as B-rep. Full build 1 (rear top r_e 0.15) was 1 body but **not watertight**, genus 3: 14 open edges at the rear-top cusp where the fillet meets the grip end (x ±66.3). The earlier cutter method is rejected: its loft never cut, which left a square edge and a 2.2 mm step at x 58 (`audit/plate/fix_report.md`). Open; see `audit/plate/handoff.md` | `PLATE_NOSE_R`, `PLATE_NOSE` |
| G1 (gate) | `gates_p2.end_wall_y(ero_tx=0.5)`: in the top-round band a chord is excluded only if erosion distance <= 2.2 **and** \|t_x\| < 0.5. Proven: p2 still reads 1.432 / 2.258 and fails; edge reads 3.1429 and passes (333 excluded, all counted chords >= 3.1429); `audit/plate/g1_proof.json` | `end_wall_y` |

- Window and camera are cut on the mirrored solid, the lower lip and the opening on the half before the mirror.
- The opening cut takes 10.24 mm3 per side (x 66.36..66.75, y -13.61..-9.0, z -8.8..8.15): the grip's inner face sat at x 66.5–66.6 there. v2 was already open for abs(x) < 66.5.
- New gates in `vgps5_v2/gates_p2.py` (topology + genus, flood-fill sky test with a sealed-void control, walls / back by `tools/form_sweep.py`, lock check against r16, change against pass corner); helpers in `checks.py`. Numbers in `audit/p2/fix_report.md`.
- Pass-2 build: 57 s to export, 296 s with all gates.

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
- **Pass top (2026-10-06), the body's outer top edge as a handle-like curve with a size that varies along y. Rejected by the user ("awful"; the latch top is better).**
  - **The law:** an ellipse opening of each body section's outer top corner (`sections.top_face`), full size 12 x 6 (equivalent r 14–16; the handle's top at y -25 is r 20–32).
  - **Run 1, 2D on the build's own sections:** a 12 x 6 starting near the pocket opens both latch pits to the outside (wall 0 above z 10.28 upper and 10.88 lower), because the pits' vertical outer faces sit at x 94.1–97.6. The largest size that keeps every pit closed is 5.25 x 4.1, which leaves 0.28 at the top of the upper pit (4.5 x 3.75 leaves 0.91).
  - **Run 2, built and gated** (SHA-256 `4A194F9D…`; hard gates pass; pit walls z 0..10.2 3.271 / 4.629, latch 3.543 / 5.979): 12 x 6 ahead of the pits and between them, eased to 4.5 x 3.75 over each pit. The edge scalloped: 1 mm in from the flank it drops 1.9 mm between the pits and rises again (z 10.16 → 8.24 → 10.10 over y 24 → 33 → 40); turn 7.5° per 0.5 mm, 14° per 1 mm. It reads as finger-like waves.
  - **Extra loft stations** at y 27–39 grew the body loft by 9944 mm³ and moved the rear corner by up to 20 mm.
  - **Process failure:** the brief came from the orchestrator's reading of the user's words. It skipped the user's marked render (`renders/VitaGripPS5_v2_latch_front.xcf`) and the form-auditor register, and it left out the marked handle-junction area (y -20..16).
  - **Do not:** vary the edge size along y between the pits.
- **Round topface (2026-10-06..08): the flat top Z 11.4 rounded. Rejected by the user ("si no se puede eliminar la cara plana siguiendo la línea de los mangos, entonces no se hace"); v2 stays at pass latch (`817c403`).**
  - **Option 2, outer edge only** (`parts/topface.py`, one lofted cutter; pit face moved in 0.6, flex gap 1.9): the handle's y -27 profile in front, a blend to a constant r 5.000 from the lower pit (y 11.34) to y 58. Builds `topface` (`14762B33…`), `topface_seams` (`B7C7CF75…`), `topface_seams2` (`A6CF4BBD…`): pit walls z 0..10.2 3.163 / 5.72, seams <= 7.94° to y 58.6, but the blend bent 14.8° / 17.9° along y at y 4.25 and the cut's rear end read 10.5° and 82–108° on 1.6–3.3 mm edges (designer's numbers). The user rejected option 2 itself: they meant the whole top face crowned ("option 4").
  - **Crown, the whole top face** (`crown_R` 27, lift 0.15; crest x 89 in front ramping to x 93 over y 0..11.34; inner side a parabola, drop 1.5 at 20 mm; `border_r` 4.5; front fade y -24..-16). Build `topface_crown` (`8DCE9A5D…`): 1 body, watertight, genus 2, 0 sealed, but the upper pit wall read 2.832 at z 10.2 (< 3.0).
  - **Why it failed, measured** (user mark `audit/topface/crown_roi_R.xcf` on crown3, located by ray-cast, silhouette IoU 0.992: x 74–106, y -12..9). The top has hollows where the latch part has none. Pooling depth along a line, W 12 mm:

    | Zone | latch | crown3 (marked) | crown (built) |
    |---|---|---|---|
    | Outer junction, x 92–108, y -20..12 | 0.008 | 0.995 at (100.8, -5.8) | 0.580 at (100, -7.3) |
    | Inner front corner, x 66–86, y -20..-9 | 0.050 | 1.269 at (74, -13.8) | 0.542 at (74.3, -15.5) |

    - Cause, at x 100 along y: a ridge at y -20 (z 9.9–10.4), where the front fade leaves the handle's root flare uncut; a plateau of 9.21 at y -15..0 (the R 27 circle with the crest at x 89); then up to 10.63 from y 10 (the crest at x 93). The two circles give exactly 9.21 / 10.63.
  - **Why the handle's line cannot be followed with the latches untouched:**
    - The handle's crest runs inward toward the body: x 91.3 at y -50, 88.4 at y -28, 87.3 at the root (y -24). It does not run toward x 93.
    - Upper pit wall at z 10.2 with the crest at x 87.3 (`crown_model.py`): 0 at R 20.2 (the handle's own radius) and at R 40, 1.6 at R 60. R 75 is the tightest that holds 3.0, a nearly flat top (about 1.3 mm drop over 13 mm). Control: crest at x 93 → R 25.2.
  - **Not tried:** a crest that drifts monotonically from 87.3 to 93 over y -24..11.34, with the cut starting from the handle's own section (no fade). In principle it leaves no hollow, but it leaves the handle's line by up to 5.7 mm.
  - **Process:** option 2 was built for a whole day from a record of the user's choice that was never checked against their marks; the crown was built by the orchestrator without a register or a designer pass.
  - **Do not:** hold the crest at one x in front and another over the pits; fade the cut in where the old surface is rising (both make a hollow). Gate any top-face change with a hollow (pooling-depth) map against the latch part.

## Verification checklist (open)
- The rear corner (y 59-77) is simplified; it is not verified against r16. The window, camera hole, lower lips and bottom opening were added in pass 2.
- Lock check against r16 (pass 2, measured on `stl/VitaGripPS5_v2_p2.stl`, `audit/p2/fix_report.md`). These pass: lip u on all four lips (max 0.0002 from r16), the floor, and the change against pass corner. These are open:
  - the bottom-bar strip differs from r16 by up to 1.29 mm (v2's simplified plate; unchanged since the spike);
  - pocket wall 0.021 at (87.68, 57.67, z 0) and 0.010 at (-87.18, 59.01, z -5), where the lock is 0.005;
  - the window outline is 0.0075 and the camera hole 0.0056 from r16's mesh. v2 sits on r16's design constants; the measured offset is r16's mesh edge;
  - upper pit walls 3.95–4.93 (r16 3.43–3.99), lower pit walls 7.72–9.50 (r16 R 7.08–9.53). This is the outer loft, untouched.
- Ring wall in front of the bottom opening's closed end (x 67): 2.28 mm at z -8.7, 2.71 at z -6 (r16: 3.30 / 3.54; r16's `OPEN_WALL` rule is 3.15). This is the loft's outer face, the same on pass corner.
- No structural check: print-tolerance-expert has not seen this geometry, including the lower fingers.
