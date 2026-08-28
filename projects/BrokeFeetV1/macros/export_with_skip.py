"""Re-export the patched grid with an extra SKIP_PILLAR_REGIONS_MM entry.

THE FRAME TRAP (BrokeFeet README, "The pillar under the 5th toe tip"):
SKIP_PILLAR_REGIONS_MM coordinates are in the SCAN'S OWN FRAME, i.e. BEFORE
MIRROR_X, because _support_islands() runs inside _bridge_bodies() and
main() mirrors only the finished mesh. The builder's own island pass runs in a
different frame and deliberately passes no skip regions.

Verified here rather than assumed: the crater sits at mesh X = -114.8, and the
pillar that appears over it is reported at X = +111.8. The sign flip IS the
mirror, so the printed pillar coordinates are pre-mirror and can be used
directly -- the same convention as the existing (135.2, -57.8, 3.0) entry.

The monkey-patch is scoped to this process. BrokeFeet/macros/segment_axial.py
is never written to; BrokeFeet/ is the shipping model.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
WORK = HERE.parent / "work"
OUT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / "BrokeFeet" / "macros"))

import segment_axial as v0  # noqa: E402
import export_from_iso as E  # noqa: E402

# The pillar the crater patch creates, in the scan's own frame (pre-mirror).
# Radius 3.0 mm matches the existing entry's convention; the nearest other
# pillar is at (102.8, -156.8), 31 mm away, so 3 mm is not delicate.
NEW_SKIP = (111.8, -126.2, 3.0)


def main():
    src = WORK / sys.argv[1]
    name = sys.argv[2]
    v0.SKIP_PILLAR_REGIONS_MM = v0.SKIP_PILLAR_REGIONS_MM + (NEW_SKIP,)
    print(f"SKIP_PILLAR_REGIONS_MM = {v0.SKIP_PILLAR_REGIONS_MM}")

    iso = np.load(src)
    print(f"{src.name}: {iso.sum() * v0.ISO_VOXEL_MM ** 3 / 1000:.3f} cm3 "
          f"tunnels {v0._tunnel_count(iso)} bones {v0._real_bone_count(iso)}")
    print(f"bodies before bridging: {E.bodies_before_bridging(iso)}")
    mesh = E.mesh_from_iso(iso)
    g = int(round((2 - mesh.euler_number) / 2))
    print(f"  mesh vol {mesh.volume / 1000:.2f} cm3 watertight="
          f"{mesh.is_watertight} bodies={mesh.body_count} genus={g} "
          f"area/volume={mesh.area / mesh.volume:.3f}")
    p = OUT / name
    mesh.export(p)
    print(f"wrote {p}")


if __name__ == "__main__":
    main()
