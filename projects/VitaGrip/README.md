# VitaGrip

Ergonomic grip handle for the Sony PS Vita PCH-1000.

## Status

**Phase: reference vectorization complete, geometry not started.**

Previous parametric handle attempt was rejected — shape did not match
reference. Restarting from properly vectorized reference geometry.

## Dimensions (PS Vita PCH-1000)

| Dimension | Value | Source 1 (vector-templates) | Source 2 (IGN) | Confidence |
|-----------|-------|-----------------------------|----------------|------------|
| Body width | 182.0 mm | 182.0 mm | 7.2" = 182.88 mm | Specified (0.5% delta) |
| Body height | 83.55 mm | 83.55 mm | 3.3" = 83.82 mm | Specified (0.3% delta) |
| Body depth | 18.6 mm | 18.6 mm | 0.7" = 17.78 mm | Specified (4.6% delta — IGN is rounded inch; Sony spec is 18.6 mm including analog sticks) |
| Screen | 5" OLED 16:9 | — | 960x544, ~16M colors | Specified |

## Reference material

All references in `references/psvitaGrip/`:

| File | Type | Use |
|------|------|-----|
| `psvita.jpg` | Orthographic template (5 views) | Dimensional reference, vectorization source |
| `Fixed_dimensions.webp` | IGN infographic | Second dimensional source, feature labels |
| `020-1.webp` | 3/4 photo with DualSense | Primary shape reference for grip |
| `054-1.webp` | Rear view showing handles | Handle profile reference |
| `039-1.webp` | Top-down of two units | Width/depth reference |
| `svg/psvita_*.svg` | Vectorized views (6 files) | Traced outlines in mm, smooth spline curves |
| `dxf/psvita_*.dxf` | DXF exports (6 files) | build123d-importable geometry |

See `references/psvitaGrip/SOURCES.md` for provenance.

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

DXF versions of all views are in `references/psvitaGrip/dxf/` and import
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

```
psvita.jpg → cv2 threshold+contour → scipy spline smooth → SVG (mm) → ezdxf → DXF → build123d
```

## Next steps

1. Use vectorized front/back/side profiles to build the console body as a
   lofted solid in build123d
2. Design grip handle geometry that mates with the console body profile
3. Verify against reference photos (`020-1.webp`, `054-1.webp`)
