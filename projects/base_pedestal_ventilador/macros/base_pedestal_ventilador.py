"""base_pedestal_ventilador: a platform that lifts a fan's round base (Ø95 × 10) by 10 mm and doubles its footprint.
Disc Ø190 × 10 with a Ø80 through hole (the Ø80..Ø95 ring is the stop), socket ring Ø95 / Ø115 × 5 on top with a
1 mm lead-in chamfer, 12 radial slots 20 mm wide through the disc to save material.

Stages (package bpv_model/):
    bpv_model/constants.py        1  real-world values (user 2026-11-26)
    bpv_model/parameters.py       2/4 derived values + build-time arithmetic checks
    bpv_model/parts/platform.py   5  the part builder
    base_pedestal_ventilador.py   6  this file: build, validate, export. Holds no geometry.

Run:   python "D:\\Proyectos\\Claude-3D\\projects\\base_pedestal_ventilador\\macros\\base_pedestal_ventilador.py" --out <folder>
       (default <project>/work/preview; previews never go to stl/. --bake writes stl/ and step/.)
Gates: python "D:\\Proyectos\\Claude-3D\\projects\\base_pedestal_ventilador\\macros\\bpv_gates.py" <stl>

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

from bpv_model.parameters import derive  # noqa: E402
from bpv_model.parts.platform import build_platform  # noqa: E402

NAME = "base_pedestal_ventilador_platform"


def build():
    p = derive()
    part = build_platform(**p)
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
    print("derived: " + ", ".join(f"{k}={v:.3f}" for k, v in p.items()))
    bb = solid.bounding_box()
    dv = (solid.volume - p["volume"]) / p["volume"] * 100
    print(f"solid: valid={solid.is_valid} volume={solid.volume:.1f} mm3 (formula {p['volume']:.1f}, {dv:+.4f} %) "
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
