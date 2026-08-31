"""Streaming 3MF reader — trimesh's loader OOMs on the 454MB psvitaManualJoin.3mf.

psvitaManualJoin.3mf is a Bambu/Orca project using the production extension:
3D/3dmodel.model holds no geometry, only an <object> whose <component>s point
at a separate 2.3 GB model part via p:path. So this reader must (a) follow
those component references and (b) parse incrementally, keeping peak memory to
one object's vertex list rather than a joined string of every triangle.

The component transforms ARE the user's manual assembly — front shell, back
shell flipped, two triggers mirrored, cart cover — so they must be applied,
not discarded.
"""
import zipfile
import numpy as np
from xml.etree import ElementTree as ET


def _strip(tag):
    return tag.rsplit("}", 1)[-1]


def _parse_transform(tr):
    """3MF transform attr: 9 rotation values (column-major) + 3 translation."""
    T = np.eye(4)
    if tr:
        v = [float(x) for x in tr.split()]
        T[:3, :3] = np.array(v[:9]).reshape(3, 3).T
        T[:3, 3] = v[9:12]
    return T


def _parse_model_part(fh, decimate=1, verbose=True):
    """Parse one .model stream -> (objects, components, build).

    objects    {id: (V, F)}          meshes defined in this part
    components {id: [(path, oid, T)]} component references
    build      [(oid, T)]            build items
    """
    objects, components, build = {}, {}, []
    cur_id = None
    verts, faces = [], []

    for event, el in ET.iterparse(fh, events=("start", "end")):
        tag = _strip(el.tag)

        if event == "start":
            if tag == "object":
                cur_id = el.get("id")
                verts, faces = [], []
            elif tag == "vertex" and cur_id is not None:
                verts.append((float(el.get("x")),
                              float(el.get("y")),
                              float(el.get("z"))))
                el.clear()
            elif tag == "triangle" and cur_id is not None:
                faces.append((int(el.get("v1")),
                              int(el.get("v2")),
                              int(el.get("v3"))))
                el.clear()
            elif tag == "component" and cur_id is not None:
                path = next((v for k, v in el.attrib.items()
                             if _strip(k) == "path" or k.endswith("}path")), None)
                components.setdefault(cur_id, []).append(
                    (path, el.get("objectid"), _parse_transform(el.get("transform")))
                )
                el.clear()

        elif event == "end":
            if tag == "object":
                if verts and faces:
                    V = np.asarray(verts, dtype=np.float64)
                    F = np.asarray(faces, dtype=np.int64)
                    objects[cur_id] = (V, F)
                    if verbose:
                        print(f"    object {cur_id}: {len(V):,} verts / {len(F):,} tris")
                cur_id, verts, faces = None, [], []
                el.clear()
            elif tag == "item":
                build.append((el.get("objectid"),
                              _parse_transform(el.get("transform"))))
                el.clear()

    return objects, components, build


def read_3mf(path, verbose=True):
    """Read a 3MF (production extension aware) -> list of (label, V, F, T)."""
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        root_name = "3D/3dmodel.model"
        if root_name not in names:
            root_name = next(n for n in names if n.endswith(".model"))

        parts = {}          # normalized path -> (objects, components, build)

        def load_part(name):
            key = name.lstrip("/")
            if key in parts:
                return parts[key]
            if verbose:
                sz = z.getinfo(key).file_size / 1e6
                print(f"  parsing {key} ({sz:,.0f} MB) ...")
            with z.open(key) as fh:
                parts[key] = _parse_model_part(fh, verbose=verbose)
            return parts[key]

        root_objects, root_components, root_build = load_part(root_name)

        out = []

        def resolve(part_name, oid, T, depth=0):
            objects, components, _ = parts[part_name.lstrip("/")]
            if oid in objects:
                V, F = objects[oid]
                out.append((f"{part_name}#{oid}", V, F, T))
                return
            for cpath, coid, cT in components.get(oid, []):
                target = cpath if cpath else part_name
                load_part(target)
                resolve(target, coid, T @ cT, depth + 1)

        for oid, T in (root_build or [(k, np.eye(4)) for k in root_objects]):
            resolve(root_name, oid, T)

    return out


def as_mesh(path, verbose=True):
    """Flatten a 3MF into one trimesh.Trimesh with all transforms applied."""
    import trimesh
    pieces = read_3mf(path, verbose=verbose)
    meshes = []
    for label, V, F, T in pieces:
        Vt = V @ T[:3, :3].T + T[:3, 3]
        m = trimesh.Trimesh(vertices=Vt, faces=F, process=False)
        if verbose:
            sz = m.bounds[1] - m.bounds[0]
            print(f"  {label}: {len(F):,} tris  "
                  f"{sz[0]:.2f} x {sz[1]:.2f} x {sz[2]:.2f}")
        meshes.append(m)
    return trimesh.util.concatenate(meshes) if len(meshes) > 1 else meshes[0]


if __name__ == "__main__":
    import sys
    from pathlib import Path

    p = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
        "D:/CAD/Claude-Projects/references/psvitaGrip/Vita 1000/psvitaManualJoin.3mf")
    print(f"Reading {p.name} ...")
    pieces = read_3mf(p)
    print(f"\n{len(pieces)} placed mesh(es):")
    for label, V, F, T in pieces:
        Vt = V @ T[:3, :3].T + T[:3, 3]
        lo, hi = Vt.min(0), Vt.max(0)
        sz = hi - lo
        print(f"  {label}: {len(F):,} tris  size {sz[0]:.2f} x {sz[1]:.2f} x {sz[2]:.2f}"
              f"  X[{lo[0]:.1f},{hi[0]:.1f}] Y[{lo[1]:.1f},{hi[1]:.1f}] Z[{lo[2]:.1f},{hi[2]:.1f}]")
