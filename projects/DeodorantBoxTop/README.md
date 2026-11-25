# DeodorantBoxTop

## Goal
A replacement cover for a printed 3 × 4 deodorant box. The current cover (photos in
`sources/DeodorantBoxTop/`) has rhombus-like holes about 37 × 46.5 mm that had to be enlarged by
hand (user, 2026-11-24: short side measured 36.9–37.2 mm). The rhombus is dropped for a more general
ellipse, 46.5 × 44.5 mm. The base's oval recesses are decorative and not modelled; the cover's hole grid
matches the base's 3 × 4 layout.

## Status
v0 built 2026-11-24, re-fitted to the gcode of the real base and posts and re-baked 2026-11-25:
`stl/DeodorantBoxTop_cover.stl`, `step/DeodorantBoxTop_cover.step`. Not printed or test-fitted.
Numbers and checks in `STATE.md`.

## Brief
User, 2026-11-24, unless marked. On 2026-11-25 the user supplied the gcode of the original cover, the base and
the posts (`sources/DeodorantBoxTop/*.gcode`) and said the gcode is the source of truth.
- Plate 200 (X, 3 holes) × **212** (Y, 4 holes) × 4 mm. 212 is from the gcode of the original cover and the
  base; the user first gave 210.
- Holes 46.5 along X × 44.5 along Y, through, kept at the user's size so they suit any deodorant
  (user, 2026-11-25). Hole edge to plate edge: 20 mm along X, 3.6 mm along Y. Webs: 10.25 mm (X), 8.933 mm (Y).
- Posts: the base and cover are joined by 4 separate posts, 46.5 long, with a right-isosceles section of
  **18.0 mm legs** and rounded corners (gcode). The earlier "base pillar, legs 16.5" did not match them.
- Cover sockets: the v0 design (user, 2026-11-25: use the STL's socket, not the gcode's): blind, on the
  underside, flush with the plate corner, wall 2.5, depth 4, clearance 0.2 per face → cavity legs 18.683.
  The original cover's sockets are built the other way up: they stand on its printed top face, and the
  cavity goes 2.6 mm into the plate.

## Verification checklist (before printing)
- [x] Base outline and post size: measured from the gcode 2026-11-25 (200 × 212; posts with 18.0 mm legs). In the
      gcode, the post fits the base cavity with 0.34 mm of clearance and the original cover cavity with 0.25 mm.
- [ ] The holes are not centred on the base's oval recesses (pitch 56.5): up to 4.6 mm off in Y. This
      follows from the hole size and margins.
- [ ] Slicer: the original profiles have `xy_hole_compensation` 0.2. With it, the cavity prints about 0.2 mm larger per side.
- [ ] 0.2 mm per face is a snug fit; test-print one corner before the full plate.

## Print
Top face down on the bed, sockets up: no supports (the sockets are open prisms on the flat face).

## Rejected approaches
- Rhombus holes 46.5 × 37 (the current cover): too tight; the user enlarged them by hand and asked for
  a general ellipse with the short side at 44.5.
- First v0 (2026-11-24): 200 × 210 plate, socket cavity for a 16.5 mm pillar. Measured on 2026-11-25
  against the gcode, the real post (18.0 mm legs) did not fit (it penetrated the cavity walls by 0.29 mm),
  and the plate was 2 mm short in Y. Exports kept locally in `work/backup_v0/` (untracked); the macro that builds it is in git at `f0a5df1`.
