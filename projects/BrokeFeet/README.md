# BrokeFeet

Left clubfoot skeleton reconstructed from a patient CT study, for pre-operative
teaching. One physical object, built across two pipeline generations that live
side by side in this folder.

> **Clinical scope:** teaching model only. **Not** for surgical planning,
> measurement, or any clinical decision. The full scope statement is in
> [`v0/README.md`](v0/README.md#clinical-scope--read-before-using-this-model)
> and applies to every version here.

## Which file to slice

**`v2/BrokeFeetV2_pinned2.stl`** — the current best foot. The operator's Blender
sculpt plus the hallux and 2nd MTP joint pins, in pipeline millimetres, loads
into OrcaSlicer with no dialog.

Everything else in `v2/` is a superseded stage or a rejected experiment kept for
the record. See [`v2/README.md`](v2/README.md#which-file-to-slice) before
picking any other file — several look shippable and are not.

## Versions

| Version | What it is | Status |
|---|---|---|
| [`v0/`](v0/README.md) | Original CT→mesh pipeline. Owns segmentation, de-identification, source-image provenance, cross-validation, laterality, and the printable teaching-model build | Superseded as the deliverable; **still the upstream pipeline v2 imports from** |
| [`v2/`](v2/README.md) | Rebuild that segments so the hollow-bone defects never form, plus crater repair, Blender sculpt handoff and joint pinning | **Current — ships `BrokeFeetV2_pinned2.stl`** |

There is no `v1/` directory: the V1 rebuild and the V2 sculpt/pin work happened
in one folder and are documented together in `v2/`. The folder is named for what
it ships, not for when it started.

### Why two generations rather than a fix

The V0 model has open windows into hollow bone interiors. Every post-hoc repair
was tried and measured, and none can work — the void that must be filled is
*darker* than the joint that must never be filled (mean grey 96.5 vs 105.2, best
single-threshold separation Youden J = 0.002). Any brightness gate fills the
ankle mortise first and welds the tibia to the talus. Full derivation in
[`v2/README.md`](v2/README.md#why-a-v1-rather-than-a-fix-to-brokefeet).

## v2 depends on v0

`v2/macros/` imports directly from `v0/macros/` (`segment_axial`,
`dicom_pipeline`, `stack_source`). **v0 is read-only** with respect to v2 — the
v2 scripts never write into it, and `export_with_skip.py` monkey-patches in-process
precisely to keep that true. Do not delete v0 as "the old one"; v2 does not run
without it.

## The negative results are the deliverable

Both READMEs are long because they are archives of *measured* failures — six
rejected discriminators, rejected crater-fill strategies, a rejected seam blend,
voxel remesh measured as a negative at every pitch tried. Read the relevant
rejection before proposing a repair; most obvious ideas here have already been
run and quantified.

| Looking for | Read |
|---|---|
| Segmentation, thresholds, tunnels, pillars, laterality | [`v0/README.md`](v0/README.md) |
| Why V1 exists, crater repair, solid STEP export | [`v2/README.md`](v2/README.md) |
| Blender sculpt handoff, smoothing, joint pinning | [`v2/README.md`](v2/README.md#blender-sculpting-handoff-blender) |

## Layout

```
BrokeFeet/
├── README.md     ← this file: which version ships, what each holds
├── v0/           ← original pipeline (upstream dependency of v2)
│   ├── README.md  macros/  holes/  renders/  *.stl *.step
└── v2/           ← current generation, ships the printable foot
    ├── README.md  macros/  blender/  cad/  work/  renders/  *.stl *.3mf
```

Paths are relative to the version folder. Version macros resolve the repo root
as `Path(__file__).resolve().parents[4]` — one level deeper than a flat project,
because of this nesting.
