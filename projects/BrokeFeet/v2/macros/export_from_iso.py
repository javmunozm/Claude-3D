"""Mesh an isotropic grid through EXACTLY V0's main() path and export it.

Nothing here re-implements the transform. The axis map, the pad, the winding
fix, the size/flake filters, the bridging and MIRROR_X are all copied verbatim
from segment_axial.main() -- because the README records that a first attempt at
re-deriving the index->mm mapping got [0.23, 0.50, 1.09] instead of
[0.5, 0.5, 0.5] and reported 0 mm3 for every crater. The point of this file is
to swap the GRID, not the geometry pipeline.

Writes into BrokeFeetV1/. BrokeFeet/ is the shipping model and is never
touched.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
WORK = HERE.parent / "work"
OUT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / "v0" / "macros"))

import segment_axial as v0  # noqa: E402


def mesh_from_iso(iso: np.ndarray, bridge: bool = True) -> trimesh.Trimesh:
    from skimage import measure

    iso = np.pad(iso, 1, mode="constant", constant_values=False)
    verts, faces, _, _ = measure.marching_cubes(iso, level=0.5)
    verts -= 1.0
    verts *= v0.ISO_VOXEL_MM
    verts = np.column_stack([verts[:, 2], -verts[:, 1], verts[:, 0]])

    mesh = trimesh.Trimesh(vertices=verts, faces=faces)
    if mesh.volume < 0:
        mesh.invert()
    mesh.update_faces(mesh.nondegenerate_faces())
    mesh.update_faces(mesh.unique_faces())
    mesh.remove_unreferenced_vertices()
    mesh.fill_holes()

    bodies = mesh.split(only_watertight=False)
    print(f"  raw bodies from marching cubes: {len(bodies)}")
    if len(bodies) > 1:
        kept, shards, flakes = [], 0, 0
        for body in bodies:
            vol = abs(body.volume)
            if vol < v0.MIN_BODY_VOLUME_MM3:
                shards += 1
                continue
            if vol > 0 and body.area / vol > v0.MAX_AREA_VOLUME_RATIO:
                flakes += 1
                continue
            kept.append(body)
        print(f"  dropped {shards} specks, {flakes} flakes; "
              f"{len(kept)} real bodies BEFORE bridging")
        if not kept:
            raise SystemExit("everything filtered out")
        if bridge:
            mesh = v0._bridge_bodies(kept)
        else:
            mesh = trimesh.util.concatenate(kept)
    else:
        print("  1 body before bridging")

    bodies = mesh.split(only_watertight=False)
    if len(bodies) > 1:
        real = [b for b in bodies if abs(b.volume) >= v0.MIN_BODY_VOLUME_MM3]
        if len(bodies) - len(real):
            print(f"  discarded {len(bodies) - len(real)} bridging shard(s)")
        mesh = trimesh.util.concatenate(real) if len(real) > 1 else real[0]

    if v0.MIRROR_X:
        mesh.apply_transform(np.diag([-1.0, 1.0, 1.0, 1.0]))
        mesh.fix_normals()
    return mesh


def bodies_before_bridging(iso: np.ndarray) -> int:
    """The joint-preservation metric: how many distinguishable bodies exist
    BEFORE any pin is added. A good sponge number can hide a fall here."""
    from skimage import measure

    pad = np.pad(iso, 1, mode="constant", constant_values=False)
    verts, faces, _, _ = measure.marching_cubes(pad, level=0.5)
    verts -= 1.0
    verts *= v0.ISO_VOXEL_MM
    verts = np.column_stack([verts[:, 2], -verts[:, 1], verts[:, 0]])
    m = trimesh.Trimesh(vertices=verts, faces=faces)
    if m.volume < 0:
        m.invert()
    m.update_faces(m.nondegenerate_faces())
    m.update_faces(m.unique_faces())
    m.remove_unreferenced_vertices()
    n = 0
    for b in m.split(only_watertight=False):
        vol = abs(b.volume)
        if vol < v0.MIN_BODY_VOLUME_MM3:
            continue
        if vol > 0 and b.area / vol > v0.MAX_AREA_VOLUME_RATIO:
            continue
        n += 1
    return n


def main():
    src = WORK / sys.argv[1]
    name = sys.argv[2]
    iso = np.load(src)
    print(f"{src.name}: {iso.sum() * v0.ISO_VOXEL_MM ** 3 / 1000:.3f} cm3  "
          f"tunnels {v0._tunnel_count(iso)}  bones {v0._real_bone_count(iso)}")
    mesh = mesh_from_iso(iso)
    g = int(round((2 - mesh.euler_number) / 2))
    print(f"  mesh {len(mesh.vertices):,} verts  vol {mesh.volume / 1000:.2f} cm3"
          f"  watertight={mesh.is_watertight}  bodies={mesh.body_count}  "
          f"genus={g}  area/volume={mesh.area / mesh.volume:.3f}")
    p = OUT / name
    mesh.export(p)
    print(f"wrote {p}")


if __name__ == "__main__":
    main()
