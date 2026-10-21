"""Export STLs of the BentoBox frame and the carbon cartridge.

One STL per piece, kept in the original assembly coordinates, plus one
combined STL of the assembled frame (preview only, not for printing).
Test pieces (male_test, female_test) and Body1 are not exported.

Run: python projects\\BentoBox\\macros\\export_parts.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import trimesh  # noqa: E402
from build123d import export_stl, import_step  # noqa: E402

from bento_model.constants import SRC_PARTS  # noqa: E402

PROJECT = Path(__file__).resolve().parents[1]

# Frame stack, bottom to top along Z in the source assembly.
FRAME = ["exhaust_base", "fan_case", "carbon", "hepa", "cover_voronoi"]
CARTRIDGE = ["CMag_1", "CMag_2"]


def write_stl(shape, path, expect_bodies):
    """Export, then drop the zero-area sliver triangles OCC's tessellator
    leaves along some edges (the B-rep itself has no free edges). Asserts the
    result is watertight with the expected body count and unchanged volume."""
    export_stl(shape, str(path), tolerance=0.01, angular_tolerance=0.1)
    m = trimesh.load(str(path))
    n0, v0 = len(m.faces), m.volume
    m.update_faces(m.nondegenerate_faces(height=1e-9))
    m.remove_unreferenced_vertices()
    bodies = len(m.split(only_watertight=False))
    assert m.is_watertight, f"{path.name}: not watertight after removing slivers"
    assert bodies == expect_bodies, f"{path.name}: {bodies} bodies"
    assert abs(m.volume - v0) < 1e-6 * abs(v0), f"{path.name}: volume changed"
    m.export(str(path))
    return n0 - len(m.faces)


def main():
    out = PROJECT / "stl"
    out.mkdir(exist_ok=True)
    for name in FRAME + CARTRIDGE:
        solids = import_step(str(SRC_PARTS / f"{name}.step")).solids()
        assert len(solids) == 1, f"{name}: {len(solids)} solids"
        s = solids[0]
        assert s.is_valid, f"{name} is not a valid solid"
        dropped = write_stl(s, out / f"{name}.stl", 1)
        bb = s.bounding_box()
        print(f"{name:14s} vol {s.volume:10.1f} mm3  size ({bb.size.X:.1f}, {bb.size.Y:.1f}, {bb.size.Z:.1f})"
              f"  slivers dropped {dropped}")
    # Preview only: the pieces nest at their joints, so one merged mesh has
    # shared edges there. Concatenate the checked piece meshes unmerged.
    meshes = [trimesh.load(str(out / f"{n}.stl")) for n in FRAME]
    trimesh.util.concatenate(meshes).export(str(out / "frame_assembly.stl"))
    print("frame_assembly  = concatenation of", ", ".join(FRAME))
    print("wrote", len(FRAME) + len(CARTRIDGE), "part STLs + frame_assembly.stl to", out)


if __name__ == "__main__":
    main()
