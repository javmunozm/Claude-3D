# Sizing plan: <Project> <short name>

<!-- Fill every <...>. A field you cannot fill is a question for the user. -->

- **Question:** <one sentence>   **Verdict it produces:** <PASS/FAIL per check | a clearance value>
- **Read:** <STATE.md sections, check script, README conventions>

## Questions before RUN
<fields the plan could not fill; contradictions with STATE.md; "none". RUN starts only when this says none.>

## Load cases
| Load | Value | Path (what bears on what) | Worst case |
|------|-------|---------------------------|------------|

## Inputs to reconcile
| Label | Value used | Name in geometry module | Direction |
|-------|-----------|--------------------------|-----------|

## Allowables
- Material: <...>   Strength: <MPa, source>   Safety factor: <...>   Anisotropy: <assumption>
- Stress concentrations: <where; Kt applied or not>

## Clearance (if any)
- Fit type: <press / slip / loose>   Printer class: <...>   Face orientation: <...>
- Input confidence: <Specified / Measured / ...>   Confirmed by: <coupon or measurement>

## What a change touches
<constant → parameters → parts that rebuild>

## Amendments
<none — at most one, written here before it is done>
