"""VitaGripPS5 v2 main (pass 2): the case's right grip end as B-rep (build123d), one loft rear face to tip (the
handle 16 mm shorter than r16, 15 mm root transition) through stations FITTED along y below y -3 (a smoothing
spline per matched point, evenly spaced stations), plate built in, upper and lower lips with pits, bottom opening,
mirrored; rear window and camera hole cut through the plate.

  timeout 300 python vita_grip_ps5_v2.py [--out-step P] [--out-stl P] [--results P] [--sections-only]
                                         [--half-brep P] [--grip-only P.stl] [--no-gates] [--off all|SWITCH,...]
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
        seam_guides, fit_along_y
    from vgps5_v2.shapes import one_solid, oval_cutter, valid, try_fillet, clip_cutter
    from vgps5_v2.parts.grip_end import build_body, build_handle, build_single, fuse_at_seam
    from vgps5_v2.parts.plate import build_plate_half, build_blend, front_round_cutter, corner_round_web
    from vgps5_v2.parts.lip import finger_profile, pit_profile, build_finger, build_pit
    from vgps5_v2.assemble import mirror_union
    from vgps5_v2.shapes import box, rounded_rect_prism, cylinder_z
    from vgps5_v2 import checks

    ap = argparse.ArgumentParser()
    ap.add_argument("--out-step", default=str(C.V2_DIR / "step" / "VitaGripPS5_v2_edge.step"))
    ap.add_argument("--out-stl", default=str(C.V2_DIR / "stl" / "VitaGripPS5_v2_edge.stl"))
    ap.add_argument("--results", default=str(C.V2_DIR / "audit" / "edge" / "edge_results.json"))
    ap.add_argument("--open-end-r", type=float, default=None, help="override OPEN_END_R (0 = pass s8)")
    ap.add_argument("--corner-round", type=float, default=None, help="override CORNER_ROUND (0 = pass front)")
    ap.add_argument("--off", default="", help="comma list of pass-2 switches to turn off, or 'all' (= pass corner)")
    ap.add_argument("--sections-only", action="store_true")
    ap.add_argument("--half-brep", default=None, help="write the half before the lip (BREP), for fillet searches")
    ap.add_argument("--no-gates", action="store_true")
    ap.add_argument("--grip-only", default=None, help="stop after the grip end + blend; write it as this STL")
    args = ap.parse_args()
    if args.corner_round is not None:
        C.CORNER_ROUND = args.corner_round
    if args.open_end_r is not None:
        C.OPEN_END_R = args.open_end_r
    p2_switches = ("LOWER_LIP_ON", "WINDOW_ON", "CAMERA_ON", "BOTTOM_OPEN_ON")
    for k in (p2_switches if args.off == "all" else [s for s in args.off.split(",") if s]):
        if k not in p2_switches:
            raise SystemExit("unknown switch %s" % k)
        setattr(C, k, False)

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
        stations = st_body + st_hand
        if C.FIT_ALONG_Y:
            stations, R["fit"] = fit_along_y(stations, C.FIT_Y0, C.FIT_RAMP, C.FIT_Y_TIP, C.FIT_TIP_RAMP,
                                             C.FIT_SPACING, C.FIT_SMOOTH)
            log("fitted along y (h %.2f): %s; stations now %d" % (C.FIT_SMOOTH, R["fit"], len(stations)))
        end, R["rim_r"], R["tip_roll"] = build_single(stations, C.TIP_Y_NEW, C.TOP_Z, C.PLATE_Y1, cutter,
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
    if C.FRONT_ROUND:
        # pass front (S2): the round is cut into the lone blend, before any fuse (no fillet on the fused half)
        cutter, info = front_round_cutter(blend, C.PLATE_Y0, C.FRONT_ROUND_X0, C.BLEND_XA + C.BLEND_EXT - 0.1,
                                          C.FRONT_ROUND, C.FRONT_ROUND_RAMP, cross=C.FRONT_ROUND_CROSS,
                                          start=C.FRONT_ROUND_START)
        v0 = blend.volume
        blend = one_solid(blend.cut(cutter), "plate blend, front round")
        R["front_round_sections"] = info
        R["front_round_top_z_max"] = max(q[4] for q in info)
        log("front round cut (x, r, zb, k, top z): %s ... %s; removed %.4f mm3; top z max %.4f (upper slab %.1f)"
            % (info[0], info[-1], v0 - blend.volume, R["front_round_top_z_max"], C.PLATE2_Z0))
    grip0 = end
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
    if C.CORNER_ROUND:
        # pass corner: rolling-ball round between the plate front (and the front round) and the grip, built from the
        # lone blend and grip end as a web solid and fused in (no fillet on the fused half)
        plane = box(50.0, 75.0, C.PLATE_Y0, 0.0, -10.5, -6.0)        # the plate front plane, past the floor
        web, info = corner_round_web([blend, plane], grip0, C.CORNER_ROUND, C.FLOOR_Z, C.CORNER_ROUND_Z_START,
                                     C.CORNER_ROUND_ALPHA_END, *C.CORNER_ROUND_GUESS, sink=C.CORNER_ROUND_SINK)
        R["corner_round_sections"] = info
        v0 = half.volume
        half = one_solid(half.fuse(web), "corner round web fused")
        log("corner round web: %d sections, first %s, last %s; web %.4f mm3, B-rep volume change %.4f mm3 (GProp, imprecise: t1 read -11.5 where the STL gained +0.33 per side)"
            % (len(info), info[0], info[-1], web.volume, half.volume - v0))
    if C.FRONT_R:
        # plate front face meeting the handle (radius from audit/p1/scripts/p1_post.py, subprocess trials)
        fx = [e for e in half.edges() if abs(e.center().Y - C.PLATE_Y0) < 0.4 and 63.0 < e.center().X < 70.0
              and e.center().Z < -9.0 and e.geom_type.name == "BSPLINE"]
        R["front_r_applied"], half = try_fillet(half, fx, [C.FRONT_R], "plate front junction", log)
    if C.BOTTOM_OPEN_ON:
        # pass 2: nothing above the floor in front of the pocket for x < OPEN_X_END (r16's bottom opening); the box
        # reaches into the pocket's air (y > POCKET_Y_BOTTOM) and starts on the floor plane
        oc = box(-1.0, C.OPEN_X_END, C.OPEN_Y_LO, C.POCKET_Y_BOTTOM + 1.0, C.FLOOR_Z, C.TOP_Z + 1.0)
        rm = half.intersect(oc)
        rms = rm.solids() if hasattr(rm, "solids") else [rm]
        R["bottom_open_removed"] = [(round(s.volume, 4), [round(v, 3) for v in tuple(s.bounding_box().min)],
                                     [round(v, 3) for v in tuple(s.bounding_box().max)]) for s in rms]
        half = one_solid(half.cut(oc), "bottom opening cut")
        log("bottom opening x < %.2f: removed %s" % (C.OPEN_X_END, R["bottom_open_removed"]))
        if C.OPEN_END_R:
            # pass edge: round the closed end's edge to the grip (the end face's edge that is on neither the floor
            # plane nor the pocket wall y POCKET_Y_BOTTOM)
            def on_end(e):
                b = e.bounding_box()
                return abs(b.min.X - C.OPEN_X_END) < 1e-3 and abs(b.max.X - C.OPEN_X_END) < 1e-3 and \
                    b.max.Y - b.min.Y > 0.01 and b.max.Z - b.min.Z > 0.01 and b.max.Y < 0.0
            ee = [e for e in half.edges() if on_end(e)]
            R["open_end_edges"] = [(round(e.length, 3), e.geom_type.name, [round(v, 3) for v in tuple(e.bounding_box().min)],
                                    [round(v, 3) for v in tuple(e.bounding_box().max)]) for e in ee]
            log("closed-end edge(s) to round: %s" % R["open_end_edges"])
            if len(ee) != 1:
                raise RuntimeError("expected one closed-end edge, found %d" % len(ee))
            radii = [C.OPEN_END_R] + [r for r in C.OPEN_END_R_FALLBACK if r < C.OPEN_END_R]
            R["open_end_r_applied"], half = try_fillet(half, ee, radii, "closed-end edge", log)
            if R["open_end_r_applied"] is None:
                raise RuntimeError("closed-end round failed at %s" % radii)

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
    if C.LOWER_LIP_ON:
        # pass 2: the lower finger, lip and pit, the upper ones' mirror about YC (r16: y_lo = 2 YC - y_up)
        n_lo = np.array(C.FINGER_N_LO) / np.linalg.norm(C.FINGER_N_LO)
        pit_lo = build_pit(C.FINGER_P_LO, n_lo, pit_profile(C.FINGER_W, C.FINGER_SLOT, C.FINGER_INNER_SLOT,
                                                            C.FINGER_T_ROOT, C.FINGER_GAP, C.PIT_CORNER_R),
                           C.ROOT_Z, C.TOP_Z + 10.0)
        half = one_solid(half.cut(pit_lo), "lower pit cut")
        half = one_solid(half.fuse(one_solid(build_finger(C.FINGER_P_LO, n_lo, C.FINGER_W, prof), "lower finger")),
                         "lower finger union")
        log("lower lip at (%.3f, %.3f) n (%.3f, %.3f): valid, half volume %.0f"
            % (C.FINGER_P_LO + tuple(n_lo) + (half.volume,)))

    full, _ = mirror_union(half)
    R["valid_full"] = valid(full)
    if not R["valid_full"]:
        raise RuntimeError("mirrored union not valid")
    log("mirrored union: valid, volume %.0f, faces %d" % (full.volume, len(full.faces())))
    if C.WINDOW_ON:
        win = rounded_rect_prism(0.0, C.WIN_Y0, C.WIN_Y1, C.WINDOW_W, C.WINDOW_R, C.HOLE_Z0, C.HOLE_Z1)
        full = one_solid(full.cut(win), "rear window cut")
        log("rear window %.2f x %.2f (y %.3f..%.3f) R %.1f: valid" % (C.WINDOW_W, C.WIN_Y1 - C.WIN_Y0, C.WIN_Y0,
                                                                      C.WIN_Y1, C.WINDOW_R))
    if C.CAMERA_ON:
        cam = cylinder_z(0.0, C.CAMERA_Y, C.CAMERA_HOLE_D / 2.0, C.HOLE_Z0, C.HOLE_Z1)
        full = one_solid(full.cut(cam), "camera hole cut")
        log("camera hole D %.1f at (0, %.3f): valid" % (C.CAMERA_HOLE_D, C.CAMERA_Y))
    R["valid_full"] = valid(full)
    R["switches"] = {k: getattr(C, k) for k in p2_switches}

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
    if C.FRONT_ROUND:
        # pass front (S2) gates: STL dihedral in the S2 box, the round's radius on the B-rep, change vs pass fit
        b6 = (C.FRONT_ROUND_X0, 70.0, -12.0, -10.4, -14.6, -12.6)
        R["front_dihedral"] = {"box x62..70": checks.box_dihedral(m, b6),
                               "box x62.25..70": checks.box_dihedral(m, (C.FRONT_ROUND_X0 + 0.25,) + b6[1:]),
                               "tangent line y-10.6..-9.6": checks.box_dihedral(m, b6[:2] + (-10.6, -9.6) + b6[4:])}
        zb6 = (C.FRONT_ROUND_X0, 70.0, -11.25, -9.8, -15.0, -12.4)
        zone = lambda q: zb6[0] < q[0] < zb6[1] and zb6[2] < q[1] < zb6[3] and q[2] < zb6[5]
        x_full = C.FRONT_ROUND_X0 + C.FRONT_ROUND_RAMP
        R["front_round_r"] = {"x62..70": checks.round_radii(half, zone, r_max=1.8, box6=zb6),
                              "x%.0f..69 (full radius)" % x_full: checks.round_radii(
                                  half, lambda q: zone(q) and x_full <= q[0] <= 69.0, r_max=1.8, box6=zb6)}
        ex = [(60.0, 72.0, -13.0, -9.0, -16.0, -10.0), (-72.0, -60.0, -13.0, -9.0, -16.0, -10.0)]
        fit_stl = C.V2_DIR / "stl" / "VitaGripPS5_v2_fit.stl"
        if fit_stl.exists():
            R["vs_fit"] = checks.change_vs(m, trimesh.load(str(fit_stl), force="mesh"),
                                           {"outside the S2 boxes": (ex, False), "inside the S2 boxes": (ex, True),
                                            "bar strip |x|<62": ([(-62.0, 62.0, -12.0, -8.5, -100.0, 100.0)], True)})
        R["front_round_r"]["x64..68"] = checks.round_radii(half, lambda q: zone(q) and 64.0 <= q[0] <= 68.0,
                                                           r_max=1.8, box6=zb6)
        for k in ("front_dihedral", "front_round_r", "vs_fit"):
            log("%s: %s" % (k, R.get(k)))
    R["max_z"] = round(float(m.bounds[1][2]), 5)
    if C.CORNER_ROUND:
        # pass corner gates: STL dihedral in the corner box (both sides), the web's radius on the B-rep, change vs
        # pass front outside the corner boxes
        cb = C.CORNER_BOX
        cbm = (-cb[1], -cb[0]) + tuple(cb[2:])
        # change box: up to z FLOOR_Z + 0.2, so it holds the web's top face on the floor plane (the dihedral box stops
        # at z -8.9, under the plate front's designed 90 deg top edge)
        cc = [tuple(b[:5]) + (C.FLOOR_Z + 0.2,) for b in (cb, cbm)]
        inb = lambda q: all(cb[2 * i] < q[i] < cb[2 * i + 1] for i in range(3))
        R["corner_dihedral"] = {"corner box": checks.box_dihedral(m, cb), "corner box (left)": checks.box_dihedral(m, cbm)}
        R["corner_round_r"] = {"in front of the plate (y < -11.22)": checks.round_radii(
                                   half, lambda q: inb(q) and q[1] < C.PLATE_Y0 - 0.02, r_max=1.8, box6=cb),
                               "corner box, r <= 1.3": checks.round_radii(half, inb, r_max=1.3, box6=cb)}
        front_stl = C.V2_DIR / "stl" / "VitaGripPS5_v2_front.stl"
        R["vs_front"] = checks.change_vs(m, trimesh.load(str(front_stl), force="mesh"),
                                         {"outside the corner boxes": (cc, False),
                                          "inside the corner boxes": (cc, True),
                                          "bar strip |x|<62": ([(-62.0, 62.0, -12.0, -8.5, -100.0, 100.0)], True)})
        for k in ("max_z", "corner_dihedral", "corner_round_r", "vs_front"):
            log("%s: %s" % (k, R.get(k)))
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
    # ring-line gate (pass fit): outer-flank turn between 1 mm chords along y, against r16 (its handle at y - 16
    # below the shared station: the same datum as the moved handle) + 1 deg
    zt = (-20.0, -10.0, 0.0, 5.0)
    R["flank_turn"] = checks.outer_flank_turn(m, -51.0, -5.0, zt)
    R["flank_turn_r16"] = checks.outer_flank_turn(r16, -51.0, -5.0, zt,
                                                  y_shift_map=lambda y: y if y >= sy else y - s)
    # the 15 mm root morph itself bends the flank (r16's own surface morphed the same way: up to 6.6 deg at z -20 /
    # -10 between 1 mm chords); in the morph the reference is the larger of r16 and this design floor
    fl = checks.outer_flank_turn(r16, sy - C.HANDLE_BLEND_T - 1.5, sy + 1.5, zt, morph=(sy, s, C.HANDLE_BLEND_T))
    ys_all = R["flank_turn"]["ys"]
    R["flank_turn_floor"] = dict(ys=ys_all, max=fl["max"], turn={k: [dict(zip(fl["ys"], v)).get(y) for y in ys_all]
                                                                 for k, v in fl["turn"].items()})
    R["flank_turn_vs_r16"] = checks.turn_vs_reference(R["flank_turn"], R["flank_turn_r16"], 1.0)
    R["flank_turn_vs_r16_or_floor"] = checks.turn_vs_reference(R["flank_turn"],
                                                               [R["flank_turn_r16"], R["flank_turn_floor"]], 1.0)
    log("outer-flank turn max (deg, y): %s; r16 %s; floor %s" % (R["flank_turn"]["max"], R["flank_turn_r16"]["max"],
                                                                 R["flank_turn_floor"]["max"]))
    for tag in ("flank_turn_vs_r16", "flank_turn_vs_r16_or_floor"):
        for k, v in R[tag].items():
            log("  %s + 1, %s: %s" % (tag[11:], k, v))
    for tag, prev, reg in (("vs_p1d", "VitaGripPS5_v2_p1d.stl",
                            {"body y>=5": (0.0, 1e3, 5.0, 80.0), "body y-3..5": (0.0, 1e3, -3.0, 5.0),
                             "handle y<-3": (0.0, 1e3, -60.0, -3.0)}),
                           ("vs_p1c", "VitaGripPS5_v2_p1c.stl",
                            {"body y-12..55": (0.0, 1e3, -12.0, 55.0), "corner y55..80": (0.0, 1e3, 55.0, 80.0)})):
        pth = C.V2_DIR / "stl" / prev
        if pth.exists():
            R[tag] = checks.deviation(m, trimesh.load(str(pth), force="mesh"), reg)
            for k, d in R[tag].items():
                log("%s %-18s %s" % (tag, k, {t: (q["rms"], q["max"], q["max_at"]) for t, q in d.items()}))
    # pass 2 gates: topology + genus, sky test, walls / back, lock check against r16, change against pass corner
    from vgps5_v2 import gates_p2
    corner_stl = C.V2_DIR / "stl" / "VitaGripPS5_v2_corner.stl"
    R["p2"] = gates_p2.run(m, r16, trimesh.load(str(corner_stl), force="mesh"), C, Path(args.results).parent,
                           args.out_stl, log)
    R["total_s"] = round(time.time() - t0, 1)
    Path(args.results).write_text(json.dumps(R, indent=1, default=str))
    log("gates written to %s" % args.results)


if __name__ == "__main__":
    main()
