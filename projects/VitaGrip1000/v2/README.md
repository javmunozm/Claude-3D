# VitaGrip1000 v2 — hollow ergonomic shell

v0's verified geometry, **hollowed to a 3 mm shell**, with the ergonomic
features the blueprint set calls for: palm swell, finger-rest grooves and a
textile grip texture.

v2 does **not** re-derive the shape. Every measured profile, keep-out and
console-side gate is inherited from v0 unchanged. What changed is that the
part is now a shell instead of a 149 cm³ brick, and that its surfaces carry
the features the drawings label.

## Status

**Builds, fits, and passes every gate — including two v0 did not have.
Not yet test-printed.**

| Property | v0 | **v2** |
|----------|-----|--------|
| Volume | 149.0 cm³ | **77.7 cm³ — 48 % less** |
| Bounding box | 223.30 × 106.08 × 43.83 | 223.30 × 106.08 × 45.57 mm |
| Mesh | watertight, 1 body | watertight, **1 solid + 2 vented voids** |
| Wall thickness | solid | **3.02 mm median** (asked 3.0) |
| Sealed void | n/a | **0 mm³** |
| Slot depth | 19.320 mm | **19.320 mm** |
| Console fit | 0 / 200,000 | **0 / 200,000** |
| Palm swell | — | 2.149 mm (asked 2.20) |
| Finger grooves | — | 3 of 3 present, 0.9 mm cutter bite |
| Grip texture | — | 1.54× vertex density |
| Reinforcement ribs | — | **3 of 3 webs, 1.96 mm** (asked 2.0) |

Regenerate:

```
python projects\VitaGrip1000\v2\macros\vita_grip.py       # build + gates
python projects\VitaGrip1000\v2\macros\fit_check.py       # fit vs real console
python projects\VitaGrip1000\v2\macros\feature_audit.py   # v2's own features
python tools\render_check.py projects\VitaGrip1000\v2\stl\VitaGrip1000.stl --views back
```

## The 173 mm problem

Both blueprints added on 2026-09-02 annotate the grip at **173 mm** overall
and an "empty installation space" of **160 × 56 mm**.

Neither can be true. The console this shell holds is **182 × 83.55 mm**. A
grip 173 mm wide is narrower than the console it wraps, and a 160 × 56 mm void
cannot contain an 182 × 83.55 mm object.

The drawings also carry bracketed placeholders (`[25]mm`, `[50]mm`) and
truncated cotes (`93m`, `98m`, `I:56mm`) — the signature of concept art, not a
dimensioned CAD set.

**So the blueprints are used for FEATURES and SHAPE, never for dimensions.**
Every dimension still comes from the photograph and the real console mesh.
v0 had already reached the same conclusion independently when it took the
lateral view's silhouette but rejected its cotes.

One number is taken from them: **WALL = 3 mm TYP**, which both drawings agree
on and which matches the value v0 had already chosen independently as a
standard moulded wall for this size.

### What the blueprints legitimately contributed

| Feature | Drawing | How it was built |
|---------|---------|------------------|
| Hollow shell, 3 mm wall | both | inner loft, every section inset by `SHELL_WALL` |
| Ergonomic palm swell | `lateralHAndleview.jpg` | raised cosine on the depth profile, f 0.30–0.62 |
| Finger rest grooves (radiused) | `lateralHAndleview.jpg` | 3 lofted scallops on the front face |
| Textile grip texture | `vistaFrontal.png` | ±45° cross-hatch, 3.2 mm pitch |
| Internal reinforcement ribs | both ("Conceptual") | 3 transverse webs cut **out of the void** |
| Handle rake ~20° | `vistaFrontal.png` | **confirmation only** — the built handle already measured 22.6° from the photo mask |

That last row is the useful one: the drawing's 20° and the photograph's
22.6° are two independent routes to the same number. The drawings are wrong
about scale, not about shape.

## Three defects the gates caught, all of which built cleanly

### 1. The hollow merged with the console pocket

The handles overlap the console in plan by ~34 mm — they reach inboard to
|X| 57.3 against the console's edge at 91.0, clearing it by passing *behind*.
So a full-depth inner void ran forward to Z +8.65 while the slot floor is at
Z −9.65: **the cavity broke through the pocket's rear wall and the two became
one cavern.** The slot gate measured **33.22 mm** against the 19.30 required —
14.6 mm of slop.

The first fix clamped every void to stay behind the slot floor. It worked, and
it cost most of the point: the clamp fired at *every* station, leaving an 8 mm
void inside a 20 mm handle. **24 % saved instead of 54 %.**

The overlap is only in X. So the hollow is taken at full depth and the wall is
**put back** afterwards as a slab over the console's footprint
(`build_pocket_wall`), restricted to the outboard band where a handle actually
sits. The pocket cut then trims its front face to the exact slot depth.

Spanning the console's *whole* footprint was the intermediate error: it laid
material across the shoulder-button zone (**12 vertices**, caught by the
keep-out gate), grew the Y extent 106.08 → 122.48 mm, and left a slab floating
clear of both handles — **2 bodies**.

### 2. The vent silently returned nothing, and the cavity was sealed

`build_vent` sized the opening from the **lowest** surviving inner station —
where the shell has nearly closed, 7.71 × 2.59 mm. Inset by `VENT_INSET = 2.0`
that leaves a half-depth of **0.59 mm**, which tripped a `> 0.6` guard and
returned `[]`.

**No vent. A sealed cavity.** And a sealed cavity is invisible to everything
this project measures: it is watertight, it is one body, the bounding box is
unchanged, and the reported volume is exactly the saving the hollowing was
meant to deliver. Then the slicer fills it, because a void with no path out is
indistinguishable from solid to a slicer that fills by ray parity.

The only reason it did not ship that way is that a *different* gate failed
first and this one never ran.

Fixed three ways: size the vent on the widest of the lowest few stations, fall
back to a proportional inset, and **raise** rather than return empty. A
`check_cavity_open()` gate now voxelises the export and flood-fills from
outside; any unreachable void over 500 mm³ fails the build. It reports
**0 mm³**.

### 3. The slot gate measured the hollow instead of the slot

v0's slot probe took the **largest** enclosed gap along each ray. That was
safe only while the part was solid — the slot was then the only enclosed void
on the ray.

v2 is hollow, so every ray through a handle crosses the shell cavity too, and
at y = −26.8 that cavity is the larger of the two. The gate reported
**14.16 mm** and failed a build whose slot was in fact exactly right.

The slot is now identified **by position, not by size**: it is the void
straddling Z = 0, where the console is centred by construction. Verified that
this still catches v0's original 21.30 mm over-deep slot, which also straddles
Z = 0 and still reports 21.30 → still fails.

## An audit that lied about its own measurement

`feature_audit.py` first measured the palm swell by comparing the handle's
rear reach at the swell's peak against its reach just outside the band, and
reported **"swell built 27.89 mm (asked 2.20)"**.

Nonsense — the handle's own depth varies by tens of millimetres along its
length, and the comparison was reading that variation, not the swell. A delta
has to be measured as a delta: the same sections built with `SWELL_AMT` on and
off. **2.149 mm against 2.20 asked.**

The groove check has a known, documented limitation in the other direction: it
samples the deepest vertex in a ±1.2 mm band, which straddles the scallop's
sloped walls as well as its floor, so it reads ~0.25 mm on a groove whose
cutter is placed to remove 0.9 mm (verified against the cutter geometry
directly). It is a **presence** check, not a depth check.

## The ribs

Both drawings show "Internal Reinforcement Ribs (Conceptual)" and neither
dimensions them — they are drawn, not specified. So their size and spacing are
a design choice, flagged as assumed below.

They are not decoration. Hollowing turned each handle into a **tube**, and a
tube squeezed by a hand fails by **ovalisation** — the section flattens long
before the material yields. The webs run **transverse** (normal to the
handle's long axis), which is the direction that resists that. A rib running
*along* the handle would stiffen it in bending, which is not the load here.

They are **subtracted from the inner void**, not added to the part. What is
removed from the void survives as solid material bridging the cavity, already
trimmed to the wall on every side. Adding rib solids to the part instead would
need them hand-trimmed to the cavity, and any overshoot would poke through the
outer surface.

Cost: 68.1 → 77.7 cm³. Still **48 % below** the solid v0.

### The fourth rib could not exist, and the audit is what noticed

`RIB_N` was 4, spanning f 0.22–0.60. Three webs appeared in the export and the
fourth did not — the audit reported **"webs found: 3 / 4"**.

It had built cleanly, then vanished: at f = 0.60 (y = −17.34) the cavity's
centre sits at Z = −6.93, which is **above the console pocket floor at
−9.65**, so the console cut and the pocket wall consume it. The console has to
win there — that region *is* the pocket.

The honest fix is to stop the rib band below it (`RIB_F1` 0.60 → 0.48, three
webs) rather than keep asking for a web that cannot exist. Nothing but the
audit would have caught it: the part built, was watertight, was one solid, and
had a plausible volume with the rib silently missing.

## A shared tool reported a false alarm

`tools/render_check.py` failed this part with **"body_count 3 (expected 1) →
part is not a single connected solid, not printable as one piece."**

That was wrong, and wrong in the dangerous direction. `mesh.body_count` counts
**surface components**, and a hollow part has one per cavity in addition to
its outer surface. v2 is a single solid with two handle cavities.

Cavity surfaces face inward, so they carry **negative signed volume** — which
is exactly how they are told apart from genuinely disjoint solids. The gate
now splits the count and reports `1 (expected 1) + 2 internal voids`.

Verified against both controls before trusting it: two disjoint cubes still
**FAIL** (2 solids, 0 voids), a cube with an internal void now **PASSES**
(1 solid, 1 void), and solid v0 is unaffected with no spurious void line.

Proving a cavity is *reachable* remains the flood-fill gate's job, not this
one's.

## Assumed — revise after a test print

Everything v0 flagged still applies (`FRONT_LIP`, `LIP_X`, `SLIM`, `TIP_FLAT`,
`CHAMFER`, `FIT_CLEAR`), plus:

| Dimension | Value | Why it is assumed |
|-----------|-------|-------------------|
| `SHELL_WALL` | 3.0 mm | the blueprints' one credible number; not verified in the hand |
| `VENT_INSET` | 2.0 mm | enough to leave a rim; not derived |
| `SWELL_AMT` | 2.2 mm | a comfort choice read off a concept drawing |
| `GROOVE_*` | 3 × 0.9 mm deep | positions eyeballed from the lateral view |
| `RIB_N` / `RIB_T` | 3 webs, 2.0 mm | the drawings show ribs but dimension none; spacing not derived |
| `TEX_PITCH` | 3.2 mm | **deliberately coarse.** A real textile pitch is under 1 mm; through a 0.4 mm nozzle that is not a texture, it is a rough surface with the grooves bridged over |

## Before printing

- **A 3 mm shell is a structural change, not just a saving.** The handles now
  carry load as tubes, with three transverse ribs each resisting ovalisation.
  **No FEA was run.** The ribs are sized by judgement, not by analysis — that
  they exist and are 1.96 mm thick is measured; that they are *enough* is not.
- Test-fit against a real PCH-1000 before trusting `FIT_CLEAR`.
- Print orientation: handles vertical, bar flat on the bed. The vent opening at
  each handle tip doubles as a drain for support material.
- The vent is a **visible hole** at each handle tip. If that is unwanted, the
  alternative is a sacrificial cap printed separately — not a sealed cavity.
