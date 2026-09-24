# SurgicalDrillGuide: traced in-plane (XY) profiles

Agent: `vector-tracer`, 2026-09-23. This is the input to `cad-designer` for the approved rebuild. It gates
against `docs/MEASUREMENTS.md` (2026-09-23) and does not replace it. It was revised the same day after
`review/ACCURACY_REVIEW.md` (verdicts: main_frame PASS; l_arm and handle NEEDS FIXES). The fix-up is recorded in
the "Fix-up round" section at the end.

## Source, scale, datum

- **Traced from:** `completeDevice1` (cd1), 1000 px, near-orthographic view along −Z
  (`attempts/rebuild-wip-2026-09-22/completeDevice1.png`). cd2 was used only to cross-check the riser width and
  the carriage angle.
- **Scale:** 3.443 px/mm, the 170 mm callout transferred via picture2 (PERSPECTIVE.md), ±2.5 % absolute. The
  engraved ruler reads 3.52 px/mm, which would make every length 2.2 % smaller. That choice is the user's (U10).
- **Datum:** the origin is the rack left tip (cd1 x 137.26 px), on the rack top edge fitted over x 150–335 px. +X
  runs **along that fitted edge** towards the hook, and +Y runs up.
  - The frame is rotated 0.123° from image horizontal so that the rack, which is the slide axis, is exactly X.
  - The analyst's CSVs use raw image axes with no rotation. Absolute positions therefore differ from
    MEASUREMENTS.md by ≤0.4 mm in Y at the hook end. The gates below state which frame each value uses.
- **Z is unmeasured.** Nothing here implies a thickness.

## Files

| File | Content | Consumer |
|---|---|---|
| `main_frame.svg/.dxf` | Layers: BODY = C-hook + bottom bar + rack, **one closed ring**. BOSS_AXIS = post-centre line (annotation). DIMENSIONS | viewing; ezdxf by layer |
| `l_arm.svg/.dxf` | Layers: L_ARM (riser + top bar + V crown, **rectified**), COLLAR, CARRIAGE, WIRE_AXIS (LINE). REF_* = as-imaged pose | viewing; ezdxf by layer |
| `handle.svg/.dxf` | Layers: GRIP, FERRULE (silhouettes), GRIP/FERRULE_REVOLVE_HALF (half-profiles about the post axis), BOSS_AXIS | viewing; ezdxf by layer |
| `import/*.dxf` | **One ring (or one line) per file.** These are the files to `import_dxf()` | **none yet**: the rebuild macro does not exist. Intended consumer: cad-designer's rebuilt `macros/surgical_drill_guide.py`, via `import_dxf()` then `Face(Wire(edges))` |
| `scripts/` | `build.py` (tracing), `export.py`, `verify.py`, `overlay.py`, `render.py`, and the `m_*.py` measurements. `work/` holds rings as JSON, `verify.json` and overlay PNGs | reproducibility |

`import_dxf()` returns a flat ShapeList and **drops layer names** (tested in `scripts/probe_import.py`). Importing
a multi-layer file merges every ring into one pile of edges. Use `import/`.

Pipeline: `python scripts/build.py` → `export.py` → `verify.py` (→ `overlay.py`, `render.py`).

## Construction

- **Straight edges** are least-squares lines through sub-pixel edge samples at threshold 245 (`h.py`), rms
  0.13–0.24 px.
- **Curved parts** are sub-pixel iso-contours:
  - hook, outer L corner: `skimage.find_contours`, with interior highlights suppressed
  - crown, collar, ferrule: per-row and per-column crossings
  - grip: the half level of B−R
- **Smoothing:** B-spline smoothing at 0.15 px rms, then Douglas-Peucker simplification at 0.008 mm.
- **Hidden spans** are bridged, not invented:
  - rack/bar under the collar and carriage: fitted lines extended to their intersection
  - bar bottom behind the post: fitted line carried across
  - collar left face across the rack rows: quadratic through the visible face, rms 0.35 px
  - collar right face behind the carriage: straight line
  - carriage bottom-right behind the pawl screw and wing hub: straight bottom line, square corner
  - carriage top behind the wing plate: fitted line
- **Rack teeth are not traced.** The rack is its tooth-tip envelope. Pitch 1.61 mm, tooth side = bottom face,
  depth unresolved (≤2.4 mm), teeth extent X 0 → ≈100.7 (MEASUREMENTS §3b, not traced). All of this is stored as
  DXF header custom vars.
- **L-arm rectification.** The top bar sits at 1.087° to the rack in cd1. The L_ARM ring is rotated −1.087°
  about the middle of the riser base (frame (64.79, 6.59)), so the top bar is parallel to X, then clipped at
  the collar top line.
  - The measured angle is metadata only.
  - The as-imaged ring is kept on REF_L_ARM_AS_IMAGED and in `import/l_arm_body_as_imaged.dxf`.
  - **In the rectified ring the riser is rebuilt, not traced** (fix-up). It is vertical, so square to the top bar,
    at a constant 7.50 mm (X 61.61 → 69.11). It is anchored at the traced outer corner, so the L outer length stays
    75.44 (traced 75.48).
  - The rotated traced riser had leaned 0.74° and tapered 7.61 → 7.35 mm, because it followed a drifting shading
    edge.
  - The riser base lies inside the collar top edge, with margins of 0.62 mm on the left and 0.78 mm on the right.
  - The inner fillet (R 4.41) is re-placed tangent to the new inner face.
  - The as-imaged ring keeps the traced riser (90.6° corner, front-face inner edge).
- **Wire axis.** A line parallel to the top-bar top edge, 4.80 mm below it (cd2: 47.7 % of 10.08). It runs from the
  riser outer face to the crown apex. Rectified, it lies at Y = 51.80.
- **Riser inner edge (as-imaged ring) = the cd1 front-face boundary, not the cd1 silhouette.** Reason: cd1 shows a
  1.3–1.4 mm dark strip at x 372–377 (the riser's +X side face).
  - Silhouette 8.84 mm − strip = 7.44–7.56 mm.
  - cd2 silhouette, with no strip: 7.57 (MEASUREMENTS) / 7.67 (my fit).
  - The inner fillet uses the radius fitted to the cd1 silhouette corner (4.41 mm), re-placed tangent to the
    front-face line. It is **constructed**, not traced.
- **Handle.**
  - Silhouettes are as imaged. The grip axis is −0.49° from the rack normal (−0.90° from the bar normal; MEAS 0.97).
  - The revolve half-profiles are the per-row half-widths on a vertical axis at the post centre, X 122.31. A round
    section is **assumed** (U11).
  - **Grip edge convention.** The grip ring sits on the B−R (colour) half level. The luminance (brightness) half
    level lies further out, so the ring is 1.5–2 % narrower than it:

    | Row | Ring (B−R) | Luminance half level |
    |---|---|---|
    | belly (760) | 23.73 | 24.17 |
    | row 700 | 21.57 | 21.91 |
    | waist (610) | 15.88 | 16.13 |

    - Source: `scripts/m_fixup.py`; the reviewer gets the same (belly 23.69 vs 24.17).
    - The length is 0.6 % short (96.20 vs 96.78, reviewer).
    - The metal rings use the gray-245 edge, so handle and frame follow different edge conventions.
    - The grip was **not** retraced. The convention is the user's call; the offset is recorded here.
  - **Ferrule (fix-up).** Its top is the nut → ferrule shoulder, **measured** at cd1 row 412.16. That is the first
    object row at x 576–580 (412.02–412.46), right of the nut, on clean pixels (R−B ≤ 13).
    - Frame Y is −19.00; the reviewer gets row 412.75 (Y −19.2).
    - Clean edges are used where they exist: right edge rows 442–521, left edge rows 451–521.
    - Hidden edges are bridged at the median measured edge (OD 14.67 mm): the right edge over rows 413–441
      (Y −19.0 → −27.3) and the left edge over rows 413–450 (Y −19.0 → −29.7). These spans are **ESTIMATED**.
    - The flat shoulder line is also Estimated.

## Validity (every ring)

All nine rings pass `LinearRing.is_simple`, `Polygon.is_valid`, min segment ≥0.144 mm, and a non-repeated closing
point. Each `import/` ring round-trips through `import_dxf()` to a closed wire and a valid face. Face areas equal
the shapely areas to <0.001 mm². A 1 mm **test** extrusion (topology test only, not a thickness) gives a valid
solid and a watertight single-body STL, with no tessellation warnings.

| ring | pts | face area mm² |
|---|---|---|
| main_frame_body | 212 | 2093.39 |
| l_arm_body (rectified) | 66 | 1047.60 |
| l_arm_body_as_imaged | 66 | 1046.61 |
| l_arm_collar | 63 | 204.42 |
| l_arm_carriage | 7 | 485.96 |
| handle_grip | 201 | 1968.98 |
| handle_grip_revolve_half | 111 | 983.85 |
| handle_ferrule | 96 | 478.44 |
| handle_ferrule_revolve_half | 54 | 239.23 |

Spur check: no pair of consecutive turns greater than 100° in either L ring.

## Gates (traced vs MEASUREMENTS.md, cd1 values unless noted)

| Gate | Traced | MEAS | Residual |
|---|---|---|---|
| Frame length, rack tip → hook outer | 176.70 | 176.7 | 0.00 |
| Rack height (X 30) | 9.18 | 9.15 (9.3 ± 0.2) | +0.03 |
| Bar height X 110 / 135 / 150 | 9.44 / 9.28 / 9.18 | 9.3 | +0.14 / −0.03 / −0.12 (taper, traced as seen) |
| C-tip top (image-topmost, raw datum) | (154.10, 57.90) | (153.7, 57.9) | X +0.40, Y 0.00 |
| C-tip top → hook outer, horizontal | 22.58 | 22.86 (cd2 22.78) | −0.28 |
| C-tip top above bar top | 57.31 | 57.5 | −0.20 |
| Rack → bar kink | 0.41° | 0.58° | −0.17°, see below |
| Handle post centre X / post width | 122.31 / 4.86 | 122.4 / 4.85 | −0.09 / +0.01 |
| Free rack, tip → collar | 60.02 | 59.9 | +0.12 |
| Hook neck width | **7.52** | 6.97 | **+0.55**, see below |
| L-arm outer length (as imaged / rectified) | 75.48 / 75.44 | 75.5 (cd2 75.1) | −0.02 / −0.06 |
| Rectified riser width at Y 10 / 25 / 40; lean | 7.50 / 7.50 / 7.50; 0.000° | 7.5 (brief) | 0 (rebuilt) |
| Rectified top edge vs X | 0.000° (X 64.60 → 133.98) | 0° | 0 |
| Top-bar height | 10.03 | 10.03 (cd2 10.08) | 0.00 |
| Throat at cd1 x 600 (as imaged) | 47.56 | 47.3 | +0.26 (rectified: 46.22) |
| L overall height | 71.53 | 71.4 | +0.13 |
| Riser width | 7.44 | 7.57 (cd2) | −0.13 (cd1 silhouette 8.84, not used) |
| Collar X-length, top / mid / bottom / widest | 8.97 / 10.11 / 9.48 / 10.42 | 9.3 | see below |
| Collar height | 21.49 | ≈22.1 (Estimated) | −0.61 |
| Carriage length | 36.63 | 36.6 | +0.03 |
| Collar + carriage | 46.46 | 45.9 (cd2 45.5) | +0.56 |
| Carriage top above rack | 1.74 | 1.7 | +0.04 |
| Top bar vs rack | 1.087° | 1.08° | +0.007° |
| Wire Y at riser / crown (as imaged, raw datum) | 51.79 / 53.38 | 52.0 / 53.4 | −0.21 / −0.02 |
| Tip gap, crown **apex** → C-tip face (as imaged / rectified) | 14.64 / 13.61 | 14.8 | −0.16 |
| Tip gap at **wire height**, wire exit in the crown notch → C-tip face (as imaged / rectified) | 15.55 / 14.47 | — | the apex sits 0.98 mm below the wire |
| Wire below C-tip top (as imaged) | 4.14 | 4.20 | −0.06 (rectified: 5.85) |
| Grip length | 96.20 | 96.4 | −0.20 (analyst counts pixels inclusively) |
| Grip flare / waist / belly | 26.10 / 15.73 / 23.69 | 25.9 / 16.0 / 23.8 | +0.20 / −0.28 / −0.11 |
| Grip widths 5–95 % | −0.10 … −0.53 | table §7c | consistent ~1 px narrower (half-level edge vs blue mask) |
| Ferrule OD (rows 486–519) / neck | 14.79 / 8.62 | 14.7 / 8.6 | +0.09 / +0.02 |
| Ferrule shoulder Y / length shoulder → neck | −19.00 / 33.06 | reviewer −19.2 | +0.20 |
| Grip start below bar bottom / butt | 43.18 / 139.38 | 43.0 / 139.1 | +0.18 / +0.28 |

## Disagreements with MEASUREMENTS.md

1. **The hook contour CSV sits inside the edge.** `hook_contour_c1_frame_mm.csv` is a pixel-centre
   `findContours` staircase. It lies 0.18 mm (mean) and up to 0.38 mm inside the threshold-245 edge that every
   other MEASUREMENTS dimension uses.
   - The hook in `main_frame` is my sub-pixel trace, not the CSV.
   - Tested: the same medial-axis width method gives a neck of 7.03 mm on the CSV contour and **7.52 mm** on the
     sub-pixel ring.
   - So the 6.97 mm neck, and the hook widths in the §3c table, are about 0.2–0.5 mm under-read (mean +0.22 mm
     over 268 stations).
2. **The 0.58° rack-to-bar kink is not robust.** The bar top edge is a staircase of near-flat runs.
   - Depending on the fit window, the kink is 0.10–0.82° in cd1 and 0.38–1.09° in cd2 (`scripts/m_kink.py`).
   - Only the sign is consistent.
   - The ring uses the full visible bar (x 506–664): 0.41°, with the vertex at X 98.5 under the carriage. That is
     within 2.2 mm of the teeth end, X ≈ 100.7.
3. **The carriage is square to the rack in cd1:** 0.17° by my fit, 0.11° by the reviewer's.
   - My earlier cd2 figure of "0.01°" is **withdrawn**. The reviewer could not reproduce it: the cd2 carriage top is
     poorly defined next to the wing plate and the collar, and gives 0.0–0.4° against the rack.
   - The conclusion still holds: at least 0.7° of the 1.08° lies between the carriage and the top bar in both
     photos, so it is not the carriage cocking on the rack. This is relevant to U4.
4. **The carriage bottom is not level with the bar bottom.** At x 380–428 px (X 69.7–84.5) the carriage silhouette
   reaches 11.3–11.6 mm below the rack top, about 2.4 mm below the rack bottom, with a dark slot (the pawl) above
   it.
   - Over **X 84.5–106.5 the bottom edge and the square bottom-right corner are ASSUMED**: the underside is hidden
     by the pawl-pivot plate, the lever and the wing hub.
   - The ring sits 0.24 mm below the silhouette at x 408–428 (reviewer).
   - Whether the dark band belongs to the carriage block or to a pawl housing is UNRESOLVED.
5. **The collar length "9.3 mm (cd1 x 343.5 → 377)" is inconsistent.** 33.5 px is 9.73 mm. The traced collar is
   8.97 wide at its top, 10.1 at mid-height and 10.42 at its widest.
6. **Riser width: I recommend 7.5, not the 8.0 ± 0.6 in MEASUREMENTS.** The cd1 front face (7.44–7.56) and the cd2
   silhouette (7.57–7.67) agree. The 8.8 mm is side face.
7. **The rectification pivot is a design choice with consequences.**
   - Rotating about the riser base moves the crown +0.85 mm in X.
   - The tip gap to the crown apex drops from 14.64 to 13.61. At wire height (the wire exits in the lower notch,
     0.98 mm above the apex) it drops from 15.55 to 14.47. State which gap the 15 mm target means.
   - The wire then passes the C-tip 5.85 mm below its top rather than 4.14 mm. The C-tip wire passage must be
     cut at the rectified wire height, Y 51.80.
   - Rotating about the C-tip instead would lift the riser base 1.4 mm off the collar.

## Not traced

- **Rack teeth:** the silhouette shows no sawtooth, and the depth is unresolved (U3).
- **Pawl, pawl-pivot screw, wing screw, release lever:** these are not among the authored parts, and their form
  is Estimated or oblique only (U7).
- **Ferrule top: corrected.** The first version stopped at row 457 and wrongly said the shoulder was hidden at rows
  ~404–442. The shoulder is visible at row 412.16 (x 576–580) and the ring now reaches it; see Construction.
  - The Ø9.8 nut above it (rows 392–412) is not an authored part and is not traced.
  - cd2 shows the whole ferrule (31.3 mm at 3.199 px/mm). It was not used: PERSPECTIVE forbids carrying handle
    dimensions across the photos.
- **Handle post, nut:** the rebuild replaces them with a printed boss and thread. Only the post axis (X 122.31)
  and the post width (4.86) are given.
- **C-tip cross-slot and crown V-groove 3D form:** their silhouettes are in the rings. The Z form is unresolved
  (U1, U8).
- **Any Z dimension.**

## Cost of the primitive alternative

- **Hook as one circle.** The best-fit circle misses the traced outer edge by up to **6.5 mm** (rms 1.6) and the
  inner edge by up to **10.4 mm** (rms 2.6). v1's "R 41.2, one circle" is worse.
- **Grip as a Ø23.8 cylinder.** It differs from the traced silhouette by 342 mm², **17 %** of its area, and
  over-sizes the waist by 7.8 mm in diameter.
- **L-arm as two rectangles** with the measured dimensions, against the rectified ring: 21 mm² (2.0 %), Hausdorff
  2.1 mm. That is the crown and the fillet.

## Fix-up round (2026-09-23, after `review/ACCURACY_REVIEW.md`)

1. **Crown spur removed** from `l_arm_body` and `l_arm_body_as_imaged`.
   - Cause: the bottom-edge vertex came from intersecting the bottom line with a lower-flank fit. That vertex lay
     0.27 mm past the traced chamfer (row 181), so the ring doubled back: a 0.42 mm spike.
   - Fix: the bottom line now ends at the traced row-182 point.
2. **Ferrule extended** to the measured shoulder (Y −19.00), in both the silhouette and the revolve half. Bridged
   spans are Estimated (see Construction).
3. **Rectified riser rebuilt** vertical at a constant 7.50 mm. The as-imaged ring is unchanged apart from fix 1.
4. **README corrections:**
   - the cd2 0.01° carriage figure is withdrawn
   - tip-gap conventions are stated
   - the carriage bottom-right is marked ASSUMED
   - the ferrule "hidden shoulder" line is corrected
   - the grip edge-convention offset is recorded
5. **`attempts/rebuild-wip-2026-09-22/ref/c1_wm.npy` is NOT a watermark mask.** It is `g < 70` anywhere, and
   16,910 of its pixels lie on the grip, the carriage shading and the riser inner corner (reviewer). Do not use it
   as an exclusion mask. `scripts/tc.py:watermark_c1()` restricts the black letters to the text band plus the
   orange swoosh.
   - That mask is also dilated, so it over-flags clean ferrule edges at rows 442–457. Those rows are now accepted
     explicitly.
6. All changed rings were re-validated: simple, valid, `import_dxf` round trip, 1 mm test extrusion, watertight
   STL. The main frame is unchanged.
