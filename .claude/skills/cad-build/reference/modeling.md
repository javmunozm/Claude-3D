# Modeling rules

Moved verbatim from the cad-designer agent (2026-10-27). Read the section you need.


## Choose the representation first

Before any geometry, decide how the part is represented, and record it in the
README:
- **B-rep in build123d by default.** Lofts, fillets, mirrors and exact booleans
  work here: a probe on 2026-10-03 lofted a freeform handle, filleted it,
  mirrored it and exported a watertight STL.
- **A mesh pipeline only when the part *is* a scan or a sculpt** (BrokeFeet).
  VitaGripPS5's case was built as 69 stacked stages on the DualSense scan mesh:
  fillets could not be made on it, and every fix pass made new defects on stage
  boundaries (28 regression IDs in r9–r16).
- **The measured B-rep limit:** large rounds at a sharp junction between a
  freeform body and a block (1 mm worked, 2 mm did not). Shape such transitions
  into the loft instead of filleting them afterwards.

See `docs/cad_method.md`.

## How you work

1. **Understand the physical object first.** Get or confirm real-world measurements (what it mates to, existing hardware dimensions, target clearances) before writing geometry. Ask the user for missing measurements rather than guessing — a wrong assumption here produces a part that doesn't fit. If the dimensions come from reference photos rather than physical measurement, get them from the photo-to-vectors skill, and carry their stated confidence level through into the README.
2. **One `.py` per stage, one short main.** Constants, inputs/derived values, shape helpers, one file per part builder (`parts/<part>.py`), and a main that calls them in order, then assembles, validates and exports. The stage files go in a package named for the project (`macros/<pkg>/`, e.g. `sdg_model/`) with relative imports, never loose in `macros/`: two projects' loose `constants.py` collide in one process, and the second one silently reads the first one's values (measured 2026-09-25). Count `parents[...]` from the file's real depth: `macros/<pkg>/x.py` reaches the project folder at `parents[2]`, `macros/<pkg>/parts/x.py` at `parents[3]`. The main stays in `macros/`. See "Parametric model pattern" in `docs/architecture.md`; `projects/SurgicalDrillGuide/macros/` is the reference layout. A new project starts this way. An existing single-file macro is split along its stages **at the first round after a bake, before any new stage is added**, and any single macro over 60 KB before its next change (`docs/architecture.md`): not as a side task, and never mid-way through someone else's round. VitaGripPS5 was reworked in 16 rounds without a split and grew to 213.5k characters. Share a helper across projects only once a second project actually uses it.
3. **Only the main runs anything.** Stage files only define. Module-level export calls fire on *import*, so a viewer script, a check script, or a reconciliation step that imports the module silently overwrites the project's exported files as a side effect. Put the generate step under `if __name__ == "__main__":` in the main. When you touch a geometry script that exports at module level, fix it.
4. **Prefer parametric, reusable builders over one-off geometry.** A builder function should accept dimensions as arguments so it can be reused for variant parts (e.g. left/right, different sizes), matching how `build_lifter(...)` is written generically and called twice with different constants.
5. **Handle splits/joints explicitly** when a part exceeds printer bed size or needs multi-piece assembly. Use the tenon/pocket (or equivalent boolean-cut) pattern already established, deriving the joint from one shared definition rather than duplicating it.


## Booleans only fuse where solids OVERLAP

A union of two solids that merely **touch** does not fuse them — it leaves them as separate solids in a `ShapeList`/`Compound`, which then fails `body_count`/watertight, or raises `AttributeError: 'ShapeList' object has no attribute 'bounding_box'` when you call a solid-only method on the result.

This has bitten three separate features in this repo: a corner tab placed flush on a face, a handle whose neck butted exactly against the part it hung from, and a lobe ending exactly at a band's edge. Every mating feature must **interpenetrate** its neighbour by a millimetre or two — build it oversized and let the union trim it. When you place a feature at a computed boundary (`y_bot`, `z_front`, a split plane), that is exactly the case that produces a zero-overlap joint, so add the overlap deliberately.

**Surfaces that exactly coincide break a union too**, not only solids that
touch. The SurgicalDrillGuide thread crest (r 8.0) sat exactly on the Ø16 core
surface. The union returned an invalid solid, and the STL export then hung (see
gate (a)). Offset one surface by at least 0.01 mm, or overlap it. When a
feature must end flush with a face, build it past the face and trim both in one
cut: the round-5 stop leg was built 0.5 mm long and trimmed with the carriage
end.

When a boolean returns a `ShapeList` or the topology gate reports extra bodies, **enumerate the pieces and their bounding boxes** rather than guessing which joint failed:

```python
for i, s in enumerate(result.solids()):
    print(i, s.volume, s.bounding_box())
```

Tiny solids (a fraction of a cm³) are almost always a detail feature that never fused; their bounding box tells you which one.

## Cut-then-refill, and height-field resolution

**Do not cut a region out of a visible surface and glue a separately built
block back in.** The outline of the cut becomes a seam that every later stage
has to hide.
- VitaGripPS5 (r7-r10) removed the trigger paddles this way: a boolean
  difference ("trigger zone clear"), then a union ("trigger zone refill").
- Four rounds of tuning the patch's fade, inset and outline each made a new
  defect on its outline. The last was an open slit 0.5-0.9 mm wide, from a
  refill inset 0.5 mm inside the clear.
- The user saw the corner as "puzzle pieces added to the main frame".
- Shape the region with the same continuous operation as its surroundings.
  In r11 the corner became the lobe cut to the same target surface as the
  rest of the back, and the slit and seams were gone.
- See `docs/lessons.md`, "Ten defect IDs were one glued-in patch".

**A height field is only as smooth as its grid.**
- On a 1 mm grid, a steep drop renders as saw-teeth. VitaGripPS5 r11's end
  roll made a 20 mm drop over 2.4 mm, and a cut easing jumped 3 mm where a
  face crossed between nodes.
- Refine the grid locally, for example 0.25 mm over the region that has the
  steep or rounded surface (`fine_axis` in `build_case_ext.py`), rather than
  tuning constants on the coarse grid.
- When a rounding still renders as a cliff on the fine grid, the cause is
  room, not resolution. Measure the room, and report the trade-off to the
  user.

**Build a rounded edge into the cutting surface itself** (for example a
rolling-ball opening of the top height field, as in `top_cut()` in r12),
instead of adding a separate fillet stage on a mesh afterwards. Mesh fillet
stages failed in VitaGripPS5 r10:
- a rolling-ball search over a refined mesh hung at 4.1 GB, or grew to
  1.45 M faces;
- vertex projection hit the face cap, folded faces, or made 35 k degenerate
  faces.

Anything cut AFTER that surface keeps sharp edges: r12's bottom opening, cut
after `top_cut()`, came out with 0.5 mm edges.

## Modeling solid, organic forms

The VitaGrip failure was partly a modeling-approach failure, not just a missed check. Two habits to avoid:

- **Don't build a solid object as an outline of thin walls.** A hand grip, handle, or any part meant to feel substantial is a *volume*. If a reference shows a body with real bulk, model bulk — a 3 mm wall and a thin connecting band will render as a wireframe-like bracket no matter how correct its outline is.
- **Check the direction of every taper against the reference before trusting the loft.** Handles and grips very often **swell** below the neck and only then round off to a tip — the shape your hand closes around. A monotonically shrinking width profile produces a spike, not a grip. When a loft station table exists, read its widths as a sequence and confirm the *sequence* matches the reference silhouette, not just its endpoints.

For any lofted organic form, get the station table from the photo-to-vectors skill's measured silhouette rather than inventing the numbers, and keep enough stations to carry a curve (a bulge needs stations on both sides of its peak).

- **Prefer edge positions over width-plus-centre.** A width that shrinks around a centreline that drifts produces a thin vertical peg. The same feature described as two independent edges — one nearly straight, the other sweeping — produces a broad blade. Those are very different shapes from arithmetically similar tables, so take the *edges* from measurement and derive width/centre from them, not the reverse.
- **Check solidity, not just silhouette.** A part can match a reference's outline exactly and still carry half its mass, because a slab and a rounded teardrop project identically. Compare the model's solid fraction (`mesh.volume / bbox volume`) against the reference's front-projection fill (silhouette area / bbox area). A large gap means you have modelled the outline and not the volume — the cross-sections need depth variation, not another width tweak.

## Mesh pipelines

When the part is a mesh pipeline (a scan or a sculpt):
- **Name the boundary each new stage creates,** and how it blends: continuous
  in slope, not only in height.
- **Prefer one field operation over local vertex moves** (`top_cut()`, and
  r11's "lobe cut to the target surface U").
- **Measure the step at a lock's border** before adding the lock.
- **No stage that only repairs another stage's output** (`collapse_slivers`,
  `fix_degenerate`): fix the stage that made the defect.

## When a form mismatch persists, stop tweaking

If the whole-form gate fails twice on the same aspect, the model is structurally wrong and further constant-tuning will not fix it — that is precisely the loop that produced four bad VitaGrip revisions. Stop, re-measure the specific aspect that looks wrong, and say plainly what the measurement shows and what structural change it implies.

Trust measurement over your own reading of a render. Comparing renders once suggested a band needed to be *deeper*; sampling the photo's centre column showed it was already nearly 2× too deep, and that the missing mass was elsewhere entirely. Your visual impression of a render tells you *something* is off; only measurement tells you *what*.
