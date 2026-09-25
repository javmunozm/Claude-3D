# VitaGrip1000

A grip for the Sony PS Vita **PCH-1000**: a slim cross-bar low across the
console's rear, with two DualSense-contoured handles at its ends. The
console's front face and rear touchpad stay exposed and nothing goes near the
shoulder buttons.

## Slice this

```
projects\VitaGrip1000\v2\stl\VitaGrip1000.stl
```

## Versions

| Version | What it is | State |
|---------|-----------|-------|
| [v0](v0/README.md) | The **solid** grip. 149 cm³. Establishes every measured profile, the console pocket and the keep-outs. | Superseded, **kept** — see below |
| [v2](v2/README.md) | v0's geometry **hollowed to a 3 mm shell**, plus palm swell, finger grooves, grip texture and internal ribs. 77.7 cm³. | **Ships.** Not yet test-printed |

**v0 is an upstream dependency in substance, not in code.** v2's macros are a
copy, not an import, so v2 runs without v0 — but v0's README is the archive of
*why the shape is what it is*: the rim-trace failure, the extrusion-vs-loft
finding, the 2 mm slot-depth bug, the speaker-covering notch. Do not delete it.

There is no `v1`. v0 and v2 are the two generations that exist; the two designs
deleted before v0 are recorded in [v0/README.md](v0/README.md), not preserved
as folders.

## The 173 mm contradiction

The blueprint set (`BackDetailedView.jpg`, `vistaFrontal.png`,
`lateralHAndleview.jpg`) annotates the grip at **173 mm** wide with a
**160 × 56 mm** installation void. The console it must hold is
**182 × 83.55 × 18.6 mm**.

Both numbers are impossible: the grip cannot be narrower than the console it
wraps, and the void cannot be smaller than the object it contains.

**Those drawings are used for features and shape only — never for dimensions.**
Every dimension comes from the product photographs and the real PCH-1000 mesh.
The one number taken from them is `WALL = 3 mm`, which both agree on and which
matches what v0 had already chosen independently.

Details in [v2/README.md](v2/README.md#the-173-mm-problem).

## Console facts

[v0/CONSOLE_FACTS.md](v0/CONSOLE_FACTS.md) — the PCH-1000's real dimensions,
why its front outline is not a rectangle, why bounding boxes lie about its
depth, and the build123d traps that cost this project real debugging passes.
Those apply to every version.

## Reference material

`sources/psvitaGrip/SOURCES.md` carries full provenance. In short:

- **Shape**: `054-1.webp` (HSV mask, primary), `lateralHAndleview.jpg` (depth)
- **Console**: `psvita.jpg` and `Vita 1000/psvitaManualJoin_decimated.stl`
- **Features**: the 2026-09-02 blueprint set — features only, not dimensions

## Verification, both versions

Geometry that builds and exports can still be physically wrong. Each version
runs, in order:

1. `vita_grip.py` — bbox, body count, keep-outs (shoulder, screen, speakers),
   ray-probed slot depth, and in v2 the sealed-cavity flood fill
2. `fit_check.py` — 200,000 points sampled on the real console mesh, **0 may
   be inside the grip**
3. v2 only: `feature_audit.py` — the shell, vent, swell, grooves, texture and
   wall thickness measured **on the exported mesh**

Zero interference does not prove the fit is comfortable or that the walls
retain the console. **Neither version has been test-printed.**
