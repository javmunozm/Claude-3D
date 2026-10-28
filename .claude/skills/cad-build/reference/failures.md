# Why the gates exist

Moved verbatim from the cad-designer agent (2026-10-27).


## The core failure mode in this work

Geometry code that runs without error, and exports files without error, can still produce a part that is **physically wrong** — and every historical defect in this repo is of exactly that kind:

- A part built as a solid slab spanning 97% of a width that was supposed to be open. Bounding box: correct. Wireframe view: looked fine. Only a *shaded* render revealed it.
- A part exported as **two disconnected bodies** — unprintable as one piece — while every dimension in it was right.
- A split part whose two halves were regenerated against **different split planes**, leaving a 70 mm gap. Both files exported cleanly. Nobody checked that they mate.
- A grip modeled from reference photos across **four revisions** that ended up looking nothing like them — a thin flat bracket where the reference is a fat controller grip, with handle horns that *taper to a 13 mm point* where the reference horns *swell to a ~53 mm teardrop*. **The taper ran backwards.** Every revision verified a local property (is the span open? is it one body? is the band thick?) and every one passed.

"It built without error" is not evidence of anything. Neither is "each feature I checked was correct." Your job is to verify the *shape*, the *fit*, and — when there is a reference — the *whole form*.

## The trap: local checks that all pass on a wrong part

The four-revision failure above is the one to internalize, because every individual step looked like diligence. The pattern:

> Change a feature → verify *that feature* in isolation → it passes → declare progress.

Repeat, and you converge on a part where every checked property is right and the object is still wrong. Correctness of parts does not compose into correctness of the whole. A checklist of local properties is not a substitute for looking at the thing you built and asking whether it is the object you were asked for.

So: whenever a reference exists, the **last** gate is always whole-form comparison against it — never a checklist item, never delegated to a metric.

## Writing about physical state

Never write a README claim about the physical world you have not verified — "already printed", "unchanged", "test-fitted", "confirmed". A stale claim of exactly this kind ("the lower half is already printed and unchanged") hid a 70 mm assembly gap for two revisions, because each later reader inherited it as fact.

Write what you verified and how: "STL on disk spans z = 0–160, consistent with a split at 150." If a claim comes from the user, attribute it: "user reports the lower half was printed at split z = 150." If you cannot verify it, put it in the README's verification checklist as an open item rather than in the body as a fact.
