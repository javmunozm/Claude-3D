# BentoBox

Modified parts for the BentoBox V2 air purifier (fan case + duct, HEPA and
activated-carbon stages).

## Source

`sources/bentoBox/bento box no screws and magnets.step`: one compound with
11 named solids. Split 2026-10-20 into `sources/bentoBox/parts/`, one STEP per
solid, named from the STEP's own solid names. Each split solid was matched to
exactly one solid of the full import (volume + bbox centre); the split volumes
sum to the original 535 632.3 mm³.

| File | Size (mm) | Role |
|---|---|---|
| `exhaust_base.step` | 52.8 × 122.8 × 55.0 | exhaust base |
| `fan_case.step` | 52.8 × 112.8 × 36.0 | fan case |
| `hepa.step` | 52.8 × 112.8 × 52.5 | HEPA stage |
| `carbon.step` | 52.8 × 112.8 × 79.9 | carbon stage housing (holds the cartridge) |
| `cover_voronoi.step` | 52.8 × 112.8 × 4.4 | cover |
| `CMag_1.step` | 72.0 × 100.0 × 26.0 | carbon cartridge tray, 4 slab grooves |
| `CMag_2.step` | 72.0 × 100.0 × 16.3 | carbon cartridge lid |
| `net_infill_x4.step` | 1.4 × 95.0 × 35.0 | carbon slab, solid as supplied (print ×4) |
| `male_test.step`, `female_test.step` | 36 × 14 × 13.8 / 10.0 | fit test pieces |
| `Body1.step` | 30.8 × 40.6 × 33.0 | unnamed body |

## Perforated carbon slab

The supplied slab is solid, so no air passes through the cartridge. The slabs sit in
1.6 mm grooves (X 1.0–2.6, 23.8–25.4, 46.6–48.2, 69.4–71.0 in `CMag_1`); the
outer two are the cartridge's side walls, the inner two divide three carbon
compartments. Each faces an open window Y 4.6–95.4, Z 4.6–35.4 (rib ends in
`CMag_1`/`CMag_2`, tray rib top Z 4.6, lid rib underside Z 35.4). The slab file
already shares the cartridge's Y/Z coordinates.

Pellets: activated carbon, pelletised, 4 mm typical diameter (supplier sheet).

Design (`macros/bento_model/parameters.py`):
- hex holes, 3.0 mm across flats (inscribed circle 3.0 < 4.0 mm pellet), flats
  facing along the slab, honeycomb lattice
- 1.2 mm web between all neighbours
- holes only inside the window; original outline and corner fillets kept

Measured result (2026-10-20, `macros/carbon_slab.py` output):
- 164 holes, removed volume 1789.6 mm³ = expected 164 full through-cuts
- open area 1278 mm² of the 2797 mm² window (45.7 %)
- solid border to slab edge 4.0 mm (ends), 3.04 mm (top/bottom)
- 1 solid, valid; STL watertight, 1 body (render_check)

Not measured: the fit in the grooves after printing, or airflow / pressure drop.

## Files

- `macros/carbon_slab.py` — run `python projects\BentoBox\macros\carbon_slab.py`
- `step/carbon_slab_perforated.step`, `stl/carbon_slab_perforated.stl` (print ×4)
- `renders/carbon_slab_perforated__*.png`

## Frame and cartridge STLs (2026-10-20)

`macros/export_parts.py` writes one STL per piece to `stl/`, in the source
assembly's coordinates:
- frame, bottom to top: `exhaust_base`, `fan_case`, `carbon`, `hepa`,
  `cover_voronoi` (top grille/shroud)
- cartridge: `CMag_1` (tray), `CMag_2` (lid)
- `frame_assembly.stl`: the five frame pieces in place, preview only. The
  pieces nest 2.3–3.5 mm into each other at the joints, so this file is
  several bodies, not one printable solid.

Not exported: `male_test`, `female_test` (test pieces), `Body1` (a separate
30.8 × 40.6 × 33 block, not part of the frame stack).

Measured: the source B-reps each have 1 shell and 0 free edges. OCC's
tessellation added 4–24 zero-area sliver triangles to six of the seven STLs,
which failed `render_check` as non-watertight. The script drops them, then
asserts 1 watertight body with unchanged volume; all seven pass `render_check`.

## Status

Perforated slab generated, not printed.
