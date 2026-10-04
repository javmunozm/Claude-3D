# Geometry method and CAD tools

*In force from 2026-10-04: the user chose to rebuild VitaGripPS5 as B-rep. This
answers "the system can't do fillets because it uses meshes; which CAD tool
could work with it?", and gives the method for bringing a scanned shape into
B-rep. Measured 2026-10-03 unless marked.*

## What VitaGripPS5 actually uses

- **Not Blender, and not build123d.**
  - `macros/build_case_ext.py` (213 KB, 69 functions, 166 constants) uses numpy,
    trimesh, shapely and scipy.
  - It imports `build_case.py`, which loads the DualSense scan
    `derived/dualsense_watertight_200k.stl`.
  - Every operation after that is a mesh or height-field edit: stretch, cut,
    warp, refill, vertex moves, smoothing, locks.
- **Blender, in this repo,** is the BrokeFeet sculpt handoff and a renderer.
- **build123d** was used for VitaGripPS5 only in the swept-tube attempt that was
  rejected on 2026-09-08.

So the case has none of what a CAD kernel gives. That is why its fillet
attempts failed:
- in r10, a rolling-ball search hung at 4.1 GB;
- vertex projection made 35k degenerate faces;
- in r15, a remesh made 43k slivers and 9k folds.

## The CAD tool is already installed

Measured on this machine, 2026-10-03:
- **build123d 0.11.1 with OpenCascade (OCP).** OpenCascade is the B-rep kernel
  FreeCAD also uses.
- **The features a v2 case would need are all present:**
  - fillet, chamfer, offset and mirror;
  - loft, sweep and `Spline`;
  - `Face.make_surface` and `Face.make_surface_from_array_of_points`, which fits
    a B-spline surface to a grid of points (the route from a scan to a smooth
    surface);
  - `import_stl`, `export_step`, `export_stl` and `export_brep` / `import_brep`.
- **Four projects already use real fillets:** BoxTest, nespressoDispenserExtension,
  NespressoPodDispenser and the BrokeFeet v0 base.
- **Synthetic probe** (2026-10-03, scratchpad only, 0.8 s; the probe scripts
  were not kept):

| Operation | Result |
|---|---|
| B-spline surface fitted to a 12×12 point grid | valid face |
| Loft through 4 closed spline sections that swell and taper (a grip) | valid solid |
| 3 mm fillet on the loft's tip edge | valid |
| Mirror plus union with a centre block | 1 valid solid |
| STL export | watertight, 1 body, 4,200 faces |
| Fillets on the 24 edges where the loft meets the block | 0.5 and 1.0 mm valid; **2, 3 and 5 mm failed**; `max_fillet` did not converge |

**What that means:**
- **Works:** freeform bodies, mirrors and small rounds.
- **Does not work:** a large round at a sharp boolean junction between a
  freeform body and a block. This is OpenCascade's known weak spot.
- **The B-rep habit:** build the transition into the shape (a loft from the body
  section to the handle section), and keep fillets for small edges. Find the
  largest radius early (`max_fillet`, or try decreasing radii).

## Two representations, compared

| | B-rep (build123d) | Triangle mesh (VitaGripPS5 today) |
|---|---|---|
| Surfaces | exact (planes, cylinders, B-splines) | facets inherited from the scan and from every operation |
| Fillets and rounds | an operation | not available; three methods failed in r10–r15 |
| Symmetry | an exact mirror | the scan's asymmetry is inherited (left handle 0.93–0.99 of the right) |
| Organic form from a scan | needs fitting (sections → splines → loft or surface fit) | direct |
| Local edits | re-run a parametric stage; no seams | each edit's region boundary can become a seam, crease or sliver; 28 regression IDs in r9–r16 |
| Export | tessellated once, at a chosen tolerance | the final mesh mixes 0.19 mm facets with 60–80 mm triangles |
| Typical failure | a fillet refused at a complex junction; an invalid solid from coincident faces | seams on stage boundaries, slivers, folds |

**Use B-rep by default.** Use a mesh pipeline only when the part *is* the scan
(BrokeFeet bones, a hand-sculpted surface).

## Bringing a scanned shape into B-rep

1. **Sections.** Cut the scan with `trimesh.section` at stations along the
   handle (every 3–5 mm, more where it curves) into 2D polylines.
2. **Clean each section.**
   - Resample it to a fixed number of points and smooth it (`scipy`
     `splprep` with smoothing).
   - If the part should be symmetric, build one side only.
3. **Surface.** Choose one:
   - `Solid.make_loft` through the closed spline sections, which carries the
     curvature;
   - or `Face.make_surface_from_array_of_points` on a (u, v) grid, for a patch.
4. **Precise features.** Model the pocket, lips, window, camera hole and flat
   top as solids and extrusions, from traced outlines (`vectors/`) or the spec.
5. **Assemble.**
   - Mirror the half.
   - Union with at least 1 mm of overlap (the cad-designer rule: solids that only
     touch do not fuse).
6. **Rounds.** Large transitions are part of the loft. Fillet small edges, and
   check the largest radius before choosing one.
7. **Deviation gate.** Sample the export and measure the distance to the scan
   (or to the previous bake) with `trimesh.proximity`. Report RMS and maximum per
   region.
8. **Export.**
   - STEP, which is exact.
   - STL with `tolerance=0.02, angular_tolerance=0.2`, giving even triangles.

## CAD tools that could work with this system

What "work with this system" requires:
- Claude Code agents drive the tool with Python scripts;
- it runs on this Windows machine without a person at the GUI;
- it exports STEP and STL;
- it keeps the repo code-first.

| Tool | Kernel / representation | Fillets and organic form | Driven by agents (headless Python) | Licence | Verdict |
|---|---|---|---|---|---|
| **build123d** (installed) | OpenCascade B-rep | fillets: yes (measured); freeform: yes, lofts and surface fits (measured); large rounds at sharp junctions: no (measured) | yes; already the repo standard | free | **Use it** |
| CadQuery | OpenCascade (same kernel) | same as build123d | yes | free | no gain |
| FreeCAD | OpenCascade (same kernel) | same kernel; GUI-centred | partly (`FreeCADCmd`) | free | excluded by the repo; no gain |
| OpenSCAD | constructive solids on meshes | no real fillets | yes | free | not suitable |
| Blender | mesh / subdivision surfaces | mesh bevels and sculpting, not exact CAD | yes (`bpy`, headless) | free | keep for sculpting and rendering only |
| Rhino 8 + Grasshopper | NURBS + SubD | strong blends and fillets; SubD → NURBS for organic forms | scripts run inside Rhino; headless through Rhino.Compute* | commercial | **the next step** if the handle-to-body blend cannot be built in build123d |
| Fusion 360 | Autodesk B-rep + T-splines | strong fillets; T-spline modelling for organic forms | its Python API runs inside the desktop app; no headless command line* | free personal tier with limits*; paid | only with a person in the loop |
| Onshape | Parasolid, in the cloud | strong fillets | REST API + FeatureScript* | the free plan makes documents public* | possible; adds a cloud dependency and API keys |
| Plasticity | Parasolid | excellent fillets, artist-oriented | no practical scripting API* | paid | manual modelling only |
| SolidWorks and similar | Parasolid | strong | COM API on Windows; GUI-bound | expensive | out of proportion |

\* From vendor documentation, not tested here. Check current terms before buying.

## Recommendation

1. **Keep build123d.** For VitaGripPS5, change the method, not the tool: rebuild
   the case as B-rep in a `v2/` (`docs/versioning.md`). The r16 STL becomes the
   deviation reference. The scan becomes a source of sections, not the part.
2. **If the spike below cannot make the handle-to-body blend,** model only the
   organic surfaces in Rhino 8 and export them as STEP. build123d imports STEP
   (`import_step`) and adds the pocket, lips and cuts. The repo pipeline stays
   the same.
3. **Not Blender for the case.** It would repeat the mesh problem.

## VitaGripPS5 v2 spike

This is a new build, so it needs your approval (CORE DIRECTIVE 2).

- **Scope.** The right handle, its junction to a simplified body, one lip and the
  flat top cut.
- **Ceilings.** cad-designer at most 60 turns, at most 6 builds, at most 6
  images; a form-auditor check at most 30 turns.
- **Location:**
  - `projects/VitaGripPS5/v2/README.md`;
  - `v2/macros/vgps5_v2/` for the stage package;
  - `v2/macros/vita_grip_ps5_v2.py` for the main.
- **Gates:**
  - deviation of the handle from r16's right handle: RMS and maximum reported;
    the target is agreed with you;
  - a 3 mm round at the handle tip and at the top edge, valid;
  - mirror deviation 0;
  - a watertight, single-body STL export;
  - the build takes under 5 minutes.
- **Deliverable.** A spike report: what was built, the measured gates, the
  largest fillet radius at the junction, and a go / no-go for a full v2.
- **Run 2026-10-04:** `projects/VitaGripPS5/v2/audit/spike/spike_report.md`.

## A stage cache (for builds over 5 minutes)

A subagent's prompt cache lasts 5 minutes; in the VitaGripPS5 r10 designer run
the re-billing after its 10-minute builds was 40 % of the cost. Cache each
stage's output under a key, and restart a run from the first stage whose key
changed, so a one-region fix rebuilds only the stages after it:

```python
# in the main: one call per stage
key = sha256(stage_source_bytes + json(stage_constants) + upstream_key)
path = project / "work" / "cache" / f"{stage_name}_{key[:12]}.brep"   # .ply / .npz for mesh stages
if path.exists():
    shape = import_brep(path)          # measured: exact round trip, 16 ms for a filleted box
else:
    shape = stage.run(params, upstream_shape)
    export_brep(shape, path)
```

`work/` is an untracked workflow folder (`docs/architecture.md`).
