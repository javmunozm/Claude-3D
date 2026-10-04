"""Whole-part form sweep of a mesh, driven by a project's audit/regions.json.

Replaces the per-round copies of v_sweep.py and of rv_review.py's diff stage
that every VitaGripPS5 review copied into its own round and retargeted by hand
(in r11 a missed retarget overwrote two r10 logs). Same measurements and the
same report lines as v_sweep.py; the project's geometry (pocket, pits,
fingers, cut-outs, region rules) comes from regions.json, not from the macro.

Writes to --out:
  chk_<tag>_cache.npz   height fields zmin / zmax (reused only for the same mesh)
  chk_<tag>_fields.npz  surface fields (dev, turn, non-convexity, back thickness)
  chk_<tag>_ysec.npz    Y-section fields (plan outline, flank radius)
  sweep_<tag>.json      the per-region summary, and the regression components
                        against --baseline
With --baseline <sweep_<tag>.json of an earlier mesh>, also reports what got
worse: per-region height changes and NEW/WORSE components (the regression count).

Usage:
  python tools/form_sweep.py <mesh.stl> --regions <project>/audit/regions.json \
      --out <dir> --tag <name> [--baseline <dir>/sweep_<tag>.json] [--stages all|hf,ys,edges,walls,sym]
"""
import argparse
import hashlib
import json
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import shapely
import trimesh
from scipy import ndimage
from scipy.spatial import cKDTree
from shapely.geometry import Point, Polygon, box as sbox
from shapely.ops import unary_union

T0 = time.time()
SUMMARY = {"reports": {}}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def classify(x, y, rules):
    """Region name per point: the first rule whose conditions all hold, plus -R (x > 0) or -L."""
    x = np.atleast_1d(np.asarray(x, dtype=float))
    y = np.atleast_1d(np.asarray(y, dtype=float))
    var = {"x": x, "y": y, "ax": np.abs(x)}
    names = np.full(x.shape, "", dtype=object)
    todo = np.ones(x.shape, dtype=bool)
    for rule in rules:
        k = todo.copy()
        for key, val in rule.items():
            if key == "name":
                continue
            v, op = key.rsplit("_", 1)
            k &= {"lt": var[v] < val, "le": var[v] <= val, "gt": var[v] > val, "ge": var[v] >= val}[op]
        names[k] = rule["name"]
        todo &= ~k
    side = np.where(x > 0, "-R", "-L")
    return np.array([a + b for a, b in zip(names, side)])


def gauss_nan(Z, sig):
    ok = np.isfinite(Z)
    a = ndimage.gaussian_filter(np.where(ok, Z, 0.0), sig, mode="nearest")
    b = ndimage.gaussian_filter(ok.astype(float), sig, mode="nearest")
    return np.where(ok, a / np.maximum(b, 1e-9), np.nan)


def report(title, X, Y, V, Zs=None, thr=None, sign=1):
    """Per-region max of sign*V (flat arrays); printed as v_sweep.py printed it, and kept for the JSON."""
    ok = np.isfinite(V)
    X, Y, V = X[ok], Y[ok], V[ok] * sign
    Zs = None if Zs is None else Zs[ok]
    regs = classify(X, Y, RULES)
    out, rows = [], {}
    for r in sorted(set(regs)):
        k = np.flatnonzero(regs == r)
        i = k[np.argmax(V[k])]
        nover = int((V[k] > thr).sum()) if thr is not None else -1
        out.append("%-15s %6.2f @(%6.1f,%6.1f%s) n>thr %d" % (r, V[i], X[i], Y[i], "" if Zs is None else ",%5.1f" % Zs[i], nover))
        rows[r] = {"max": round(float(V[i]), 4), "at": [round(float(X[i]), 2), round(float(Y[i]), 2)]
                   + ([] if Zs is None else [round(float(Zs[i]), 2)]), "n_over": nover}
    print("--- %s (thr %s)" % (title, thr))
    for o in out:
        print("   " + o)
    SUMMARY["reports"][title] = {"thr": thr, "sign": sign, "regions": rows}


def hfield(mesh, xs, ys):
    """zmin / zmax of the mesh over an (x, y) grid, from X-plane sections."""
    zmin = np.full((len(xs), len(ys)), np.nan)
    zmax = np.full((len(xs), len(ys)), np.nan)
    dy = ys[1] - ys[0]
    for i, x in enumerate(xs):
        seg = trimesh.intersections.mesh_plane(mesh, [1, 0, 0], [x, 0, 0])
        if len(seg) == 0:
            continue
        y0, z0, y1, z1 = seg[:, 0, 1], seg[:, 0, 2], seg[:, 1, 1], seg[:, 1, 2]
        lo, hi = np.minimum(y0, y1), np.maximum(y0, y1)
        j0 = np.ceil((lo - ys[0]) / dy).astype(int)
        j1 = np.floor((hi - ys[0]) / dy).astype(int)
        j0 = np.clip(j0, 0, len(ys))
        j1 = np.clip(j1, -1, len(ys) - 1)
        cnt = np.maximum(j1 - j0 + 1, 0)
        if cnt.sum() == 0:
            continue
        rep = np.repeat(np.arange(len(seg)), cnt)
        off = np.arange(cnt.sum()) - np.repeat(np.cumsum(cnt) - cnt, cnt)
        jj = j0[rep] + off
        den = (y1 - y0)[rep]
        t = np.where(np.abs(den) > 1e-12, (ys[jj] - y0[rep]) / np.where(np.abs(den) > 1e-12, den, 1), 0.0)
        z = z0[rep] + t * (z1 - z0)[rep]
        a2 = np.full(len(ys), np.inf)
        b2 = np.full(len(ys), -np.inf)
        np.minimum.at(a2, jj, z)
        np.maximum.at(b2, jj, z)
        zmin[i] = np.where(np.isfinite(a2), a2, np.nan)
        zmax[i] = np.where(np.isfinite(b2), b2, np.nan)
    return zmin, zmax


def zsection(mesh, z):
    """The mesh's cross-section at height z, as one shapely geometry (from the VitaGripPS5 macro)."""
    s = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if s is None:
        return Polygon()
    T = np.eye(4)
    T[2, 3] = -z
    pl, _ = s.to_planar(to_2D=T, check=False)
    return unary_union([p for p in pl.polygons_full if p is not None and p.area > 0])


def surf_metrics(Z, name, mask_extra, X, Y, G, thr_bump, thr_turn):
    ok = np.isfinite(Z)
    interior = ndimage.binary_erosion(ok, iterations=6)          # 3 mm from any nan edge
    gx, gy = np.gradient(np.where(ok, Z, 0.0), G)
    slope = np.hypot(gx, gy)
    mk = interior & (slope < 1.0) & mask_extra
    dev = Z - gauss_nan(Z, 3.0 / G)                               # bumps: deviation from gaussian sigma 3 mm
    dev = np.where(mk, dev, np.nan)
    under = name.startswith("UNDER")
    report(name + " lump  (z below smooth, mm; underside: lump=bulge out)", X.ravel(), Y.ravel(),
           (-dev if under else dev).ravel(), thr=thr_bump)
    report(name + " hollow (mm)", X.ravel(), Y.ravel(), (dev if under else -dev).ravel(), thr=thr_bump)
    w = int(2.0 / G)                                             # crease: slopes fitted 2 mm either side
    turn = np.full(Z.shape, np.nan)
    for axis in (0, 1):
        Zs = np.moveaxis(np.where(ok, Z, np.nan), axis, 0)
        before = (Zs[w:-w] - Zs[:-2 * w]) / (w * G)
        after = (Zs[2 * w:] - Zs[w:-w]) / (w * G)
        t = np.abs(np.degrees(np.arctan(after) - np.arctan(before)))
        full = np.full(Zs.shape, np.nan)
        full[w:-w] = t
        turn = np.fmax(turn, np.moveaxis(full, 0, axis))
    turn = np.where(mk, turn, np.nan)
    report(name + " crease turn (deg, 2mm|2mm)", X.ravel(), Y.ravel(), turn.ravel(), thr=thr_turn)
    return dev, turn, mk


def flank_band(YY, TH, Rr, fl):
    thd = np.degrees(TH)[None] + 0 * Rr
    return (YY < fl["all_round_y_lt"]) | ((thd > fl["theta_deg"][0]) & (thd < fl["theta_deg"][1]))


def new_components(vb, vn, thr, delta, Xg, Yg, Zg=None, title="", n=8, tags=("base", "new")):
    """Cells where new > thr and new exceeds base by delta (or base missing); 8-connected components of >= 3 cells."""
    ab = np.nan_to_num(vb, nan=-1e9)
    msk = np.nan_to_num(vn, nan=-1e9) > thr
    msk &= (np.nan_to_num(vn, nan=-1e9) > ab + delta)
    lab, k = ndimage.label(msk, structure=np.ones((3, 3)))
    rows = []
    for i in range(1, k + 1):
        w = lab == i
        if w.sum() < 3:
            continue
        j = np.nanargmax(np.where(w, vn, np.nan))
        jj = np.unravel_index(j, vn.shape)
        rows.append((vn[jj], vb[jj], w.sum(), Xg[w].min(), Xg[w].max(), Yg[w].min(), Yg[w].max(),
                     np.nan if Zg is None else Zg[jj], classify(Xg[jj], Yg[jj], RULES)[0]))
    rows.sort(key=lambda r: -r[0])
    print("--- NEW/WORSE %s (thr %s, worse by > %s): %d comps" % (title, thr, delta, len(rows)))
    for r in rows[:n]:
        print("   %s %6.2f (%s %6.2f) cells %4d x %6.1f..%6.1f y %6.1f..%6.1f z %6.1f %s" % (tags[1], r[0], tags[0], *r[1:]))
    SUMMARY.setdefault("regressions", {})[title] = [
        {"value": round(float(r[0]), 3), "baseline": round(float(r[1]), 3), "cells": int(r[2]),
         "x": [round(float(r[3]), 1), round(float(r[4]), 1)], "y": [round(float(r[5]), 1), round(float(r[6]), 1)],
         "z": None if not np.isfinite(r[7]) else round(float(r[7]), 1), "region": r[8]} for r in rows]


def main():
    global RULES
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("mesh")
    ap.add_argument("--regions", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--baseline", default=None)
    ap.add_argument("--stages", default="all")
    a = ap.parse_args()
    cfg = json.loads(Path(a.regions).read_text(encoding="utf-8"))
    RULES = cfg["regions"]
    th = cfg["thresholds"]
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    stages = set(a.stages.split(","))
    run = lambda s: "all" in stages or s in stages  # noqa: E731
    files = {k: str(out / ("chk_%s_%s.npz" % (a.tag, k))) for k in ("cache", "fields", "ysec")}
    digest = sha256(a.mesh)
    js = out / ("sweep_%s.json" % a.tag)
    try:  # a partial run (--stages) adds to the summary of the same mesh instead of replacing it
        old = json.loads(js.read_text(encoding="utf-8"))
        if old.get("sha256") == digest:
            SUMMARY.update(old)
    except Exception:
        pass
    SUMMARY.update(mesh=str(Path(a.mesh).resolve()), sha256=digest, tag=a.tag, regions=str(Path(a.regions).resolve()),
                   created=time.strftime("%Y-%m-%d %H:%M:%S"), files=files)

    m = trimesh.load(a.mesh)
    print("mesh faces %d watertight %s euler %d extent %s" % (len(m.faces), m.is_watertight, m.euler_number,
                                                              np.round(m.extents, 2).tolist()))
    SUMMARY["mesh_info"] = {"faces": int(len(m.faces)), "watertight": bool(m.is_watertight),
                            "euler": int(m.euler_number), "extent": np.round(m.extents, 3).tolist()}
    P = np.array(cfg["pocket"])
    oval = Polygon(P)
    R0 = oval.buffer(cfg["wall"], resolution=64)
    pit_fps = [Polygon(q) for q in cfg["pits"]]
    fingers = [np.array(p) for p in cfg["fingers"]]
    Y1, YC = cfg["y1"], cfg["yc"]
    print("Y1 %.2f; pits at %s" % (Y1, [np.round(p, 1).tolist() for p in fingers]))

    gr = cfg["grid"]
    G = gr["step"]
    xs = np.arange(gr["x"][0], gr["x"][1] + 0.001, G) + gr["offset"][0]
    ys = np.arange(gr["y"][0], gr["y"][1] + 0.001, G) + gr["offset"][1]
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    zmin = zmax = None
    try:
        c = np.load(files["cache"])
        if str(c["sha256"]) == digest:
            zmin, zmax = c["zmin"], c["zmax"]
    except Exception:
        pass
    if zmin is None:
        zmin, zmax = hfield(m, xs, ys)
        np.savez(files["cache"], zmin=zmin, zmax=zmax, sha256=digest)
    print("height field %.0fs" % (time.time() - T0))
    inPocket = shapely.contains_xy(oval.buffer(-0.6), X.ravel(), Y.ravel()).reshape(X.shape)
    inR0 = shapely.contains_xy(R0.buffer(1.0), X.ravel(), Y.ravel()).reshape(X.shape)

    if run("hf"):
        devU, turnU, mkU = surf_metrics(zmin, "UNDER", ~inPocket | True, X, Y, G, th["bump"], th["turn"])
        devT, turnT, mkT = surf_metrics(zmax, "TOP", ~inR0, X, Y, G, th["bump"], th["turn"])
        hd = np.full(zmin.shape, np.nan)                         # convexity of each column (lower hull), y >= -14
        for i in range(len(xs)):
            v = np.isfinite(zmin[i]) & (ys > -14)
            edges = np.flatnonzero(np.diff(np.concatenate([[0], v.astype(int), [0]])))
            for s, e in zip(edges[::2], edges[1::2]):
                if e - s < 10:
                    continue
                yy, zz = ys[s:e], zmin[i, s:e]
                hx, hy = [], []
                for p_, q_ in zip(yy, zz):
                    while len(hx) >= 2 and (hx[-1] - hx[-2]) * (q_ - hy[-2]) - (hy[-1] - hy[-2]) * (p_ - hx[-2]) <= 0:
                        hx.pop()
                        hy.pop()
                    hx.append(p_)
                    hy.append(q_)
                hd[i, s:e] = zz - np.interp(yy, hx, hy)
        hd = np.where(mkU, hd, np.nan)
        report("UNDER column non-convexity (z above lower hull, mm)", X.ravel(), Y.ravel(), hd.ravel(), thr=th["bump"])
        bk = cfg["back"]                                          # back wall under the pocket
        ex = [q.buffer(bk["pit_buffer"]) for q in pit_fps]
        for e in bk["exclude"]:
            ex.append(sbox(*e["box"]).buffer(e["buffer"]) if "box" in e else Point(*e["circle"]).buffer(e["r"]))
        ex = unary_union(ex)
        kk = inPocket & ~shapely.contains_xy(ex, X.ravel(), Y.ravel()).reshape(X.shape)
        bt = np.where(kk, bk["floor_z"] - zmin, np.nan)
        report("BACK thickness under pocket (min; thr %s)" % th["back"], X.ravel(), Y.ravel(), bt.ravel(),
               thr=-(th["back"] - 0.01), sign=-1)
        SUMMARY["pit_pads"] = []
        for q, p in zip(pit_fps, fingers):
            k2 = shapely.contains_xy(q, X.ravel(), Y.ravel()).reshape(X.shape)
            pad = bk["pit_root_z"] - np.nanmax(zmin[k2])
            print("   under pit at %s: zmin max %.2f -> pad below pit bottom %.2f (need 3.0)"
                  % (np.round(p, 1).tolist(), np.nanmax(zmin[k2]), pad))
            SUMMARY["pit_pads"].append({"pit": np.round(p, 1).tolist(), "pad": round(float(pad), 3)})
        np.savez(files["fields"], devU=devU, turnU=turnU, devT=devT, turnT=turnT, hd=hd, bt=bt)
        print("hf metrics %.0fs" % (time.time() - T0))

    sc = cfg["sections"]
    yS = np.arange(sc["y"][0], sc["y"][1], sc["step"]) + sc["offset"]
    TH = np.radians(np.arange(-180, 180, 2.0))
    side = sc["side_ax_gt"]
    if run("ys"):
        xout = np.full((2, len(yS)), np.nan)
        Rf = np.full((2, len(yS), len(TH)), np.nan)
        cen = np.full((2, len(yS), 2), np.nan)
        segs_all = []
        for j, y in enumerate(yS):
            seg = trimesh.intersections.mesh_plane(m, [0, 1, 0], [0, y, 0])
            segs_all.append(seg)
            for si, s in enumerate((-1, 1)):
                k = (s * seg[:, :, 0] > side).all(axis=1)
                if k.sum() < 4:
                    continue
                q = seg[k][:, :, [0, 2]]
                xout[si, j] = (s * q[:, :, 0]).max()
                hull = shapely.MultiPoint(q.reshape(-1, 2)).convex_hull
                cen[si, j] = [hull.centroid.x, hull.centroid.y]
        for si in range(2):
            for d in range(2):
                v = cen[si, :, d]
                okc = np.isfinite(v)
                cen[si, okc, d] = ndimage.gaussian_filter1d(v[okc], 8.0, mode="nearest")
        for j, y in enumerate(yS):
            seg = segs_all[j]
            for si, s in enumerate((-1, 1)):
                if not np.isfinite(cen[si, j, 0]):
                    continue
                k = (s * seg[:, :, 0] > side).all(axis=1)
                q = seg[k][:, :, [0, 2]]
                cx, cz = cen[si, j]
                dx = s * (q[:, :, 0] - cx)
                dz = q[:, :, 1] - cz
                thv = np.arctan2(dz, dx)
                r = np.hypot(dx, dz)
                ta, tb = thv[:, 0], thv[:, 1]
                okk = np.abs(ta - tb) < np.pi
                ta, tb, ra, rb = ta[okk], tb[okk], r[okk, 0], r[okk, 1]
                for ti, t in enumerate(TH):
                    c_ = (np.minimum(ta, tb) <= t) & (t < np.maximum(ta, tb))
                    if not c_.any():
                        continue
                    f = (t - ta[c_]) / (tb[c_] - ta[c_])
                    Rf[si, j, ti] = (ra[c_] + f * (rb[c_] - ra[c_])).max()
        np.savez(files["ysec"], xout=xout, Rf=Rf, cen=cen, yS=yS, TH=TH)
        print("y-sections %.0fs" % (time.time() - T0))
        print("--- PLAN outline x_out(y): dev from gaussian sigma 2 mm, and max 0.5 mm step")
        SUMMARY["plan"] = {}
        for si, nm in enumerate("LR"):
            v = xout[si]
            dv = v - gauss_nan(v, 4.0)
            st = np.abs(np.diff(v))
            for lo, hi, rn in cfg["plan_bands"]:
                kk = (yS >= lo) & (yS < hi)
                kd = kk[1:] & kk[:-1]
                i = np.nanargmax(np.abs(np.where(kk, dv, np.nan)))
                i2 = np.nanargmax(np.where(kd, st, np.nan))
                print("   %s %-7s max|dev| %.2f @y %.1f | max step %.2f @y %.1f (x %.1f->%.1f)"
                      % (nm, rn, abs(dv[i]), yS[i], st[i2], yS[i2], v[i2], v[i2 + 1]))
                SUMMARY["plan"]["%s %s" % (nm, rn)] = {"max_dev": round(float(abs(dv[i])), 3), "at_y": round(float(yS[i]), 2),
                                                        "max_step": round(float(st[i2]), 3), "step_y": round(float(yS[i2]), 2)}
        sig_y, sig_t = 4.0, 1.5     # 2 mm along y; 3 deg along theta
        for si, s in enumerate((-1, 1)):
            Rr = Rf[si]
            dy_ = Rr - gauss_nan(Rr, (sig_y, 0.01))
            dt_ = Rr - gauss_nan(Rr, (0.01, sig_t))
            XX = s * (np.abs(cen[si, :, 0])[:, None] + Rr * np.cos(TH)[None])
            ZZ = cen[si, :, 1][:, None] + Rr * np.sin(TH)[None]
            YY = np.repeat(yS[:, None], len(TH), axis=1)
            band = flank_band(YY, TH, Rr, cfg["flank"])
            for nm, dd in (("Y-dir (scar/seam across sections)", dy_), ("theta-dir (ridge along Y)", dt_)):
                v = np.where(band & (np.abs(dd) < 3.0), dd, np.nan)
                report("FLANK %s %s lump" % ("LR"[si], nm), XX.ravel(), YY.ravel(), v.ravel(), ZZ.ravel(), thr=th["bump"])
                report("FLANK %s %s hollow" % ("LR"[si], nm), XX.ravel(), YY.ravel(), -v.ravel(), ZZ.ravel(), thr=th["bump"])
            w = 4
            b_ = (Rr[w:-w] - Rr[:-2 * w]) / (w * 0.5)
            a_ = (Rr[2 * w:] - Rr[w:-w]) / (w * 0.5)
            tv = np.full(Rr.shape, np.nan)
            tv[w:-w] = np.abs(np.degrees(np.arctan(a_) - np.arctan(b_)))
            tv = np.where(band, tv, np.nan)
            report("FLANK %s turn along Y (deg)" % "LR"[si], XX.ravel(), YY.ravel(), tv.ravel(), ZZ.ravel(), thr=th["turn"])
        print("flank %.0fs" % (time.time() - T0))

    if run("edges"):
        ang = np.degrees(m.face_adjacency_angles)
        E2 = m.face_adjacency_edges[ang > 30.0]
        adj = defaultdict(list)
        for p_, q_ in E2:
            adj[p_].append(q_)
            adj[q_].append(p_)
        used = set()
        chains = []
        starts = [v for v in adj if len(adj[v]) != 2] + list(adj.keys())
        for v0 in starts:
            for nb in adj[v0]:
                e = (min(v0, nb), max(v0, nb))
                if e in used:
                    continue
                ch = [v0]
                prev, cur = v0, nb
                used.add(e)
                while True:
                    ch.append(cur)
                    if len(adj[cur]) != 2 or cur == v0:
                        break
                    nx = adj[cur][0] if adj[cur][0] != prev else adj[cur][1]
                    e = (min(cur, nx), max(cur, nx))
                    if e in used:
                        break
                    used.add(e)
                    prev, cur = cur, nx
                chains.append(ch)
        rows = []
        for ch in chains:
            Pp = m.vertices[ch]
            L = np.linalg.norm(np.diff(Pp, axis=0), axis=1).sum()
            if L < 6.0:
                continue
            s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(Pp, axis=0), axis=1))])
            ss = np.arange(0, s[-1], 0.1)
            Q = np.column_stack([np.interp(ss, s, Pp[:, k]) for k in range(3)])
            closed = ch[0] == ch[-1]
            Qs = ndimage.gaussian_filter1d(Q, 12.0, axis=0, mode="wrap" if closed else "nearest")
            dv = np.linalg.norm(Q - Qs, axis=1)
            if not closed:
                dv[(ss < 2.0) | (ss > s[-1] - 2.0)] = 0
            if dv.max() < 0.15:
                continue
            pk = (dv[1:-1] > dv[:-2]) & (dv[1:-1] >= dv[2:]) & (dv[1:-1] > 0.25)
            i = int(np.argmax(dv))
            rows.append((dv.max(), int(pk.sum()), L, Q[i], Pp.min(0), Pp.max(0)))
        rows.sort(key=lambda r: -r[0] * max(r[1], 1))
        print("--- SHARP-EDGE chains (dihedral > 30 deg), serration = dev from gaussian sigma 1.2 mm; %d chains, top 22"
              % len(chains))
        for r in rows[:22]:
            print("   tooth %.2f peaks>0.25: %2d len %5.1f at (%.1f,%.1f,%.1f) %s bbox x%.0f..%.0f y%.0f..%.0f z%.0f..%.0f"
                  % (r[0], r[1], r[2], *r[3], classify(r[3][0], r[3][1], RULES)[0], r[4][0], r[5][0], r[4][1], r[5][1],
                     r[4][2], r[5][2]))
        SUMMARY["edges"] = {"chains": len(chains), "tooth_over": int(sum(r[0] >= th["tooth"] for r in rows)),
                            "top": [{"tooth": round(float(r[0]), 3), "peaks": r[1], "length": round(float(r[2]), 1),
                                     "at": np.round(r[3], 1).tolist(), "region": classify(r[3][0], r[3][1], RULES)[0]}
                                    for r in rows[:22]]}
        print("edges %.0fs" % (time.time() - T0))

    if run("walls"):
        wl = cfg["walls"]
        big = sbox(-200, -200, 200, 200)
        cav = unary_union([oval] + pit_fps).buffer(0.15)
        print("--- WALLS: min distance from pocket end (|x|>70) / pit outline to outer air, per Z (thr %s)" % th["wall"])
        pts_end = [Point(p) for p in P if abs(p[0]) > wl["end_ax_gt"] and wl["end_y"][0] < p[1] < wl["end_y"][1]
                   and min(np.hypot(*(p - f_)) for f_ in fingers) > wl["finger_clear"]]
        SUMMARY["walls"] = {}
        for z in wl["z"]:
            sec = zsection(m, z)
            air = big.difference(sec).difference(cav)
            res, row = [], {}
            for si, s in enumerate((-1, 1)):
                pe = [q for q in pts_end if np.sign(q.x) == s]
                d = np.array([air.distance(q) for q in pe])
                i = int(np.argmin(d))
                res.append("end%s %.2f@(%.0f,%.0f)" % ("LR"[si], d[i], pe[i].x, pe[i].y))
                row["end" + "LR"[si]] = round(float(d[i]), 3)
            for q, p in zip(pit_fps, fingers):
                ring = q.exterior
                pp = [ring.interpolate(t) for t in np.arange(0, ring.length, 0.25)]
                d = np.array([air.distance(u) for u in pp])
                i = int(np.argmin(d))
                lab = "pit%s%s" % ("LR"[int(p[0] > 0)], "u" if p[1] > YC else "l")
                res.append("%s %.2f" % (lab, d[i]))
                row[lab] = round(float(d[i]), 3)
            print("   Z %5.1f: %s" % (z, " | ".join(res)))
            SUMMARY["walls"]["%.1f" % z] = row
        print("walls %.0fs" % (time.time() - T0))

    if run("sym"):
        pts, fi = trimesh.sample.sample_surface_even(m, 300000, seed=1) if hasattr(trimesh.sample, "sample_surface_even") else (None, None)
        if pts is None or len(pts) < 100000:
            pts, fi = trimesh.sample.sample_surface(m, 300000, seed=1)
        mir = pts * [-1, 1, 1]
        d, _ = cKDTree(pts).query(mir)
        top = np.argsort(-d)[:3000]
        cp, dd, _ = trimesh.proximity.closest_point(m, mir[top])
        print("--- SYMMETRY mirror x->-x: sample NN max %.2f p99 %.2f p99.9 %.2f; exact on top 3000: max %.2f"
              % (d.max(), np.percentile(d, 99), np.percentile(d, 99.9), dd.max()))
        q = pts[top]
        cell = np.floor(np.column_stack([np.abs(q[:, 0]), q[:, 1], q[:, 2]]) / 8.0).astype(int)
        keys = {}
        for c_, dv, p_ in zip(map(tuple, cell), dd, q):
            if c_ not in keys or dv > keys[c_][0]:
                keys[c_] = (dv, p_)
        SUMMARY["symmetry"] = {"nn_max": round(float(d.max()), 3), "p99": round(float(np.percentile(d, 99)), 3),
                               "exact_max": round(float(dd.max()), 3), "top": []}
        for dv, p_ in sorted(keys.values(), key=lambda t: -t[0])[:10]:
            reg = classify(p_[0], p_[1], RULES)[0]
            print("   dev %.2f at (%.1f, %.1f, %.1f) %s" % (dv, *p_, reg))
            SUMMARY["symmetry"]["top"].append({"dev": round(float(dv), 3), "at": np.round(p_, 1).tolist(), "region": reg})
        print("sym %.0fs" % (time.time() - T0))

    if a.baseline:
        diff(cfg, json.loads(Path(a.baseline).read_text(encoding="utf-8")), files, a.tag, X, Y, G, oval, th, m)

    SUMMARY["seconds"] = round(time.time() - T0, 1)
    js.write_text(json.dumps(SUMMARY, indent=1), encoding="utf-8")
    print("wrote %s" % js)


def diff(cfg, base, files, tag, X, Y, G, oval, th, m):
    """rv_review.py's diff stage: the new mesh against the baseline sweep's fields."""
    bt, nt = base["tag"], tag
    tags = (bt, nt)
    C = {bt: np.load(base["files"]["cache"]), nt: np.load(files["cache"])}
    F = {bt: np.load(base["files"]["fields"]), nt: np.load(files["fields"])}
    S = {bt: np.load(base["files"]["ysec"]), nt: np.load(files["ysec"])}
    Mb = trimesh.load(base["mesh"])
    print("=== DIFF %s (baseline %s, %s) -> %s" % (bt, base["mesh"], base["sha256"][:8], nt))
    for t, mm_ in ((bt, Mb), (nt, m)):
        b = mm_.bounds
        i = np.argmax(mm_.vertices[:, 2])
        print("%s bounds %s .. %s extent %s; max-Z vertex %s" % (t, np.round(b[0], 2).tolist(), np.round(b[1], 2).tolist(),
              np.round(b[1] - b[0], 2).tolist(), np.round(mm_.vertices[i], 2).tolist()))
    z8, z9 = C[bt]["zmax"], C[nt]["zmax"]
    u8, u9 = C[bt]["zmin"], C[nt]["zmin"]
    dT, dU = z9 - z8, u9 - u8
    regs = classify(X.ravel(), Y.ravel(), RULES).reshape(X.shape)
    print("--- per region: top dz (%s-%s) min/max, underside dz min/max (+ = moved up), cells |d|>0.05 top/under" % (nt, bt))
    for r in sorted(set(regs.ravel())):
        k = regs == r
        if not np.isfinite(dT[k]).any():
            continue

        def mm(d, f):
            v = np.where(k, d, np.nan)
            j = f(v)
            return v.ravel()[j], X.ravel()[j], Y.ravel()[j]
        a = mm(dT, np.nanargmin)
        b_ = mm(dT, np.nanargmax)
        c = mm(dU, np.nanargmin)
        d = mm(dU, np.nanargmax)
        print("   %-15s top %+6.2f@(%.0f,%.0f) %+6.2f@(%.0f,%.0f) | under %+6.2f@(%.0f,%.0f) %+6.2f@(%.0f,%.0f) | n %d/%d"
              % (r, *a, *b_, *c, *d, int((np.abs(np.where(k, dT, 0)) > 0.05).sum()), int((np.abs(np.where(k, dU, 0)) > 0.05).sum())))
    only8 = np.isfinite(z8) & ~np.isfinite(z9)
    only9 = np.isfinite(z9) & ~np.isfinite(z8)
    for nm, w in (("footprint lost in %s" % nt, only8), ("footprint gained in %s" % nt, only9)):
        for s in (-1, 1):
            ww = w & (np.sign(X) == s)
            if ww.any():
                print("   %s %s: %d cells (%.1f mm2) x %.1f..%.1f y %.1f..%.1f" % (nm, "LR"[s > 0], ww.sum(), ww.sum() * G * G,
                      X[ww].min(), X[ww].max(), Y[ww].min(), Y[ww].max()))
    inP = shapely.contains_xy(oval.buffer(-0.6), X.ravel(), Y.ravel()).reshape(X.shape)
    print("   pocket columns (oval-0.6): max |dz top| %.3f, max |dz under| %.3f (under excludes nothing)"
          % (np.nanmax(np.abs(dT[inP])), np.nanmax(np.abs(dU[inP]))))
    drop = dT < -0.1
    for s in (-1, 1):
        w = drop & (np.sign(X) == s)
        if w.any():
            th8 = (z8 - u8)[w]
            th9 = (z9 - u9)[w]
            j = np.nanargmin(np.where(w, dT, np.nan))
            print("   crest drop %s: %d cells x %.1f..%.1f y %.1f..%.1f, max drop %.2f at (%.1f,%.1f) z %.2f->%.2f; "
                  "column thickness min %s %.2f %s %.2f" % ("LR"[s > 0], w.sum(), X[w].min(), X[w].max(), Y[w].min(), Y[w].max(),
                  dT.ravel()[j], X.ravel()[j], Y.ravel()[j], z8.ravel()[j], z9.ravel()[j], bt, np.nanmin(th8), nt, np.nanmin(th9)))
    for t in tags:
        j = np.nanargmax(C[t]["zmax"])
        print("   %s top-field max %.2f at (%.1f,%.1f)" % (t, C[t]["zmax"].ravel()[j], X.ravel()[j], Y.ravel()[j]))
    dl = cfg["regression_delta"]
    for nm, key, thr, delta, sg in (("UNDER turn", "turnU", th["turn"], dl["turn"], 1), ("UNDER lump", "devU", th["bump"], dl["bump"], -1),
                                    ("UNDER hollow", "devU", th["bump"], dl["bump"], 1), ("UNDER non-convexity", "hd", th["bump"], dl["bump"], 1),
                                    ("TOP turn", "turnT", th["turn"], dl["turn"], 1), ("TOP lump", "devT", th["bump"], dl["bump"], 1),
                                    ("TOP hollow", "devT", th["bump"], dl["bump"], -1)):
        new_components(sg * F[bt][key], sg * F[nt][key], thr, delta, X, Y, C[nt]["zmin" if nm.startswith("U") else "zmax"], nm, 8, tags)
    for si, s in enumerate((-1, 1)):
        vals = {}
        for t in tags:
            Rr = S[t]["Rf"][si]
            yS, TH, cen = S[t]["yS"], S[t]["TH"], S[t]["cen"]
            w = 4
            b_ = (Rr[w:-w] - Rr[:-2 * w]) / 2.0
            a_ = (Rr[2 * w:] - Rr[w:-w]) / 2.0
            tv = np.full(Rr.shape, np.nan)
            tv[w:-w] = np.abs(np.degrees(np.arctan(a_) - np.arctan(b_)))
            dy_ = Rr - gauss_nan(Rr, (4.0, 0.01))
            YY = np.repeat(yS[:, None], len(TH), 1)
            band = flank_band(YY, TH, Rr, cfg["flank"])
            XX = s * (np.abs(cen[si, :, 0])[:, None] + Rr * np.cos(TH)[None])
            ZZ = cen[si, :, 1][:, None] + Rr * np.sin(TH)[None]
            vals[t] = (np.where(band, tv, np.nan), np.where(band & (np.abs(dy_) < 3), np.abs(dy_), np.nan), XX, YY, ZZ)
        new_components(vals[bt][0], vals[nt][0], th["turn"], dl["turn"], vals[nt][2], vals[nt][3], vals[nt][4],
                       "FLANK %s turn-Y" % "LR"[si], 6, tags)
        new_components(vals[bt][1], vals[nt][1], th["bump"], dl["bump"], vals[nt][2], vals[nt][3], vals[nt][4],
                       "FLANK %s |dev-Y|" % "LR"[si], 6, tags)
    SUMMARY["baseline"] = {"tag": bt, "mesh": base["mesh"], "sha256": base["sha256"]}
    SUMMARY["regression_components"] = sum(len(v) for v in SUMMARY.get("regressions", {}).values())
    print("regression components (new or worse, >= 3 cells): %d" % SUMMARY["regression_components"])
    print("diff %.0fs" % (time.time() - T0))


RULES = []
if __name__ == "__main__":
    main()
