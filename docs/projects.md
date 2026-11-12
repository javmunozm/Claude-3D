# Projects

**State on 2026-11-11, after the disk format** (`docs/lessons.md`, last entry).
Every project lost its `sources/`, `stl/`, `step/`, `renders/` and `audit/`
folders; the Status column below describes each project **before** that.
Measured on 2026-11-11 by building into a scratch folder:

| Project | Rebuilds from the repo alone? |
|---|---|
| NespressoPodDispenser | Yes, both parts: valid, 1 solid, watertight; 120.49 cm³ (README 120.5) and bbox 62.9 × 49.3 × 30.2 for the base repair |
| nespressoDispenserExtension | Yes, both pieces: valid, 1 solid, watertight; 48.82 / 56.59 cm³ against the README's 48,9 / 56,7 (0.2 % apart, cause not looked into) |
| SurgicalDrillGuide | No: the macro imports `vectors/import/*.dxf`, which were lost (`STATE.md`) |
| VitaGripPS5 | No, stated from the paths the code reads: r16 needs the scans in `sources/`, v2 needs the r16 STL (`STATE.md`) |
| BentoBox | No, stated from the code: it imports the split STEP parts from `sources/bentoBox/parts/` |

<!-- Add one line per project as they are created -->
| Folder | Description | Status |
|--------|-------------|--------|
| BentoBox | Modified parts for the BentoBox V2 air purifier: a perforated carbon slab (hex through-holes) replacing the solid one supplied, and STL exports of the frame and cartridge parts split from the downloaded STEP | Carbon slab and exports built 2026-10-20; see the README. Row added 2026-11-11: the project never had one |
| NespressoPodDispenser | Forward-facing gravity Nespresso pod cage; solid-wall rebuild of a hex-perforated reference, for faster printing | Print 1 failed (filament ground); base-repair foot ready |
| SurgicalDrillGuide | Ratcheting K-wire / drill guide, a teaching model. Three printed parts, all outlines traced from photos: `main_frame` (C-hook, bar and toothed rack), `l_arm_slider` (L-arm with a compliant pawl) and `handle` (Tr16x4 thread into a Ø22 boss), plus a removable end-stop pin | **Round 5 built, audited and strength-checked at 25 N (PETG assumed). Not printed or test-fitted.** Tip gap 14.472 / 43.452 / 74.042 mm at MIN / MID / MAX. Macro split into stages in `macros/sdg_model/` on 2026-09-25, with identical output. Build `macros/surgical_drill_guide.py` (`--part` for one part), gate with `macros/sdg_gates.py`. See README |
| VitaGripPS5 | PS5-style grip for the PS Vita **PCH-1000**, handles contoured after a DualSense. Built from scratch; shares nothing with VitaGrip1000. | **r16 case baked 2026-10-03** (`stl/VitaGripPS5_case_r16.stl`): a snap-in case built on the DualSense scan by `macros/build_case_ext.py`, reviewed ACCEPT WITH LISTED ARTIFACTS. Next: the first test print. Current state: `projects/VitaGripPS5/STATE.md`. The 2026-09-14 socket grip (`stl/VitaGripPS5.stl`, `build_socket_grip.py`) is superseded and kept on purpose. |
| nespressoDispenserExtension | Extensión de capacidad para el dispensador de cápsulas Nespresso. **Dos piezas de 150 mm** que se acoplan: `A_base` se inserta en la boca del holder (40 x 37,5 internos, con calibre) y `B_acople` va encima con un **zócalo local** de 12 mm que recibe a A. Cápsulas **de lado**; chute 37,10 x 33,40 idéntico en ambas para no dejar escalón. Corte de inspección de 20 mm con **pico a 45°** arriba (no arco: un semicírculo deja 14,1 mm de techo plano y se imprime sin soportes). Pared asimétrica en A (1,2 en las caras normales a X, las de 37,0 de ancho) porque el holder impide ensancharla. **Independiente de NespressoPodDispenser**. | **Geometría lista, sin imprimir.** Ambas watertight, 1 cuerpo. ⚠️ margen del reborde **+0,00** contra el peor caso de la ficha (Ø37,10): imprimir un cupón antes de los 150 mm. Falta el chaflán de inserción |
