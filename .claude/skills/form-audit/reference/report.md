# Report format and verdicts

Moved from the form-auditor agent (2026-10-27).


## Reporting format

**Start the deliverable with the summary block** from
`docs/templates/review_summary.md`: at most 30 lines, with the verdict, one plain
sentence per changed region, the open entries, fixed and worse IDs, new
regressions, the user marks by class, the unswept regions, this run's cost and
the decision needed. Write it with your first result and keep it current as you
go. The user reads this block, not the whole file, and if the session stops
early the block is what survives.

```
## Form Audit: <Part>

<the summary block, docs/templates/review_summary.md>

**Axis convention**: X = <what>, Y = <what>, Z = <what>  (derived from <dimension>)
**Overall extent**: <x> x <y> x <z> mm

### <Feature> cross-sections
| position | width | depth | w/d | note |
|----------|-------|-------|-----|------|
| root     | 40.3  | 35.3  | 1.14|      |
| tip      | 29.3  | 23.2  | 1.26| flat cap — full section at final slab |

**Intended** (from macro constants): W_ROOT=40 → W_TIP=28, D_ROOT=32 → D_TIP=24
**Built**: matches within 1 mm at root; tip 1.3 mm over

### Sweep
Regions swept: <list>. Thresholds: <turn deg, bump mm, tooth mm, wall mm>.
Unswept: <regions, and why — or "none">

### Defect register
| ID | Region / location | Measurement | Source | Cause | Proposed fix | Interacts with | Status |
|----|-------------------|-------------|--------|-------|--------------|----------------|--------|
| D1 | lobe back R, x 64-82, y 52-54 | turn 24-32 deg (thr 8) | sweep | measured: zone edge Y 52 | cut outside zone, ease 0.5 mm | D2 | open |

Status is `open` on a first audit. In review mode it is fixed / improved /
unchanged / worse, with the before and after numbers.

### Fix proposal
One paragraph per cause group: which IDs it closes, what changes in the
macro, and any conflict that needs a decision.

### Not defects
- <thing that looked wrong in a render, or a user mark, that measured correct — with its number>

### Verdict: [FORM MATCHES INTENT / ACCEPT WITH LISTED ARTIFACTS / DEFECTS FOUND / METHOD REVIEW / CANNOT ESTABLISH ORIENTATION]
```

FORM MATCHES INTENT requires no open entries and no unswept regions. ACCEPT
WITH LISTED ARTIFACTS means nothing blocks a bake and every open entry is
listed with its size against the layer and the nozzle.

**METHOD REVIEW** overrides the others when the method-change trigger is met:
the fix pass created 3 or more regression IDs, or a region is in its third
consecutive register. Say which condition, with the IDs. The next step is then
a method decision for the user, not another fix pass (`docs/agents.md`, "Fix
rounds").

Paste-ready tables only for open entries. Fixed and carried entries get one
line each.

The **"Not defects"** section is mandatory when you were asked to check something
that turned out fine. Silently omitting it invites a rebuild of correct geometry.
