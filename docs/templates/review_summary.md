<!-- Summary block: at most 30 lines. It is the first thing in every register and every review.
     The orchestrator reads this block, not the whole file. -->
## Summary

- **Verdict:** <FORM MATCHES INTENT | ACCEPT WITH LISTED ARTIFACTS | DEFECTS FOUND | METHOD REVIEW | CANNOT ESTABLISH ORIENTATION>
- **What the geometry physically is now,** one sentence per changed region:
  - <region>: <sentence>
- **Open entries:** <ID: number vs threshold>; ...
- **Fixed:** <IDs>. **Worse:** <IDs>.
- **New regressions from the last pass:** <count> (<IDs>).
- **Method-change trigger:** <met / not met>. Met means 3 or more regressions, or a region in its third consecutive register.
- **User marks:** <n> in total:
  - geometry <a>;
  - designed edge not rounded <b>;
  - tessellation / shading <c>;
  - not reproducible <d>.
- **Unswept:** <regions, or "none">.
- **This run:** <tool calls> tool calls, peak context <k>, list price $<x>.
- **Decision needed from the user:** <...>
