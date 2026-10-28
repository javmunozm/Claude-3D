---
name: photo-to-vectors
description: Turn reference photos, drawings or product images into numbers and outlines a build123d script can consume — qualify each image (on-axis? perspective? which axes it can measure), set the scale from an anchor, measure, trace outlines to SVG/DXF, and review the vectors against the source. One chain, in that order. Writes a plan first, runs it once, reports. Use whenever a part starts from a photo, a drawing, a screenshot or a downloaded model rather than physical measurements, and before comparing any render to a photo. Not for building geometry (cad-build) or tolerances (fdm-tolerance).
---

# photo-to-vectors

A photograph has proportions, not scale, and it can only measure the axes in
its image plane. This skill turns references into **dimensioned, traced,
reviewed** inputs, and says plainly what they cannot establish. It never
writes geometry.

The chain is fixed. A later stage never starts on an image an earlier stage
did not pass:

```
1 QUALIFY   is this image usable, for which axes?          reference/perspective.md
2 MEASURE   anchor → px/mm → measurement table              reference/measuring.md
3 TRACE     outlines → SVG/DXF, round-tripped             reference/tracing.md
4 REVIEW    vectors vs source and documented dimensions     reference/vector-review.md
```

A request may need only the first stages (a usability question stops at 1; a
size question at 2). Any part whose **outline** carries information (not a
rectangle, a taper, a swelling handle) goes through 3 and 4: a table of two
numbers for a shape is its bounding box, and `Rectangle(182, 83.55)` overcut
the VitaGrip1000 console by 1232 mm² (8.8 %).

Three phases, always in this order: **PLAN → RUN → REPORT**. No pixel is
measured and nothing is traced before the plan is written and shown.

## 1. PLAN (no measuring)

Read the subject's `sources/<subject>/SOURCES.md` first (it held the right
VitaGripPS5 grip width, 223.3 / 222.6 mm, while 237.9 shipped), the project's
`STATE.md`, and any existing `docs/MEASUREMENTS.md` and `vectors/README.md`.
Look at each image once, cropped, only to plan.

Write the plan from `plan_template.md` (this folder) to
`projects/<Project>/work/plan_reference.md` and show it in chat. It must say:
- **Per image:** what it is (photo, CAD render, drawing), how many physical
  objects are in the frame, and the on-axis test it will get (mirror IoU and
  its threshold 0.85, `reference/perspective.md` step 2). An image not yet
  qualified is not used.
- **The anchor:** which object carries the known dimension, its source (spec,
  user measurement), and how the span will be read: the **maximum exposed
  span**, with max vs median reported. An occluder only shortens a span.
- **Per dimension wanted:** the image and view that can see that axis, the
  method, the expected confidence (Specified / Measured / Estimated /
  Judgement), and any independent value to cross-check against.
- **Per outline:** the trace method, the documented dimensions it will be
  gated against, the script and function that will `import_dxf()` it. The
  part **being designed** is traced, not only the part it mounts to; each
  axis comes from a traced view, never a formula.
- **Ceilings:** images read (default 8), scripts (one per stage, edited).

## 2. RUN (the plan, once, stage by stage)

- **QUALIFY** each image with the number that decides it. Below 0.85 mirror
  IoU it is a shape reference only; say which axes it is **blind** on. A 3/4
  render is never a side view: `psvitarearbackside.webp` read as one gave a
  round bridge where the print is a C-channel.
- **MEASURE** against the anchor, row by row, with Python, not by eye. State
  the anchor's pixel coordinates and px/mm before any other number. Two axes
  off by the same factor is one scale error: check the anchor first. Deliver
  width-vs-position tables with the profile's direction in words.
- **A stated explanation is a claim.** If a README says why a number came out
  as it did, re-run what it implies before citing it (the S>150 story changed
  the grip span by 1.1 %, and could not produce 237.9).
- **TRACE** to SVG and DXF; check the ring is simple and closed; round-trip
  `import_dxf()` and report the face area and `is_valid`; compute the error
  the naive primitive would have made.
- **REVIEW** the vectors as a separate step: against the source image (IoU)
  and the documented dimensions (README, SOURCES.md, the measurement table),
  never against the tracer's own printout. More than 3% off on any
  anchor-derived dimension fails. An unverifiable file is not a passing file.
- **Nothing outside the plan** without a written amendment in the plan file
  (what, why, the number that forced it); at most one. **Two failures** on a
  stage → stop it, report what failed with its numbers.

## 3. REPORT

Write `projects/<Project>/docs/MEASUREMENTS.md` (one row per dimension:
Dimension | Value | Source image | Method | Confidence), `vectors/` with a
`README.md` naming each file's source image, anchor and consumer, and a
pointer line in `STATE.md`. In chat, at most 25 lines:
1. Per image: usable for which axes, with its number.
2. The anchor, its span and px/mm.
3. The dimensions, with confidence, and every contradiction between sources.
4. Vectors written, their review verdict (PASS / NEEDS FIXES / REJECT), and
   who imports them.
5. What the references **cannot** establish.

When a built part is later compared to a photo, this skill's QUALIFY stage
runs on that photo first, and the comparison is judged on form, by looking at
`_vs_reference.png`: the silhouette-profile table is not evidence.

## Reference (read the section you need)

| File | Holds |
|---|---|
| `reference/perspective.md` | Metadata, mirror-IoU on-axis test, what it cannot see (pitch), perspective evidence, which axes a view can measure, matching a render to a photo, report format |
| `reference/measuring.md` | The anchor rule, sourcing and `SOURCES.md`, the capture protocol for the user, how to measure, the deliverable and confidence levels, shapes that need an outline, protrusions |
| `reference/tracing.md` | vtracer and cv2+scipy pipelines, SVG→DXF, scale calibration, output conventions, the quality checks (the simple-ring check is not optional), shapely for offsets, vectors must be consumed |
| `reference/vector-review.md` | Scale, outline IoU, feature inventory, curve quality, watermark contamination, multi-view files, report format |

## Rules

- No anchor, no measurements: ask for one dimension.
- Never present a photo-derived number as a specification, or blur the
  confidence levels: fdm-tolerance refuses to anchor a tight fit on anything
  below Specified.
- Say which variant the reference shows; split spec (absolute) from photo
  (proportional) values when they differ.
- A downloaded mesh is checked against known specs before any use, and its
  remeshing history stated (a 2.2 mm voxel remesh lost the Vita's buttons).
- Don't claim a camera parameter not read from metadata. Don't treat an axis
  a view cannot see as agreement: say "blind", never "matches".
- **Don't trace only the body when the object has parts that stand proud of it.**
  Separate body from protrusion by occupancy and report each protrusion's
  height (the Vita's 18.6 mm depth read 23.4 from the top view, 37.8 from the
  bottom).
- A tool given a dimension by hand prints that value and its source.
- An image found unusable for what it was being used for is a finding:
  report it plainly, even when it invalidates work already done.

## Session rules

- **Write as you go.** Each finished result goes into the deliverable when you
  have it. If the session must end mid-run, write `work/handoff.md`
  (`docs/templates/handoff.md`: done / not done / files / next step); the next
  session starts from the plan plus the handoff.
- **Two failures, then stop** that approach: report what failed, with its
  numbers, and what you would try next.
- **One scratch script, edited,** printing at most about 50 lines.
- **Images confirm, they do not search.** Measure numerically; look once at a
  cropped region.
- **Read only what you need.** Grep long docs and the README by section. Never
  `Glob` `**/*`.
- **Parallel calls.** Put independent reads and checks in one response.
- **Scripts and builds** run in the foreground with `timeout 300 python …` in
  the Bash tool (in PowerShell `timeout` is a different command). Anything over
  5 minutes is a defect to report, not something to wait out.
- **Shell.** One command per call, absolute paths, no `cd`, no `python -c`, no
  `sleep` loops; view files with Read / Glob / Grep. A hook denies the rest and
  says how to rewrite it.
- **Tools.** Installed packages and the DXF/SVG import pipeline are in `docs/system.md`
  and `docs/commands.md`: Grep them for what you need.
