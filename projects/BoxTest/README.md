# BoxTest

Hollow open-top box with rounded edges, from hand-drawn sketches.

## Dimensions

| Parameter | Value |
|-----------|-------|
| Width (X) | 150 mm |
| Length (Y) | 200 mm |
| Height (Z) | 150 mm |
| Wall thickness | 5 mm |
| Fillet radius | 2 mm |

## Files

| File | Purpose |
|------|---------|
| `macros/box_test.py` | build123d geometry script. Run: `python "D:\CAD\Claude-Projects\projects\BoxTest\macros\box_test.py"`. Exports only when run, not on import |
| `step/BoxTest.step` | STEP export |
| `stl/BoxTest.stl` | STL export |
| `renders/BoxTest_*.png` | `render_check.py` renders (flat, unlit: they do not show the open top) |

Sketches: `sources/boxTest/`.

## Status

Generated. Open top, 5 mm walls, all edges filleted at 2 mm.

**Fix 2026-09-25:**
- **Export now runs only under `__main__`.** Before, importing the file overwrote the exports. The unused `FILLET_OUTER = 6.0` is removed; every fillet was always 2.0. The geometry is unchanged: the STEP is byte-identical, header excluded.
- **The STL is now watertight.** OCC's tessellator left one zero-area triangle at each of the 12 corner blends (8 outer corners, 4 at the inner floor), at every tolerance tried (0.001 to 0.1 mm). The STL failed `is_watertight` because of them. The macro now exports the raw mesh to a temporary file and drops those triangles. It writes `stl/BoxTest.stl` only if the cleaned mesh is watertight; otherwise it stops and leaves the old file in place. That refusal path has not been exercised, because the current mesh passes.
- **`render_check`:** all gates PASS. 1 body, watertight, bounding box 150.0 × 200.0 × 150.0, volume 641.79 cm³, unchanged by the cleanup.
