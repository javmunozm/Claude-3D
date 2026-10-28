# Build plan: <Project> r<NN> <short name>

<!-- Fill every <...>. A field you cannot fill is a question for the user. -->

- **Goal:** <one sentence: what changes and why; who approved it, when>
- **Read:** <STATE.md sections; register IDs; stage modules — by path>

## Questions before RUN
<fields the plan could not fill, and anything that contradicts STATE.md (e.g. uncommitted work it does not describe); "none". RUN starts only when this says none.>

## Arithmetic (done before any edit)
- Load path: <what bears on what>
- Clearances touched: <name: before → after, from the constants>
- Sizing check run: <command and result, or "none exists">

## Changes
| # | IDs | File / function | Constant or step: from → to | Expected effect (number) | Proved by (check, threshold) |
|---|-----|-----------------|-----------------------------|--------------------------|------------------------------|
| 1 | <D..> | <path:function> | <...> | <...> | <...> |

## Ceilings
- Builds: <4>   Images: <6>   Scratch scripts: 1
- Fallback: if a ceiling is reached, stop at the last state that passes the hard gates with rows 1–<k> done.

## Not touched
- Locks: <list, with tolerances>
- `stl/`, other rounds' folders

## Gates at the end
- <the five gates that apply, and the reference image for (e) or "no reference">

## Amendments
<none — at most one, written here before it is done: what, why, the number that forced it>
