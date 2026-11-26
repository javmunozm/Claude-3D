"""base_pedestal_ventilador numeric gates. Every probe is derived from bpv_model.parameters.derive(), never a fixed number.

Usage: python bpv_gates.py <stl>
Each check prints its number and PASS/FAIL. Controls are cases that must FAIL; a control that passes means the
probe measures nothing. Sections are read as 3D loops in the model's own XY.
"""

import math
import sys
from pathlib import Path

import numpy as np
import trimesh
from shapely import affinity
from shapely.geometry import Point, Polygon

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from bpv_model.parameters import derive  # noqa: E402

TOL = 0.1      # section extents (mesh chord tolerance 0.01 mm)
TOL_Z = 0.05   # ray-measured heights
TOL_V = 0.001  # volume, relative

results = []


def report(name, value, ok, unit="mm"):
    results.append(bool(ok))
    print(f"{'PASS' if ok else 'FAIL'}  {name}: {value}{(' ' + unit) if unit else ''}")


def loops_at(mesh, z):
    sec = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if sec is None:
        return []
    return sorted((Polygon(d[:, :2]) for d in sec.discrete), key=lambda q: -q.area)


def diam(poly):
    b = poly.bounds
    return (b[2] - b[0] + b[3] - b[1]) / 2


def ray_z(mesh, x, y):
    locs, _, _ = mesh.ray.intersects_location([[x, y, 50]], [[0, 0, -1]])
    return sorted(round(float(l[2]), 4) for l in locs)


def main(stl):
    p = derive()
    mesh = trimesh.load(stl, force="mesh")
    bodies = len(mesh.split(only_watertight=False))
    print(f"mesh: {stl}  faces={len(mesh.faces)} watertight={mesh.is_watertight} bodies={bodies}")
    report("watertight, 1 body", f"watertight={mesh.is_watertight} bodies={bodies}", mesh.is_watertight and bodies == 1, "")

    # 1. overall and volume
    ext = mesh.bounds[1] - mesh.bounds[0]
    top = p["h_disc"] + p["h_socket"]
    for i, (k, t) in enumerate((("x", 2 * p["r_out"]), ("y", 2 * p["r_out"]), ("z", top))):
        report(f"overall {k}", f"{ext[i]:.3f} (target {t:.3f})", abs(ext[i] - t) <= TOL)
    dv = (mesh.volume - p["volume"]) / p["volume"]
    report("volume", f"{mesh.volume:.1f} mm3 (formula {p['volume']:.1f}, {dv * 100:+.3f} %)", abs(dv) <= TOL_V, "")

    # 2. disc section at mid-height: outline, stop hole, slots
    zd = p["h_disc"] / 2
    loops = loops_at(mesh, zd)
    outer, rest = loops[0], loops[1:]
    stop = [q for q in rest if q.centroid.distance(Point(0, 0)) < 1]
    slots = [q for q in rest if q.centroid.distance(Point(0, 0)) >= 1]
    report(f"disc z={zd:.1f}: loops", f"{len(loops)} (target {2 + p['n_slots']})", len(loops) == 2 + p["n_slots"], "")
    report("disc outer diameter", f"{diam(outer):.3f} (target {2 * p['r_out']:.3f})", abs(diam(outer) - 2 * p["r_out"]) <= TOL)
    d_stop = diam(stop[0]) if len(stop) == 1 else float("nan")
    report("stop hole diameter", f"{d_stop:.3f} (target {2 * p['r_stop']:.3f})", abs(d_stop - 2 * p["r_stop"]) <= TOL)

    angs = sorted(math.degrees(math.atan2(q.centroid.y, q.centroid.x)) % 360 for q in slots)
    pitch_err = max((abs(((a - i * 360 / p["n_slots"]) + 180) % 360 - 180) for i, a in enumerate(angs)), default=np.nan)
    report("slot angular positions, worst deviation", f"{pitch_err:.3f} deg", pitch_err <= 0.1, "")
    lens, wids, r0s, rims = [], [], [], []
    for q in slots:
        a = math.atan2(q.centroid.y, q.centroid.x)
        local = affinity.rotate(q, -a, origin=(0, 0), use_radians=True)
        b = local.bounds
        lens.append(b[2] - b[0])
        wids.append(b[3] - b[1])
        r0s.append(b[0])
        rims.append(p["r_out"] - max(math.hypot(x, y) for x, y in q.exterior.coords))
    report("slot length min/max", f"{min(lens):.3f}/{max(lens):.3f} (target {p['slot_len']:.3f})",
           max(abs(v - p["slot_len"]) for v in lens) <= TOL)
    report("slot width min/max", f"{min(wids):.3f}/{max(wids):.3f} (target {p['slot_w']:.3f})",
           max(abs(v - p["slot_w"]) for v in wids) <= TOL)
    report("slot inner end radius min/max", f"{min(r0s):.3f}/{max(r0s):.3f} (target {p['slot_r0']:.3f})",
           max(abs(v - p["slot_r0"]) for v in r0s) <= TOL)
    report("outer rim at slot corners, min", f"{min(rims):.3f} (target {p['r_out'] - math.hypot(p['slot_r1'], p['slot_w'] / 2):.3f})",
           abs(min(rims) - (p["r_out"] - math.hypot(p["slot_r1"], p["slot_w"] / 2))) <= TOL)
    by_ang = sorted(slots, key=lambda q: math.atan2(q.centroid.y, q.centroid.x))
    spokes = [by_ang[i].distance(by_ang[(i + 1) % len(by_ang)]) for i in range(len(by_ang))]
    report("spoke width at inner end, min", f"{min(spokes):.3f} (target {p['spoke_in']:.3f})",
           abs(min(spokes) - p["spoke_in"]) <= TOL)

    # 3. socket ring at mid-height of its straight part, and inside the chamfer
    zs = p["h_disc"] + (p["h_socket"] - p["chamfer"]) / 2
    sl = loops_at(mesh, zs)
    ok = len(sl) == 2
    report(f"socket z={zs:.2f}: loops", f"{len(sl)} (target 2)", ok, "")
    if ok:
        report("socket OD", f"{diam(sl[0]):.3f} (target {2 * p['r_sock_od']:.3f})", abs(diam(sl[0]) - 2 * p["r_sock_od"]) <= TOL)
        report("socket hole (fit to the fan base)", f"{diam(sl[1]):.3f} (target {2 * p['r_sock']:.3f})",
               abs(diam(sl[1]) - 2 * p["r_sock"]) <= TOL)
        report("inner rim, socket OD to slot ends", f"{min(r0s) - diam(sl[0]) / 2:.3f} (target {p['slot_r0'] - p['r_sock_od']:.3f})",
               abs(min(r0s) - diam(sl[0]) / 2 - (p["slot_r0"] - p["r_sock_od"])) <= TOL)
    zc = top - p["chamfer"] / 2
    cl = loops_at(mesh, zc)
    dc = diam(cl[1]) if len(cl) == 2 else float("nan")
    tc = 2 * (p["r_sock"] + p["chamfer"] / 2)
    report(f"chamfer z={zc:.2f}: hole diameter", f"{dc:.3f} (target {tc:.3f})", abs(dc - tc) <= TOL)

    # 4. heights by ray (probe radii are the middles of each feature)
    r_stop_mid = (p["r_stop"] + p["r_sock"]) / 2
    hz = ray_z(mesh, r_stop_mid, 0)
    report(f"stop ring at r={r_stop_mid:.2f}: hits", f"{hz} (target [0, {p['h_disc']}])",
           len(hz) == 2 and abs(hz[0]) <= TOL_Z and abs(hz[1] - p["h_disc"]) <= TOL_Z, "")
    r_wall = (p["r_sock"] + p["r_sock_od"]) / 2
    hz = ray_z(mesh, r_wall, 0)
    report(f"socket wall at r={r_wall:.2f}: hits", f"{hz} (target [0, {top}])",
           len(hz) == 2 and abs(hz[0]) <= TOL_Z and abs(hz[1] - top) <= TOL_Z, "")
    r_slot = (p["slot_r0"] + p["slot_r1"]) / 2
    hz_slot = ray_z(mesh, r_slot, 0)
    report(f"slot centre at r={r_slot:.2f}: empty", f"{len(hz_slot)} hits (target 0)", len(hz_slot) == 0, "")
    sa = math.pi / p["n_slots"]
    hz_spoke = ray_z(mesh, r_slot * math.cos(sa), r_slot * math.sin(sa))
    report("spoke centre: solid", f"{hz_spoke} (target [0, {p['h_disc']}])",
           len(hz_spoke) == 2 and abs(hz_spoke[1] - p["h_disc"]) <= TOL_Z, "")

    print("-- controls (each must be FAIL-as-expected) --")
    ctrl_ok = True
    bad = abs(d_stop - 81.0) <= TOL
    print(f"{'BAD ' if bad else 'ok  '} control: stop diameter {d_stop:.3f} against a wrong target 81.000 passes={bad} (must be False)")
    ctrl_ok &= not bad
    filled = len(hz_spoke) == 0
    print(f"{'BAD ' if filled else 'ok  '} control: slot probe moved onto a spoke reads empty={filled} (must be False)")
    ctrl_ok &= not filled
    try:
        derive(d_stop=96.0)
        print("BAD  control: derive(d_stop=96) did not raise")
        ctrl_ok = False
    except ValueError as e:
        print(f"ok   control: derive(d_stop=96) raised: {e}")
    results.append(ctrl_ok)

    print(f"== {'ALL PASS' if all(results) else 'FAILED'} ({sum(results)}/{len(results)})")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
