"""VitaGripPS5 v2 main (pass 1d): the case's right grip end as B-rep (build123d), two lofts sharing the station
y -13.5 with a tangent (G1) seam (body/corner and handle; the handle 16 mm shorter than r16, 15 mm root
transition), plate built in, mirrored.

  timeout 300 python vita_grip_ps5_v2.py [--out-step P] [--out-stl P] [--results P] [--sections-only]
                                         [--half-brep P] [--grip-only P.stl] [--no-gates]
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
    from vgps5_v2.sections import load_mesh, station_loops, extrapolate, blend_profile, uturn_field, morph, \
        seam_guides
    from vgps5_v2.shapes import one_solid, oval_cutter, valid, try_fillet, clip_cutter
    from vgps5_v2.parts.grip_end import build_body, build_handle, build_single, fuse_at_seam
    from vgps5_v2.parts.plate import build_plate_half, build_blend
    from vgps5_v2.parts.lip import finger_profile, pit_profile, build_finger, build_pit
    from vgps5_v2.assemble import mirror_union
    from vgps5_v2 import checks

    ap = argparse.ArgumentParser()
    ap.add_argument("--out-step", default=str(C.V2_DIR / "step" / "VitaGripPS5_v2_p1d.step"))
    ap.add_argument("--out-stl", default=str(C.V2_DIR / "stl" / "VitaGripPS5_v2_p1d.stl"))
    ap.add_argument("--results", default=str(C.V2_DIR / "audit" / "p1d" / "p1d_results.json"))
    ap.add_argument("--sections-only", action="store_true")
    ap.add_argument("--half-brep", default=None, help="write the half before the lip (BREP), for fillet searches")
    ap.add_argument("--no-gates", action="store_true")
    ap.add_argument("--grip-only", default=None, help="stop after the grip end + blend; write it as this STL")
    args = ap.parse_args()

    t0 = time.time()

    def log(msg):
        print("[%6.1f s] %s" % (time.time() - t0, msg), flush=True)

    R = {}
    r16 = load_mesh(C.R16_STL)
    sp = dict(inner_x=C.INNER_X, rowfill_z0=C.ROWFILL_Z0, top_z=C.TOP_Z, cut_z=C.CUT_Z, ext_max=C.EXT_TOP_MAX,
              handle_top_y0=C.HANDLE_TOP_Y0, handle_top_slope=C.HANDLE_TOP_SLOPE, n_pts=C.N_PTS, rms=C.SMOOTH_RMS,
              cap_ref_y=C.CAP_REF_Y, cap_h=C.CAP_H, force_ext_y=C.FORCE_EXT_Y,
              round_r=C.ROUND_R, round_h=C.TOP_Z + C.ROUND_EPS, round_band=C.ROUND_BAND,
              seg_counts=C.SEG_COUNTS, seg_depth=C.SEG_DEPTH, rear_cut_z=C.REAR_CUT_Z, rear_lean=C.REAR_LEAN,
              rear_outer_lean=C.REAR_OUTER_LEAN, uturn=C.UTURN, s5=C.S5)
    log("U-turn field (3D ball opening)")
    sp["uturn_field"] = uturn_field(r16, sp, C.ROWFILL_Y, log)
    dense = {}
    log("sections (body / rear corner)")
    body_src = C.REAR_STATIONS + [y for y in C.MAIN_STATIONS if y >= C.SHARED_Y]
    st_body = station_loops(r16, body_src, sp, rowfill_from=C.ROWFILL_Y, log=log, dense=dense)
    st_body = extrapolate([st_body[1], st_body[0]], [C.REAR_EXTRAP_Y]) + st_body
    log("sections (handle: root morph, then r16 moved +%.1f)" % C.HANDLE_SHIFT)
    root = station_loops(r16, C.MORPH_YS, sp, rowfill_from=C.ROWFILL_Y, log=log)
    src = [y - C.HANDLE_SHIFT for y in C.MORPH_YS] + C.HANDLE_SRC
    moved = [(y + C.HANDLE_SHIFT, lp) for y, lp in station_loops(r16, src, sp, rowfill_from=C.ROWFILL_Y, log=log)]
    nm = len(C.MORPH_YS)
    st_hand = morph(root, moved[:nm], C.SHARED_Y, C.HANDLE_BLEND_T) + moved[nm:]
    st_hand += extrapolate(st_hand, C.HANDLE_EXTRAP)
    if abs(st_body[-1][0] - C.SHARED_Y) > 1e-9:
        raise RuntimeError("the body stations must end at the shared station")
    # the lofts END at the shared section (identical caps, no trim at the seam)
    body_loft = st_body
    hand_loft = [st_body[-1]] + st_hand
    if C.SEAM_GUIDE:
        # G1 seam (pass 1d): one guide station on each side, from a cubic spline through both sides' stations
        gb, gh = seam_guides(st_body[-C.SEAM_GUIDE_N:], st_hand[:C.SEAM_GUIDE_N], C.SHARED_Y, C.SEAM_GUIDE)
        body_loft = st_body[:-1] + [gb, st_body[-1]]
        hand_loft = [st_body[-1], gh] + st_hand
    log("stations: body %d (to %.1f), handle %d (from %.1f); tip plane y %.4f"
        % (len(body_loft), body_loft[-1][0], len(hand_loft), hand_loft[0][0], C.TIP_Y_NEW))
    log("sections (blend)")
    station_loops(r16, [y for y in C.BLEND_STATIONS if y not in dense], sp, rowfill_from=C.ROWFILL_Y,
                  log=log, dense=dense)
    bp = dict(z0=C.PLATE_Z0, x_s=C.BLEND_XS, x_h=C.BLEND_XH, x_a=C.BLEND_XA, z_t=C.BLEND_ZT, ext=C.BLEND_EXT,
              alpha=C.BLEND_ALPHA, grip_x=C.INNER_X)
    blend_pr = []
    for y in C.BLEND_STATIONS:
        pr = blend_profile(dense[y], bp)
        blend_pr.append((y, pr))
        log("  blend y %6.2f  underside z %.2f slope %.3f -> blend slope %.3f, margin under grip %.3f"
            % (y, pr["za"], pr["slope_grip"], pr["slope_blend"], pr["margin"]))
    blend_pr.append((C.BLEND_EXTRAP_Y, blend_pr[-1][1]))
    R["blend_min_margin"] = round(min(p["margin"] for _, p in blend_pr), 3)
    if R["blend_min_margin"] <= 0.0:
        raise RuntimeError("blend crosses the grip before x_a (margin %.3f)" % R["blend_min_margin"])
    if args.sections_only:
        return

    log("grip end")
    cutter = clip_cutter(C.CLIP_W, C.CLIP_PHI, C.CLIP_K, C.ROUND_R, C.CLIP_RF, C.TOP_Z + C.ROUND_EPS, C.FLOOR_Z)
    sc = C.SHARED_Y
    if C.SINGLE_LOFT:
        end, R["rim_r"], R["tip_roll"] = build_single(st_body + st_hand, C.TIP_Y_NEW, C.TOP_Z, C.PLATE_Y1, cutter,
                                                      C.RIM_RADII, (C.FLOOR_Z, 75.0, 55.0), C.TIP_ROLL, log)
        R["seam_union"] = "none (one loft)"
    else:
        # trim boxes stop 1 mm past the seam: the lofts' own end caps (one section) are the seam faces
        body, R["rim_r"] = build_body(body_loft, sc - 1.0, C.TOP_Z, C.PLATE_Y1, cutter, C.RIM_RADII,
                                      (C.FLOOR_Z, 75.0, 55.0), log, loft_opts=C.BODY_LOFT_OPTS)
        hand, R["tip_roll"] = build_handle(hand_loft, sc + 1.0, C.TOP_Z, C.TIP_Y_NEW, C.TIP_ROLL, log,
                                           loft_opts=C.HANDLE_LOFT_OPTS)
        end, R["seam_union"] = fuse_at_seam(body, hand, sc, log)
    R["seam_creases"] = checks.edge_creases(end, lambda c: abs(c.Y - sc) < 0.05 and c.X > 60, n=41)
    log("seam edges at y %.2f (centre, length, type, max / median crease deg): %s" % (sc, R["seam_creases"]))
    blend = build_blend(blend_pr, C.BLEND_XS, C.PLATE_Y1)
    log("blend loft valid, volume %.0f" % blend.volume)
    end = one_solid(end.fuse(blend), "grip end + blend")
    log("blend fused: valid")
    if args.grip_only:
        export_stl(end, args.grip_only, tolerance=0.002, angular_tolerance=0.05)
        log("grip end written to %s" % args.grip_only)
        return
    pocket = oval_cutter(C.CAP_XC, C.CAP_A, C.CAP_B, C.YC, C.POCKET_Y_BOTTOM, C.POCKET_Y_TOP, C.FLOOR_Z, C.TOP_Z + 10.0)
    end = one_solid(end.cut(pocket), "pocket cut")
    log("pocket cut: valid")

    plate = build_plate_half(C.BLEND_XS, C.PLATE2_X, C.PLATE2_Z0, C.PLATE_Y0, C.PLATE_Y1, C.PLATE_Z0, C.FLOOR_Z)
    half = one_solid(end.fuse(plate), "grip end + plate")
    log("plate fused: valid")
    if C.FRONT_R:
        # plate front face meeting the handle (radius from audit/p1/scripts/p1_post.py, subprocess trials)
        fx = [e for e in half.edges() if abs(e.center().Y - C.PLATE_Y0) < 0.4 and 63.0 < e.center().X < 70.0
              and e.center().Z < -9.0 and e.geom_type.name == "BSPLINE"]
        R["front_r_applied"], half = try_fillet(half, fx, [C.FRONT_R], "plate front junction", log)

    n = np.array(C.FINGER_N) / np.linalg.norm(C.FINGER_N)
    prof, info = finger_profile(C.LIP_U, C.LIP_TOP_Z, C.ROOT_Z, C.FINGER_T_ROOT, C.FINGER_T_TIP, C.LIP_OVERHANG,
                                C.LIP_LEAD_DEG, C.LIP_RET_DEG, C.LIP_FLAT, C.LIP_LAND, C.FINGER_INNER_SLOT,
                                C.FINGER_GAP, C.FINGER_ROOT_R)
    R["finger"] = {k: round(float(v), 4) for k, v in info.items()}
    pit = build_pit(C.FINGER_P, n, pit_profile(C.FINGER_W, C.FINGER_SLOT, C.FINGER_INNER_SLOT, C.FINGER_T_ROOT,
                                                C.FINGER_GAP, C.PIT_CORNER_R), C.ROOT_Z, C.TOP_Z + 10.0)
    if args.half_brep:
        export_brep(half, args.half_brep)
        log("half before the lip written to %s" % args.half_brep)
    half = one_solid(half.cut(pit), "pit cut")
    finger = one_solid(build_finger(C.FINGER_P, n, C.FINGER_W, prof), "finger")
    half = one_solid(half.fuse(finger), "finger union")
    log("lip: valid, half volume %.0f" % half.volume)

    full, _ = mirror_union(half)
    R["valid_full"] = valid(full)
    if not R["valid_full"]:
        raise RuntimeError("mirrored union not valid")
    log("mirrored union: valid, volume %.0f, faces %d" % (full.volume, len(full.faces())))

    for pth in (args.out_step, args.out_stl):
        Path(pth).parent.mkdir(parents=True, exist_ok=True)
    export_step(full, args.out_step)
    # 0.02 / 0.2 gave 28 mm triangles and a 0.37 mm chord error (review_spike.md, S4)
    export_stl(full, args.out_stl, tolerance=0.002, angular_tolerance=0.05)
    R["build_s"] = round(time.time() - t0, 1)
    log("exported %s, %s" % (args.out_step, args.out_stl))
    Path(args.results).parent.mkdir(parents=True, exist_ok=True)
    if args.no_gates:
        Path(args.results).write_text(json.dumps(R, indent=1, default=str))
        return

    m = trimesh.load(args.out_stl, force="mesh")
    R["topology"] = checks.topology(m)
    log("topology %s" % R["topology"])
    R["mirror_dev_max_rms"] = checks.mirror_deviation(m)
    log("mirror deviation max/rms %s" % (R["mirror_dev_max_rms"],))
    sy = C.SHARED_Y
    R["seam_creases_half"] = checks.edge_creases(half, lambda c: abs(c.Y - sy) < 0.05 and c.X > 60, n=41)
    log("seam edges on the half at y %.1f: %s" % (sy, R["seam_creases_half"]))
    R["seam_dihedral_stl"] = checks.band_dihedral(m, (60.0, 200.0, sy - 0.6, sy + 0.6))
    log("STL dihedral, y %.1f +- 0.6: %s" % (sy, R["seam_dihedral_stl"]))
    h = C.TOP_Z
    ut = (-46.0 + C.HANDLE_SHIFT, -38.0 + C.HANDLE_SHIFT)
    zones = {"flanks y%.0f..55" % ut[1]: lambda q: q[0] > 60 and ut[1] < q[1] < 55.0 and h - 1.6 < q[2] < h - 0.15,
             "U-turn y%.0f..%.0f" % ut: lambda q: q[0] > 60 and ut[0] < q[1] < ut[1] and h - 1.6 < q[2] < h - 0.15,
             "corner y55..66": lambda q: q[0] > 84 and 55.0 < q[1] < 66.0 and h - 1.6 < q[2] < h - 0.15,
             "rim crest x>84 y>62 z<-5": lambda q: q[0] > 84 and q[1] > 62.0 and q[2] < -5.0,
             "plate front x62..70 y<-10": lambda q: 62.0 < q[0] < 70.0 and -11.6 < q[1] < -10.0 and q[2] < -9.0}
    R["round_radius"] = {k: checks.round_radii(half, z) for k, z in zones.items()}
    for k, v in R["round_radius"].items():
        log("round radius %s: %s" % (k, v))
    R["top_edge_creases"] = checks.edge_creases(half, lambda c: abs(c.Z - h) < 0.02 and c.X > 60)
    log("top-face edges, crease: %s" % R["top_edge_creases"])
    R["handle_smooth"] = checks.handle_smoothness(m, y_lo=-63.0 + C.HANDLE_SHIFT)
    log("handle smoothness %s" % R["handle_smooth"])
    for name, bx in (("grip end x>60 y<55", (60.0, 200.0, -70.0, 55.0)), ("corner x>60 y>55", (60.0, 200.0, 55.0, 80.0))):
        R["sharp30 " + name] = checks.sharp_edges(m, bx)
        log("edges > 30 deg, %s: %s" % (name, R["sharp30 " + name]))
    outline = checks.flat_top_outline(m, h)
    s = C.HANDLE_SHIFT
    r16m = r16.copy()
    r16m.apply_translation([0.0, s, 0.0])
    root_y = -14.48
    reg_h = {"root morph y%.1f..%.1f" % (sy - C.HANDLE_BLEND_T, root_y): (0.0, 1e3, sy - C.HANDLE_BLEND_T, root_y),
             "middle y%.1f..-44" % (sy - C.HANDLE_BLEND_T): (0.0, 1e3, -44.0, sy - C.HANDLE_BLEND_T),
             "tip y%.2f..-44" % C.TIP_Y_NEW: (0.0, 1e3, C.TIP_Y_NEW - 0.01, -44.0)}
    reg_b = {"body/corner x>66 y>-12": (66.0, 1e3, -12.0, 80.0), "corner x>66 y>55": (66.0, 1e3, 55.0, 80.0)}
    for tag, b in (("dev_band_excluded", (outline, 4.0)), ("dev_band_included", None)):
        R[tag] = {"handle vs r16 moved +%.0f" % s: checks.deviation(m, r16m, reg_h, band=b),
                  "body vs r16": checks.deviation(m, r16, reg_b, band=b)}
        for grp, v in R[tag].items():
            for k, d in v.items():
                log("%s %s %-26s %s" % (tag[4:], grp, k, {t: (q["rms"], q["max"], q["max_at"]) for t, q in d.items()}))
    R["inner_flank_rate"] = {"transition y%.1f..%.1f" % (sy, sy - C.HANDLE_BLEND_T):
                             checks.inner_flank_rate(m, sy, sy - C.HANDLE_BLEND_T),
                             "moved y%.1f..-46" % (sy - C.HANDLE_BLEND_T):
                             checks.inner_flank_rate(m, sy - C.HANDLE_BLEND_T, -46.0)}
    log("inner flank rate (mm/mm, at y): %s" % R["inner_flank_rate"])
    prev = C.V2_DIR / "stl" / "VitaGripPS5_v2_p1c.stl"
    if prev.exists():
        R["vs_p1c"] = checks.deviation(m, trimesh.load(str(prev), force="mesh"),
                                       {"body y-12..55": (0.0, 1e3, -12.0, 55.0), "corner y55..80": (0.0, 1e3, 55.0, 80.0),
                                        "handle y<-13.5": (0.0, 1e3, -60.0, sy)})
        for k, d in R["vs_p1c"].items():
            log("vs p1c %-18s %s" % (k, {t: (q["rms"], q["max"], q["max_at"]) for t, q in d.items()}))
    R["total_s"] = round(time.time() - t0, 1)
    Path(args.results).write_text(json.dumps(R, indent=1, default=str))
    log("gates written to %s" % args.results)


if __name__ == "__main__":
    main()
