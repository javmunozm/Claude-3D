# BedLifter

## Goal

Raise the head end of a bed by 30 cm using two 3D-printed adapter pieces
(HeadLifter ×2, MiddleLifter ×2) that slot between the existing wheel /
support rods and their sockets in the bed. The wheels and middle floor
support stay in their original positions on the floor; the bed itself
tilts head-up.

## Bed geometry

| Parameter | Value |
|-----------|-------|
| Bed length | 200 cm |
| Head wheel rod | Ø 10 mm × 50 mm, socket 5 cm from head end |
| Middle support rod | Ø 15 mm × 40 mm, located 100 cm from each end (centre) |
| Target head lift | 30 cm |
| Pivot | Foot end of bed (x = 200 cm) |
| Lever arm to head wheel | 195 cm |
| **Tilt angle** | **8.85°** (arcsin 30/195) |
| Height at middle support | **~15.4 cm** (100 cm × sin 8.85°) |

## Design — straight body, angled top

Each lifter is a **straight vertical cylinder** standing on the floor.
Only the **top is angled at 8.85°** so it mates flush with the tilted
underside of the bed. The angled top face slopes down toward the foot
end of the bed.

The top rod and collar are **perpendicular to the angled cut face** — they
tilt at 8.85° toward the head end so they plug straight into the bed's
leg sockets, which are themselves perpendicular to the bed underside.

Coordinates per piece (local): +X = toward foot of bed, +Z = up.

### 1. HeadLifter (×2, one per head-end wheel) — **split in two for printing**

| Feature | Dimension |
|---------|-----------|
| Lower body | Ø 50 mm vertical cylinder |
| Upper body | Ø 50 mm at split, tapers to Ø 70 mm over 20 mm, then straight to angled top |
| Body high-side height (head edge) | ~277.8 mm |
| Top male rod | Ø 12.5 mm × 20 mm, perpendicular to angled top face (8.85° from vertical) |
| Collar | Ø 22.5 mm × 8 mm, perpendicular to top face — seats against bed underside |
| Bottom socket | Ø 11 mm × 53 mm, vertical — receives the existing Ø 10 × 50 mm wheel rod |
| Rod-tip height above floor | 300 mm |
| **Horizontal split plane** | z = 230 mm |
| **Cross tenon (lower half)** | 20 × 10 × 10 mm, centred on body axis |
| **Tenon pocket (upper half)** | 20.4 × 10.4 × 10.2 mm (tenon + 0.2 mm clearance + 0.2 mm bottom for glue) |
| Joint resists | Rotation (rectangular cross-section) AND lateral shear |

The lower half (below z = 230 mm) is already printed and unchanged.
Only the upper half needs reprinting when the design changes above the split.

### 2. MiddleLifter (×2, one per middle support leg) — single piece

| Feature | Dimension |
|---------|-----------|
| Body | Ø 40 mm vertical cylinder |
| Body high-side height | ~129.3 mm |
| Top male rod | Ø 15 mm × 20 mm, perpendicular to angled top face (8.85° from vertical) |
| Collar | Ø 25 mm × 8 mm, perpendicular to top face |
| Bottom socket | Ø 16 mm × 43 mm, vertical — receives the existing Ø 15 × 40 mm middle rod |
| Rod-tip height above floor | ~153.8 mm |

## Material & structural verdict

- **Material:** PETG (preferred for load-bearing 3D prints)
- **Design load:** 200 kg static + 30 % lateral
- **Safety factor:** 3× on PETG strengths (50 / 60 / 30 MPa tensile / compressive / shear, E ≈ 1.7 GPa)
- **All checks PASS** — see `macros/structural_check.py`.

## Files

| File | Description |
|------|-------------|
| `macros/bed_lifter_b123d.py` | build123d script — generates all STEP + STL files |
| `macros/view_parts.py` | 3D viewer — serves parts to browser via ocp-vscode |
| `macros/structural_check.py` | Standalone stress / buckling checks (no CAD needed) |
| `HeadLifter_Lower.step / .stl` | Lower half of head-end lifter (already printed) |
| `HeadLifter_Upper.step / .stl` | Upper half of head-end lifter (current version) |
| `MiddleLifter.step / .stl` | Middle-support lifter |

## How to regenerate

```
pip install build123d ocp-vscode
python "D:\CAD\Claude-Projects\BedLifter\macros\bed_lifter_b123d.py"
```

## How to view

```
# Terminal 1 — start viewer server
python -m ocp_vscode --port 3939 --axes --grid_xy --theme dark

# Browser — open http://localhost:3939

# Terminal 2 — send parts
python "D:\CAD\Claude-Projects\BedLifter\macros\view_parts.py"
```

## Run structural check

```
python "D:\CAD\Claude-Projects\BedLifter\macros\structural_check.py"
```

## Dimensions to verify before printing

- [ ] Exact wheel-rod diameter (assumed 10 mm — bottom socket sized 11 mm)
- [ ] Exact middle-support rod diameter (assumed 15 mm — bottom socket sized 16 mm)
- [ ] Bed leg socket inner diameter (assumed 12.5 mm for head / 15 mm for middle)
- [ ] Bed leg socket depth ≥ 20 mm so the top rod fully seats
- [ ] Confirm pivot is at the foot end of the bed

## Print notes

- Print orientation:
  - **HeadLifter_Lower**: flat bottom on bed plate, tenon pointing up
  - **HeadLifter_Upper**: flat split face on bed plate (pocket pointing up); angled top and tilted rod will overhang — use tree supports under the rod
  - **MiddleLifter**: flat bottom on bed plate (single piece, ≤154 mm tall)
- Infill: 60–80 % for load-bearing (or 100 % solid)
- Walls: 4+ perimeters
- Layer height: 0.2 mm acceptable; 0.15 mm for cleaner socket fit

## Assembly

1. Dry-fit the tenon into the pocket — should slip in with light friction.
2. Apply glue to pocket walls and horizontal mating face:
   - PETG-compatible plastic cement, or
   - Two-part epoxy (5-minute or longer), or
   - Cyanoacrylate (CA) — apply sparingly, the 0.2 mm clearance leaves room for a thin film
3. Press upper half onto tenon. Pocket walls handle shear and rotation.
4. Clamp lightly and let cure before loading.
