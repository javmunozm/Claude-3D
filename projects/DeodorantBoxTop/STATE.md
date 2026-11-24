# DeodorantBoxTop: STATE

Updated: 2026-11-24, by the v0 build (`work/plan_build.md`, `work/build_report.md`).

Keep this file under about 150 lines. Skills read it instead of the README. History, rejected approaches and narrative stay in the README.

## Current
- **Bake:** `stl/DeodorantBoxTop_cover.stl` (SHA-256 `fc553dd8944caaf284249f8cbe1c7558082229f7fe2c510c62c1eb9543121fa3`) and `step/DeodorantBoxTop_cover.step`, baked 2026-11-24 with `--bake` from the unchanged macro; `dbt_gates.py` ALL PASS 30/30 on the baked STL.
- **Working preview:** `work/preview/DeodorantBoxTop_cover.stl` / `.step` (92 920 mm³, 200 × 210 × 8 mm).
- **Macro:** entry `macros/deodorant_box_top.py`; stage package `macros/dbt_model/`.
- **Method:** B-rep in build123d, decided 2026-11-24 (a plate with prismatic cuts; no reason for a mesh).

## Open entries
| ID | Region (x, y, z) | Number vs threshold | Class | Status | Decision |
|----|------------------|---------------------|-------|--------|----------|
| U1 | sockets, 4 corners | pillar position on the base assumed at (2.7, 2.7) from each edge | unverified input | open | user to measure the base |

## Locks (must not move)
| Lock | Tolerance | Why |
|------|-----------|-----|
| Plate 200 × 210 × 4 | ±0.1 | user brief |
| Hole 46.5 (X) × 44.5 (Y), margins 20 / 3.6 | ±0.1 | user brief |
| Socket cavity leg 17.183, wall 2.5, depth 4, flush | ±0.1 | user brief (pillar 16.5 + 0.2 per face) |

## Gates
- **Hard:** `dbt_gates.py` ALL PASS (30 checks + 2 controls): watertight, 1 body; overall; 12 holes, axes,
  centres, webs, margins; 4 sockets: cavity leg, outer leg, flush, walls; plate thickness, socket depth,
  cavity floor at z = 0. `tools/render_check.py --views front` topology PASS.
- **Surface bar:** none agreed yet.

## Commands
- **Build:** `python projects\DeodorantBoxTop\macros\deodorant_box_top.py` (about 1 s; `--bake` writes `stl/` and `step/`).
- **Gates:** `python projects\DeodorantBoxTop\macros\dbt_gates.py projects\DeodorantBoxTop\work\preview\DeodorantBoxTop_cover.stl`.
- **Region render:** `python tools/render_roi.py <stl> <out.png> --center 20 20 -2 --size 60`.

## Rounds
| Round | Date | Steps (tool calls) | Peak context | List price | Result |
|-------|------|---------------------|--------------|------------|--------|
| v0 build | 2026-11-24 | ~30 | not measured | not measured | preview, all gates pass |

## Decisions pending for the user
- Measure the base pillar position (U1) before printing; consider a one-corner test print for the 0.2 mm fit.
