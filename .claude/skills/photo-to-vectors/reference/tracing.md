# Tracing to SVG / DXF

Moved from the vector-tracer agent (2026-10-27). Read the section you need.

## Pipeline

The established pipeline in this repo is:

```
reference image (.jpg/.png/.webp)
    │
    ├─► vtracer (color-aware raster→SVG vectorization)
    │   OR
    ├─► cv2 + scipy (threshold → contour → spline smooth → SVG)
    │
    ▼
raw SVG (traced outlines, possibly noisy)
    │
    ├─► svgpathtools (parse, clean, filter paths)
    ├─► scale calibration (anchor dimension → px/mm)
    │
    ▼
clean SVG (mm units, smooth curves, labeled features)
    │
    ├─► svgpathtools + ezdxf (SVG paths → DXF polylines/splines)
    │
    ▼
DXF (importable by build123d via import_dxf)
```

### Tools available

Versions are in `docs/system.md`; they are not repeated here, so they cannot drift.

| Tool | Package | Purpose |
|------|---------|---------|
| vtracer | `vtracer` | Rust-based raster→SVG vectorizer with color clustering. Use `convert_image_to_svg_py(image_path, out_path, ...)` |
| OpenCV | `cv2` | Image loading, thresholding, contour finding, morphological operations |
| scipy | `scipy` | B-spline fitting (`splprep`/`splev`) for smoothing traced contours |
| svgpathtools | `svgpathtools` | Parse SVG paths, extract/manipulate Bezier curves, compute path lengths |
| svgwrite | `svgwrite` | Write SVG files programmatically |
| ezdxf | `ezdxf` | Write DXF files — convert SVG paths to DXF polylines/splines |
| build123d | `build123d` | `import_dxf()` and `import_svg()` for direct CAD import |

**Not available:** potrace (won't build on Windows), Inkscape CLI (not installed). Use vtracer or cv2+scipy instead.

### vtracer parameters

For technical drawings / orthographic views of products:
- `colormode="binary"` — best for line drawings and silhouettes
- `filter_speckle=4` — remove noise specks (pixels)
- `corner_threshold=60` — preserve sharp corners
- `path_precision=3` — decimal places in SVG path coordinates
- `mode="spline"` — output cubic Bezier splines (smoother than polygon mode)

For photographs with gradients:
- `colormode="color"` — preserve color regions
- `layer_difference=16` — color quantization step
- `filter_speckle=8` — more aggressive noise removal

### cv2+scipy approach (when vtracer produces too much noise)

1. Load image, convert to grayscale
2. Threshold to isolate the body outline (watch for watermarks — use morphological opening to remove thin features)
3. Find contours with `cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)`
4. Smooth each contour with `scipy.interpolate.splprep/splev` (B-spline, 300-400 output points for body, 100-150 for features)
5. Multi-threshold feature detection: cascade through thresholds (e.g. 190, 170, 150) to catch features at different gray levels
6. Deduplicate overlapping features by bounding-box IoU

### SVG→DXF conversion (Python, no Inkscape)

```python
import svgpathtools
import ezdxf

# Parse SVG paths
paths, attributes = svgpathtools.svg2paths("input.svg")

# Create DXF
doc = ezdxf.new()
msp = doc.modelspace()

for path in paths:
    # Sample path to polyline points
    points = []
    for t in np.linspace(0, 1, 200):
        pt = path.point(t)
        points.append((pt.real, pt.imag))
    msp.add_lwpolyline(points)

doc.saveas("output.dxf")
```

For cubic Bezier curves, use `msp.add_spline()` with control points extracted from `path.bpoints()` to preserve curve quality.

## Scale calibration

**Every SVG you produce must be in real-world mm units.** The scale comes from an anchor dimension — a known measurement that maps pixels to mm.

1. Identify the anchor: a spec-sheet dimension, an annotation in the reference image, or a ruler in the frame
2. Measure the anchor in pixels (the span between two known points)
3. Compute `scale = anchor_mm / anchor_px`
4. Apply scale to all coordinates: `coord_mm = coord_px * scale`

If no anchor exists, say so and ask for one. Never produce mm-dimensioned output from unscaled pixel measurements.

## Output conventions

### SVG files
- Store in `projects/<Project>/vectors/` — generated output belongs to the
  project that produced it, never back in `sources/` (which holds inputs only)
- Filename: `<subject>_<view>.svg` (e.g. `psvita_front.svg`)
- Use mm units in the SVG viewBox and width/height attributes
- Include a `<title>` element naming the subject and view
- Include a `<desc>` element documenting the source image and scale anchor
- Style: body outline as `.body` class, internal features as `.feat` class
- Add dimension lines for known dimensions (red, with arrowhead markers)

### DXF files
- Store in `projects/<Project>/vectors/` alongside the SVG
- All coordinates in mm
- Body outline on layer "BODY", features on layer "FEATURES", dimensions on layer "DIMENSIONS"

## Quality checks

After generating vector output, verify:

1. **Bounding box matches known dimensions** — body outline width/height should match the anchor-derived values within 1%
2. **No stray paths** — watermark text, dimension annotations from the source image, or noise should not appear as geometry
3. **Smooth curves** — zoom into corners and tangent transitions; jagged pixel stair-stepping is a sign of insufficient smoothing
4. **Feature count** — compare the number of detected features against what's visible in the reference image
5. **Closed paths** — body outlines and feature boundaries should be closed (start point = end point)
6. **The ring is SIMPLE** — `shapely.geometry.LinearRing(pts).is_simple` must be
   True, and every segment must be longer than ~0.02 mm.

Open the SVG in a viewer or render it to an image and compare side-by-side with the source. A vector file that "looks right in the code" but has never been visually compared to its source is not verified.

### Check 6 is not optional, and here is what it costs

A traced outline that self-intersects — even by a fraction of a millimetre, even
at a single vertex — imports through `import_dxf()` as a **closed wire with the
right number of edges, the right length and the right bounding box**. Nothing
about it looks wrong. But `make_face()` on it yields a face whose `is_valid` is
False, and any solid extruded from that face:

- reports **one body**,
- reports **consistent winding**,
- reports the **correct volume and bounding box**,
- and is **not watertight**.

So the repo's topology gate fails three stages downstream, pointing at the
boolean union, while the actual defect is a 0.3 mm crossing in your SVG. In
VitaGrip1000 this cost several debugging passes: the union, the mouth prism and
the stick relief were each rewritten before the profile itself was tested.

Two specific causes, both worth checking for:

- **The spline's closing point repeated exactly.** `splev` with `per=True`
  returns the start point again at the end; that becomes a zero-length segment
  and build123d warns `N faces have been skipped due to null triangulation`.
  Treat that warning as an error, not noise.
- **A stroked drawing traced with `RETR_EXTERNAL`.** Technical templates draw
  the body as an outline, not a fill, so the contour follows the *outer edge of
  the stroke* and gets dragged inward wherever that stroke meets an internal
  feature. Fill the contour first (`drawContours(..., -1)`), then re-trace.

Repair with `shapely`: `Polygon(ring).buffer(0)` resolves a self-intersecting
ring into a valid polygon; take the largest part if it returns a MultiPolygon.

### Prefer shapely for offset and scale, not the CAD kernel

When the downstream script needs the outline offset (a fit clearance) or scaled
onto a spec dimension, do that arithmetic on the **points**, in shapely, before
the DXF is written or immediately after it is read. build123d's `offset()` and
`scale()` each touch every one of a traced outline's several hundred vertices
and reliably produce an invalid face from a valid one — with exactly the silent
symptoms above. `shapely`'s `buffer(d, join_style=2)` is robust on dense
polygons.

## The vectors must be CONSUMED, not just produced

Your output is not a deliverable on its own. It exists so a build123d script can
`import_dxf()` it and build from the real outline. A `vectors/` folder full of
beautiful SVGs that no macro imports is **worse than nothing**: it looks like
the tracing stage happened, so nobody checks, while the geometry is quietly
built from `Rectangle()` and `Circle()`.

That is exactly what happened in VitaGrip1000's first pass. The pipeline in
`docs/agents.md` was skipped entirely: pixel measurements went straight into
build123d primitives, the console's curved face was modelled as
`Rectangle(182, 83.55)`, and the resulting pocket cut **1232 mm² (8.8 %) more
than the console's face actually occupies** — the material that should have
wrapped its tapered ends. Every topology gate passed. It took the user pointing
at the reference image to catch it. The `VitaGrip-hori` project has the same
failure recorded from its own history: `vectors/` was generated and then
abandoned when the approach changed, and the README still has to explain why the
files are kept.

So, before you report done:

1. **Name the consumer.** State which script imports each file you wrote, and
   which function does the importing. If no script imports it yet, say so
   explicitly and say what it is for — do not let it look finished.
2. **Prove the import works.** Actually run `import_dxf()` on your output and
   report the resulting face's area and `is_valid`. Do not hand over a DXF you
   have not round-tripped.
3. **Say what the primitive alternative would cost.** Compute the difference
   between your traced outline and the naive primitive someone would otherwise
   reach for (area, or max deviation in mm). That number is the argument for
   the vector stage existing, and it belongs in the project README.
