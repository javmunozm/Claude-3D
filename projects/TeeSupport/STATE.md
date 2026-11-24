# TeeSupport: STATE

Updated: 2026-11-15, by r00 pass 2 (gusset option C).

## Current
- **Bake:** `stl/TeeSupport_reinforced.stl` (SHA-256 `603FD657E231999A580F494943623F59673C09056B5A5C60220344F4E935E746`), identical to `work/preview/TeeSupport_reinforced.stl`. Plates run to both tips (option C).
- **Working preview:** `work/preview/TeeSupport_reinforced.stl`.
- **Macro:** entry `macros/tee_support.py`; stage package `macros/tee_model/`.
- **Method:** B-rep in build123d, decided 2026-11-15.

## Open entries
| ID | Region (x, y, z) | Number vs threshold | Class | Status | Decision |
|----|------------------|---------------------|-------|--------|----------|
| — | — | — | — | — | — |

## Locks (must not move)
| Lock | Tolerance | Why |
|------|-----------|-----|
| Bore = ROD_D + BORE_CLEARANCE | ± 0.05 | 8 mm rod (user) |
| Wall | 4.00 ± 0.05 | user |
| Overall per axis | 50.0 ± 0.1 | user |
| Gusset thickness | ≥ 5.0 (built 6.0) | user |
| Gusset shape | plates to both tips, 4.0 proud of the tube at the tip | user chose option C 2026-11-15 |

## Gates
- **Hard:** watertight, 1 body (`tools/render_check.py`); `macros/tee_gates.py` ALL PASS (32 checks + 2 controls).

## Commands
- **Build (preview):** `python projects/TeeSupport/macros/tee_support.py` (0.1 s); `--bake` writes `stl/`, `step/`.
- **Gates:** `python projects/TeeSupport/macros/tee_gates.py <stl>`.
- **Region render:** `python tools/render_roi.py <stl> <out.png> --center X Y Z --size 40`.

## Rounds
| Round | Date | Steps (tool calls) | Peak context | List price | Result |
|-------|------|---------------------|--------------|------------|--------|
| r00 | 2026-11-15 | not recorded | not recorded | not recorded | built and baked; 3 builds, 2 images read |
| r00 pass 2 | 2026-11-15 | not recorded | not recorded | not recorded | gusset option C baked; 2 builds, 2 images read |

## Decisions pending for the user
- Frame span and number of loaded corners, for the fdm-tolerance strength check (6 kg, PETG).
- Caliper measurement of the rod; the bore clearance follows from it.
- Adding TeeSupport to `docs/projects.md` (a repo-wide file).
