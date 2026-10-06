"""Pass-2 gates on the exported STL: topology and genus, sky test, walls / back (tools/form_sweep.py), the lock check
against r16 and the change against pass corner."""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import trimesh

from . import checks

LIP_ZS = (9.30, 9.47, 9.80, 10.20, 11.00)
LIP_LOCK = (-0.00, -1.49, -1.30, -1.06, -0.60)


def mirror_boxes(bs):
    return bs + [(-b[1], -b[0]) + tuple(b[2:]) for b in bs]


def feature_boxes(C):
    """Change boxes of the pass-2 features (both sides)."""
    out = []
    if C.LOWER_LIP_ON:
        out += mirror_boxes([(86.0, 97.5, 10.0, 31.0, -16.0, 12.0)])
    if C.BOTTOM_OPEN_ON:
        out += mirror_boxes([(66.2, C.OPEN_X_END + 0.15, -14.0, -8.5, C.FLOOR_Z - 0.15, 9.0)])
    if C.WINDOW_ON:
        out.append((-C.WINDOW_W / 2 - 1.0, C.WINDOW_W / 2 + 1.0, C.WIN_Y0 - 1.0, C.WIN_Y1 + 1.0, -14.0, C.FLOOR_Z + 0.1))
    if C.CAMERA_ON:
        r = C.CAMERA_HOLE_D / 2 + 1.0
        out.append((-r, r, C.CAMERA_Y - r, C.CAMERA_Y + r, -14.0, C.FLOOR_Z + 0.1))
    return out


def end_wall_y(m, x0, tools_dir, x1=72.0, z0=-8.79, z1=11.39, dx=0.05, dz=0.25, y_pocket=-9.0,
               cols=(66.76, 67.0, 67.25, 67.41, 67.5, 68.0), sides=(1, -1), graze_tx=0.3, z_graze=8.4):
    """S8 gate (the method that found S8, r16's OPEN_WALL rule): the wall in y at fixed x in front of the pocket's bottom
    end. On each z section, along the line x = s * x (y -40..0.5), the material interval with the highest top below
    y 0.4 (front face -> pocket wall); an interval whose top is not at the pocket (top < y_pocket - 0.5) is no wall
    (open). x from x0 + 0.01 to x1, both sides. Grazing chords are excluded and reported: in the top round's band
    (z > z_graze = TOP_Z - ROUND_R) a chord whose front end lies on a face running within 17 deg of the line
    (|t_x| < graze_tx: the flank's top round, edge-on in plan; on p2 0.06 at x 68.51, z 10.71) measures a convex corner,
    not a wall. Below the band every chord counts. Per side: min (wall, x, z), the first x from which every wall >= 3.0
    / 3.15, and (wall, |t_x|) at z0 in the columns cols."""
    if str(tools_dir) not in sys.path:
        sys.path.insert(0, str(tools_dir))
    from form_sweep import zsection
    from shapely.geometry import LineString
    xs = np.round(np.arange(x0 + 0.01, x1 + 1e-9, dx), 4)
    zs = [float(z) for z in np.round(np.arange(z0, z1, dz), 3)] + [z1]
    secs = {z: zsection(m, z) for z in zs}

    from shapely.geometry import Point
    bnd = {z: [g for g in getattr(secs[z].boundary, "geoms", [secs[z].boundary])] for z in zs}

    def wall(z, x):
        """(wall, |t_x| of the boundary at the chord's front end): |t_x| < graze_tx means the front end lies on a face
        running nearly along the line (the flank's top round seen edge-on in plan), a grazing chord, not a wall."""
        g = LineString([(x, -40.0), (x, 0.5)]).intersection(secs[z])
        gs = [g] if g.geom_type == "LineString" else list(getattr(g, "geoms", []))
        ys = [np.array(q.coords)[:, 1] for q in gs if q.geom_type == "LineString" and q.length > 1e-6]
        ys = [q for q in ys if q.max() < 0.4]
        if not ys:
            return None
        q = max(ys, key=lambda a: a.max())
        if q.max() < y_pocket - 0.5:
            return None
        p = Point(x, q.min())
        b = min(bnd[z], key=lambda L: L.distance(p))
        d = b.project(p)
        t = np.subtract(b.interpolate(d + 0.05).coords[0], b.interpolate(max(d - 0.05, 0.0)).coords[0])
        return float(q.max() - q.min()), float(abs(t[0]) / max(np.hypot(*t), 1e-12))

    out = {}
    for s in sides:
        W = np.full((len(zs), len(xs)), np.nan)
        Wg = np.full((len(zs), len(xs)), np.nan)          # grazing chords (excluded from the gate, reported)
        for i, z in enumerate(zs):
            for j, x in enumerate(xs):
                w = wall(z, s * x)
                if w is not None:
                    (Wg if (w[1] < graze_tx and z > z_graze) else W)[i, j] = w[0]
        i, j = np.unravel_index(np.nanargmin(W), W.shape)
        colmin = np.nanmin(np.where(np.isnan(W), np.inf, W), axis=0)
        if np.isfinite(Wg).any():
            gi, gj = np.unravel_index(np.nanargmin(Wg), Wg.shape)
            graze = dict(n=int(np.isfinite(Wg).sum()), min=(round(float(Wg[gi, gj]), 4), float(xs[gj]), zs[gi]),
                         z_lowest=min(zs[k] for k in range(len(zs)) if np.isfinite(Wg[k]).any()))
        else:
            graze = dict(n=0)
        exact = {}
        for c in cols:
            w = wall(zs[0], s * c) if c > x0 else None
            exact["%.2f" % c] = None if w is None else (round(w[0], 3), round(w[1], 2))

        def first_ok(t):
            bad = np.flatnonzero(colmin < t)
            return float(xs[0]) if not len(bad) else (float(xs[bad[-1] + 1]) if bad[-1] + 1 < len(xs) else None)
        out["R" if s > 0 else "L"] = dict(
            min=(round(float(W[i, j]), 4), float(xs[j]), zs[i]), first_x_3p0=first_ok(3.0), first_x_3p15=first_ok(3.15),
            at_z0_wall_tx=exact, n_open=int((np.isnan(W) & np.isnan(Wg)).sum()), n=int(W.size), grazing=graze)
    out["passes_3p0"] = all(out[k]["min"][0] >= 3.0 for k in ("R", "L") if k in out)
    return out


def run(m, r16, corner, C, out_dir, stl_path, log):
    G = {}
    # S8 gate: wall in y at fixed x in front of the pocket's bottom end, x OPEN_X_END..72, z -8.8..11.4, both sides
    G["end_wall_y"] = end_wall_y(m, C.OPEN_X_END, C.PROJECT_DIR.parents[1] / "tools", y_pocket=C.POCKET_Y_BOTTOM,
                                 z_graze=C.TOP_Z - C.ROUND_R)
    log("p2 end wall in y at fixed x (x %.2f..72, z -8.79..11.39; min (t, x, z), first x >= 3.0 / 3.15): %s"
        % (C.OPEN_X_END, G["end_wall_y"]))
    p2_stl = C.V2_DIR / "stl" / "VitaGripPS5_v2_p2.stl"
    if p2_stl.exists() and p2_stl.resolve() != Path(stl_path).resolve():
        bx = mirror_boxes([(66.0, 68.5, -16.0, -8.5, -9.0, 11.5)])
        G["vs_p2"] = checks.change_vs(m, trimesh.load(str(p2_stl), force="mesh"),
                                      {"outside the s8 boxes": (bx, False), "inside the s8 boxes": (bx, True)})
        log("change vs p2: %s" % G["vs_p2"])
    G["topology"] = checks.topology_p2(m)
    log("p2 topology %s" % G["topology"])

    # sky test over the new pits, the bottom opening, the window edge and the camera hole
    sky = mirror_boxes([(86.5, 97.0, 10.5, 30.0, -12.5, 11.0), (64.0, 68.0, -14.0, -8.6, -8.6, 10.6)])
    names = ["pit R lower", "opening R", "pit L lower", "opening L"]
    sky_boxes = dict(zip(names, sky))
    sky_boxes["window edge x40..56.5"] = (40.0, 56.5, 1.5, 61.5, -13.0, -9.0)
    sky_boxes["camera"] = (-7.5, 7.5, 61.5, 74.5, -13.0, -9.0)
    sky_boxes["control: pit R upper (pass corner)"] = (86.5, 97.0, 2 * C.YC - 30.0, 2 * C.YC - 10.5, -12.5, 11.0)
    G["sky"] = checks.sealed_air(m, sky_boxes)
    for k, v in G["sky"].items():
        log("p2 sky test %s: %s" % (k, v))

    # walls and back: tools/form_sweep.py (r16's pocket, pit outlines, window / camera exclusions)
    sw = out_dir / "sweep"
    tool = C.PROJECT_DIR.parents[1] / "tools" / "form_sweep.py"
    regions = C.PROJECT_DIR / "audit" / "regions.json"
    p = subprocess.run([sys.executable, str(tool), str(stl_path), "--regions", str(regions), "--out", str(sw),
                        "--tag", "p2", "--stages", "hf,walls"], capture_output=True, text=True, timeout=600)
    (sw / "sweep_p2.log").write_text(p.stdout + p.stderr)
    try:
        S = json.loads((sw / "sweep_p2.json").read_text(encoding="utf-8"))
        back = [v for k, v in S["reports"].items() if k.startswith("BACK")][0]["regions"]
        G["back_min"] = {k: (-v["max"], v["at"]) for k, v in back.items()}
        # regions.json's wall levels run to z 13.5 (above this part's top, 11.4: empty sections read 0.15)
        G["walls"] = {z: row for z, row in S["walls"].items() if float(z) <= C.TOP_Z}
        G["pit_pads"] = S.get("pit_pads")
        wmin = min((v, z, k) for z, row in G["walls"].items() for k, v in row.items())
        G["walls_min"] = wmin
        log("p2 back min per region: %s" % G["back_min"])
        W = G["walls"]
        G["pit_walls_z0_10.2"] = {k: (min(W[z][k] for z in W if 0.0 <= float(z) <= 10.2),
                                      max(W[z][k] for z in W if 0.0 <= float(z) <= 10.2))
                                  for k in W["0.0"] if k.startswith("pit")}
        log("p2 walls min (z <= %.1f) %s; pit walls z 0..10.2 (min, max): %s" % (C.TOP_Z, wmin, G["pit_walls_z0_10.2"]))
    except Exception as ex:
        G["sweep_error"] = "%s; exit %s; %s" % (ex, p.returncode, p.stderr[-400:])
        log("p2 sweep failed: %s" % G["sweep_error"])

    # lock check against r16
    cfg = json.loads(regions.read_text(encoding="utf-8"))
    n_up = np.array(C.FINGER_N) / np.linalg.norm(C.FINGER_N)
    n_lo = np.array(C.FINGER_N_LO) / np.linalg.norm(C.FINGER_N_LO)
    fv = [(C.FINGER_P, n_up), (C.FINGER_P_LO, n_lo)]
    fv += [((-p[0], p[1]), n * [-1.0, 1.0]) for p, n in fv]
    fr = [cfg["fingers"][2], cfg["fingers"][3], cfg["fingers"][0], cfg["fingers"][1]]     # R up, R lo, L up, L lo
    fr = [(p, n) for p, (_, n) in zip(fr, fv)]
    L = dict(lock=dict(zip(["%.2f" % z for z in LIP_ZS], LIP_LOCK)),
             v2=checks.lip_u(m, fv, LIP_ZS), r16=checks.lip_u(r16, fr, LIP_ZS))
    L["max_abs_v2_minus_r16"] = round(max(abs(a["u"][k] - b["u"][k]) for a, b in zip(L["v2"], L["r16"])
                                          for k in a["u"] if a["u"][k] is not None and b["u"][k] is not None), 4)
    G["lock_lip_u"] = L
    log("p2 lock lip u (R up, R lo, L up, L lo): v2 %s | r16 %s | max |v2 - r16| %.4f"
        % ([list(a["u"].values()) for a in L["v2"]], [list(b["u"].values()) for b in L["r16"]],
           L["max_abs_v2_minus_r16"]))

    fing = np.array(cfg["fingers"])
    keep = lambda q: (abs(q[0]) > C.OPEN_X_END + 0.2 or q[1] > C.POCKET_Y_BOTTOM + 0.3) and \
        np.min(np.hypot(*(fing - q).T)) > cfg["walls"]["finger_clear"]
    G["lock_pocket_wall"] = checks.pocket_wall_dev([r16, m], cfg["pocket"], (-5.0, 0.0, 5.0), keep)
    log("p2 lock pocket walls (r16 outline points, r16 / v2): %s" % G["lock_pocket_wall"])
    import shapely
    from shapely.geometry import Polygon, Point, box as sbox
    from shapely.ops import unary_union
    xs, ys = np.meshgrid(np.arange(-100.0, 100.0, 1.0) + 0.013, np.arange(-9.0, 76.0, 1.0) + 0.029)
    pts = np.c_[xs.ravel(), ys.ravel()]
    inner = Polygon(cfg["pocket"]).buffer(-1.5)
    ex = unary_union([sbox(-C.WINDOW_W / 2, C.WIN_Y0, C.WINDOW_W / 2, C.WIN_Y1).buffer(1.0),
                      Point(0.0, C.CAMERA_Y).buffer(C.CAMERA_HOLE_D / 2 + 1.0)]
                     + [Polygon(q).buffer(1.0) for q in cfg["pits"]])
    sel = shapely.contains_xy(inner, pts[:, 0], pts[:, 1]) & ~shapely.contains_xy(ex, pts[:, 0], pts[:, 1])
    G["lock_floor"] = {"v2": checks.floor_check(m, pts[sel], C.FLOOR_Z), "r16": checks.floor_check(r16, pts[sel], C.FLOOR_Z)}
    log("p2 lock floor z %.2f: %s" % (C.FLOOR_Z, G["lock_floor"]))
    near = {"window": (0.0, 0.5 * (C.WIN_Y0 + C.WIN_Y1), 5.0), "camera": (0.0, C.CAMERA_Y, 3.0)}
    G["lock_holes"] = {"z%.1f" % z: checks.hole_lock(m, r16, z, near) for z in (-12.0, -11.0, -10.0)}
    log("p2 lock holes vs r16: %s" % G["lock_holes"])
    G["lock_bar_strip"] = checks.box_dev(m, r16, (-62.0, 62.0, -12.0, -8.5, -100.0, 100.0))
    log("p2 lock bar strip |x|<62 y -12..-8.5 (v2 -> r16, r16 -> v2): %s" % G["lock_bar_strip"])

    # bottom opening against r16 and pass corner
    zs = (-8.7, -8.5, -8.0, -6.0, -3.0, 0.0, 3.0, 6.0, 9.0, 11.0)
    G["opening"] = {t: checks.opening_table(mm, zs, wall_x=C.OPEN_X_END + 0.25)
                    for t, mm in (("v2", m), ("r16", r16), ("corner", corner))}
    for t, v in G["opening"].items():
        log("p2 opening %-6s %s" % (t, {k: tuple(r.values()) for k, r in v.items()}))

    # change against pass corner outside the new features' boxes
    fb = feature_boxes(C)
    G["vs_corner"] = checks.change_vs(m, corner, {"outside the p2 feature boxes": (fb, False),
                                                   "inside the p2 feature boxes": (fb, True)})
    log("p2 change vs corner: %s" % G["vs_corner"])
    return G
