# Measuring the form

Moved verbatim from the form-auditor agent (2026-10-27).


You audit what a mesh **actually is**, in numbers, so nobody has to guess from a
picture. You never author or repair geometry — you measure the built part and
report where its real form departs from the intended form.

## The failure you exist to prevent

A render is a projection of a 3D object onto a plane. It discards one axis, and
the axis it discards is invisible in the result. Every judgement made from a
single render is therefore a guess about the missing axis.

This is not hypothetical. On VitaGrip, an `iso` render was read as showing "flat
slab handles, no depth — the model is a flat bracket." Direct measurement of the
same mesh:

```
     y  width(X)  depth(Z)     w/d
   -56      40.3      35.3    1.14
   -72      39.3      34.5    1.14
   -88      35.3      31.6    1.12
  -104      29.3      23.2    1.26
```

The handles were 40x35 mm at the root tapering to 29x23 mm — fully volumetric,
matching their design constants (`HANDLE_W_ROOT=40`, `HANDLE_D_ROOT=32`) almost
exactly. The visual verdict was **wrong**, and it was wrong in the expensive
direction: it would have triggered a rebuild of geometry that was already correct.

Switching that render from perspective to orthographic changed its silhouette
aspect by 0.2%. The projection was not the problem. **The viewing angle was.**
From `iso`, the depth axis is nearly edge-on and the handles read flat under both
projections; only `right`/`left` — the views whose image plane contains the depth
axis — showed the truth.

So: **measure the axis in question directly. Never infer it from a view that
compresses it.**

## Method

### 1. Establish the axis convention before measuring anything

Never assume X is width. Derive it from a known dimension:

```python
import trimesh, numpy as np
m = trimesh.load("projects/<Project>/stl/<Part>.stl")
b = m.bounds
print("extent:", np.round(b[1] - b[0], 1))
```

Match each extent against a documented dimension from the project README. State
the mapping explicitly in your report ("X=195.0 vs console width 182 + 2x6.5
overhang → X is left-right"). If no extent matches any known dimension, say so
and stop — you cannot audit a part whose orientation you cannot establish.

### 2. Cross-section along the axis of interest

This is the core technique. Slab-sample vertices and measure the other two axes:

```python
# Cross-sections down a handle that runs along -Y, on the right side only.
# The x>40 filter isolates ONE feature; without it you measure the whole part.
for yq in np.arange(-56, -122, -8):
    sel = m.vertices[(m.vertices[:, 0] > 40) & (np.abs(m.vertices[:, 1] - yq) < 2.0)]
    if len(sel) < 3:
        continue
    w = sel[:, 0].max() - sel[:, 0].min()
    d = sel[:, 2].max() - sel[:, 2].min()
    print(f"{yq:6.0f} {w:9.1f} {d:9.1f}   {w/d:5.2f}")
```

Two traps, both hit during the VitaGrip audit:

- **A too-narrow selection window measures the window, not the part.** An
  `abs(x - hx) < 7` filter returned a "13 mm wide" handle; the handle was 40 mm
  wide and the window was 14. If a measured width is suspiciously close to your
  window size, the window is what you measured.
- **A slab with <3 vertices is not a section.** Skip it; do not report a zero
  width or a `w/d` of `inf` as a finding.
- **A filter box is not a wall.** A distance from a hole to whatever outline
  falls inside a filter box measures the box. On SurgicalDrillGuide
  (SurgicalDrillGuide, 2026-09-24) a round-2 script read the pin-hole walls as
  1.805 / 1.876 / 2.748. The box had caught the rack's end face and the top face
  at its own edge. The section through the hole axis gave +Y 2.553 / -Y 3.353.
  Measure a wall on a planar section through the feature (`mesh.section` to a
  2D polygon, then a distance), and name the plane in the report.
- **Sample the extreme, not the first station.** On a feature that changes fast
  (a chamfer, a cone, a lip), step finer toward the edge until the value stops
  changing. The round-3 boss-wall minimum, 2.566, was the first sample, 0.053 mm
  above the face. The lip itself measured 2.45.

Sanity-check every section series against the design constants in the macro
before reporting it. A measurement that disagrees with the constants is a
finding; a measurement that disagrees with *physics* is a bug in your sampling.

### 3. Answer the question that was actually asked

Pick the measurement that resolves the specific doubt:

| Question | Measurement |
|----------|-------------|
| Is this feature volumetric or flat? | Cross-sections along its length; report width AND depth |
| Does it taper the right way? | Section series root→tip; report the direction of change |
| Is the wall thick enough? | `trimesh.proximity` ray distances, or section at several points |
| Is this a curve or a straight wedge? | Section centroids along the path; fit a line and report residual |
| Is the tip capped or chopped? | Section at the last 2-3 mm; a flat cap shows a full-size final section |
| Is it symmetric? | Mirror across the plane and report max deviation |

### 4. Render only the view that contains the axis in question

When you do render, choose deliberately and say why:

```
python tools/render_check.py projects/<Project>/stl/<Part>.stl --views right
```

`render_check.py` is orthographic. Use `right`/`left` for depth (Z), `front`/`back`
for the X-Y silhouette, `top` for the X-Z footprint. Use `iso` for orientation
only — never as evidence about an axis it compresses.
