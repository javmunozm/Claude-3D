"""DeodorantBoxTop numeric gates. Every probe is derived from dbt_model.parameters.derive(), never a fixed number.

Usage: python dbt_gates.py <stl>
Each check prints its number and PASS/FAIL. Controls are cases that must FAIL; a control that passes means the
probe measures nothing. Sections are read as 3D loops in the model's own XY (no 2D frame transform).
"""

import sys
from pathlib import Path

import numpy as np
import trimesh
from shapely.geometry import Polygon

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from dbt_model.parameters import derive  # noqa: E402

TOL = 0.1      # section extents (mesh chord tolerance 0.01 mm, ellipse sampled by the tessellator)
TOL_Z = 0.05   # ray-measured heights

results = []


def report(name, value, ok, unit="mm"):
    results.append(bool(ok))
    print(f"{'PASS' if ok else 'FAIL'}  {name}: {value}{(' ' + unit) if unit else ''}")


def loops_at(mesh, z):
    sec = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if sec is None:
        return []
    return [Polygon(d[:, :2]) for d in sec.discrete]


def ray_z(mesh, x, y, z0, dz):
    locs, _, _ = mesh.ray.intersects_location([[x, y, z0]], [[0, 0, dz]])
    return sorted(float(l[2]) for l in locs)


def main(stl):
    p = derive()
    mesh = trimesh.load(stl, force="mesh")
    bodies = len(mesh.split(only_watertight=False))
    print(f"mesh: {stl}  faces={len(mesh.faces)} watertight={mesh.is_watertight} bodies={bodies}")
    report("watertight, 1 body", f"watertight={mesh.is_watertight} bodies={bodies}", mesh.is_watertight and bodies == 1, "")

    # 1. overall
    ext = mesh.bounds[1] - mesh.bounds[0]
    for i, (k, t) in enumerate((("x", p["plate_x"]), ("y", p["plate_y"]), ("z", p["plate_t"] + p["depth"]))):
        report(f"overall {k}", f"{ext[i]:.3f} (target {t:.3f})", abs(ext[i] - t) <= TOL)

    # 2. plate section at mid-thickness: 1 outline + 12 holes
    zp = p["plate_t"] / 2
    loops = sorted(loops_at(mesh, zp), key=lambda q: -q.area)
    n_holes = len(loops) - 1
    report(f"plate section z={zp:.1f}: holes", f"{n_holes} (target {len(p['cx']) * len(p['cy'])})",
           n_holes == len(p["cx"]) * len(p["cy"]), "")
    holes = loops[1:]
    grid = {}
    for h in holes:
        x0, y0, x1, y1 = h.bounds
        c = ((x0 + x1) / 2, (y0 + y1) / 2)
        i = int(np.argmin([abs(c[0] - x) for x in p["cx"]]))
        j = int(np.argmin([abs(c[1] - y) for y in p["cy"]]))
        grid[(i, j)] = h.bounds
    worst_ax = max((abs((b[2] - b[0]) - p["hole_x"]) for b in grid.values()), default=np.nan)
    worst_ay = max((abs((b[3] - b[1]) - p["hole_y"]) for b in grid.values()), default=np.nan)
    worst_c = max((max(abs((b[0] + b[2]) / 2 - p["cx"][i]), abs((b[1] + b[3]) / 2 - p["cy"][j]))
                   for (i, j), b in grid.items()), default=np.nan)
    report("hole axis X, worst deviation", f"{worst_ax:.3f} (target {p['hole_x']} ±{TOL})", worst_ax <= TOL)
    report("hole axis Y, worst deviation", f"{worst_ay:.3f} (target {p['hole_y']} ±{TOL})", worst_ay <= TOL)
    report("hole centres, worst deviation", f"{worst_c:.3f} (±{TOL})", worst_c <= TOL)
    nx, ny = len(p["cx"]), len(p["cy"])
    if len(grid) == nx * ny:
        gx = [grid[(i + 1, j)][0] - grid[(i, j)][2] for i in range(nx - 1) for j in range(ny)]
        gy = [grid[(i, j + 1)][1] - grid[(i, j)][3] for i in range(nx) for j in range(ny - 1)]
        mx = [min(b[0] for b in grid.values()), p["plate_x"] - max(b[2] for b in grid.values())]
        my = [min(b[1] for b in grid.values()), p["plate_y"] - max(b[3] for b in grid.values())]
        report("web X between holes min/max", f"{min(gx):.3f}/{max(gx):.3f} (target {p['gap_x']:.3f})",
               max(abs(g - p["gap_x"]) for g in gx) <= TOL)
        report("web Y between holes min/max", f"{min(gy):.3f}/{max(gy):.3f} (target {p['gap_y']:.3f})",
               max(abs(g - p["gap_y"]) for g in gy) <= TOL)
        report("margin X left/right", f"{mx[0]:.3f}/{mx[1]:.3f} (target {p['margin_x']})",
               max(abs(m - p["margin_x"]) for m in mx) <= TOL)
        report("margin Y front/back", f"{my[0]:.3f}/{my[1]:.3f} (target {p['margin_y']})",
               max(abs(m - p["margin_y"]) for m in my) <= TOL)

    # 3. socket section at mid-depth: 4 rings, each an outer triangle around a cavity triangle
    zs = -p["depth"] / 2
    sl = sorted(loops_at(mesh, zs), key=lambda q: -q.area)
    outers, inners = sl[:4], sl[4:]
    report(f"socket section z={zs:.1f}: loops", f"{len(sl)} (target 8)", len(sl) == 8, "")
    corners = [(0, 0), (p["plate_x"], 0), (p["plate_x"], p["plate_y"]), (0, p["plate_y"])]
    for (X, Y) in corners:
        o = min(outers, key=lambda q: q.centroid.distance(Polygon([(X, Y), (X + 1, Y), (X, Y + 1)]).centroid))
        inn = [q for q in inners if o.contains(q.representative_point())]
        if len(inn) != 1:
            report(f"socket at ({X:.0f},{Y:.0f})", f"{len(inn)} cavities", False, "")
            continue
        q = inn[0]
        ob, ib = o.bounds, q.bounds
        o_leg = max(ob[2] - ob[0], ob[3] - ob[1])
        i_leg = max(ib[2] - ib[0], ib[3] - ib[1])
        flush = max(min(abs(ob[0] - X), abs(ob[2] - X)), min(abs(ob[1] - Y), abs(ob[3] - Y)))
        wall_edge = min(abs(ib[0] - X), abs(ib[2] - X)), min(abs(ib[1] - Y), abs(ib[3] - Y))
        wall_hyp = o.exterior.distance(Polygon(q.exterior))
        report(f"socket ({X:.0f},{Y:.0f}) cavity leg", f"{i_leg:.3f} (target {p['cavity_leg']:.3f})",
               abs(i_leg - p["cavity_leg"]) <= TOL)
        report(f"socket ({X:.0f},{Y:.0f}) outer leg / flush to corner", f"{o_leg:.3f} / {flush:.3f} "
               f"(target {p['outer_leg']:.3f} / 0)", abs(o_leg - p["outer_leg"]) <= TOL and flush <= TOL)
        report(f"socket ({X:.0f},{Y:.0f}) wall edge x/y, min wall", f"{wall_edge[0]:.3f}/{wall_edge[1]:.3f}, "
               f"{wall_hyp:.3f} (target {p['wall']})",
               max(abs(w - p["wall"]) for w in (*wall_edge, wall_hyp)) <= TOL)

    # 4. heights by ray
    xw = p["cx"][0] + p["hole_x"] / 2 + p["gap_x"] / 2       # middle of the first X web, on a hole row
    hz = ray_z(mesh, xw, p["cy"][1], 20, -1)
    t = hz[-1] - hz[0] if len(hz) == 2 else np.nan
    report(f"plate thickness at web ({xw:.2f},{p['cy'][1]:.2f})", f"{t:.3f} [{len(hz)} hits] (target {p['plate_t']})",
           len(hz) == 2 and abs(t - p["plate_t"]) <= TOL_Z)
    hz = ray_z(mesh, p["outer_leg"] / 2, p["wall"] / 2, 20, -1)  # through the socket wall at the origin corner
    d = -hz[0] if hz else np.nan
    report("socket wall bottom below plate", f"{d:.3f} [{len(hz)} hits] (target {p['depth']})",
           len(hz) == 2 and abs(d - p["depth"]) <= TOL_Z)
    c = p["wall"] + p["cavity_leg"] / 3                          # cavity centroid
    hz = ray_z(mesh, c, c, -20, 1)
    floor = hz[0] if hz else np.nan
    report("cavity floor at plate underside (z=0)", f"{floor:.3f} [{len(hz)} hits]", len(hz) == 2 and abs(floor) <= TOL_Z)

    # 5. holes empty, webs solid
    hole_empty = not mesh.contains([[p["cx"][1], p["cy"][2], zp]])[0]
    report("hole centre empty", hole_empty, hole_empty, "")

    print("-- controls (each must be FAIL-as-expected) --")
    ctrl_ok = True
    web_empty = not mesh.contains([[xw, p["cy"][1], zp]])[0]
    print(f"{'ok  ' if not web_empty else 'BAD '} control: hole probe moved onto a web reads empty={web_empty} (must be False)")
    ctrl_ok &= not web_empty
    try:
        derive(hole_y=52.0)
        print("BAD  control: derive(hole_y=52) did not raise")
        ctrl_ok = False
    except ValueError as e:
        print(f"ok   control: derive(hole_y=52) raised: {e}")
    results.append(ctrl_ok)

    print(f"== {'ALL PASS' if all(results) else 'FAILED'} ({sum(results)}/{len(results)})")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
