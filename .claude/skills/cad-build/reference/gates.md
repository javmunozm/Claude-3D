# Arithmetic first, then the five gates

Moved verbatim from the cad-designer agent (2026-10-27).


### Before you build: run the arithmetic

On SurgicalDrillGuide (SurgicalDrillGuide, 2026-09-24) the build itself was cheap: macro and 11
exports 11 s, full gates 26 s, one render view 1.4-12.5 s. What cost time was
whole rounds. Round 4 (one designer run of 14 min, then a form audit and a
strength re-check) existed only because the round-3 handle had nothing to seat
against. The constants already said so: a Ø16 core cannot bear on a Ø16.85
mouth. The round-3 boss-pad taper conflict (0.175 into a 2.0 clearance) was
also plain arithmetic.

Before writing geometry for a change:

- **Write down the load path and every clearance the change touches, and do the
  arithmetic from the constants.** What does each part bear on? Which clearance
  shrinks? If `projects/<Project>/docs/mechanism_sizing.py` or a similar check exists, run it with
  the proposed constants first. It takes seconds.
- **Check each new solid with `is_valid` and a 2D section before any export,
  render or assembly gate.**

### 6. Verify before you claim done — all five gates

While iterating, run only the gates the change can affect: (a) regenerate, (b) topology, and (d) mating if an interface moved. Run **all five**, including the render in (c) and the comparison in (e), once before you report done. Do not report work complete until each has passed, and report what each one actually said. Do not render after every intermediate edit. In one build, 14 render runs took 15 minutes, and their 15 image reads stayed in context for every later call.

**(a) It regenerates.** Run the script with plain `python` and confirm `.step`/`.stl` are written without error. This is the *start* of verification, not the end.

Before any export, check every part: `is_valid` is True and it has exactly one
solid. Make the generate step refuse to export otherwise. **An invalid solid
does not always raise. It can hang the export.** The SurgicalDrillGuide handle
(its male thread started inside a core whose surface sat exactly on the crest
radius) hung the STL export for 81 minutes. Once valid, it exported in 0.7 s.

**Do not edit the script after the final export.** If you must, re-export and
re-run the gates. One round-4 run changed a line after exporting, and the
orchestrator had to rebuild and re-gate before anything could rely on the
files.

**(b) Topology gate.** Run the shared checker on every exported STL:

```
python tools/render_check.py projects/<Project>/stl/<Part>.stl
```

`body_count == 1` and `is_watertight` are hard gates — a part failing either is not printable, regardless of how correct its dimensions are. If a part is legitimately multi-piece, pass `--expect-bodies N` deliberately, never to silence a failure you don't understand.

**(c) Form render, actually looked at.** Render and then **read the image back** and describe what you see:

```
python tools/render_views.py projects/<Project>/stl/<Part>.stl --views front back
```

`render_check.py`'s own images are flat, unlit silhouettes: they show the outline and hide every cross-section and surface defect inside it. Judge form on the lit views of `render_views.py`.

Use `Read` on each PNG and state in your response what the render shows about the features you changed — spans that should be open are open, curves read as curves, nothing spans the middle that shouldn't. Never render wireframe; wireframe hides exactly the bugs this catches. Generating a render and not looking at it is worse than not rendering, because it produces false confidence.

**(d) Mating check, for any multi-piece or mating geometry.** When a part splits, plugs, or seats into anything, verify the interface **numerically** — do not eyeball it:

- Load both STLs and compare the actual Z (or mating-axis) bounds. The mating faces must coincide, and a tenon must land inside its pocket with the intended clearance.
- Confirm the assembled stack reaches the intended overall dimension.
- If one piece is already printed and you change the other, **the printed piece's real geometry is the constraint** — read its exported STL's actual bounds rather than trusting a constant in the script or a claim in the README. This is precisely the check that would have caught the 70 mm HeadLifter gap: the script said `split_z = 230`, the file on disk topped out at 160, and no one compared them.

**Derive every gate probe from the geometry, never from a fixed height.** The
SurgicalDrillGuide hook gate cast its rays at a fixed +0.55 mm. Once the pawl
overlap fell to 0.461 mm, the rays passed over the tooth and measured nothing.
Compute probe positions from the features they test, and give each gate a
control case it must fail.

**Measure a wall on a planar section, not on a filtered set of triangles.** A
"triangles within 15 mm of the hole" filter read a pin-hole wall as 3.114. The
section through the hole axis gave 2.553. See `docs/lessons.md`.

Never regenerate only one half of a split part. If you change a split, either re-export both halves or state explicitly, in your response and the README, which half on disk is now inconsistent and why.

**(e) Whole-form comparison against the reference — whenever a reference exists.** This is the gate that four VitaGrip revisions skipped.

```
python tools\render_check.py projects\<Project>\stl\<Part>.stl --views front --reference sources\<subject>\<photo>
```

Then `Read` the generated `_vs_reference.png` and answer, in your response, one question in plain words:

> **Is this the same object as the reference?**

Not "are the dimensions right." Not "did each feature I changed come out as intended." Is the **form** the same — overall proportion, how solid or skeletal it reads, where mass sits, whether shapes swell or taper in the same direction.

Rules for this gate:

- **The image is the evidence; the printed profile table is not.** That table measures each row's outer bounds, so a hollow frame and a solid body with the same outline score identically. On the known-bad VitaGrip part it showed near-perfect agreement while the images were obviously different objects. Never report the table as agreement.
- **Answer honestly and specifically.** "Looks close" is not an answer. If the reference is fat and solid and yours is thin and skeletal, say exactly that. A mismatch found here is a success of the process, not a failure of your work.
- **If it doesn't match, stop and say so** rather than proceeding to a fifth revision of local tweaks. Report the specific formal difference and, if the fix isn't obvious, re-measure the silhouette with the photo-to-vectors skill.
- When the reference shows a **different variant** of the target object (e.g. photos of a PCH-2000 grip while building for a PCH-1000), you are matching **shape language, proportion, and volume** — not copying absolute dimensions. Say which is which in your report, and take the absolute numbers from the spec, the photos' proportions from the photos.

7. **Sanity-check fit in reasoning too.** Beyond the numeric gates, reason explicitly about how the part mates with its neighbors/hardware (socket vs rod diameters, angles, overlap for clean boolean fuses). For load-bearing parts, flag that structural verification is needed and run the fdm-tolerance skill on the dimensions rather than asserting the part is strong enough yourself.
8. **Update the project README** (goal, dimensions table, file list, status) when geometry or dimensions change — READMEs must stay accurate per `docs/system.md`. When you change a dimension a structural check also uses, say so explicitly and re-run the fdm-tolerance skill to re-reconcile; a geometry change silently invalidates any check that hardcoded the old value.
