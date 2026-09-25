# Discarding attempts

A rejected attempt leaves two things behind: files nobody will slice, and a
lesson worth keeping. Separate them.

## Where work-in-progress lives

**Work that is not the current shipping artifact goes in
`projects/<Project>/attempts/<slug>/`** — superseded exports, probe scripts,
parameter sweeps, a geometry approach under evaluation. Never the project root.

`attempts/` is gitignored (`.gitignore` covers both `projects/*/attempts/` and
the nested `projects/*/*/attempts/`); nothing in it is committed.

## Never delete on your own judgment

**Only an explicit rejection from the user triggers cleanup.** An attempt that
merely looks stale, failed a gate, or has been superseded stays until the user
says so. A rejection is also not permission to delete *neighbouring* attempts.

## The rejection procedure

When the user rejects an attempt, delete it in the same turn — but record the
lesson first, in this order:

1. **Append one row to the project README's "Rejected approaches" table**: the
   slug, what was tried, and the measured reason it failed. A number, not
   "didn't look right".

2. **Check nothing depends on it:**

   ```
   grep -rn "<slug>" projects/ tools/ docs/
   ```

   BrokeFeet's v2 imports from `v0/macros/`; the same trap applies to any
   attempt another script quietly reaches into.

3. **Delete `attempts/<slug>/`.**

## The lesson outlives the bytes

`projects/VitaGrip-hori/README.md` ("Rejected approaches") keeps its rejected
attempts as rows, with no folders left behind. Its `parametric-clamshell` row
is the target state: 172.8 cm³ against the real part's 47.1, median wall 6.20
against 2.13 mm, genus 2 against 48. The record of a *measured* negative
result is what stops a future session re-walking work already quantified. Its
`parametric-handle` row is the counter-example: "did not match the reference
photos" gives no number, so it cannot stop anyone.

See [versioning.md](versioning.md) for the related rule on retiring a whole
version rather than a single attempt.
