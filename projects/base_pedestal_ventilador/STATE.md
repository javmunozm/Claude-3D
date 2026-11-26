# base_pedestal_ventilador: STATE

Updated: 2026-11-26, by the v0 build session (`work/plan_build.md`, `work/build_report.md`).

Keep this file under about 150 lines. Skills read it instead of the README. History, rejected approaches and narrative stay in the README.

## Current
- **Bake:** `stl/base_pedestal_ventilador_platform.stl` (SHA-256 `51024E7B300A0AC2865A09A4BFB111605255BE00FCBEE80EEB9DCF67E451847A`),
  `step/base_pedestal_ventilador_platform.step`; byte-identical to the preview `work/preview/base_pedestal_ventilador_platform.stl`.
- **Macro:** entry `macros/base_pedestal_ventilador.py`; stage package `macros/bpv_model/`.
- **Method:** B-rep in build123d, decided 2026-11-26 (a simple prismatic part; no scan or sculpt).
- **Part:** disc Ø190 × 10 with a Ø80 through hole (stop ring Ø80–Ø95 at z = 10), socket ring Ø95 / Ø115 × 5 on top with a
  1 mm × 45° lead-in, 12 radial through-slots 20 × 26.943. Volume 184.94 cm³ (B-rep), 184.84 cm³ (mesh).

## Open entries
| ID | Region (x, y, z) | Number vs threshold | Class | Status | Decision |
|----|------------------|---------------------|-------|--------|----------|
| F1 | socket hole, r = 47.5, z 10–15 | hole Ø95.0 − fan base Ø95.0 = 0.0 mm | fit | open, unverified | user chose 0 play (2026-11-26); test-print before the full part |

## Locks (must not move)
| Lock | Tolerance | Why |
|------|-----------|-----|
| socket hole Ø95.0 | exact | user: "la medida tiene que ser exacta 95mm, no puede haber juego" |
| stop hole Ø80, disc Ø190 × 10, socket wall 10 × 5 | exact | user brief 2026-11-26 |

## Gates
- **Hard:** watertight, 1 body; `macros/bpv_gates.py` ALL PASS (24 checks + 3 controls).
- **Surface bar:** none agreed.

## Commands
- **Build:** `python macros\base_pedestal_ventilador.py` (preview to `work/preview/`; `--bake` to `stl/`, `step/`), about 0.2 s.
- **Gates:** `python macros\bpv_gates.py <stl>`; `python tools\render_check.py <stl> --views front`; `python tools\render_views.py <stl> --views front back`.

## Rounds
| Round | Date | Steps (tool calls) | Peak context | List price | Result |
|-------|------|---------------------|--------------|------------|--------|
| v0 build | 2026-11-26 | not measured | not measured | not measured | baked, gates 24/24 |

## Decisions pending for the user
- Print a test ring (the socket only) to check the 0.0 mm fit before the full 185 cm³ part.
- Commit and push the project, and add its row to `docs/projects.md` (repo-wide: needs approval).
