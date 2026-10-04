"""VitaGripPS5 v2 spike main: the case's right grip end as B-rep (build123d), mirrored.

  timeout 300 python vita_grip_ps5_v2.py [--out-step P] [--out-stl P] [--results P] [--sections-only]
"""
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def main():
    import numpy as np
    import trimesh
    from build123d import export_brep, export_step, export_stl
    from vgps5_v2 import constants as C
    from vgps5_v2.sections import load_mesh, station_loops, extrapolate, shrunk
    from vgps5_v2.shapes import one_solid, oval_cutter, valid, try_fillet
    from vgps5_v2.parts.grip_end import build_grip_end, roll_top
    from vgps5_v2.parts.plate import build_plate_half
    from vgps5_v2.parts.lip import finger_profile, pit_profile, build_finger, build_pit
    from vgps5_v2.assemble import junction_edges, mirror_union
    from vgps5_v2 import checks

    ap = argparse.ArgumentParser()
    ap.add_argument("--out-step", default=str(C.V2_DIR / "step" / "VitaGripPS5_v2_spike.step"))
    ap.add_argument("--out-stl", default=str(C.V2_DIR / "stl" / "VitaGripPS5_v2_spike.stl"))
    ap.add_argument("--results", default=str(C.V2_DIR / "audit" / "spike" / "spike_results.json"))
    ap.add_argument("--sections-only", action="store_true")
    ap.add_argument("--junction-brep", default=None, help="write the half before the junction fillet (BREP)")
    args = ap.parse_args()

    t0 = time.time()

    def log(msg):
        print("[%6.1f s] %s" % (time.time() - t0, msg), flush=True)

    R = {}
    r16 = load_mesh(C.R16_STL)
    sp = dict(inner_x=C.INNER_X, rowfill_z0=C.ROWFILL_Z0, top_z=C.TOP_Z, cut_z=C.CUT_Z, ext_max=C.EXT_TOP_MAX,
              handle_top_y0=C.HANDLE_TOP_Y0, handle_top_slope=C.HANDLE_TOP_SLOPE, n_pts=C.N_PTS, rms=C.SMOOTH_RMS,
              cap_ref_y=C.CAP_REF_Y, cap_h=C.CAP_H, force_ext_y=C.FORCE_EXT_Y)
    log("sections (main)")
    main_st = station_loops(r16, C.MAIN_STATIONS, sp, rowfill_from=C.ROWFILL_Y, log=log)
    main_st += extrapolate(main_st, C.EXTRAP_STATIONS)
    log("sections (rear)")
    rear_st = station_loops(r16, C.REAR_STATIONS, sp, rowfill_from=C.ROWFILL_Y, log=log)
    rear_st.append((C.REAR_OVERLAP_Y, shrunk(rear_st[-1][1], C.REAR_OVERLAP_SCALE)))
    if args.sections_only:
        return

    log("grip end")
    end, res = build_grip_end(main_st, rear_st, C.TOP_Z, C.TIP_Y, C.TIP_ROLL, (C.CLIP_Y0, C.CLIP_SLOPE), log)
    R.update(res)
    R["top_roll"], end = roll_top(end, C.TOP_Z, C.TOP_ROLL, -1e9, [], log)
    pocket = oval_cutter(C.CAP_XC, C.CAP_A, C.CAP_B, C.YC, C.POCKET_Y_BOTTOM, C.POCKET_Y_TOP, C.FLOOR_Z, C.TOP_Z + 10.0)
    end = one_solid(end.cut(pocket), "pocket cut")
    log("pocket cut: valid")

    plate = build_plate_half(C.PLATE_X1, C.PLATE_Y0, C.PLATE_Y1, C.PLATE_Z0, C.FLOOR_Z)
    half = one_solid(end.fuse(plate), "grip end + plate")
    log("plate fused: valid")
    j_edges = junction_edges(half, C.INNER_X - 2.5, C.PLATE_X1 + 0.5,
                             dict(Z=(C.PLATE_Z0, C.FLOOR_Z), Y=(C.PLATE_Y0, C.PLATE_Y1)), log)
    R["junction_edges"] = len(j_edges)
    half_pre = half
    if C.JUNCTION_R:
        R["junction_r_applied"], half = try_fillet(half, j_edges, [C.JUNCTION_R], "junction", log)

    n = np.array(C.FINGER_N) / np.linalg.norm(C.FINGER_N)
    prof, info = finger_profile(C.LIP_U, C.LIP_TOP_Z, C.ROOT_Z, C.FINGER_T_ROOT, C.FINGER_T_TIP, C.LIP_OVERHANG,
                                C.LIP_LEAD_DEG, C.LIP_RET_DEG, C.LIP_FLAT, C.LIP_LAND, C.FINGER_INNER_SLOT,
                                C.FINGER_GAP, C.FINGER_ROOT_R)
    log("finger profile: %s" % {k: round(v, 3) for k, v in info.items()})
    R["finger"] = {k: round(float(v), 4) for k, v in info.items()}
    pit = build_pit(C.FINGER_P, n, pit_profile(C.FINGER_W, C.FINGER_SLOT, C.FINGER_INNER_SLOT, C.FINGER_T_ROOT,
                                                C.FINGER_GAP, C.PIT_CORNER_R), C.ROOT_Z, C.TOP_Z + 10.0)
    half = one_solid(half.cut(pit), "pit cut")
    finger = one_solid(build_finger(C.FINGER_P, n, C.FINGER_W, prof), "finger")
    half = one_solid(half.fuse(finger), "finger union")
    log("lip: valid, half volume %.0f" % half.volume)

    full, _ = mirror_union(half)
    R["valid_full"] = valid(full)
    log("mirrored union: valid %s, volume %.0f" % (R["valid_full"], full.volume))

    for pth in (args.out_step, args.out_stl):
        Path(pth).parent.mkdir(parents=True, exist_ok=True)
    export_step(full, args.out_step)
    # 0.02 / 0.2 gave 28 mm triangles and a 0.37 mm chord error (review_spike.md, S4)
    export_stl(full, args.out_stl, tolerance=0.002, angular_tolerance=0.05)
    R["build_s"] = round(time.time() - t0, 1)
    log("exported %s, %s" % (args.out_step, args.out_stl))

    m = trimesh.load(args.out_stl, force="mesh")
    R["topology"] = checks.topology(m)
    log("topology %s" % R["topology"])
    R["mirror_dev_max_rms"] = checks.mirror_deviation(m)
    log("mirror deviation max/rms %s" % (R["mirror_dev_max_rms"],))
    R["handle_dev"] = checks.handle_deviation(m, r16, {"root y-30..-14.5": (-30.0, -14.5),
                                                       "middle y-60..-30": (-60.0, -30.0),
                                                       "tip roll y-68..-60": (-68.01, -60.0)})
    for k, v in R["handle_dev"].items():
        log("dev %-20s %s" % (k, {t: {q: (round(w, 3) if isinstance(w, float) else w) for q, w in d.items()}
                                  for t, d in v.items()}))
    R["total_s"] = round(time.time() - t0, 1)
    Path(args.results).parent.mkdir(parents=True, exist_ok=True)
    Path(args.results).write_text(json.dumps(R, indent=1))
    log("gates written")
    if args.junction_brep:
        # the junction fillet search runs on this file in subprocesses (audit/spike/scripts/junction_search.py):
        # a failing OCC fillet at r 1 ended this process twice without a Python error
        export_brep(half_pre, args.junction_brep)
        log("pre-junction half written to %s" % args.junction_brep)
    log("done")


if __name__ == "__main__":
    main()
