# SurgicalDrillGuide

A printable functional replica of a ratcheting K-wire / drill guide, rebuilt from photos. A Ø3 mm K-wire runs along the L-arm top bar and through the C-hook tip on one line. The L-arm slides on a toothed rack that is part of the main frame, and a flexure pawl with a hooked tooth locks it against opening. A threaded handle screws into a boss under the bar, and a removable pin stops the slider at maximum opening.

**Status (2026-10-17, later): fix round 7 is built (build + 2 fix passes), gated, form-audited and structurally checked.** New ratchet for a 0.4 nozzle (pitch 2.6, depth 1.4, 4-tooth pawl, flexure variant B), reinforced release stops, and a flat on the handle's −X face. See "Fix round 7". Nothing printed.

**Round 6 (2026-10-17): built (3 passes), gated and form-audited.** The threaded handle joint is replaced by a lug, a blind socket and a snap finger; the frame is a uniform 10 mm slab; the bar top is raised; the C-hook has an outer band. The user accepted the base design on 2026-10-17 ("está bien el diseño base"); the four form-audit entries R6-1…R6-4 are left as built (see "Fix round 6"). Nothing printed. Sections below "Fix round 6" that describe the boss, thread and collar are the rounds 3–5 record.
- Round 4 implements the user decisions after the 25 N re-check (`docs/MECHANISM_STRATEGY.md`, "Round 3 re-check at 25 N"): a **Ø22 handle collar that seats on the boss face**, carriage **top wall 2.5** and carriage **floor 2.5**. See "Round 4" below.
- All 11 export files were regenerated in round 4; every part was `is_valid` True (1 solid) before any file was written (the build now refuses to export otherwise). The gates below were run on those files.
- Round 3 implemented hooked teeth, tab hard stop, Tr16×4 thread, Ø22 boss, Ø16 handle core, new clearances, `RACK_EXT` 4.6.
- Structural checks and final clearances belong to `print-tolerance-expert`.
- Nothing has been printed or test-fitted.

v1 (wire bored through Z, no long bar, a hard-coded "0.00" coaxiality gate) is parked in `attempts/v1-zbore-separate-parts/`. The history and the earlier user decisions are in `attempts/rebuild-wip-2026-09-22/HANDOFF.md`.

## Inputs

| Input | File | Status |
|---|---|---|
| Measurements | `docs/MEASUREMENTS.md` (reference-analyst, 2026-09-23) | Photo-derived. Scale 3.443 px/mm, ±2.5 % absolute. The ruler reads 2.2 % smaller (user's call, U10) |
| In-plane outlines | `vectors/import/*.dxf` (vector-tracer; all rings PASS on accuracy re-review) | **Imported at build time** with `import_dxf()` |
| Form audit | `docs/FORM_AUDIT.md` (form-auditor, 2026-09-23) | Its findings drove rounds 2 and 3 |
| Reference photo | `attempts/rebuild-wip-2026-09-22/completeDevice1.png` | Used for the whole-form comparison |

Every in-plane outline comes from a traced ring. Primitives are used only for designed features that no photo shows, and for fusion slugs inside traced outlines. The exceptions are the documented, user-approved additions: the **C-tip pad**, the **rack extension**, the **carriage top wall** and the **handle core**.

## Parts and files

All parts share the vector datum:
- the origin is the rack left tip, on the rack top edge;
- +X runs along the rack towards the hook;
- +Y is up;
- +Z is thickness.

The frame mid-plane is Z 5.000. This departs on purpose from the repo's "origin at bottom-face centre" convention, so that assemblies need no re-derived placement.

| Part | Files | Volume (STEP) | Bounding box (STL), mm | Solid fraction (STL vol / bbox) |
|---|---|---|---|---|
| main_frame (round 7): C-hook with outer band, bar (raised to Y 7.5 on the hook side), rack with r7 teeth and flat underside (+4.8 mm extension), lug and snap finger, uniform Z 0…10 | `SurgicalDrillGuide_main_frame.step/.stl` | 30 787.8 mm³ (STL) | X −4.850…182.029, Y −29.850…57.643, Z 0.000…10.000 | not re-measured |
| l_arm_slider (round 7): L, collar, carriage (2.5 top wall, 2.5 floor), 4-tooth pawl on a 1.759 flexure, release pad, two-point stop on a reinforced beam and leg, one slab | `SurgicalDrillGuide_l_arm_slider.step/.stl` | 27 476.09 mm³ (STL) | X 60.022…137.040, Y −33.890…56.705, Z −3.300…13.300 | not re-measured |
| handle (round 7): grip (butt faced 1.5) with a flat on the −X face at X 111.111, Ø16 core, square head with lug socket and snap notch | `SurgicalDrillGuide_handle.step/.stl` | 45 952.9 mm³ (STL) | X 111.111…135.347, Y −147.046…−9.850, Z −8.036…18.036 | not re-measured |
| end_stop_pin (separate, removable) | `SurgicalDrillGuide_end_stop_pin.step/.stl` | 117.1 mm³ (STL) | Ø3.0 × 16.6 at X −1.484, Y −3.852 (round 7), Z −3.3…13.3 | 0.785 |
| Assemblies at MIN / MID / MAX | `SurgicalDrillGuide_assembly_{min,mid,max}.stl` (4 parts each; see note) | | | |
| Renders (round 4) | `*_front.png` and `*_iso.png` for slider and handle; `assembly_min_front.png`, `assembly_min_vs_reference.png`. Frame front/iso are round 3 (frame geometry unchanged: same volume 25 996.96) | | | |

**Assembly STL note (round 4):** the collar's r 11 edge and the boss's r 11 edge are the same circle at the seated pose, so a mesh loader that merges vertices joins frame and handle there. `render_check.py` on `assembly_min.stl` now reports body_count 5 and not watertight; the four part STLs are each 1 watertight body. The assembly files are visualisation only. `sdg_gates.py` gate 5 therefore places the per-part STLs with the macro's own `slider_at()` and cross-checks them against the assembly file (volume 93 471.5 = 93 471.5; 12/12 rays agree at every pose).

Source and gates:
- `macros/surgical_drill_guide.py` builds the parts. Run: `python "D:\CAD\Claude-Projects\projects\SurgicalDrillGuide\macros\surgical_drill_guide.py"` (11.1 s, all parts and the three assemblies). Export happens only under `if __name__ == "__main__":`.
  - Add `--part main_frame|l_arm_slider|handle|end_stop_pin` to build and export one part only: 7.6 / 5.3 / 6.3 / 4.3 s. About 4.3 s of each run is fixed cost (imports and `parameters()`). This does **not** rewrite the assembly STLs, so run the full build before the gates.
  - Split into stage files on 2026-09-25, in the package `macros/sdg_model/`: `constants.py`, `rings.py`, `shapes.py`, `mechanisms.py`, `parts/<part>.py`, `parameters.py`. The main holds no geometry. The package name is unique to this project. With the stage files loose in `macros/`, a second project's `constants.py` was tested in the same process: SurgicalDrillGuide loaded first gave the second project SurgicalDrillGuide's `T_Z` silently, and the reverse order raised an `ImportError`. With the package, both orders read the right values. The split is output-identical: all 11 exports byte-identical (STEP header excluded), and the macro stdout, the 134-line gate log and the 219-line `docs/mechanism_sizing.py` log unchanged. The main re-exports every stage name, so `sdg_gates.py` and `tools/reconcile.py` run unchanged.
- `macros/sdg_gates.py` measures every gate on the exported STL/STEP. Run: `python "D:\CAD\Claude-Projects\projects\SurgicalDrillGuide\macros\sdg_gates.py"`.

## User decisions

**Rebuild, 2026-09-23:**
- 10 mm Z for the frame, rack and hook.
- Match the photos' opening range.
- Ø3 K-wire, with the bore drawn Ø3.4 as a teardrop and reamed to 3.2.
- A closed C-tip bore.
- A separate printed handle: female thread in a boss, male thread on the handle.

**Fix round 2, after the form audit:**
1. **The L-arm is 16.6 mm in Z** (−3.3…13.3, centred on Z 5). The riser, top bar and crown match the collar and carriage, so the slider is one slab. The frame, rack and hook stay 10 mm. The wire bore stays at Y 51.796, Z 5.000.
2. **The frame is thickened around the handle boss**, flush with the boss on both faces, and tapers back to the 10 mm bar.
3. **The C-tip is thickened round the wire bore, never cut.** The wall must be ≥ 1.5 mm, measured perpendicular to the faces.
4. **A removable end-stop pin** goes through a Z hole near the rack's free end; the rack is extended so that the last seated pose gives a tip gap of ≥ 74.0 mm.
5. **The pawl seat gap is uniform.**
6. **Printability is not a design criterion.** Supports and orientation are the slicer's job.

**Fix round 3:**
1. **Hooked teeth:** 10° undercut on the rack locking wall and the pawl tooth face (`TOOTH_HOOK_DEG`).
2. **Tab hard stop:** the pawl can drop at most 0.80 mm (`TAB_STOP_DROP`).
3. **Carriage top wall 2.0 mm** over the channel ceiling (`CARRIAGE_TOP_WALL`).
4. **Tr16×4 thread** (was Tr10×2) with a **Ø22 boss** (was Ø16); boss pad Z −6…16.
5. **Handle core Ø16** from 2 mm inside the grip to the shoulder; no section between thread and grip narrower than the thread major.
6. **Clearances:** `SLIDE_CLEAR_Y` 0.20, `PIN_FIT_CLEAR` 0.20 (with the pin's c/2 slop in the stop), thread 0.30 radial / 0.15 axial.
7. **`RACK_EXT` 4.6** (was 4.5). User accepted.

**Fix round 4 (after print-tolerance-expert's 25 N re-check):**
1. **Handle seating, option (a):** a Ø22 collar on the handle whose flat face seats on the boss face, so side load puts the thread in tension instead of radial bearing. The collar changes the traced ferrule form (accepted).
2. **`CARRIAGE_TOP_WALL` 2.0 → 2.5.**
3. **Carriage floor to 2.5** (was the traced 1.97–2.05), or the largest value that fits (≥ 2.0), without changing the pawl, rack or channel.

### Round 4: what changed and what was measured

| Item | Before (round 3) | Round 4 | Measured on the STL |
|---|---|---|---|
| `CARRIAGE_TOP_WALL` | 2.0 (1.517 at the squared corner) | **2.5**, end squared | 2.500 at every station X 72…106.45, incl. the end (vertical rays, Z 5) |
| `CARRIAGE_FLOOR` (new) | traced, 1.97–2.05 | **2.5** outside the tongue | 2.500 at X 70.5, 95.5, 100, 103, 106.45; 45° chamfer 2.427 / 2.127 at X 72.0 / 72.3 |
| Pawl tongue | traced bottom, t 1.979–2.015 | **unchanged** (built from the traced carriage) | 1.979 (X 73), 1.994 (X 80), 2.015 (X 90) |
| Carriage +X end | traced end 106.46–106.48 + top box to 106.486 (0.048 sliver) | squared, one plane at X 106.475 (traced end at channel mid-height) | X 106.475…106.475 on 18 rays over the full height |
| Handle collar (new) | none: Ø16 core stopped short of the Ø17.1 mouth | Ø22 × 3.0, face at Y −19.003, 45° cone under it to r 7 | r 10.993 at the face and 3 mm down, 8.998 at 5 mm, 7.995 (core) at 7.3 mm |
| Female mouth | "45° chamfer 1.0" (never built as such) | same geometry, now named `BOSS_MOUTH_FACE_CLEAR` 0.25 / `BOSS_MOUTH_DEPTH` 1.0 | contact annulus starts at r 8.55 |

**Why the floor stops at the tongue.** The tongue is the carriage floor between X 72.5 and 94.0. At the tab hard stop its stress is set by displacement (3Eδc/x²), so a thicker tongue is *more* stressed: print-tolerance-expert put it at SF 3.15 (t 1.917) / 2.99 (t 2.017). A 2.5 tongue would scale to about 2.4. So the floor is 2.5 left of the anchor and right of the free-end slot, and the tongue keeps the traced bottom. There was no other conflict: nothing of the frame lies under the carriage at any pose (interference 0.0 at MIN / MID / MAX), the tab stop leg merges into the thicker floor, and the window cut still reaches below the new floor (Y −14.5 vs −12.065).

**Why the female mouth read r 8.42.** The mouth cutter was `cone_y(y_bot − 0.5 → y_bot + chamfer, r = f_crest + chamfer + 0.5 → f_root)`. It starts on a 45° line (9.8 at 0.5 outside the face) but ends at the female **minor** radius 6.05 instead of the major 8.30. The cone therefore has a slope of 2.5 (68.2° from the axis, 21.8° from the face). The face radius is 8.55, and 0.05 in it is 8.425, which is form-auditor's 8.42. It was never the 45° chamfer the constant described. Round 4 keeps this geometry (frame volume unchanged) and names it with its own constants. The reason: it clears the male crest at the face by 0.55, gives full female ridges from 1.0 deep, and leaves a **2.45 mm seating annulus** (r 8.55 → 11.0). A true 45° countersink to r 9.3 would leave 1.70 mm and cut the ridges down to 3.25 deep.

**Seating arithmetic.** The model is the seated pose, with collar face = boss face = Y −19.003. The male tip is at −11.003 and the hole floor at −10.387, so **tip → floor is 0.616 > 0**. Nothing wider than the male crest (r 8.0) sits above the collar face. The Ø16 core now ends 4.5 mm below the face, inside the collar. The first female material inside r 7.9 is 0.253 mm above the face. So, screwed in, the collar lands on the boss face first. The axial engagement is unchanged from round 3 (same male and female positions): full profile over 6.0 mm (1.0 → 7.0 above the face: mouth to male tip chamfer), and possible contact over 0.22 → 8.0.

**Fix round 5 (user decisions, 2026-09-24):**
1. **Stop pad raised: `TAB_STOP_DROP` 0.80 → 0.73.** print-tolerance-expert: the pawl tongue stress at the hard stop is displacement-set, SF 3.00 at a 0.80 drop, 3.29 at 0.73. 0.73 keeps 0.10 over the worst tooth overlap it used (0.630). Measured on the STLs (gate 5): gap under the tab 0.730 at every pose; margins over the drop needed to OPEN / CLOSE are **0.124 / 0.120** (MIN), 0.194 / 0.190 (MID), 0.268 / 0.264 (MAX). Slider∩frame interference 0.0 mm³ at all three poses.
2. **Stop leg flush with the squared carriage end.** The leg's +X face was `carriage_x1 − 0.1` = X 106.386 (from the traced max 106.486), a 0.089 step behind the squared end at 106.475 below the floor (form-auditor, Y −12.08…−31). The leg is now built 0.5 past the end and the whole end is trimmed at `carriage_end_x` in one cut. Gate 3 end-face rays now run from the beam bottom to the top wall (41 rows, Y −30.95…2.71, Z −3 / 12.9): **X 106.4755 on every ray, including the 16 leg rows below the floor; step 0.0000.** The gate was not re-run on the round-4 mesh (overwritten), so it has not been shown to catch the old step on a mesh. It does cast rays through Y −30.95…−12.2, where form-auditor measured the leg face at 106.386.
3. **Pad clearance unchanged:** a new gate-5 check (Y-normal sections every 0.25 from Y −31.95 to 3, form-auditor's method) gives a true 2D minimum of **2.0581** at Y −9.2 at MIN. On the stop-leg rows (below the floor) the nearest frame material is 4.841 away. The earlier ray check still reads 2.199.

**Fix round 6 (user decisions, 2026-10-17).** Sizing and reviews are in `attempts/coupling-review-2026-10-17/` (local only): `coupling_sizing.md`, `bar_and_snap.md`, `neck_audit.md`, `neck_sizing.md`; build reports `r6/build_report.md`, `r6/pass2_report.md`, `r6/pass3_report.md`; form audit `r6/review_register.md`. Structural check: `docs/mechanism_sizing.py` (rewritten for round 6 pass 3; its output is not recorded here).
1. **Uniform Z 0…10, frame prints flat (−Z on the bed).** The boss, boss pad, Tr16×4 female, mouth cone, handle collar, male thread and ferrule are removed. Retired constants: `BOSS_*`, `THREAD_*`, `HANDLE_COLLAR_*`, `BOSS_MOUTH_*`, `BOSS_PAD_*`. The pad clearance check is replaced by `COUPLING_CARRIAGE_CLEAR` 2.0, applied to every new material at bar level (the build raises below it).
2. **Coupling, concept D** (`coupling_sizing.md`, `bar_and_snap.md`):
   - **Lug** on the frame: 14 × 10, X 115.311–129.311, from the bar bottom to Y −29.85; r 3 in-plane root fillets; 0.4 × 45° foot chamfer on the straight Z 0 edges.
   - **Head** on the handle: 22.4 (X) × 22.0 (Z) × 23.0 (Y), Y −9.85…−32.85. Blind socket 14.4 × 10.4 × 20 (`SOCKET_CLEAR` 0.20 per side), floor 3.0. Mouth chamfer 2.0 × 45° on ±X (clears the lug root fillets: measured gap 0.160) and 0.5 on ±Z. 1.2 × 45° chamfer on the top +X edge. A 40° cone runs from the head into the Ø16 core.
   - **Snap finger** on the frame: 1.6 × 10 plate at X 133.711–135.311, root r 1, tip Y −29.4. Hook Z 2–8, 0.9 deep, 30° insertion ramp, 45° gable retention face with a 10° back-cut, 0.9 × 0.95 under-chamfer. Notch in the head's +X face: depth 1.2, Z 1.7–8.3, floor Y −26.68, roof rising 10° toward −X.
   - Measured (gates): lug-in-socket 0.2000 per side; push stop (lug end on floor) 0.0000; head top → bar bottom 0.485–0.799; hook engagement 0.700; pull slack 0.315; interference 0.0 mm³ for all pairs at MIN / MID / MAX.
3. **Raised bar:** 45° ramp from X 108.475 (2.0 past the carriage end at MIN) to a flat top at Y 7.5, blended (r 3, adds only) into the hook's inner contour at X 166.5. Bar depth 16.3–16.7. **The throat to the slider top bar is now 39.0 (was 46.3)**; bar top to the wire line 44.3. Slider → new material at MIN 2.0081 in-plane.
4. **C-hook outer band** (pass 2 sized by `neck_sizing.md` §4; pass 3 smoothed): outer contour offset 5.6 over s 18–32 (blend from 0 at s 12), 3.6 from s 36 to 63, to 0 at s 66; built as the convex hull of that disc sweep with an r 4 fillet at the bar bottom, ending on the traced corner at the C-tip pad's bore-exit face. Frame X max 176.700 → 182.029; added 287.15 mm². Wire-axis clearance beyond the bore exit 2.030 (limit 2.0). At s 64–66 the band is below print-tolerance-expert's X-mid requirement (the 2.0 wire clearance binds).
5. **Handle butt faced 1.5 mm** (`BUTT_FLAT` 0.06 → 1.5, user decision): the traced 1.45 mm dome is removed; the handle prints standing on a 207.2 mm² flat.
6. **Slider and pin:** byte-identical to round 5 (SHA-256).

**Round 6 form audit (`r6/review_register.md`), left as built by user decision:**
- R6-1: where the band leaves the bar bottom (X 156–172) the outline has a 1.11 mm wave (notch 1.555 below the hull).
- R6-2: across the back, R 30 → a tight R 7.32 turn at (182.03, 13.54) → a 10.8 mm straight.
- R6-3: the band ends against the C-tip pad in an unfilleted 97.8° corner (r5: 139°).
- R6-4: both bar-ramp corners are sharp (designed polyline).

**Fix round 7 (user decisions, 2026-10-17).** Files in `attempts/r7-ratchet-2026-10-17/` (local only): sizing `ratchet_sizing.md`; coupons `coupon/` (not printed: the user judged the fit from the slicer); build and fix reports `full/build_report.md`, `full/fix_report.md`, `full/reinforce_report.md`; form audit `full/review_register.md`; structural log `full/sizing_r7reinforce.log` (from `docs/mechanism_sizing.py`, reconciled strictly against the macro).
1. **Why:** with a 0.4 nozzle the old teeth (pitch 1.61, depth 0.80) do not grip. Print-tolerance-expert's model: corner rounding of about half a line costs 0.656 of the 0.46–0.61 overlap, so the 10° hook is not reproduced. Not measured on a print.
2. **Rack teeth:** pitch 2.6, depth 1.4, cutter land 0.5 (tooth tip 0.875), 15° undercut locking wall, ramp 33.69°. 38 notches. Rack underside flat at Y −9.351 to X 100.7 (deviation from the trace; it was sloped 0.145). `TEETH_START_MARGIN` 2.45, `RACK_EXT` 4.8. Poses: MID 12, MAX 23 teeth (travel 59.80, tip gap 74.272). The jaw now opens in 2.6 mm steps.
3. **Pawl:** 4 teeth on a rigid 5 mm block (X 90.82–101.6). Uniform flexure, **t 1.759 (variant B, user decision: firmer release, stop SF 2.69 nominal accepted)**, anchor X 70.5; root is an r 0.5 fillet onto the collar wall (no V-groove), with an r 0.5 fillet at the top step in the outer Z bands. Free length 19.878 (centre band) / 19.820 (outer bands). Measured on the STL: overlap 1.1697 and seat gap 0.1000 for every tooth at MIN / MID / MAX; flat locking contact 1.184 in CAD (about 0.43 after the assumed print rounding).
4. **Release:** pad X 90.32–103.4, full slider Z, Y −24 kept. Release force 4.3–5.6 N (sizing). Two-point stop: inner gap 1.30 at the inner tooth face, outer gap 2.77 at X 102.4. Pressed to the inner stop, the 4 teeth clear the rack (gate: lift check 0 mm², controls collide). Stop beam 3.62 thick with an r 1 beam-leg fillet; stop leg 4.0 below the floor underside (X 103.975–107.975), 2.5 where it joins the floor (the carriage end stays one plane at X 106.475 above the floor, the coupling clearance lock), r 1 fillet at its −X top corner.
5. **Handle flat:** one plane on the −X side at the head's −X face (X 111.111, derived from the constants), over the whole length. It cuts only the two grip swells; the flat totals 832.04 mm² (head face 582.92, grip 170.55 + 78.58). No knife edge (smallest edge angle 106.9°).
6. Round-6 interfaces (coupling, snap, raised bar, hook band) are unchanged and re-gated: interference 0.0 for all pairs at MIN / MID / MAX.

**Round 7 structural check (25 N, PETG assumed, Kt values are assumed chart readings):**
- Holding load through the teeth: SF 4.07 at the flexure root; teeth 8.4–17.2; no cam-out; rack net section 3.14.
- **Below 3, accepted by the user:**
  - Flexure at the stop: 2.69 nominal (user decision, variant B); 1.64–1.81 with Kt.
  - Flexure root under a 25 N press on the pad: 1.60.
  - Flexure → block square corner: 1.73.
  - **Stop leg** where it joins the floor: 1.27 (−X, tension) and 1.21 (+X square corner, compression). It holds about 11 N of finger force on the pad at SF 3. The user's reasoning (2026-10-17): the stop is only a travel limit; the working load goes through the teeth.
- Click stress with Kt 22.3 MPa vs an untested 10.6 MPa fatigue estimate.
- Pin → collar at MAX 0.118: within FDM positional error. If the collar reaches the pin first, MAX seats at 22 teeth and the tip gap is 71.67.

### Assembly and use

- **Release (round 7):** with the jaws unloaded, press the pad under the carriage with one finger (about 5 N) and slide. Do not lean on the pad: the stop holds about 11 N at full margin.

- **Handle (round 6):** push the handle up onto the lug until the finger clicks into the notch; the lug end then rests on the socket floor. Under a pull the handle drops 0.315 before the hook bears on the notch roof. To remove: with the handle unloaded, lift the finger tip about 1 mm in +X and slide the handle off (−Y). There is no over-lift stop; do not lift more than about 1 mm (`bar_and_snap.md`: 2.45 % strain at 2 mm).
- *(Rounds 4–5, retired)* The threaded handle had to be screwed fully home until the collar seated on the boss face.

## What was built

1. **main_frame.** `main_frame_body.dxf` extruded to Z 0…10. Added to it:
   - **Rack teeth** on the bottom face: 62 notches at a pitch of 1.61 mm, X −0.486 → 99.334, continued in phase into the extension.
     - Each notch is a sawtooth: closing (+X) rides the ramp, opening (−X) is blocked by the locking wall.
     - **Round 3:** the locking wall leans 10° (undercut). Measured on the STL: 10.00° at every pose.
   - **Closed C-tip wire bore**, Ø3.4 teardrop, on Y 51.796, Z 5.
   - **C-tip pad** (DESIGNED, user-approved): a sleeve round the wire line, Y 51.796 ± 3.50, from the jaw face (X 150.648, unchanged) to X 163.605, blended by a 1.5 mm closing that only adds material.
   - **Boss pad** (round 3): the bar is Z −6…16 over the flat X 111.311…133.311 (= the Ø22 boss width), tapering to 10 mm over **2.8 mm at 65.0°** each side (from X 108.511 and to X 136.111). The taper length is forced by `BOSS_PAD_CARRIAGE_CLEAR`: the taper starts 2.026 mm past the carriage end at MIN (the build raises an error below 2.0). Clipped to the traced bar outline, so the in-plane outline is unchanged. Measured slope 2.143 = 65.0° at Y −1, −5 and −8.5.
   - **Handle boss:** Ø22, axis X 122.311, down to the ferrule shoulder (Y −19.003). Blind **Tr16×4** female thread, floor at Y −10.387 (first frame hit up the axis).
   - **Rack extension**, 4.6 mm (`RACK_EXT`). See "Rack extension and end-stop pin".
   - **End-stop pin hole:** Ø3.20 (pin 3.0 + `PIN_FIT_CLEAR` 0.20), a Z through-hole at X −1.292, Y −4.152, inside the extension.
2. **l_arm_slider.** Built from `l_arm_body.dxf`, `l_arm_collar.dxf` and `l_arm_carriage.dxf`, all over Z −3.3…13.3; 1 solid.
   - **Rack channel:** Y −9.565…0.257 (frame envelope −9.365…0.057 + `SLIDE_CLEAR_Y` 0.20), Z −0.3…10.3.
   - **Carriage top wall** (round 4: 2.5): 2.500 mm over the channel ceiling at X 72–106.45 (vertical rays, Z 5), including the squared end. Adds 38.673 mm² to the traced carriage at Z 5, max offset 1.082 along the top (X < 105.49), 1.295 including the squared corner.
   - **Carriage floor** (round 4): 2.500 under the channel from inside the collar to the anchor (45° chamfer up to the tongue) and from the free-end slot to the end; the tongue keeps the traced bottom. **+X end squared** at X 106.475.
   - **Wire bore:** Ø3.4 teardrop along the full top bar.
   - **Compliant pawl** (DESIGNED substitution): tension tongue X 72.5…94.0, hooked sawtooth tooth seated in notch 57 (a = 91.284) at MIN, 0.8 mm free-end slot, release tab with thumb pad.
   - **Tab hard stop** (round 3; round 5 drop 0.73): a stop block under the tab leaves a 0.730 mm gap (measured), so the pawl can drop 0.73 and no further; 2.000 mm relief under the pad end. The stop leg's +X face is flush with the squared carriage end (X 106.4755, round 5).
3. **handle.** The traced grip and ferrule halves revolved about X 122.311, Z 5.
   - **Ø16 core** (round 3) from 2 mm inside the grip top; round 4 ends it 4.5 mm below the shoulder, inside the collar. Measured STL radius from grip top to shoulder ≥ 7.995; it adds 66.05 mm² to the traced silhouette, max offset 1.384 mm.
   - **Ø22 seating collar** (round 4, user decision): one revolved profile, a Ø22 × 3.0 cylinder whose top face (Y −19.003) is flat, square to and coaxial with the handle axis, plus a 45° cone under it down to r 7 inside the core. It adds 39.22 mm² to the traced silhouette at Z 5. The traced ferrule (r ≤ 7.49) is clipped 1.0 below the face, so no face coincides with the collar face.
   - The butt has a 0.06 mm flat (the traced 0.05 mm cone otherwise tessellates to a degenerate pole triangle).
   - **Male Tr16×4**, exposed 8 mm from the collar face (Y −19.003) to the tip (Y −11.003), 1 mm 45° lead-in, phase-locked to the female (see below). Round 4: the cam starts one pitch **below** the face, inside the collar (r 11), so that no surface coincides with the crest r 8.0 and the fuse is a real overlap. The phase is unchanged: the male and female origins still differ by whole pitches.
4. **end_stop_pin.** A Ø3.0 cylinder, Z −3.3…13.3, fitted after the slider is on.

### Handle export hang (round 3 blocker)

- **Symptom:** the full build wrote `SurgicalDrillGuide_handle.step` and then ran 81 min on 2 cores without writing the STL.
- **Measured cause** (`cad3/probe.py`, each stage in a child process with a timeout): the handle solid was **`is_valid` False** (240 faces). Every input was valid on its own (body, butt flat, clipped male thread); only the final `handle + male` fuse was invalid. The male thread started one pitch **below** the shoulder, inside the new Ø16 core, and the core's surface coincides with the male crest radius (r = 8.0). Coincident surfaces in that fuse gave an invalid solid. STL at 0.03/0.2 then timed out (> 90 s in the probe, 81 min in the build). At 0.01/0.1 it finished in 2.4 s, but that probe run also printed "23 faces have been skipped due to null triangulation" (the output did not show which stage), and the solid was still invalid, so tolerances were not treated as the fix.
- **Fix** (`build_handle`): the male now starts **at** the shoulder (length = engage, 8 mm). Its bottom face lands flat on the core top. Result: `is_valid` True, 1 solid, 211 faces, STL 0.03/0.2 in **0.7 s**, watertight, 1 body. The alternative (core r + 0.25) also worked but changes the core Ø.
- **Phase lock kept:** the female cam starts at y_sh − 2P and the male at y_sh; they differ by 2 whole pitches. The female is the male cam + 0.30 radially with the crest 0.15 wider per flank.
- Full build after the fix: all 11 files written, about 10 s.

### Rack extension and end-stop pin

**Why the rack is extended.** On the traced rack the collar's −X face is at X 0.452 at a 74 mm opening while the free end is at X ≈ 0. A Z pin has to sit left of the collar face to catch it; on the traced rack the pin would limit MAX to a 69.2 mm tip gap.

**`RACK_EXT` = 4.6 mm** (user decision; 4.5 in round 2, 4.6 accepted in round 3). With `PIN_FIT_CLEAR` 0.20 and the pin's c/2 slop, 4.5 leaves a worst-case MAX→pin gap of 0.044 (< `PIN_STOP_MIN_GAP` 0.10), MAX falls to 36 teeth and a 72.432 tip gap, and the build refuses.
- Measured on the STL: free end X −4.650 against the traced −0.050, **4.600 mm added**, 29.15 mm² above the teeth band. The pin hole takes 0.376 mm² of traced rack end.
- Rack height on the STL at Z 1: 8.490 at X −3, 9.105 at X −1, 9.110 at X +1; top at Y 0.000 in all three.
- The build refuses to run unless the MAX tip gap is at least `TARGET_MAX_GAP` (74.0).

**Poses (measured on the assembly STLs):**

| Pose | Travel | Tip gap at wire height |
|---|---|---|
| MIN | 0 | 14.472 |
| MID (18 teeth) | 28.980 | 43.452 |
| MAX (37 teeth, the last seated tooth) | 59.570 | **74.042** |
| Stop (collar on the pin), pin centred / pin 0.10 towards the collar | 59.834 / 59.734 | 74.306 / 74.206 |

At MAX the collar is 0.264 mm from the centred pin, 0.164 with the pin at the collar side of its hole.

### Thread choice (DESIGNED, round 3)

Tr16×4 (ISO 2904 pitch for d = 16): 30° trapezoid; male major Ø16, root Ø11.5 (`THREAD_H` 2.25), crest 0.366P; female = male + 0.30 radially, groove 0.15 wider per flank. Modelled as a cam section extruded with 360° of twist per pitch (an exact helix). Measured at MIN over one pitch: male r 5.739…7.999, female r 6.041…8.300, **engagement 1.958 mm, minimum radial gap 0.294 mm**.

## Constants and their status

Z is not measurable in any photo, so **every Z value is ASSUMED or a user decision.** PLACEHOLDER = a clearance for print-tolerance-expert to set.

| Constant | Value | Status |
|---|---|---|
| `T_Z` frame / rack / hook | 10.0 | ASSUMED (user decision) |
| L-arm Z (`L_ARM_FULL_WRAP_Z`) | −3.3…13.3 (16.6) | ASSUMED (user decision, fix round) |
| `WRAP_WALL_Z` / `SLIDE_CLEAR` (Z) | 3.0 / 0.30 | ASSUMED / PLACEHOLDER (print-tolerance-expert: keep) |
| `SLIDE_CLEAR_Y` (channel Y, only in `derive_channel`) **[round 3]** | 0.20 | PLACEHOLDER (print-tolerance-expert) |
| `CARRIAGE_TOP_WALL` **[round 4]** | **2.5** (was 2.0) over the channel ceiling, +X corner squared | DESIGNED (user decision, round 4) |
| `CARRIAGE_FLOOR` **[round 4, new]** | 2.5 under the channel, outside the pawl tongue (tongue = traced, 1.98–2.02) | DESIGNED (user decision, round 4) |
| Carriage end X **[round 4]** | 106.475 = traced end face at channel mid-height (traced max 106.486) | DERIVED |
| `HANDLE_COLLAR_OD` / `HANDLE_COLLAR_T` / `HANDLE_COLLAR_TAPER_R` **[round 4, new]** | 22.0 (= `BOSS_OD`) / 3.0 / 7.0 (45° cone under the collar) | DESIGNED (user decision, round 4, for the OD and seating; T and taper DESIGNED) |
| `BOSS_MOUTH_FACE_CLEAR` / `BOSS_MOUTH_DEPTH` **[round 4, new]** | 0.25 (mouth r 8.55 at the face) / 1.0 (reaches the female minor 6.05) — the as-built round-3 mouth, now named | DESIGNED (round 4) |
| `THREAD_TIP_CHAMFER` | 1.0, 45°, **male tip only** (the comment used to claim the female mouth too) | DESIGNED |
| `TOOTH_HOOK_DEG` **[round 3]** | 10° undercut, rack wall and pawl tooth face | DESIGNED (user decision) |
| `TAB_STOP_DROP` / `STOP_LEG_W` / `STOP_BEAM_T` / `STOP_RELIEF` **[round 3]** | **0.73** (round 5, was 0.80) / 2.5 / 2.5 / 2.0 | DESIGNED (`TAB_STOP_DROP`: user decision round 5); leg +X face = carriage end X 106.4755 (round 5, was 106.386) |
| `BORE_D` / `REAM_D` / `WIRE_D` | 3.4 / 3.2 / 3.0 | user decision |
| `TOOTH_PITCH` / `TOOTH_DEPTH` / `TOOTH_LAND` / `TOOTH_CUT_EPS` | 1.61 / 0.80 / 0.20 / 0.05 | MEASURED / ASSUMED / DESIGNED / DESIGNED |
| `TEETH_X_END` | 100.7 | DERIVED in MEASUREMENTS §3b |
| Pawl: anchor 72.5, free end 94.0, slot 0.8, window top −7.5, tab and pad | | DESIGNED |
| `PAWL_SEAT_CLEAR` | 0.10 | PLACEHOLDER |
| `CTIP_WALL_MIN` / `CTIP_PAD_MARGIN` / `CTIP_PAD_EXIT_MARGIN` / `CTIP_PAD_BLEND_R` | 1.5 / 0.3 / 0.3 / 1.5 | user requirement / DESIGNED |
| `BOSS_OD` / `BOSS_HOLE_FLOOR` **[round 3]** | 22.0 (was 16) / 1.2 | ASSUMED (user decision) / DESIGNED |
| Boss pad flat half-length (= `BOSS_OD`/2, derived) / `BOSS_PAD_BLEND` / `BOSS_PAD_CARRIAGE_CLEAR` **[round 3]** | 11.0 / **2.8 (was 5.0)**, 6 mm per face = 65.0° / 2.0 (the build raises an error if it is violated) | DESIGNED |
| Thread **[round 3]**: Tr16×4 (was Tr10×2), `THREAD_H` 2.25 (root Ø11.5), `THREAD_ENGAGE` 8.0 | | DESIGNED (user decision) |
| `THREAD_RADIAL_CLEAR` / `THREAD_AXIAL_CLEAR` **[round 3]** | 0.30 / 0.15 (were 0.25 / 0.10) | PLACEHOLDER (print-tolerance-expert) |
| `HANDLE_CORE_GRIP_DEPTH` **[round 3]** (Ø16 core from 2 mm inside the grip to the shoulder; replaces `NECK_BRIDGE_R` 4) | 2.0 | DESIGNED |
| `PIN_D` / `PIN_TIP_WALL` / `PIN_PROTRUDE` / `PIN_STOP_MIN_GAP` | 3.0 / 1.7 / 3.3 / 0.10, applied after the pin's c/2 slop **[round 3]** | DESIGNED |
| `PIN_FIT_CLEAR` **[round 3]** (hole Ø = pin + this, slip fit) | 0.20 (hole Ø3.20; was 0.05) | PLACEHOLDER (print-tolerance-expert) |
| `RACK_EXT` / `TARGET_MAX_GAP` | 4.6 (was 4.5; round 3, user accepted) / 74.0 (the build refuses to run below it) | user decision (extend) / designed length |
| `TESS_TOL` / `TESS_ANG` | 0.03 / 0.2 | STL export tolerances |
| Poses | MIN 0; MID 18 × 1.61 = 28.98; MAX 37 × 1.61 = 59.57 | DERIVED from the pin stop (whole pitches) |

## Gates (round 5: full `macros/sdg_gates.py` run 2026-09-24 on the round-5 exports)

**Round 5 summary.** All 4 STEP files 1 valid solid; all 4 STLs watertight, 1 shell, 0 sealed voids (slider volume 26306.51 mm³ STEP). Interference 0.0 mm³ for all 5 pairs at MIN / MID / MAX. Changed numbers: tab stop gap 0.730 and its margins (table in gate 5); carriage +X end face X 106.4755 on all 82 rays from Y −30.95 to 2.71 (step 0.0000); new true 2D pad clearance 2.0581. Rechecked against the gate-5 table on this run: tip gap, coaxiality, overlap, backlash and seat gap are unchanged. Two small differences that round 5 did not cause: thread min radial gap reads 0.293 (0.294 in the text below), and carriage → boss (Y −11) reads 4.839 (4.853 below, from the old end X). The rest of the text below is the round-4 record and was not re-compared line by line (gate 3 still quotes round-3 carriage-top numbers: this run reads 38.673 mm² / 1.082 / 1.295). `render_check.py` on the slider: 1 body, watertight; front render shows one straight +X edge from the top wall to the beam bottom, and the open gap between the pad and the stop block.
Gate-script changes in round 5: the end-face rays cover the stop leg (Y down to the beam bottom); a Y-section true-minimum pad clearance at MIN.

### Round 4 gate record

**Round 4 summary.** All 4 STEP files: 1 valid solid each. All 4 part STLs: watertight, 1 shell, 0 sealed voids. Interference 0.0 mm³ for all 5 pairs at MIN / MID / MAX. The tip gap, coaxiality, pawl overlap, tab-stop margins, thread engagement, C-tip wall, pin-hole walls and pin stop are identical to the round-3 values in the tables below. That is expected: round 4 did not move any of those features.

**Round 4 seating gate** (gate 5 at MIN, on the placed part meshes, i.e. the assembly datum; rays start 1.5 below the boss face inside the handle and run into the hole, at 24 angles):

| Check | Measured | Requirement |
|---|---|---|
| Collar face → boss face gap | **+0.0000…+0.0000 mm** over r 8.55…10.95 | 0 (contact) |
| Contact annulus (flat: every contact ray leaves the handle at the face) | r 8.55 → 10.95 (0.05 steps), **width 2.45** | real, flat |
| Male tip → hole floor | **0.616 mm** | > 0 |
| Widest handle feature above the face | r 7.998 (the male crest) | no core/collar enters |
| First female material inside r 7.9, above the face | **0.253 mm** | > 0 |
| Push the handle +0.02 mm into the hole | handle∩frame 3.031 mm³ at Y −19.003…−18.983, r 8.494…11.000 (annulus × push = 2.941) | only the annulus touches |
| Push +0.10 mm | 15.682 mm³ at Y −19.003…−18.903, r 8.287…11.000: the annulus plus the mouth edge, **no thread flank** (axial play 0.15) | collar first |

Other round-4 numbers: carriage floor 2.500 / tongue 1.979–2.015 / top wall 2.500 (gate 3); carriage end face X 106.475 on every ray; carriage → boss-pad gap at MIN: rays beside the rack read a minimum of **2.199** (Y −8, Z 10.35, carriage X 106.475 → pad X 108.675). The X gap from the squared end to the taper start is 108.511 − 106.475 = **2.036**. The build checks 2.026 against the traced maximum X 106.486 (≥ 2.0). Gate-script change in round 4: gate 5 uses the placed part STLs (see the assembly STL note under "Parts and files").

Gate-script change in round 3: the pawl hook/backlash rays were at land +0.15 / +0.55. The traced rack underside rises 0.145 mm from the MIN notch to the MAX notch, so the overlap falls to 0.535 (MID) and 0.461 (MAX) and the +0.55 ray passed over the tooth apex (the gate crashed at MID). The rays are now at +0.10 / +0.40.

**1. Solids and topology.**
- All 4 STEP files are 1 valid solid each.
- All 4 STLs are watertight, winding-consistent, 1 shell each, 0 sealed voids. Euler: frame −2, slider −4, handle 2, pin 2.
- **Z columns measured:** slider riser, top bar and crown Z −3.3…13.3; frame bar at X 100 and 140: 0…10; at X 122.311: −6…16.
- `render_check.py` passes for slider and handle (round 4; 1 body, watertight each). On `assembly_min.stl` it reports body_count 5 and not watertight, because the collar and the boss share the r 11 contact circle (see the assembly STL note).

**2. Through-holes.** Rays from both ends.
- Slider bore and C-tip bore: 0 hits on the axis ray; 0 at r 1.50 (Ø3.0 wire); 0 at r 1.60 (Ø3.2 ream). Control rays at r 1.85 hit on 15 of 16.
- Rack channel: 0 hits. Female hole: open, floor at Y −10.387. Pin hole: 0 hits on the axis and at the pin radius.

**3. The traced outline survives.** STL sections against the DXF rings, excluding the listed feature zones.
- **Frame** at Z 1 and Z 5: max deviation 0.0000 mm.
- **Slider** at Z −2, 1, 5 and 12 against L ∪ collar ∪ carriage: max 0.0000 mm. L ring alone: symmetric difference 0.0002 mm². Control (as-imaged L ring) fails as it should: max 1.53 mm.
- **Handle:** max 0.016 mm.
- **Allowed deviations, measured:** rack extension 4.600 mm / 29.15 mm² (0.376 mm² traced removed by the pin hole); C-tip pad 17.20 mm², max offset 3.825, 0.0000 traced removed; carriage top 20.403 mm², max offset 0.582 along the top / 0.926 incl. the squared corner, 0.0000 removed; handle core 60.25 mm², max offset 1.379, 0.0005 removed; boss pad taper 2.8 mm at 65.0° both sides.
- **Entry trough:** the bore removes 0.706 mm² of traced end-face ledge in front of the jaw face (X 150.062…150.648), outside the enclosed span.

**4. C-tip wall, perpendicular.** 3D closest-face distance, 48 points × 50 stations over X 150.648…163.605.
- **Minimum wall 1.799 mm** (X 150.90). **0 of 50 stations below 1.5.** Z walls 2.596 (top) / 3.300 (bottom).
- **Control:** the same code on the slider bore finds its known thin crown exit, 0.299 mm at X 135.86.

**Pin hole walls** (STL section at Z 5, measured equivalent hole Ø3.197):

| Towards | Straight ray | Minimum in the 90° sector |
|---|---|---|
| Rack free end (−X) | 1.701 | 1.700 (at 178°, the overall minimum) |
| Rack top (+Y) | 2.553 | 2.101 (at 135°) |
| Teeth (−Y) | 3.353 | 2.194 (at 225°) |
| Hook (+X) | no exterior within 30 mm | 3.022 (at 45°) |

**Resolution of the pin-wall discrepancy.** Round 2 reported 3.114 / 2.742 / 4.220 (+Y / −Y / +X) with a method that keeps only triangles whose **centroid** is within 15 mm of the hole; long faces (rack top, rack bottom) have far centroids and are dropped, so it read too thick. The gate still prints that method as a CONTROL: 1.699 / 3.169 / 2.678 / 4.229 on this mesh. The current gate does **not** assume the rack top is at Y 0: it reads the section's outer boundary, and the STL section itself puts the rack top at Y 0.000 at X −3 and −1. The +Y ray 2.553 equals 0 − (−4.152 + 1.599), consistent. form-auditor's 1.805 / 1.876 / 2.748 were taken on the round-2 mesh (hole Ø3.05 at X −1.267) by a method I have not reproduced, so I cannot say which directions they map to; on the round-3 mesh no direction is below 1.700.

**5. Assembly at MIN / MID / MAX.** Measured on the written assembly STLs; axes fitted from the mesh.

| | MIN | MID | MAX |
|---|---|---|---|
| Travel | 0 | 28.980 (18 teeth) | 59.570 (37 teeth) |
| Radial offset / angle, C-bore axis vs slider-bore axis | 0.0006 mm / 0.0019° | 0.0007 / 0.0019° | 0.0008 / 0.0019° |
| Axis ray / Ø3.0 wire-surface rays | 0 / 0 hits | 0 / 0 | 0 / 0 |
| Axis enclosed by the C-tip | X 150.70–163.60 | same | same |
| Interference, all 5 pairs | 0.0 mm³ | 0.0 | 0.0 |
| Tip gap at wire height (Z 1 and Z 9) | **14.472** | 43.452 | **74.042** |
| Hook angle, pawl tooth face / rack wall | 10.00° / 10.00° | 10.00° / 10.00° | 10.00° / 10.00° |
| Horizontal backlash on the locking wall | 0.102 | 0.089 | 0.076 |
| Pawl overlap (tooth apex − land) | 0.605 | 0.535 | 0.461 |
| Seat gap along the ramp | 0.115 | 0.185 | 0.259 |
| Tab stop gap / drop needed to OPEN / margin (round 5) | 0.730 / 0.606 / **0.124** | 0.730 / 0.536 / 0.194 | 0.730 / 0.462 / 0.268 |
| Drop needed to CLOSE (ratchet over the ramp) / margin (round 5) | 0.610 / **0.120** | 0.540 / 0.190 | 0.466 / 0.264 |

More measurements:
- **Coaxiality controls:** the as-imaged pose (1.087°) reads 1.761 mm, 1.085°, 22 wire hits; a 0.5 mm Y shift reads 0.501 mm, 14 hits.
- **Carriage to boss pad at MIN (round 5):** rays beside the rack min **2.199 mm** (Y −8, Z 10.35: carriage end X 106.475 → pad X 108.675), max 3.436; true 2D minimum on Y sections **2.0581** (Y −9.2); stop-leg rows 4.841. Carriage to boss (Y −11, Z 5): 4.839 mm.
- **Thread at MIN:** engagement 1.958, minimum radial gap 0.294.
- **Pin to collar at MAX:** 0.264 mm (pin centred) / 0.164 (pin 0.10 towards the collar), at Z −2 and Z 12. Contact at travel 59.834 / 59.734.
- The overlap falls and the seat gap grows from MIN to MAX because the traced rack underside rises towards the free end while the slider channel is straight.

**6. Whole-form comparison against completeDevice1.** File: `SurgicalDrillGuide_assembly_min_vs_reference.png` (read 2026-09-24).

Verdict: **the same object.** Same C-frame with the rack running left past the L-arm, the rounded C-hook at the right with its tip gap to the L-arm crown, the L-arm rising from the collar, and a solid handle hanging below the bar under the hook side. Proportions agree (pixel positions read by eye from the side-by-side image, not a fitted measurement): rack overhang left of the L-arm ≈ 0.37 of the frame width in the render against ≈ 0.35 in the photo; handle drop ≈ 0.80 of the frame width against ≈ 0.82. The handle reads as a solid, swelling grip in both. Visible differences:
- the pawl and its tab-stop loop hang **below** the carriage, where the photo has a lever and knob **above** the collar (designed substitution, deviation 6);
- the boss column is a plain Ø22 post where the photo has a thin post, nut and spring-like ferrule;
- no wing screw;
- a squared sleeve on the C-tip (C-tip pad).

The silhouette fill (17.1 % vs 11.6 %) is not used as evidence.

**Round 4 re-read** (`assembly_min_vs_reference.png`, regenerated): still the same object. Frame, rack, L-arm, C-hook and handle proportions look unchanged. The one visible change is under the bar: the boss and the seated collar now read as one Ø22 column, with a small step where the collar's cone meets the Ø16 core. In the photo the same region is a thin post, a nut and a spring ferrule, a difference that already existed. Silhouette fill 17.2 % vs 11.6 %, not used as evidence.

## Deviations from the reference (deliberate)

1. **The top-bar tilt is removed.** In the photos the top bar sits 1.087° to the rack. Here it is built parallel to the rack (rectified L).
2. **The rectified wire passes the C-tip 1.7 mm lower** (5.847 mm below the tip top).
3. **The C-tip pad adds 17.20 mm²** to the traced outline, max offset 3.825 mm. It makes the tip end squared, not curved. User-approved.
4. **The rack is extended by 4.6 mm** (user accepted) past its traced free end (X −0.050 → −4.650), adding 29.15 mm² above the teeth band; the frame is 181.35 mm long instead of 176.8. The pin hole removes 0.376 mm² of the traced rack end.
5. **Carriage top wall 2.5 mm and floor 2.5 mm** (round 4). The top adds 38.673 mm² at Z 5: +1.082 mm along the top, +1.295 at the squared +X corner. The floor sits up to 0.53 mm below the traced bottom outside the tongue. The +X end is squared at X 106.475.
5a. **Ø22 handle collar seated on the boss face** (round 4, user decision). It replaces the top 3 mm of the traced ferrule (r 7.19–7.49) with Ø22 and adds a 45° cone under it: +39.22 mm² over the traced silhouette. In the side view the boss and handle read as one Ø22 column with a step at the collar's lower edge.
6. **Flexure pawl with a 10° hooked tooth, release tab and tab hard stop** replace the reference pawl, pivot screw and lever (U7). **No wing screw** (function unknown).
7. **A printed Ø22 boss with a Tr16×4 thread** replaces the post and nut. The **boss pad tapers at 65°** over 2.8 mm (not a gentle blend) because the carriage must clear it by 2.0 at MIN.
8. **Ø16 handle core** replaces the traced ferrule neck (r 4.30…7.50) between the grip and the shoulder: +60.25 mm², max 1.379 mm outside the traced silhouette.
9. **L-arm 16.6 mm and boss region 22 mm in Z.** Z is not measured in any photo.
10. **A printed end-stop pin** (not in the reference). MAX tip gap 74.042 mm (seated), 74.206–74.306 at contact, against about 75 in the photos.
11. **Construction features:** the 0.06 mm butt flat and the fusion slugs.
12. **Not modelled** (3D form unresolved): the C-tip cross-slot (U1; closed bore by user decision) and the crown V-groove (U8).
13. **Carried from the vectors:** the riser rebuilt vertical at 7.50 mm; the 0.41° rack-to-bar kink; the grip on the colour half level, about 2 % under the luminance edge.

## Open items and verification checklist

Round 7:
- [ ] On the first print: flat locking contact on the teeth, release force at the pad, hold under load, and the pin → collar gap at MAX (0.118).
- [ ] Click fatigue of the flexure (22.3 MPa with Kt vs an untested 10.6 MPa estimate).
- [ ] The coupons in `attempts/r7-ratchet-2026-10-17/coupon/` predate the root and stop fixes.
- [ ] Whole-form photo comparison (gate e) not re-run in round 7.

Round 6:
- [ ] print-tolerance-expert: confirm D3/D4 with the socket bearing starting 2.0 below the head top (mouth chamfer), and the hook band at s 64–66 with the built widths.
- [ ] Snap coupon (`bar_and_snap.md`).
- [ ] Handle standing: 0.43 mm² down-facing remains, a 0.01 mm ring at the butt-flat edge (cause not investigated).
- [ ] User: the throat is now 39.0 to the slider top bar; the largest bone size is not given.
- [ ] `mechanisms.py` still holds the unused thread code (`cam_thread`, `thread_radius_fn`).

Rounds 3–5 (the boss/thread/collar items below are retired with round 6):

- [ ] **Round 4 re-check, hand-off to print-tolerance-expert.** Values that changed and that `docs/mechanism_sizing.py` hard-codes:
  - top wall 2.5 (was 2.0); floor 2.5 outside the tongue (was 1.90 in the script; the traced floor actually measures 1.97–2.05 since `SLIDE_CLEAR_Y` moved the channel);
  - tongue **unchanged** at 1.979–2.015 (measured). The script's "not re-measured" tongue can now use these values;
  - handle collar Ø22 × 3.0 on the boss face: contact annulus r 8.55–11.0 (2.45 wide); edge bearing on the r 11 edge and collar root bending are not modelled; engagement unchanged (6.0 mm full profile);
  - carriage → pad X gap 2.036 (squared end at 106.475).
- [ ] form-auditor: collar face flatness and squareness, the floor chamfer, and the squared carriage end.
- [ ] Round 3 items (kept for the record), not yet reconciled by any structural check:
  - pawl hook 10°, overlap 0.605 (MIN) → 0.461 (MAX), backlash 0.102 → 0.076; tab stop margins 0.190–0.338; pawl tongue stiffness, release force and stress;
  - Tr16×4 male on a Ø11.5 root and Ø16 core; handle bending; boss Ø22 around a Ø16.6 female crest (boss wall derived as (22 − 16.6)/2 = 2.7 mm at the crest, **not measured**);
  - carriage top wall 2.0 (1.517 at the squared corner, X 106.45); carriage-to-pad gap 2.191 at MIN;
  - pin Ø3.0 in a Ø3.20 hole, end wall 1.700, stop gap at MAX 0.164–0.264;
  - every PLACEHOLDER clearance (`SLIDE_CLEAR_Y`, `PIN_FIT_CLEAR`, thread 0.30/0.15, `PAWL_SEAT_CLEAR`).
  - `docs/MECHANISM_STRATEGY.md` and `docs/mechanism_sizing.py` are **v1-era** and do not describe this build.
- [ ] **form-auditor re-run** on the round-3 meshes, including the pin-hole walls (its round-2 figures 1.805 / 1.876 / 2.748 are not reproduced here).
- [ ] The iso renders were regenerated in round 4 for the slider and handle only. The frame and assembly iso renders predate round 4.
- [ ] From MEASUREMENTS §9c, still unresolved: every Z dimension; absolute scale (one caliper reading); tooth depth and form; C-tip slot open or closed; the real maximum opening; whether the 1.08° is play or built in; riser width; grip cross-section.
- [ ] Nothing has been printed or test-fitted.
