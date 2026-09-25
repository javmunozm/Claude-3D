"""BoxTest - hollow open-top box with rounded edges.

A rectangular box from hand-drawn sketches in sources/boxTest/.
5 mm walls, all edges filleted, top face open.

Dimensions (mm):
  outer width   150.0  (X)
  outer length  200.0  (Y)
  outer height  150.0  (Z)
  wall          5.0
  fillet        2.0   (every edge, inside and out)

Origin at the centre of the bounding box.

Run: python "D:\\CAD\\Claude-Projects\\projects\\BoxTest\\macros\\box_test.py"
Exports to ../stl/ and ../step/ only when run, never on import.
"""

from pathlib import Path

from build123d import (
    Box,
    BuildPart,
    Location,
    Locations,
    Mode,
    export_step,
    export_stl,
    fillet,
)

PROJECT_DIR = Path(__file__).resolve().parent.parent

WIDTH = 150.0
LENGTH = 200.0
HEIGHT = 150.0
WALL = 5.0
FILLET_R = 2.0


def build_box(width, length, height, wall, fillet_r):
    with BuildPart() as part:
        Box(width, length, height)

        with Locations([Location((0, 0, wall))]):
            Box(
                width - 2 * wall,
                length - 2 * wall,
                height,
                mode=Mode.SUBTRACT,
            )

        fillet(part.edges(), radius=fillet_r)
    return part.part


def export_watertight_stl(shape, stl_path):
    """OCC's tessellator leaves one zero-area triangle at each of the 12 corner blends (8 outer corners, 4 at
    the inner floor), at every tolerance tried (0.001-0.1); the STL is then not watertight (measured
    2026-09-25). They hold no volume, so removing them changes nothing but the topology. The raw mesh goes to
    a temporary file; stl_path is written only if the cleaned mesh is watertight, otherwise it is left as it
    was."""
    import tempfile

    import trimesh

    with tempfile.TemporaryDirectory() as tmp:
        raw = Path(tmp) / "raw.stl"
        export_stl(shape, str(raw))
        mesh = trimesh.load(str(raw), force="mesh")
    n0, v0 = len(mesh.faces), mesh.volume
    mesh.update_faces(mesh.nondegenerate_faces())
    mesh.remove_unreferenced_vertices()
    if not mesh.is_watertight:
        raise SystemExit(f"{stl_path.name}: not watertight after dropping degenerate triangles; not written")
    mesh.export(str(stl_path))
    print(f"{stl_path.name}: dropped {n0 - len(mesh.faces)} zero-area triangles; watertight; "
          f"volume {v0:.2f} -> {mesh.volume:.2f} mm3")


if __name__ == "__main__":
    box = build_box(WIDTH, LENGTH, HEIGHT, WALL, FILLET_R)
    if not box.is_valid or len(box.solids()) != 1:
        raise SystemExit(f"invalid part: valid {box.is_valid}, solids {len(box.solids())}; nothing exported")
    (PROJECT_DIR / "step").mkdir(exist_ok=True)
    (PROJECT_DIR / "stl").mkdir(exist_ok=True)
    export_step(box, str(PROJECT_DIR / "step" / "BoxTest.step"))
    export_watertight_stl(box, PROJECT_DIR / "stl" / "BoxTest.stl")

    print(f"Exported BoxTest  {WIDTH} x {LENGTH} x {HEIGHT} mm, wall {WALL} mm")
