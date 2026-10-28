# Mesh plan: <Project> <REPAIR | BLENDER prep | BLENDER import> <short name>

<!-- Fill every <...>. A field you cannot fill is a question for the user. -->

- **Mesh:** <path, how it was made>   **Goal:** <one sentence>
- **Read:** <README rejected approaches — what they rule out>

## Questions before RUN
<fields the plan could not fill; contradictions with the README or STATE.md; "none". RUN starts only when this says none.>

## Baseline (measured now)
| watertight | bodies | genus | volume | open edges | bodies before bridging |
|---|---|---|---|---|---|

Per band (area/volume): <Z ranges and values>

## Defects
| # | Where (bone / region, coords) | Class (tunnel / crater / terracing / sponge / REAL) | Number that decides it | Action |
|---|------|------|------|------|

## Operation
- Method: <...>, applied to: <regions>   Not used, and why: <rejected methods>

## Predicted cost
- Joints at risk: <...>   Expected after: bodies <..>, genus <..>, volume <..>

## Gates (in order, with thresholds)
1. watertight, bodies == <1>
2. genus and volume together (falling genus + rising volume = fusion → FAIL)
3. bodies before bridging ≥ <baseline>
4. per-band area/volume
5. <cross-validation / inward-travel ≤ 0.5 mm / raw-triangle diff>
6. region renders looked at

## BLENDER (if any)
- Transform: recentre only, 1 unit = 1 mm, `TRANSFORM.json`   Dyntopo detail: <mm>   X-symmetry: off
- Sculptor: touch <...>; do not touch <...>; expected topology when done: <...>

## Amendments
<none — at most one, written here before it is done>
