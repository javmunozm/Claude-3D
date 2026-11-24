"""DeodorantBoxTop: cover for a 3 x 4 deodorant box. 200 x 210 x 4 mm plate, 12 elliptical holes 46.5 x 44.5,
four blind triangular sockets underneath for the base's corner pillars.

Stages (package dbt_model/):
    dbt_model/constants.py     1  real-world values (all from the user, 2026-11-24)
    dbt_model/parameters.py    2/4 derived values + build-time arithmetic checks
    dbt_model/parts/cover.py   5  the part builder
    deodorant_box_top.py       6  this file: build, validate, export. Holds no geometry.

Run:   python "D:\\Proyectos\\Claude-3D\\projects\\DeodorantBoxTop\\macros\\deodorant_box_top.py" --out <folder>
       (default <project>/work/preview; previews never go to stl/. --bake writes stl/ and step/.)
Gates: python "D:\\Proyectos\\Claude-3D\\projects\\DeodorantBoxTop\\macros\\dbt_gates.py" <stl>

No stage cache: one part, builds in seconds.
"""

import argparse
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
sys.path.insert(0, str(HERE))

from build123d import export_step, export_stl  # noqa: E402

from dbt_model.parameters import derive  # noqa: E402
from dbt_model.parts.cover import build_cover  # noqa: E402

NAME = "DeodorantBoxTop_cover"


def _fmt(v):
    if isinstance(v, list):
        return "[" + ", ".join(f"{x:.3f}" for x in v) + "]"
    return f"{v:.3f}"


def build():
    p = derive()
    part = build_cover(**p)
    solids = part.solids()
    if len(solids) != 1 or not solids[0].is_valid:
        raise RuntimeError(f"refusing to export: {len(solids)} solid(s), valid={[s.is_valid for s in solids]}")
    return p, solids[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(PROJECT / "work" / "preview"))
    ap.add_argument("--bake", action="store_true", help="write stl/ and step/ instead of --out")
    a = ap.parse_args()

    t0 = time.time()
    p, solid = build()
    print("derived: " + ", ".join(f"{k}={_fmt(v)}" for k, v in p.items()))
    bb = solid.bounding_box()
    print(f"solid: valid={solid.is_valid} volume={solid.volume:.1f} mm3 "
          f"bbox=({bb.min.X:.3f},{bb.min.Y:.3f},{bb.min.Z:.3f})..({bb.max.X:.3f},{bb.max.Y:.3f},{bb.max.Z:.3f})")

    if a.bake:
        stl_dir, step_dir = PROJECT / "stl", PROJECT / "step"
    else:
        stl_dir = step_dir = Path(a.out)
    stl_dir.mkdir(parents=True, exist_ok=True)
    step_dir.mkdir(parents=True, exist_ok=True)
    export_stl(solid, str(stl_dir / f"{NAME}.stl"), tolerance=0.01, angular_tolerance=0.1)
    export_step(solid, str(step_dir / f"{NAME}.step"))
    print(f"written: {stl_dir / (NAME + '.stl')} and .step  ({time.time() - t0:.1f} s)")


if __name__ == "__main__":
    main()
