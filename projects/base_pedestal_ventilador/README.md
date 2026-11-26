# base_pedestal_ventilador

## Goal
A platform for a pedestal fan. The fan's existing round base (Ø95 × 10 mm, user) drops into it: the platform lifts the
base by 10 mm and doubles its footprint to Ø190.

## Status
v0 built and baked 2026-11-26: `stl/base_pedestal_ventilador_platform.stl`, `step/base_pedestal_ventilador_platform.step`.
Not printed or test-fitted. Numbers and checks in `STATE.md`; the build in `work/plan_build.md` and `work/build_report.md`.

## Brief
User, 2026-11-26.
- Fan base today: a circle Ø95, 10 mm tall. Two goals: raise it 10 mm and double the diameter.
- Disc Ø190, 10 mm tall, with a Ø80 hole: the ring Ø80–Ø95 is the internal stop the fan base sits on.
- On top of the disc: a socket with a Ø95 hole, 5 mm tall, 10 mm wall so it resists the insertion (OD 115, confirmed).
- Hole **Ø95.0 exactly, no play** (user: "la medida tiene que ser exacta 95mm, no puede haber juego"). A 0.2 mm-per-side
  clearance was offered and declined.
- 1 mm lead-in chamfer at the socket mouth (user accepted the offer).
- Not solid: rectangular holes to save material (user: "no tiene sentido que sea sólido"). The user chose 12 radial slots,
  20 mm wide, through the disc, with 5 mm solid rims inside (to the socket) and outside (to the edge, at the slot corners).

## Dimensions (as built)
| Feature | Value |
|---|---|
| Disc | Ø190 × 10, bottom face on the bed |
| Stop hole | Ø80 through; stop ring Ø80–Ø95, top at z = 10 |
| Socket | hole Ø95.0, OD 115, z 10–15; 1 mm × 45° chamfer at the mouth (Ø97 at the top face) |
| Slots | 12 at 30°, 20 × 26.943, from r = 62.5 to r = 89.443; spokes 13.03 (inner end) to 26.06 (outer end) |
| Volume | 184.94 cm³ (the solid version would be 249.76 cm³) |

## Verification checklist (before printing)
- [ ] **Fit:** hole Ø95.0 for a Ø95 base is 0.0 mm of play. An FDM hole usually prints undersize, so the base may not go in.
      Not measured. Print the socket alone first.
- [ ] Fan base diameter Ø95 and its flat underside: user's value, not measured here. Anything under the fan base must fit inside Ø80.
- [ ] Bed: Ø190 needs at least 190 × 190 mm. Printer not stated.
- [ ] Strength and tipping: not checked (fan weight and height unknown).

## Print
Bottom face on the bed, socket up. Slots and holes are vertical through-cuts; no supports.

## Method
B-rep in build123d (2026-11-26): a prismatic part, nothing scanned or sculpted.

## Rejected approaches
- A solid disc (first plan, 249.76 cm³): rejected by the user as wasteful, replaced by the 12 slots.
