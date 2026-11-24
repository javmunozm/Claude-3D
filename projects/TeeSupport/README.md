# TeeSupport: reinforced 3-way corner connector

## Brief (user, 2026-11-15)
The user's printer enclosure is a rod frame joined by 3-way 90° corner connectors (product photo:
`sources/TeeSupport/Captura de pantalla 2026-11-15 163614.png`, labelled "Inner Dia 8mm", "38mm", "90°"). The
user reports that the original connectors have 2 mm walls and that they break because the user's cat (about 6 kg)
lies on top of the enclosure. Requested: longer arms, wall 4 mm, larger triangular gussets between the arms, at least
5 mm thick. Choices made by the user on 2026-11-15: keep the 8 mm bore (outer Ø grows to 16), 50 mm overall,
gusset 6 mm, PETG, rod 8 mm.

## Method
B-rep in build123d (decided 2026-11-15): three revolved arms + a corner sphere + three extruded triangular gussets,
three revolved blind bores cut. Macro: `macros/tee_support.py`, stage package `macros/tee_model/`.

## Dimensions
| | Original (photo / user) | This part |
|---|---|---|
| Bore | 8 | 8.3 (rod 8.0 + 0.3 placeholder clearance) |
| Wall | 2 | 4.0 |
| Outer Ø | 12 | 16.3 |
| Overall (tip to far skin) | 38 | 50.0 |
| Socket depth | about 26 (derived, not measured) | 33.7 (bores stop at the other arms' skin; the core is solid) |
| Gussets | thin triangles, about 60 % of the arm (photo) | 3 plates, 6.0 thick, one per arm pair, running to both tips (ends 0.5 short of the tip, at the chamfer). At the tip each stands 4.0 proud of the tube (12.15 from the axis). Outer corner cut on the diagonal |
| Volume | — | 31.5 cm³ |
| Bending stiffness I_min of the arm section, × plain Ø16.3 tube | — | ×17.4 at 12 from the centre, ×2.83 at 36 (socket mouth), ×1.88 at 40 (scratch measurement, 2026-11-15) |
| Plain tube I (geometry only) | 817 mm⁴ (Ø12/8) | 3232 mm⁴ (Ø16.3/8.3), before the plates |

All numbers in the "This part" column, except the stiffness row, were measured on the baked STL by
`macros/tee_gates.py` (32/32, 2026-11-15).

## Files
- `stl/TeeSupport_reinforced.stl` (SHA-256 `603FD657…4E935E746`), `step/TeeSupport_reinforced.step`. Not tracked.
- Preview builds: `work/preview/`. Build plan and report: `work/plan_build.md`, `work/build_report.md`.

## Verification checklist (before printing)
- [ ] **Rod diameter:** 8.0 is the user's figure and the photo label. It has not been caliper-measured.
- [ ] **Bore clearance 0.3:** placeholder, to be set by the fdm-tolerance skill.
- [ ] **Strength for a 6 kg cat in PETG:** not computed. The fdm-tolerance skill needs the frame span and how many
      corners share the load.
- [ ] **Print orientation:** not decided (fdm-tolerance). With one arm vertical, that arm bends across its layers.
- [ ] Not printed or test-fitted.

## History
- 2026-11-15 r00: first build (plan `work/plan_build.md`). Build 1 was a valid single B-rep solid, but its STL had
  one open and one non-manifold edge: a degenerate triangle at the exposed −Z pole of the corner sphere. The fix
  turns the sphere's axis to (1, 1, −1), so both poles sit inside the arms. Build 2 passed all gates, and build 3 baked.

- 2026-11-15 pass 2: the user asked why the gussets did not run along the arms. A measurement on scratch builds
  (sections of the X arm) showed the 30 mm triangle added no section beyond 22 mm from the centre, so the socket
  mouth was plain tube. A triangle extended to the tip still left the last 8 mm plain. The user chose option C:
  plates running to both tips. One preview build passed all gates; the bake is identical to it.

## Rejected approaches
- Corner sphere with its default Z axis: its −Z pole is exposed and tessellates into a degenerate triangle (build 1).
- Triangular gusset, legs 30 (r00 bake): no added section from 24 mm to the tip (I_min 1.00 × tube), measured 2026-11-15.
- Triangular gusset extended to the tip: ×1.00 at 36 and 40 mm; the last ~8 mm stay plain tube (measured 2026-11-15).
