# NespressoPodDispenser

## Goal

A forward-facing gravity Nespresso pod dispenser cage — pods stack in a
vertical chute and roll down a rear-to-front ramp to a dispensing mouth at
the bottom front.

This is a **solid-wall rebuild** of the reference model
`references/nespressoDispenser/nespresso-cage-forward-facing.3mf`. The
reference's walls are pierced by a dense honeycomb pattern; every hex is a
separate perimeter the slicer has to trace, which is what makes that model
slow to print. This version keeps the **same envelope, same wall
thicknesses and the same ramp**, but with plain solid walls, so each layer
is a handful of long perimeters instead of hundreds of short ones.

Only the cage is modelled. The reference 3mf contains the cage alone — the
base tray visible in `nespressoimage.png` is a separate part and is not
included here.

## Status

✅ **Macro ready.** Geometry matches the reference within 0.01 mm at every
sampled cross-section.

⚠️ **Print attempt 1 failed** (2026-08-01) — filament ground at 22.2 mm
remaining, losing the base foot. See [Base repair](#base-repair-failed-print-2026-08-01)
for the replacement foot that joins to the salvaged piece without glue.

## Files

| File | What it is |
|---|---|
| `macros/nespresso_dispenser.py` | build123d script that generates the geometry |
| `NespressoPodDispenser.step` | generated STEP output |
| `NespressoPodDispenser.stl` | generated STL, ready to slice |
| `macros/nespresso_base_repair.py` | replacement base foot for the failed print (see below) |
| `NespressoPodDispenser_BaseRepair.step` / `.stl` | that foot, ready to slice |

Regenerate with:

```
python "D:\CAD\Claude-Projects\NespressoPodDispenser\macros\nespresso_dispenser.py"
```

## Dimensions

Measured off the reference mesh; all values mm.

| Feature | Value |
|---|---|
| Outer envelope | 60.2 (X) × 109.2 (Y) × 210.0 (Z) |
| Wall thickness (back / front / sides) | 2.0 |
| Ramp thickness (perpendicular) | 3.0 |
| Ramp incline | ~30° from vertical (slope dy/dz = −0.5773) |
| Front wall | spans Z = +28.79 to +105.0 |
| Retaining lip | vertical, at Y = −9.6, from Z = −75.0 to −45.0 |
| Volume | 120.5 cm³ |

Origin is the centre of the reference bounding box: X across the width,
**+Y toward the back**, **−Y toward the front** (dispensing side), +Z up.

## How it was derived

The reference `.3mf` is a mesh, not parametric, so the dimensions were
recovered from it directly:

1. Sliced the mesh at many Z heights and cast rays through it to read off
   wall positions — this gave the uniform 2.0 mm wall thickness.
2. Extracted the boundary loop of the outer side-wall face at X = +30.1.
   It is exactly an 8-point polygon, which is reproduced verbatim as
   `SIDE_PROFILE` in the script and defines the whole outer silhouette.
3. Fitted the ramp's upper and lower surfaces as separate lines. Fitting
   them over the **inclined section only** matters — including the flat
   lip region skews the slope and puts the ramp ~3 mm out of position.

## Verification

```
python tools\render_check.py NespressoPodDispenser\NespressoPodDispenser.stl --views front right
```

Current result: `body_count = 1`, watertight, consistent winding, bbox
60.2 × 109.2 × 210.0 mm — all gates pass.

Beyond the gates, the part was checked against the reference by casting
rays through both meshes at 15 heights spanning the full model and
comparing every wall crossing. All 15 agree to within 0.01 mm. The eight
corner points of the reference's side profile were also confirmed to lie
on this part's surface.

The `right` render shows the silhouette that confirms the shape is correct:
vertical back spine, front wall down to the ramp, the inclined ramp, the
notch at the retaining lip, and the base foot.

## Base repair (failed print, 2026-08-01)

The first print was run **inverted** — tower on the bed, base wedge last — and
the extruder ground the filament with 22.2 mm still to go. The piece in hand is
the upper ~187.8 mm, complete with ramp, lip and dispensing mouth. What is
missing is the bottom foot:

    Z = -105.0 (bed) .. Z = -82.8    22.2 mm, 4.7 cm³

`macros/nespresso_base_repair.py` regenerates just that foot, with a **socket**
so it joins without glue and **without modifying the printed part**.

### How the joint works

The foot is built up past the cut plane as a U-shaped trench. The printed
part's wall bottom slides straight down into it and is gripped on both its
inner and its outer face. You cut nothing off the salvaged piece.

| | |
|---|---|
| Trench width | 2.4 mm |
| Wall entering it | 1.95 mm |
| Clearance | 0.2 mm per face |
| Socket depth | 8.0 mm |
| Jaw thickness | 1.2 mm each side |

A 0.4 mm chamfer around the mouth lets the part self-centre as it goes in.

### Why a socket and not a tongue

A tongue has to fit *inside* the 2 mm wall band, competing for the same
material as the foot's own wall. Sampling the STL at the cut plane shows the
section there is a thin U (back wall Y 52.6–54.6, side walls |X| 28.1–30.1)
with the dispensing mouth open in the middle — so a tongue sized to clear the
printed part ends up inboard of that band, hanging over the open mouth with
nothing beneath it to fuse to. Built that way the mesh comes back as two
separate bodies, which is that defect showing up.

The socket sidesteps it entirely by sitting *outboard and inboard* of the wall
band, both of which are free space. It needs no room within the wall at all.

**One consequence:** the outer jaw stands 1.2 mm proud of the original
envelope, reading as a thin band around the base — there is nowhere inboard
for it to go, since the trench's outer face is already at the part's outer
surface. Clamping it to the envelope deletes it and leaves a one-sided socket
that cannot grip.

### Load path

The joint is in pure compression: the pods bear on the ramp, which is in the
printed part *above* the seam, and the foot carries that straight down through
the full 303 mm² bearing face. The socket only stops the foot shifting
sideways — it is not carrying the load.

### Verification

```
python tools\render_check.py NespressoPodDispenser\NespressoPodDispenser_BaseRepair.stl --views front right
```

`body_count = 1`, watertight, consistent winding, bbox 62.9 × 49.3 × 30.2 mm
(wider than the wedge itself because of the proud outer jaw). Beyond the gates:

- The wedge was compared against the parent by ray-casting both meshes at
  every 1 mm of height and all sampled cross-sections **match exactly**.
- The socket was checked for interference by sampling 120 000 points of the
  repair solid and testing them against the parent mesh: **zero collisions**
  above the cut plane, so the printed part drops in without forcing.
- The trench was measured directly off the exported mesh: 2.4 mm wide against
  the 1.95 mm wall, i.e. the intended 0.2 mm per face.

### Printing the foot

Print it **the right way up** (flat face on the bed, tongue at the top). In
that orientation the sloped underside becomes an upward-facing surface and
needs no support.

## Printing notes

- **Orientation:** print as modelled (tower upright, Z up) — **base on the
  bed, not inverted.** The first attempt was sliced upside-down, which puts
  the small sloped foot last, 188 mm up in the air; when the filament ground
  at that height the whole foot was lost. Base-down also gives the widest
  first layer. The ramp is self-supporting at ~30° from vertical; the walls
  are all vertical.
- The front wall's bottom edge at Z = +28.79 overhangs the dispensing
  mouth — check this region in the slicer preview; it may want a small
  amount of support depending on the printer.
- Reference prints in the photo are PETG/PLA; either is fine, there is no
  meaningful structural load beyond the weight of the pods.
