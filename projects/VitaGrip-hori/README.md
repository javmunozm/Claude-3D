# VitaGrip

Ergonomic grip handle for the Sony PS Vita PCH-1000.

## Status

**Phase: split-and-widen adaptation COMPLETE. Not yet test-printed.**

Both half-shells of the Hori Remote Play Assist grip have been widened by
3.6 mm to accept a PCH-1000. Run `python projects/VitaGrip/macros/widen_hori_grip.py`
(~5 min) to regenerate.

| Part | Source | Output | Depth | Volume | Gates |
|------|--------|--------|-------|--------|-------|
| Rear | `Rear Cleaned.stl` | `VitaGrip_rear.stl` | 32.94 → **36.54** mm | 47.12 → 53.10 cm³ | watertight, 1 body, 0 bad edges |
| Front | `Front Cleaned.stl` | `VitaGrip_front.stl` | 36.91 → **40.51** mm | 46.42 → 48.12 cm³ | watertight, 1 body, 0 bad edges |

**Console pocket, measured before and after:**

| | Original wrap | Widened wrap | Gain |
|---|---|---|---|
| Rear (plate top → wall top) | 11.50 mm | **15.25 mm** | +3.75 |
| Front (retention band) | 7.75 mm | **11.25 mm** | +3.50 |

**Hori geometry is preserved exactly.** Cross-section areas below the cut plane
are identical to the original at every probe — rear delta 0.000 mm² at
z = 5/10/14/16. The handle, wing and plate are the Hori originals, untouched;
only the console pocket grew. (The front shows up to −4.3 mm² of 4459 at z=21,
0.1%: that is pymeshfix closing pinch points, not the split — the pre-repair
union measured 0.000 delta there too.)

X and Y are unchanged: 194.61 × 105.49 (rear), 194.75 × 100.37 (front).

**The STL outputs are gitignored** (110–134 MB each). Regenerate from the macro.

### Before printing

- Test-fit against a real PCH-1000; the pocket is sized from measured wrap
  depth, not from a fit trial.
- The PCH-1000 is 1.6 mm narrower and 1.55 mm shorter than the PCH-2000, so the
  pocket is ~0.8 mm loose per side in-plane. A thin liner takes that up; the
  shell was deliberately not reshaped.
- The triggers and `Top Latch.stl` are unmodified and have not been re-checked
  against the widened shells.
- 2.2–2.6M faces per part. Most slicers handle this, but decimate if yours
  struggles — and re-check watertightness if you do.

## Dimensions (PS Vita PCH-1000)

| Dimension | Value | Source 1 (vector-templates) | Source 2 (IGN) | Confidence |
|-----------|-------|-----------------------------|----------------|------------|
| Body width | 182.0 mm | 182.0 mm | 7.2" = 182.88 mm | Specified (0.5% delta) |
| Body height | 83.55 mm | 83.55 mm | 3.3" = 83.82 mm | Specified (0.3% delta) |
| Body depth | 18.6 mm | 18.6 mm | 0.7" = 17.78 mm | Specified (4.6% delta — IGN is rounded inch; Sony spec is 18.6 mm including analog sticks) |
| Screen | 5" OLED 16:9 | — | 960x544, ~16M colors | Specified |

## Reference material

Inputs live in `sources/psvitaGrip/` — read by the pipeline, never regenerated:

| File | Type | Use |
|------|------|-----|
| `psvita.jpg` | Orthographic template (5 views) | Dimensional reference, vectorization source |
| `Fixed_dimensions.webp` | IGN infographic | Second dimensional source, feature labels |
| `020-1.webp` | 3/4 photo with DualSense | Primary shape reference for grip |
| `054-1.webp` | Rear view showing handles | Handle profile reference |
| `039-1.webp` | Top-down of two units | Width/depth reference |
| `Vita 1000/` | Downloaded STLs | Shape cross-check (envelope contradicts spec — see SOURCES.md) |

See `sources/psvitaGrip/SOURCES.md` for provenance.

Generated output lives in `vectors/` (SVG + DXF) and this folder's
`.step` / `.stl` files.

## Vectorized views

Generated from `psvita.jpg` using cv2+scipy spline tracing. Scale anchor:
back view width = 462 px = 182 mm (2.538 px/mm).

| View | Dimensions | Features | File |
|------|-----------|----------|------|
| Front | 182.0 x 83.5 mm | 10 (d-pad+stick panel, action-button panel, speakers, SONY, PS bar) | `psvita_front.svg` |
| Back | 182.0 x 83.5 mm | 10 (touchpad, camera, memory slot, headphone jack, multi-use port) | `psvita_back.svg` |
| Top | 182.0 x 18.6 mm | 5 (shoulder buttons, power/volume, accessory port) | `psvita_top.svg` |
| Bottom | 182.0 x 18.6 mm | 7 (ports, charging area) | `psvita_bottom.svg` |
| Left side | 18.6 x 83.5 mm | 7 (trigger, slot, ports) | `psvita_left_side.svg` |
| Right side | 18.6 x 83.5 mm | 7 (trigger, slot, ports) | `psvita_right_side.svg` |

SVG and DXF versions of all views are in `vectors/`. The DXFs import
directly via `build123d.import_dxf()`.

### Known limitations

- **Individual buttons not separated.** The d-pad, analog sticks, and
  action buttons (triangle/circle/cross/square) merge into panel-level
  blobs. The source image at 750 px wide has buttons only ~5-10 px across
  on a panel whose background (gray ~198) and button faces (gray ~68-100)
  both fall below any single threshold. A higher-resolution source or
  edge-detection approach would be needed to separate them.
- **Screen not traced as a feature.** The screen area is *lighter* than
  the body in the reference drawing, so threshold-based detection
  (which finds darker regions) does not capture it. The screen boundary
  is implicit in the body outline and the surrounding features.

## Pipeline

Current task — mesh adaptation:

```
grip2000/*.stl → trimesh (align to origin) → widen console pocket by ~3.6 mm → verify → export
```

Vectorization pipeline used for the rejected from-scratch approach, retained for
console-dimension reference:

```
psvita.jpg → cv2 threshold+contour → scipy spline smooth → SVG (mm) → ezdxf → DXF → build123d
```

## Verification lessons from the rejected attempts

The geometry is deleted; these are the method lessons worth keeping.

**Topology gates cannot detect the wrong object.** The rejected clamshell passed
every gate — watertight, one body, consistent winding — while being 3.7x the
volume of the grip it claimed to be. `body_count == 1` says nothing about whether
you built the right thing.

**A render is not a measurement.** An `iso` render of the rejected part was read
as showing "flat slab handles". Direct cross-sectioning showed 40.3 x 35.3 mm
volumetric handles on a genuinely curved loft path (8.68 mm deviation from a
best-fit line). The visual verdict was wrong in the expensive direction — acting
on it would have rebuilt geometry that matched its own constants. Switching that
render from perspective to orthographic changed its silhouette aspect by 0.2%:
the projection was never the problem, the **viewing angle** was. `iso` compresses
depth; only `right`/`left` showed it. Use `form-auditor` for a number before
believing a picture.

**Check the docstring against the imports.** The rejected macro opened with
"adapted from the Hori Remote Play Assist (grip2000) rescaled for the PCH-1000"
and imported only `build123d`, `pathlib`, `math`. The prose described the
assigned task; the code did something else entirely. Nothing in the pipeline
compared the two.

**Register source geometry in SOURCES.md.** `grip2000/` had no entry, so the file
that *was* the task was invisible to every review that read the provenance table.

## Rejected approaches

Attempts the user discarded. Files deleted; the measured reason kept here so
the approach is not re-walked. See [docs/attempts.md](../../docs/attempts.md).

| Slug | What was tried | Why it was rejected |
|------|----------------|---------------------|
| `parametric-handle` | Grip handle generated from parametric primitives, no traced profile | Shape did not match the reference photos; restarted from vectorized geometry |
| `downloaded-grip-stl` | `newVita_1k_Grip_2.stl` used as a shape reference | Envelope 170x170x123 mm contradicts the confirmed 182x83.5x18.6 mm body — matches neither console revision |
| `parametric-clamshell` | Full clamshell built from build123d primitives while the docstring claimed it was "adapted from the Hori grip2000, rescaled" | **The Hori STL was never opened.** Imports were only `build123d`, `pathlib`, `math`; every `.stl` string was an *export* path. A repo-wide grep for `grip2000` returned one hit — the docstring itself. Measured vs the real Hori rear: 155.9 mm tall vs 105.5 (+48%), 47.5 deep vs 32.9 (+44%), **172.8 cm³ vs 47.1 (3.67x volume; ~214 g PLA vs ~58 g)**. Wall thickness median **6.20 mm vs 2.13**, p75 **32.2 mm vs 2.27** — a solid block with pockets, not a moulded shell. Genus 2 vs 48: 46 topological features (ports, vents, bosses, latch) absent. Handles were volumetric and matched their own constants, but the Hori rear has no Z-protruding handles at all — that volume lives on the `Front` part. |

## Next steps

**Adapt the Hori mesh. Do not author new grip geometry** — that is what all
three rejected attempts did.

The operation is a **split-and-widen (spacer insert)**, not a scale of any kind:

1. Load `Rear Cleaned.stl` and `Front Cleaned.stl` with trimesh and rigid-align
   them into a common frame (they sit on separate print beds; see above).
2. Cut each half on a plane parallel to the console's back face, just above the
   retaining-rim root — around z ≈ 2–3 in the rear's local frame: above the
   plate, below where the wall starts curving.
3. Translate the rim/wall portion **+3.6 mm** along the depth axis.
4. Bridge the gap. **The audit's "same loop shape, close to a straight
   extrusion" premise is wrong** — measured, the rear's cross-section is not
   prismatic anywhere near the cut: loop count swings 19→23→29→20→11 and area
   falls 2099→1151 mm² across z = 17–22. A loop-to-loop triangulation would
   produce garbage. What works instead: extrude the *actual* section polygon at
   the cut plane by 3.6 mm to build a spacer that matches the cut face exactly,
   then boolean-union lower + spacer + translated upper (manifold engine).
5. **Leave X and Y untouched.** The PCH-1000 being 1.6/1.55 mm smaller in-plane
   makes the pocket ~0.8 mm looser per side — take that up with a thin liner
   rather than reshaping the shell.
6. Re-check that the two mating flanges still meet, and that the triggers and
   `Top Latch.stl` still register.
7. Verify with `form-auditor`: does the pocket now measure 18.6 mm + clearance,
   and is the handle geometry **unchanged** from the Hori original? Unchanged
   handles are the point — they are why we started from the real grip.

**Do the cut and bridge on the full-resolution mesh.** Decimating to 60k faces
preserved volume to 0.04% but **broke watertightness**; decimate for rendering
only. The files load in under 5 s at full 2.6M-face resolution.

### Open question

The `vectors/` SVG/DXF set was traced for the from-scratch approach that is now
rejected. It is retained as console-dimension reference, but it is not needed to
adapt the Hori mesh.
