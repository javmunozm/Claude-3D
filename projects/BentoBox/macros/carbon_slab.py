"""Build the perforated carbon slab and export STEP + STL.

Run: python projects\\BentoBox\\macros\\carbon_slab.py
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build123d import export_step, export_stl  # noqa: E402

from build123d import import_step  # noqa: E402

from bento_model.carbon_slab import build  # noqa: E402
from bento_model.constants import SLAB_SRC, SLAB_Y, SLAB_Z  # noqa: E402


def original_volume():
    return import_step(str(SLAB_SRC)).solids()[0].volume
from bento_model.constants import PELLET_D, WINDOW_Y, WINDOW_Z  # noqa: E402
from bento_model.parameters import HOLE_FLAT, WEB  # noqa: E402

PROJECT = Path(__file__).resolve().parents[1]


def main():
    part, centres = build()
    solids = part.solids()
    assert len(solids) == 1, f"expected 1 solid, got {len(solids)}"
    solid = solids[0]
    assert solid.is_valid, "result is not a valid solid"
    assert HOLE_FLAT < PELLET_D
    # holes must actually remove material: every hex is a full through-cut
    t = 1.4
    removed = original_volume() - solid.volume
    expected = len(centres) * math.sqrt(3) / 2 * HOLE_FLAT ** 2 * t
    print(f"removed {removed:.1f} mm3, expected {expected:.1f} mm3")
    assert abs(removed - expected) < 0.01 * expected, "holes did not cut as expected"

    hex_area = math.sqrt(3) / 2 * HOLE_FLAT ** 2
    window_area = (WINDOW_Y[1] - WINDOW_Y[0]) * (WINDOW_Z[1] - WINDOW_Z[0])
    print(f"holes: {len(centres)}  hex flat {HOLE_FLAT} mm  web {WEB} mm")
    print(f"open area: {len(centres) * hex_area:.0f} mm2 of window {window_area:.0f} mm2 "
          f"({100 * len(centres) * hex_area / window_area:.1f} %)")
    ys = [y for y, _ in centres]
    zs = [z for _, z in centres]
    hy, hz = HOLE_FLAT / 2, HOLE_FLAT / math.sqrt(3)
    print(f"hole extents Y {min(ys) - hy:.2f}..{max(ys) + hy:.2f} (window {WINDOW_Y}), "
          f"Z {min(zs) - hz:.2f}..{max(zs) + hz:.2f} (window {WINDOW_Z})")
    print(f"solid border to slab edge: Y {min(ys) - hy - SLAB_Y[0]:.2f} / {SLAB_Y[1] - max(ys) - hy:.2f}, "
          f"Z {min(zs) - hz - SLAB_Z[0]:.2f} / {SLAB_Z[1] - max(zs) - hz:.2f}")
    bb = solid.bounding_box()
    print(f"volume {solid.volume:.1f} mm3  bbox ({bb.size.X:.2f}, {bb.size.Y:.2f}, {bb.size.Z:.2f})")

    (PROJECT / "step").mkdir(exist_ok=True)
    (PROJECT / "stl").mkdir(exist_ok=True)
    solid.label = "carbon_slab_perforated"
    export_step(solid, str(PROJECT / "step" / "carbon_slab_perforated.step"))
    export_stl(solid, str(PROJECT / "stl" / "carbon_slab_perforated.stl"),
               tolerance=0.01, angular_tolerance=0.1)
    print("wrote step/carbon_slab_perforated.step and stl/carbon_slab_perforated.stl")


if __name__ == "__main__":
    main()
