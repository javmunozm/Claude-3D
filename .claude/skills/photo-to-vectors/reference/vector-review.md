# Reviewing the traced vectors

Moved from the accuracy-reviewer agent (2026-10-27). Read the section you need.

## What you check

### 1. Scale accuracy

The most critical check. Every vectorized file should carry real-world mm dimensions derived from a known anchor.

- **Read the SVG/DXF metadata** to identify what anchor was used and what scale was applied
- **Verify the anchor independently**: if the file claims 182 mm width based on a pixel measurement, re-measure those pixels yourself from the source image. The anchor is the **only** photo measurement you repeat. See "Scope" below.
- **Cross-check derived dimensions**: if the file says the body is 182 x 83.5 mm, check whether 83.5/182 matches the height/width pixel ratio in the source image
- **Flag scale drift**: a 1-2% error is typical for photo-derived measurements; >5% means the anchor is wrong or the crop missed the true edge

### 2. Outline fidelity

Compare the vectorized outline against the source image:

- **Render the SVG to an image** at the same resolution as the source
- **Overlay or side-by-side compare** with the source image
- **Check for shape distortion**: rounded corners that should be sharp (or vice versa), convex curves that should be concave, flat edges that should be curved
- **Check for outline bloat/shrink**: the traced outline should follow the body's visible edge, not the shadow, the background boundary, or a watermark

Use cv2 for programmatic comparison:
```python
import cv2
import numpy as np

# Load source and rendered SVG as grayscale
src = cv2.imread("source.jpg", cv2.IMREAD_GRAYSCALE)
vec = cv2.imread("rendered_svg.png", cv2.IMREAD_GRAYSCALE)

# Threshold both to binary silhouettes
_, src_bin = cv2.threshold(src, 200, 255, cv2.THRESH_BINARY_INV)
_, vec_bin = cv2.threshold(vec, 128, 255, cv2.THRESH_BINARY_INV)

# Resize to match
vec_resized = cv2.resize(vec_bin, (src_bin.shape[1], src_bin.shape[0]))

# Compute IoU (intersection over union)
intersection = np.logical_and(src_bin, vec_resized).sum()
union = np.logical_or(src_bin, vec_resized).sum()
iou = intersection / union if union > 0 else 0
print(f"Silhouette IoU: {iou:.3f}")  # > 0.90 is good, > 0.95 is excellent
```

### 3. Feature inventory

Count and identify features in the vector file and compare against the source:

- **List all paths/shapes** in the SVG with their bounding boxes and approximate areas
- **Classify each**: body outline, screen, button, port, speaker, camera, etc.
- **Compare against the source image**: are any features missing? Are there extra paths that don't correspond to real features (watermark fragments, noise)?
- **Check feature placement**: is each feature in roughly the right position relative to the body outline?

### 4. Curve quality

Zoom into the vector paths and check:

- **Stair-stepping**: pixel-level jagged edges from insufficient smoothing — the path should be smooth curves, not polylines following pixel boundaries
- **Over-smoothing**: features that have been rounded away or merged — sharp corners on the Vita's d-pad should be sharp, not bulbous
- **Self-intersections**: paths that cross themselves, creating fill artifacts
- **Gaps**: paths that should be closed but have a visible gap at the start/end junction

### 5. Watermark and annotation contamination

Reference images often contain watermarks, dimension annotations, logos, or grid lines. These should NOT appear in the vectorized output.

- **Check for text-like paths**: isolated small paths with high curvature that look like letter fragments
- **Check for straight diagonal lines**: watermarks are often diagonal text across the image
- **Check for thin features**: annotation lines and arrows are much thinner than product outlines; they should have been filtered by morphological opening

## Reporting format

Produce a structured review with:

```
## Vector Accuracy Review: <filename>

**Source**: <reference image filename>
**Scale anchor**: <what dimension, what value, confidence>

### Dimensions
| Measurement | Expected | Actual (SVG) | Error | Verdict |
|-------------|----------|--------------|-------|---------|
| Body width  | 182.0 mm | 182.0 mm     | 0.0%  | PASS    |
| Body height | 83.5 mm  | 85.2 mm      | 2.0%  | WARN    |

### Features
| Feature | In source? | In SVG? | Position OK? | Shape OK? |
|---------|------------|---------|--------------|-----------|
| Screen  | Yes        | Yes     | Yes          | Yes       |
| D-pad   | Yes        | No      | -            | -         |

### Quality
- Curve smoothness: [GOOD / FAIR / POOR]
- Contamination: [CLEAN / <list of issues>]
- Silhouette IoU: <value>

### Verdict: [PASS / NEEDS FIXES / REJECT]

### Fixes needed (if any):
1. <specific actionable fix>
```

## Handling multi-view files

When reviewing a set of SVGs for the same object (front, back, top, bottom, left, right):

- **Cross-check dimensions between views**: the width in the front view must match the width in the back view; the height in the front must match the height in the side view
- **Check depth consistency**: the top/bottom view depth should match the side view depth
- **Flag any view where the aspect ratio is implausible** given the known dimensions

## Scope: review the vectors, do not re-measure the photos

Your inputs are the vector files, the source images, and the MEASURE stage's
measurement table (`projects/<Project>/docs/MEASUREMENTS.md` or the project README). Check the
vectors against those inputs: overlay each ring on its source image, compare its
dimensions with the table, and check that the ring is valid.

- Re-measure only the scale anchor.
- If a number in the measurement table looks wrong, report it as a finding for
  the MEASURE stage, with the evidence. Do not derive a new value yourself.
- On a re-review after fixes, re-check **every** finding from the previous
  review, not only the ones the fix targeted. Re-run the ring checks (validity,
  dimensions against the table, overlay) on **every** ring, in one script, so
  that a fix that broke a different ring is caught. Give each finding a status
  (fixed / unchanged / worse) and one verdict. Do not re-measure the photos.

The first full review of SurgicalDrillGuide v2 wrote 25 scripts in 94 calls,
several of which re-measured the photos. The narrow re-review that followed used
17 calls. Re-checking every ring with one scripted pass keeps a full re-review
near that cost. Checking only the named findings misses regressions
(VitaGripPS5, rounds 7-8: see `docs/agents.md`, *Fix rounds*).
