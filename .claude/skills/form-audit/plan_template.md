# Audit plan: <Project> r<NN> <QUESTION | REGISTER | REVIEW>

<!-- Fill every <...>. A field you cannot fill is a question for the user. -->

- **Mesh:** <path>   **Baseline (REVIEW):** <sweep_rMM.json named in STATE.md>
- **Axis convention:** derive from <known dimension → expected extent per axis>

## Questions before RUN
<fields the plan could not fill, and anything that contradicts STATE.md; "none". RUN starts only when this says none.>

## Questions and marks
| # | Source (plan / user mark <file> / entry D..) | Where (region, coords or section plane) | Measurement | Intended value (constant) | Threshold |
|---|------|-------|-------------|----------------|-----------|
| 1 | <...> | <...> | <...> | <...> | <...> |

## Sweep (REGISTER, REVIEW)
- Command: `python tools/form_sweep.py <mesh> --regions projects/<Project>/audit/regions.json --out audit/r<NN>/sweep --tag r<NN> [--baseline <...>]`
- Thresholds: turn <deg>, bump <mm>, tooth <mm>, wall <mm>
- Unswept, known now: <regions and why, or "none">

## Extra checks (at most 3, functions in one scratch script)
1. <name: what, where>

## Ceilings
- Builds: <0 | 1>   Images: <2 | 4 | 3>   Scratch scripts: 1

## Deliverable and done-when
- File: `audit/r<NN>/<question|register|review>.md`
- Done when: rows <...> each have a number (or "not measured" with the reason).

## Amendments
<none — at most one, written here before it is run: what, why, the number that forced it>
