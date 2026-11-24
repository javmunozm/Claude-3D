# DeodorantBoxTop

## Goal
A replacement cover for a printed 3 × 4 deodorant box. The current cover (photos in
`sources/DeodorantBoxTop/`) has rhombus-like holes about 37 × 46.5 mm that had to be enlarged by
hand (user, 2026-11-24: short side measured 36.9–37.2 mm). The rhombus is dropped for a more general
ellipse, 46.5 × 44.5 mm. The base's oval recesses are decorative and not modelled; the cover's hole grid
matches the base's 3 × 4 layout.

## Status
v0 built 2026-11-24 and baked the same day: `stl/DeodorantBoxTop_cover.stl`,
`step/DeodorantBoxTop_cover.step`. Not printed or test-fitted. Numbers and checks in `STATE.md`.

## Brief (all values from the user, 2026-11-24)
- Plate 200 (X, 3 holes) × 210 (Y, 4 holes) × 4 mm (first given as 3 mm, corrected to 4).
- Holes 46.5 along X × 44.5 along Y, through. Hole edge to plate edge: 20 mm along X, 3.6 mm along Y.
  The webs between holes follow: 10.25 mm (X), 8.267 mm (Y).
- Base pillars: right-isosceles triangle, legs 16.5 mm. Cover sockets: blind, on the underside, outer
  edge flush with the plate corner, wall 2.5 mm, insertion depth 4 mm, clearance 0.2 mm per face
  (cavity legs 17.183 mm).
- The current cover's sockets stand on its top face (photos 3–4); the user chose blind sockets
  underneath for v0.

## Verification checklist (before printing)
- [ ] **Unverified:** the base pillar's right-angle corner sits 2.7 mm in from each base edge (the socket
      geometry assumes it, copied from "flush, 2.5 mm wall"). Measure on the base.
- [ ] **Unverified:** the base outline matches 200 × 210 and the pillars are on the same corners.
- [ ] 0.2 mm per face is a snug fit; test-print one corner before the full plate.

## Print
Top face down on the bed, sockets up: no supports (the sockets are open prisms on the flat face).

## Rejected approaches
- Rhombus holes 46.5 × 37 (the current cover): too tight; the user enlarged them by hand and asked for
  a general ellipse with the short side at 44.5.
