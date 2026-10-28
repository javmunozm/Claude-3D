# Is the photo usable, and for which axes

Moved from the perspective-checker agent (2026-10-27). Read the section you need.

## The failure you exist to prevent

A photograph is a perspective projection taken from an unknown camera position.
A CAD render is an orthographic projection from an exactly known one. Comparing
them and concluding "the shape is wrong" is only valid if the photo was taken
close to on-axis. Nothing in this repo checked that before you existed.

Two concrete cases from VitaGrip:

**A view can be blind to the axis you care about.** `054-1.webp` is shot straight
down the depth axis. The grip's handles project ~35 mm toward the camera, and in
that image that depth is *completely invisible* — the handles read as flat lobes.
Geometry built from that silhouette alone would faithfully reproduce the outline
and have no depth at all. The image is not wrong; it simply cannot answer the
question. Silence is not confirmation.

**The reference may not be the target object.** VitaGrip's photos show a
PCH-2000 (slim, ~15 mm deep) while the project targets a PCH-1000 (18.6 mm). A
perspective check that validates camera geometry but not subject identity passes
a photo that is measuring the wrong console.

## Method

### 1. Read the metadata, and expect it to be missing

```python
from PIL import Image
im = Image.open("sources/<subject>/<photo>")
ex = im.getexif()
print("EXIF tags:", len(ex) if ex else 0)
```

Product photos in this repo are cropped to square and carry **zero** EXIF tags —
no focal length, no sensor size. Assume you must work from image evidence alone.
Never state a focal length or camera distance you did not read from metadata.

### 2. Test on-axis-ness by mirror symmetry

For an object that is symmetric in reality, a straight-on shot has a symmetric
silhouette and an off-axis shot does not. This needs no metadata:

```python
import cv2, numpy as np
im = cv2.imread("sources/<subject>/<photo>", cv2.IMREAD_GRAYSCALE)
_, b = cv2.threshold(im, 235, 255, cv2.THRESH_BINARY_INV)
cols = np.where(b.any(axis=0))[0]
crop = b[:, cols.min():cols.max() + 1]
inter = np.logical_and(crop, crop[:, ::-1]).sum()
union = np.logical_or(crop, crop[:, ::-1]).sum()
print(f"mirror-IoU {inter / union:.3f}")
```

Measured on this repo's references:

| Photo | mirror-IoU | Reading |
|-------|-----------|---------|
| `054-1.webp` | 0.967 | Near on-axis. Usable for X-Y measurement. |
| `020-1.webp` | 0.562 | Strongly off-axis / three-quarter. Not usable for measurement. |

Guidance: **>0.95** on-axis enough to measure; **0.85–0.95** measurable with a
stated error bar; **<0.85** shape reference only, never a dimension source.

This test is only valid if the subject is genuinely symmetric. Say so when it
isn't, and fall back to the checks below.

**Sweep the threshold and use the lowest score.** A single threshold of 235
can put a photo in the wrong band. Measured 2026-09-24:

| Photo | 225 | 235 | 245 | Otsu |
|-------|-----|-----|-----|------|
| `054-1.webp` | 0.943 | 0.967 | 0.962 | 0.989 |
| `020-1.webp` | 0.468 | 0.562 | 0.706 | 0.326 |

At 225, `054-1` falls from "on-axis" to "measurable with error bar". Report
every value and band on the lowest one. A spread wider than about 0.05 means
the mask, not the camera, is setting the verdict. Crop or clean the background
before you trust it.

**The bands assume the object scores near 1.0 when on-axis. Check that
first.** Render the model on-axis and run the same test on the render.
`VitaGrip1000.stl` scores **0.911** with the camera exactly on-axis, so it can
never reach the 0.95 band. When the model's own score is under 0.95, do not use
the bands. Get the yaw verdict from the outline match in step 5.

The mirror axis was measured and needs no search. Searching ±20 px of offset
and ±6° of roll on both photos above found the best axis within 1 px of the
bounding-box centre, with no roll, and did not raise the score.

### 2b. Mirror-IoU cannot see pitch

Left-right mirror symmetry responds to **yaw** (the camera swinging sideways).
It does not respond to **pitch** (the camera rising or falling), because a
symmetric object tilted toward or away from the camera stays left-right
symmetric. `VitaGrip1000.stl` was rotated and projected orthographically:

| yaw° / pitch° | 0/0 | 5/0 | 10/0 | 30/0 | 0/5 | 0/10 | 0/20 | 0/30 |
|---|---|---|---|---|---|---|---|---|
| mirror-IoU | 0.911 | 0.737 | 0.647 | 0.498 | 0.913 | 0.923 | 0.928 | 0.906 |
| outline IoU vs on-axis render | 1.000 | 0.889 | 0.817 | 0.399 | 0.799 | 0.758 | 0.731 | 0.661 |
| bbox height, % of on-axis | 100.0 | 100.0 | 100.0 | 100.0 | 100.1 | 100.4 | 99.9 | 96.3 |

A photo taken 30° from above passes the mirror test at the same score as a
straight-on one. The bounding box does not catch it either: height moves under
0.5 % up to 20° of pitch. Only the whole-outline comparison responds to pitch,
so a high mirror-IoU never clears pitch on its own. Clear it with step 5, or
mark the vertical in-plane axis **"pitch not established"**.

### 3. Look for perspective evidence directly

- **Converging parallels.** Edges parallel in reality converge in a perspective
  shot. Detect long straight edges (`cv2.HoughLinesP`) and check whether nominally
  parallel pairs share a slope. Strong convergence means significant perspective.
- **Visible faces.** If you can see the front *and* a side of a box-like object,
  the camera is off-axis, and every dimension along the compressed axis is
  foreshortened.
- **Near/far scale.** In a perspective shot the near end of an object is
  measurably larger than the far end. On a symmetric object, compare the left and
  right halves' heights.

### 4. State which axes the view can measure

This is your most important output. For each image, name the two axes in the
image plane (measurable, subject to the on-axis result) and the one along the
view direction (**not measurable, at any confidence**).

```
054-1.webp  view along -Z  →  measurable: X, Y   |  BLIND: Z (grip depth)
020-1.webp  three-quarter  →  measurable: none   |  shape reference only
```

Never let a dimension be taken from an axis you have marked blind.

### 5. Match the render to the photo

Before a render-vs-photo comparison is trusted, confirm:

- `render_check.py` renders **orthographic** (`set_proj_type("ortho")`). A
  perspective photo compared to an ortho render carries an inherent mismatch —
  state it as a floor on the achievable agreement.
- The render's view corresponds to the photo's camera direction. `VIEWS` in
  `tools/render_check.py` maps names to `(elev, azim)`; name the one that matches
  and say why.
- The photo shows the **same object variant** as the model. Check the project
  README and SOURCES.md for a recorded revision difference before comparing.

Measured note: switching this repo's renders from perspective to orthographic
changed silhouette aspect by only 0.2–0.4%. Projection type is a real but small
effect — **the viewing angle dominates**. A wrong view invalidates a comparison
that a correct projection cannot rescue.

**Find the view by matching outlines.** Rotate the model through a grid of yaw
and pitch values, project it orthographically, and score each outline against
the photo's mask. Centre both masks on their centroids and compare at the same
scale. The best-scoring (yaw, pitch) is the photo's camera direction, and that
score is the ceiling on how well the two can ever agree. The table in 2b shows
the sensitivity on VitaGrip1000: 5° of yaw or pitch lowers the outline IoU to
0.89 or 0.80. Projecting with numpy and filling with `cv2.fillPoly` is fast:
11 poses of `VitaGrip1000.stl` took 4.0 s in total, including Python startup and
the STL load. That is fast enough for a 5° grid over ±30° (169 poses). Pyvista
rendering at 1.4–12.5 s per view is not.

```python
R = trimesh.transformations.euler_matrix(np.radians(pitch), np.radians(yaw), 0, "sxyz")[:3, :3]
xy = ((m.vertices - m.centroid) @ R.T)[:, :2]            # orthographic, view along -Z
pts = np.rint((xy - off) * scale).astype(np.int32); pts[:, 1] = H - 1 - pts[:, 1]
img = np.zeros((H, W), np.uint8); cv2.fillPoly(img, list(pts[m.faces]), 255)
```

The photo must show the same object as the model. A photo of the grip mounted
on its console is compared against a render of the grip and console together,
or it is not compared by outline at all. Grid pose search against a real photo
has **not yet been run** in this repo. Before you trust it, test it on
`054-1.webp`, which should come out near `front`, and on `020-1.webp`, which
should come out three-quarter. Report the result either way.

## Reporting format

```
## Perspective Check: <photo> vs <render or intended use>

**EXIF**: <tags found, or "none — cropped, no camera data">
**Subject identity**: <same variant as target? cite README/SOURCES.md>

| Test | Result | Reading |
|------|--------|---------|
| Mirror-IoU (225/235/245/Otsu, lowest used) | 0.943–0.989 | near on-axis in yaw; pitch not established |
| Model's own on-axis mirror-IoU | <value> | bands usable / not usable |
| Best outline match (yaw, pitch) | <°, °, IoU> | <view name> |
| Converging parallels | none detected | low perspective |
| Visible faces | front only | on-axis |

**View direction**: along <axis>
**Measurable axes**: <list>
**BLIND axes**: <list> — no dimension may be taken from these

**Matching render view**: `<name>` (elev, azim) — <why it corresponds>

### Verdict: [COMPARABLE / COMPARABLE WITH CAVEATS / NOT COMPARABLE]

### Caveats
- <each one, with the number behind it>
```
