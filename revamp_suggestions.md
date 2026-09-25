# Revamp suggestions

Outcome of the 2026-09-24 audit of the agents, the perspective checks, the mesh
code and the macro structure. It records what was decided, what was already
done, and what is left to apply when each project is next reworked. Every
number below was measured in that session. Anything not measured says so.

## Decisions

| Decision | Detail |
|----------|--------|
| **One `.py` per stage, one short main** | Constants, inputs/derived values, shape helpers, one file per part (`parts/<part>.py`), and a main that calls them in order, assembles, validates and exports. Recorded in `docs/architecture.md` ("Parametric model pattern") and the cad-designer agent. |
| **Apply on rework, not now** | Existing single-file macros stay as they are until their project is next reworked. |
| **YAGNI for sharing** | A helper moves to a shared module only once a second project actually uses it. No framework, no stage runner, no build cache, no speculative library. A C#-style `cadkit/` library + runner + cache was proposed and **rejected** for this reason. |
| **Output folders** | Every project (and version folder) keeps meshes in `stl/`, STEP in `step/`, PNGs in `renders/`. Done for all projects (see below). |
| **BrokeFeet is finished** | No further work on it, including the STEP validity defect listed under open items. |
| **Hash maps were not the problem** | The heavy mesh work already runs inside numpy / trimesh / scipy / OCC. The problem is structure, not loops. |

## The structural problem

- **Big single files.** `VitaGrip1000/v2/macros/vita_grip.py` is 1324 lines,
  `SurgicalDrillGuide/macros/surgical_drill_guide.py` 920,
  `SurgicalDrillGuide/macros/sdg_gates.py` 707. Changing one part means reading
  and running the whole model.
- **A full run rebuilds everything.** One SurgicalDrillGuide run took 10.1 s:
  import of build123d/OCP 3.65 s, `build_all()` 4.50 s (all four parts, even if
  one changed), validity checks 0.86 s, exports about 1 s. Each separately
  launched script pays the 3.65 s import again.
- **Copies instead of imports.** VitaGrip1000 v0 and v2 hold identical copies
  of `trace_grip.py`, `trace_console.py` and `trace_dualsense.py` (39
  functions), against the repo rule that v2 imports from v0.
- **Rewritten helpers.** `write_svg` / `write_dxf` exist in 6 files. DXF/SVG
  reading, ring → face → extrude, bore/slot/window cutters and basic mesh
  checks are reimplemented per project. Export + folder + validation code is
  repeated in every macro.
- **Script-style files.** `sdg_gates.py` has 129 top-level statements and no
  `main`. The SurgicalDrillGuide `vectors/scripts/*.py` run everything at import.

## Per-project suggestions (apply when the project is next reworked)

### SurgicalDrillGuide

> **DONE 2026-09-25** (user approved doing it now instead of at the next round).
> The stages are in the package `macros/sdg_model/`, not loose in `macros/` as
> the table below says, because loose stage files collide across projects (see
> "Module names collide" below). `horizontal_chord` went to `rings.py` next to
> `vertical_chord`, since the handle builder uses it too, and `ctip_pad_region` went
> to `parts/main_frame.py`. The main gained `--part <name>`. Result: all 11
> exports byte-identical (STEP header excluded), and the macro stdout, the 134-line
> gate log and the 219-line `docs/mechanism_sizing.py` log unchanged. Timings:
> full build 11.1 s; `--part` 4.3–7.6 s, of which about 4.3 s is fixed (imports
> and `parameters()`); gates 27 s, now the slowest step. Not done: `sdg_gates.py`,
> and making the part builders take every dimension as an argument (they still
> read some constants directly).

Original plan (the split followed these seams):

| Section | Lines | New file |
|---------|-------|----------|
| §1 CONSTANTS | 56–212 | `constants.py` |
| §2 RING IMPORT + DERIVED | 213–347 | `rings.py` |
| §3 generic helpers (`extrude_z`, `box`, `polygon_face`, `teardrop_bore_x`, `cone_y`, `cyl_y`, `one_solid`, `shapely_faces`) | 348–514 | `shapes.py` |
| §3 mechanism helpers (`cam_thread`, `thread_radius_fn`, `sawtooth_cutter_face`, `pawl_tooth_pts`) | inside 348–514 | `mechanisms.py` |
| §3 part builders | 515–726 | `parts/main_frame.py`, `parts/l_arm_slider.py`, `parts/handle.py` |
| §4 PARAMETER BUNDLES (`horizontal_chord`, `derive_pin`, `parameters`, `seat_notch`) | 727–845 | `parameters.py` |
| `build_pin` (sits in §4 today) | 846–850 | `parts/end_stop_pin.py` |
| `build_all`, `slider_at`, `part_path` + §5 GENERATE | 851–920 | `surgical_drill_guide.py` (main; `--part <name>` builds one part) |

- Keep the names `sdg_gates.py` uses available from the main module, so the
  gates run unchanged.
- Acceptance: build output and the full 5-gate log identical before and after.
- `sdg_gates.py`: same treatment in a second pass (one function per gate, a
  main that runs them).
- (Superseded: the plan was to split during the next rebuild round, and
  `RESUME_HERE.md`, since deleted, tracked that rebuild. The user approved the
  split on 2026-09-25 instead; see the DONE note above.)

### VitaGrip1000

- Replace the v2 copies of `trace_grip.py`, `trace_console.py` and
  `trace_dualsense.py` with imports from `v0/macros/`. Keep v0.
- Split `vita_grip.py` into stages as above.

### Small projects (BedLifter, BoxTest, NespressoPodDispenser, nespressoDispenserExtension)

- Split into stages only if they are reworked. Their export/folder code is the
  first candidate for a shared helper, since it is identical in all of them.

### Module names collide (found 2026-09-25)

Python caches a module by its bare name. Tested with a fake second project
that has its own loose `constants.py`, in one process with SurgicalDrillGuide:

| Layout | Load order | Result |
|---|---|---|
| Loose stage files in `macros/` | SDG first | second project read SDG's `T_Z` 10.0 instead of its own 99.0, **silently** |
| Loose stage files in `macros/` | other first | SDG failed: `ImportError: cannot import name 'IMPORT_DIR'` |
| Package with a unique name (`macros/sdg_model/`) | both | each read its own values |

Rule, now in `docs/architecture.md` and the cad-designer agent: stage files go in
a package named for the project, with relative imports.

### Shared helpers, once a second project needs them

- Output paths and validate → export STEP + STL.
- DXF / SVG ring read and write.
- Ring / polygon → face → extrude.
- Basic mesh gates (watertight, bodies, sealed voids).

## Already done in this session

- **`/verify` skill deployed.** It sat at `.claude/skills/verify.md` and never
  loaded. Now `.claude/skills/verify/SKILL.md`.
- **Agent paths fixed.** bone-morphologist pointed at a missing
  `sources/brokenfeet_deid_axial/`. Two SurgicalDrillGuide paths are now
  written out in full. The audit of all 9 agents finds no missing paths.
- **perspective-checker refined:**
  - Mirror-IoU depends on the threshold: `054-1.webp` scores 0.943–0.989
    across 225/235/245/Otsu, so the lowest value is used.
  - The bands assume the model scores near 1.0 on-axis, and VitaGrip1000
    scores 0.911. Check the model first.
  - Mirror-IoU cannot see pitch: 0/30° pitch 0.906 against 0.911 on-axis.
    Whole-outline matching against a render does see it: 5° of pitch gives
    0.80.
- **STEP export** (`tools/mesh_to_step.py`). Builds the shell from the mesh's
  own edges instead of sewing, and falls back to sewing when the mesh is not a
  closed 2-manifold. 82k faces: 6.6 s against 180 s. On the BrokeFeet mesh it
  gives 1 shell where sewing gave 4, with the same faces and volume.
- **Loop fixes, identical output:**
  - vectorised `to_index`: 2.43 s → 0.029 s
  - cached KD-trees in the two bone-fusing functions: 12.7 → 11.1 s and
    3.9 → 2.6 s, on 3 bodies
- **Output folders.**
  - 90 files moved into `stl/` / `step/` / `renders/`.
  - Scripts and tools updated: `render_check` and `render_views` default to
    the sibling `renders/`.
  - `.gitignore` updated. The 110–134 MB VitaGrip-hori STLs were never ignored
    before.
  - Fast builds and the SurgicalDrillGuide gates re-run from the new paths.
- **Convention recorded** in `docs/architecture.md` and the cad-designer agent.

## Open items

- **Pose search not yet tested on a photo.** Outline pose search has not been
  run against a real photo. Test: `054-1.webp` should come out near `front`,
  `020-1.webp` three-quarter.
- **BrokeFeet STEP defect (not to be fixed).** The STEP fails OCC's validity
  check because of 40 zero-area triangles from `manifold3d.simplify`. The
  project is finished, so this is recorded here only.
- **New renders are not committed by default.** `.gitignore` ignores every
  `renders/` folder. PNGs already tracked stay tracked. New ones need
  `git add -f`.
- **Workflow folders not moved.** `derived/`, `blender/`, `holes/` and the
  SurgicalDrillGuide `vectors/` work images keep their own PNG/STL files.
- **Fixed but not run.** `locate_views.py`, `make_locator.py` and
  `prep_for_blender.py` pointed at folders that no longer existed. Their paths
  are fixed, but none of them has been run.
- **Not committed yet.** As of 2026-09-25, none of the above is committed.
  The memory entry for SurgicalDrillGuide was corrected on 2026-09-25: it
  pointed at `RESUME_HERE.md`, which had been deleted.
