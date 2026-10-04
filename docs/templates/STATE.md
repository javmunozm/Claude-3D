# <Project>: STATE

Updated: <date>, by <session / round>.

Keep this file under about 150 lines. Agents read it instead of the README. History, rejected approaches and narrative stay in the README.

## Current
- **Bake:** `stl/<file>` (SHA-256 `<...>`), copied from `audit/r<NN>/case_preview_r<NN>.stl`.
- **Working preview:** `<path>`.
- **Macro:** entry `macros/<main>.py`; stage package `macros/<pkg>/`.
- **Method:** <B-rep in build123d | mesh pipeline>, decided <date>. See the README section on it.

## Open entries
One line each.

| ID | Region (x, y, z) | Number vs threshold | Class | Status | Decision |
|----|------------------|---------------------|-------|--------|----------|

## Locks (must not move)
| Lock | Tolerance | Why |
|------|-----------|-----|

## Gates
- **Hard:**
  - watertight, 1 body, genus <n>;
  - walls ≥ <x> mm and back ≥ <x> mm, both on a grid of 0.5 mm or finer;
  - no sealed voids, no enclosed slits.
- **Surface bar,** agreed with the user on <date>:
  - the bar: <text>;
  - review cameras: <list>.

## Commands
- **Build:** `<cmd>` (about <s> s).
- **Gates:** `<cmd>`.
- **Sweep:** `<cmd>`.
- **Region render:** `python tools/render_roi.py <stl> <out.png> --center X Y Z --size 40`.

## Rounds
One line each.

| Round | Date | Agents (tool calls) | Peak context | List price | Result |
|-------|------|---------------------|--------------|------------|--------|

## Decisions pending for the user
- <...>
