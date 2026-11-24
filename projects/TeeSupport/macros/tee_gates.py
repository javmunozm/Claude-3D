"""TeeSupport numeric gates. Every probe is derived from tee_model.parameters.derive(), never a fixed number.

Usage: python tee_gates.py <stl>
Each check prints its number and PASS/FAIL. Controls are cases that must FAIL; a control that passes means the
probe measures nothing.
"""

import math
import sys
from pathlib import Path

import numpy as np
import trimesh
from shapely.geometry import Point, Polygon

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from tee_model.parameters import derive  # noqa: E402

TOL_BBOX, TOL_WALL, TOL_BORE, TOL_SOCKET, TOL_GUSSET = 0.1, 0.05, 0.05, 0.2, 0.05

AXES = {"x": np.array([1.0, 0, 0]), "y": np.array([0, 1.0, 0]), "z": np.array([0, 0, 1.0])}
# the two other axes spanning each gusset plane: plane (a, b) -> its normal
GUSSETS = [("x", "y", "z"), ("y", "z", "x"), ("z", "x", "y")]

results = []


def report(name, value, ok, unit="mm"):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}: {value}{(' ' + unit) if unit else ''}")


def ring_section(mesh, axis, station):
    """Planar section normal to `axis` at `station`; returns shapely polygons in the plane."""
    sec = mesh.section(plane_origin=AXES[axis] * station, plane_normal=AXES[axis])
    if sec is None:
        return []
    planar, _ = sec.to_2D()
    return list(planar.polygons_full)


def ray_hits(mesh, origin, direction):
    locs, _, _ = mesh.ray.intersects_location([origin], [direction])
    return sorted(float(np.dot(l - origin, direction)) for l in locs)


def main(stl):
    p = derive()
    mesh = trimesh.load(stl, force="mesh")
    print(f"mesh: {stl}  faces={len(mesh.faces)} watertight={mesh.is_watertight} bodies={len(mesh.split(only_watertight=False))}")

    # 1. overall per axis
    ext = mesh.bounds[1] - mesh.bounds[0]
    for i, k in enumerate("xyz"):
        report(f"overall {k}", f"{ext[i]:.3f} (target {p['overall']:.1f})", abs(ext[i] - p["overall"]) <= TOL_BBOX)

    # 2. wall, bore and plate edges on a section normal to each arm, in the socket, beyond the core
    #    The two plates on each arm run to the tip, so the section is a ring with two flanges: the min wall is the
    #    ring-to-hole distance; each flange's edge must sit at the diagonal (tip + w - station) and the bare sides
    #    at r_out.
    station = (p["r_out"] + p["gusset_tip"]) / 2 + 6.0
    edge = p["gusset_tip"] + p["gusset_w"] - station
    for k in "xyz":
        sec = mesh.section(plane_origin=AXES[k] * station, plane_normal=AXES[k])
        polys = list(sec.to_2D()[0].polygons_full) if sec is not None else []
        if len(polys) != 1 or len(polys[0].interiors) != 1:
            report(f"arm {k} section at {station:.2f}", f"{len(polys)} polygon(s), not one body with one bore", False, "")
            continue
        hole = Polygon(polys[0].interiors[0])
        wall = polys[0].exterior.distance(hole.exterior)
        bore = 2 * math.sqrt(hole.area / math.pi)
        report(f"arm {k} min wall at {k}={station:.2f}", f"{wall:.3f} (target {p['wall']:.2f})",
               abs(wall - p["wall"]) <= TOL_WALL)
        report(f"arm {k} bore (area-equivalent)", f"{bore:.3f} (target {p['bore_d']:.2f})",
               abs(bore - p["bore_d"]) <= TOL_BORE)
        # flange edges, read from the 3D vertices of the section (axis-aligned, no 2D frame ambiguity)
        v = np.vstack([e for e in sec.discrete])
        for j, other in enumerate("xyz"):
            if other == k:
                continue
            hi, lo = v[:, j].max(), v[:, j].min()
            report(f"arm {k} extent along +{other}/-{other} at {k}={station:.2f}",
                   f"{hi:.3f}/{lo:.3f} (target {edge:.2f}/{-p['r_out']:.2f})",
                   abs(hi - edge) <= TOL_WALL and abs(lo + p["r_out"]) <= TOL_WALL)

    # 3. socket depth: a ray down each arm axis from beyond the tip hits the bore floor first
    for k in "xyz":
        d = AXES[k]
        start = p["reach"] + 5
        hits = ray_hits(mesh, d * start, -d)
        floor = start - hits[0] if hits else float("nan")    # coordinate of the bore floor on the axis
        depth = p["reach"] - floor
        report(f"arm {k} socket depth", f"{depth:.3f} (target {p['socket']:.2f})", abs(depth - p["socket"]) <= TOL_SOCKET)

    # 4. plate thickness: rays along each plate's normal at two points clear of all tubes:
    #    the inner corner (s, s) and 2 mm short of each tip, halfway between the tube skin and the plate edge
    s = p["gusset_w"]
    u = p["gusset_tip"] - 2.0
    h = (p["r_out"] + (p["gusset_tip"] + p["gusset_w"] - u)) / 2
    assert s > p["r_out"] and h > p["r_out"], (s, h, p)
    for a, b, n in GUSSETS:
        for label, ca, cb in (("corner", s, s), (f"near {a} tip", u, h), (f"near {b} tip", h, u)):
            pt = AXES[a] * ca + AXES[b] * cb
            hits = ray_hits(mesh, pt + AXES[n] * 20, -AXES[n])
            t = hits[1] - hits[0] if len(hits) == 2 else float("nan")
            report(f"plate {a}{b} thickness {label} ({a},{b})=({ca:.2f},{cb:.2f})",
                   f"{t:.3f} [{len(hits)} hits] (target {p['gusset_t']:.2f})",
                   len(hits) == 2 and abs(t - p["gusset_t"]) <= TOL_GUSSET)

    # 5. core solid, bores empty just past their floors
    report("core solid at origin", bool(mesh.contains([[0, 0, 0]])[0]), bool(mesh.contains([[0, 0, 0]])[0]), "")
    for k in "xyz":
        empty = not mesh.contains([AXES[k] * (p["r_out"] + 1.0)])[0]
        report(f"bore {k} empty 1 mm past its floor", empty, empty, "")

    # controls: must FAIL
    print("-- controls (each must be FAIL-as-expected) --")
    ctrl_ok = True
    core_probe_empty = not mesh.contains([AXES["x"] * (p["r_out"] - 1.0)])[0]
    print(f"{'ok  ' if not core_probe_empty else 'BAD '} control: bore probe placed 1 mm inside the core reads empty={core_probe_empty} (must be False)")
    ctrl_ok &= not core_probe_empty
    try:
        derive(gusset_t=4.0)
        print("BAD  control: derive(gusset_t=4.0) did not raise")
        ctrl_ok = False
    except ValueError as e:
        print(f"ok   control: derive(gusset_t=4.0) raised: {e}")
    results.append(ctrl_ok)

    print(f"== {'ALL PASS' if all(results) else 'FAILED'} ({sum(results)}/{len(results)})")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
