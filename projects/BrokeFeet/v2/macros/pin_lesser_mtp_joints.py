"""Pin the 3rd, 4th and 5th MTP joints -- the lesser-toe rays not already
treated by pin_hallux_joint.py (ray 0) or pin_2nd_mtp_joint.py (ray 1).

THE PROBLEM
-----------
pin_2nd_mtp_joint.py measured all four lesser-toe MTP joints as comparably
fragile to the hallux's pinned 0.295 mm bridge, but only pinned ray 1 (the
one the operator circled):

    ray            MTP joint gap    site (mm)
    1 (2nd toe)    0.276 mm         (-103.23, -68.42, 26.39)  -- pinned
    2 (3rd toe)    0.283 mm         (-118.46, -69.83, 14.98)  -- this script
    3 (4th toe)    0.260 mm         (-120.60, -76.87, 15.00)  -- this script
    4 (5th toe)    0.297 mm         (-137.52, -71.43,  9.79)  -- this script

Same pipeline-wide segmentation artefact, not one ray's problem. This script
treats the remaining three.

THE FIX
-------
Reuses the ray1 method unchanged, generalised over RAY_INDEX instead of
hardcoding it:

1. Isolate the ray's forefoot component at Y > FOREFOOT_Y (5 components
   expected: hallux, 2nd..5th, sorted by face count -- same ordering
   pin_2nd_mtp_joint.py relies on).
2. Find that ray's own MTP joint waist -- NOT a fixed Y like the hallux
   script's JOINT_CUT_Y=-55, because only the hallux ray is isolated as a
   single component all the way to its own joint. Rays 1-4 are still fused
   to their neighbours/tarsus below Y~-85 to -110, so the real joint is an
   internal waist found by scanning cross-sectional area (convex hull area
   of each Y-slice) for its local minimum -- this is what pin_2nd_mtp_joint's
   docstring describes doing by hand for ray 1 (minimum at Y=-68.5); here it
   is automated per ray rather than hand-measured, since three more rays
   need it and their sites above were only ever measured as point gaps, not
   as scanned waists.
3. Fit the joint axis from local bone centroids (direction only), then
   RE-CENTRE in two stages -- lateral grid search perpendicular to the axis,
   then axial recentre onto the real open-air span -- exactly as
   pin_2nd_mtp_joint.py's own recentring, because the raw closest-approach
   point is a surface artefact off the true bone bulk at every condylar
   joint measured so far, not just ray 1.
4. Build the pin, verify with the SAME two gates as ray 1: axial centreline
   profile (one clean gap, no end reaching an open span) and a 24-angle
   pin-surface edge check (the surface, not just the axis, must stay inside
   bone at both ends -- this is what caught the 1.5mm/6mm failure on ray 1).

Diameter/length default to 2.5mm / 8mm, the values that passed ALL 24 angles
clean on ray 1 (see pin_2nd_mtp_joint.py's docstring for why 1.5mm/6mm and
2.0-2.5mm/6mm both failed). These are NOT re-swept per ray here -- if a
lesser ray's neck turns out thinner than ray 1's, the surface-edge check
will report FAILS and the diameter/length should be reduced/lengthened for
that ray specifically and re-run, same as was done for ray 1.

Usage:
  python macros/pin_lesser_mtp_joints.py [--rays 2 3 4] [--diameter MM]
      [--length MM] [--out FILE]

Runs all three lesser rays (2, 3, 4) by default and unions all pins into one
output in a single pass, so genus/watertightness are checked on the final
combined result rather than three separate partial files.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import trimesh
from scipy.spatial import ConvexHull, cKDTree

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SRC = ROOT / "BrokeFeetV2_pinned2.stl"   # sculpt + hallux pin + ray1 (2nd MTP) pin

FOREFOOT_Y = -85.0     # isolates the toe rays from the midfoot
RAY_NAMES = {1: "2nd (index)", 2: "3rd (middle)", 3: "4th (ring)", 4: "5th (little)"}


def forefoot_components(mesh):
    """Split the model at Y > FOREFOOT_Y into per-ray components, sorted by
    face count (largest first) -- same ordering pin_2nd_mtp_joint.py uses."""
    V, F = mesh.vertices, mesh.faces
    fore = (V[F][:, :, 1] > FOREFOOT_Y).all(1)
    sub = trimesh.Trimesh(vertices=V, faces=F[fore], process=False)
    sub.remove_unreferenced_vertices()
    parts = sorted(sub.split(only_watertight=False), key=lambda x: -len(x.faces))
    if len(parts) < 5:
        raise RuntimeError(
            f"expected 5 forefoot components at Y>{FOREFOOT_Y}, got {len(parts)} "
            "-- ray ordering assumption (sorted by face count) may not hold, "
            "re-check before trusting RAY_INDEX"
        )
    return parts


def find_joint_waist(ray_mesh, y_lo, y_hi, n=60, edge_margin=0.15):
    """Scan cross-sectional convex-hull area over Y in (y_lo, y_hi) and
    return the Y of the INTERIOR local-minimum waist -- the joint gap sits
    at a pinch in cross-section flanked by the metatarsal-head bulge on one
    side and the phalanx-base bulge on the other, exactly the manual method
    pin_2nd_mtp_joint.py's docstring describes for ray 1 (minimum at
    Y=-68.5), generalised.

    A plain global argmin fails here: cross-sectional area also shrinks
    monotonically toward the distal toe tip (the phalanx just tapers to a
    point), which is a SMALLER area than the joint waist and always wins a
    global argmin -- measured: with no interior constraint, rays 2/3/4 all
    "found" their waist at the very last scanned sample, i.e. the tip
    itself, not a real joint. The fix is two-fold: exclude a margin at each
    end of the scan (so the taper and the proximal bulk are never eligible)
    and require a true local minimum -- lower area than both neighbours --
    rather than the global smallest value.
    """
    V = ray_mesh.vertices
    lo, hi = min(y_lo, y_hi), max(y_lo, y_hi)
    ys = np.linspace(lo, hi, n)
    band_width = (hi - lo) / n
    areas = np.full(n, np.inf)
    for i, y in enumerate(ys):
        band = V[np.abs(V[:, 1] - y) < band_width]
        if len(band) < 4:
            continue
        pts2d = band[:, [0, 2]]
        try:
            areas[i] = ConvexHull(pts2d).volume  # 2D hull "volume" = area
        except Exception:  # noqa: BLE001 -- degenerate slice, skip
            continue
    finite = np.isfinite(areas)
    if not finite.any():
        raise RuntimeError(f"no valid cross-sections found in Y in [{y_lo}, {y_hi}]")

    m = max(1, int(edge_margin * n))
    interior = slice(m, n - m)
    idxs = np.arange(n)[interior]
    a = areas[interior]
    fin = finite[interior]

    # true local minima: lower than both neighbours, ignoring inf slices
    local_min_mask = np.zeros(len(a), dtype=bool)
    for k in range(1, len(a) - 1):
        if fin[k] and fin[k - 1] and fin[k + 1] and a[k] < a[k - 1] and a[k] < a[k + 1]:
            local_min_mask[k] = True

    if local_min_mask.any():
        cand = np.where(local_min_mask)[0]
        j_local = cand[np.argmin(a[cand])]
        j = idxs[j_local]
    else:
        # no strict local minimum in the interior (flat or monotonic) --
        # fall back to the smallest interior value, still excluding the
        # tip/proximal margins so it can't collapse to the taper
        if not fin.any():
            raise RuntimeError(
                f"no valid interior cross-sections found in Y in [{y_lo}, {y_hi}] "
                f"after excluding {edge_margin*100:.0f}% edge margins")
        j_local = np.argmin(np.where(fin, a, np.inf))
        j = idxs[j_local]

    return float(ys[j])


def split_at_y(ray_mesh, cut_y):
    rv, rf = ray_mesh.vertices, ray_mesh.faces
    prox = (rv[rf][:, :, 1] < cut_y).all(1)   # metatarsal-head side
    dist = (rv[rf][:, :, 1] >= cut_y).all(1)  # phalanx side
    P = trimesh.Trimesh(vertices=rv, faces=rf[prox], process=False)
    D = trimesh.Trimesh(vertices=rv, faces=rf[dist], process=False)
    P.remove_unreferenced_vertices()
    D.remove_unreferenced_vertices()
    return P, D


def joint_axis(P, D):
    tree = cKDTree(P.vertices)
    d, i = tree.query(D.vertices, k=1)
    j = int(np.argmin(d))
    a = D.vertices[j]
    b = P.vertices[i[j]]
    mid = (a + b) / 2.0
    axis = a - b
    n = np.linalg.norm(axis)
    axis = axis / n if n > 1e-9 else np.array([0.0, 1.0, 0.0])
    return mid, axis, float(d.min())


def near(sm, pt, r):
    return sm.vertices[np.linalg.norm(sm.vertices - pt, axis=1) < r]


def recentre_pin(mesh, base_mid, ray_axis, recenter_scan=16.0):
    """Two-stage recentre: lateral grid search perpendicular to the axis,
    then axial recentre onto the real open-air span. Identical to
    pin_2nd_mtp_joint.py's method."""
    tmp_v = np.array([1.0, 0.0, 0.0]) if abs(ray_axis[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    u_hat = np.cross(ray_axis, tmp_v); u_hat /= np.linalg.norm(u_hat)
    v_hat = np.cross(ray_axis, u_hat)

    Ls = recenter_scan
    ts_scan = np.linspace(-Ls / 2, Ls / 2, int(Ls * 10) + 1)
    margin_scan = max(3, int(0.4 * len(ts_scan) / Ls))
    MAX_GAP_WIDTH = 3.0
    MAX_GAP_OFFCENTER = 2.5

    def largest_open_span(ins_bool, ts_arr):
        spans, cur = [], None
        for i, v in enumerate(ins_bool):
            if not v:
                cur = [i, i] if cur is None else [cur[0], i]
            elif cur is not None:
                spans.append(cur); cur = None
        if cur is not None:
            spans.append(cur)
        if not spans:
            return None
        widest = max(spans, key=lambda s: ts_arr[s[1]] - ts_arr[s[0]])
        width = float(ts_arr[widest[1]] - ts_arr[widest[0]])
        center = float((ts_arr[widest[0]] + ts_arr[widest[1]]) / 2.0)
        return width, center, len(spans)

    best = None
    offsets = np.linspace(-3.0, 3.0, 13)
    for du in offsets:
        for dv in offsets:
            probe_mid = base_mid + du * u_hat + dv * v_hat
            pts = probe_mid[None, :] + ts_scan[:, None] * ray_axis[None, :]
            p_ins = mesh.contains(pts)
            ends_ok = bool(p_ins[:margin_scan].all() and p_ins[-margin_scan:].all())
            frac = float(p_ins.mean())
            span_info = largest_open_span(p_ins, ts_scan)
            width, center, n_spans = span_info if span_info else (0.0, 0.0, 0)
            valid_gap = (ends_ok and n_spans >= 1
                         and 0.0 < width <= MAX_GAP_WIDTH
                         and abs(center) <= MAX_GAP_OFFCENTER)
            key = (ends_ok, valid_gap, -width)
            if best is None or key > (best[0], best[1], best[2]):
                best = (ends_ok, valid_gap, -width, du, dv, p_ins, frac, width, center)

    ends_ok, valid_gap, _, du, dv, _, frac, width, center = best
    if not ends_ok:
        print(f"    WARNING: no lateral offset in +/-3mm gave clean ends "
              f"(best inside {frac*100:.0f}% at du={du:.1f} dv={dv:.1f})")
    elif not valid_gap:
        print(f"    WARNING: best clean-ends offset has no valid narrow "
              f"centred gap (widest span {width:.1f} mm at t={center:+.1f})")
    if not valid_gap:
        raise RuntimeError("no valid narrow centred gap found -- cannot place "
                            "a pin that bridges the joint capsule rather than "
                            "solid bone or open space; treat this joint by hand")

    lat_mid = base_mid + du * u_hat + dv * v_hat
    mid = lat_mid + center * ray_axis
    print(f"    lateral recentre du={du:+.1f} dv={dv:+.1f} mm, "
          f"axial recentre on gap width {width:.2f} mm at t={center:+.2f} mm")
    return mid


def pin_edge_checks(mesh, mid, ray_axis, diameter, length):
    ts = np.linspace(-length / 2, length / 2, max(80, int(length * 20) + 1))
    samples = mid[None, :] + ts[:, None] * ray_axis[None, :]
    ins = mesh.contains(samples)
    print(f"    centreline: inside {100.0 * ins.mean():.0f}%", end="")
    spans, cur = [], None
    for t, v in zip(ts, ins):
        if not v:
            cur = [t, t] if cur is None else [cur[0], t]
        elif cur:
            spans.append(tuple(cur)); cur = None
    if cur:
        spans.append(tuple(cur))
    print(f", open spans {[(round(x, 2), round(y, 2)) for x, y in spans]} mm from centre")
    centre_end_open = spans and (abs(spans[0][0]) > length / 2 - 0.4
                                  or abs(spans[-1][1]) > length / 2 - 0.4)
    if centre_end_open:
        print("    WARNING: open span reaches a pin end on the CENTRELINE -- protrudes.")

    tmp_v = np.array([1.0, 0.0, 0.0]) if abs(ray_axis[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    u_hat = np.cross(ray_axis, tmp_v); u_hat /= np.linalg.norm(u_hat)
    v_hat = np.cross(ray_axis, u_hat)
    r_off = diameter / 2.0
    margin_n = max(3, int(0.4 * len(ts) / length))
    edge_fail = []
    for ang_deg in range(0, 360, 15):
        off = r_off * (np.cos(np.radians(ang_deg)) * u_hat + np.sin(np.radians(ang_deg)) * v_hat)
        pts = (mid + off)[None, :] + ts[:, None] * ray_axis[None, :]
        e_ins = mesh.contains(pts)
        if not (e_ins[:margin_n].all() and e_ins[-margin_n:].all()):
            edge_fail.append(ang_deg)
    ok = not edge_fail
    print(f"    pin-surface edge check (24 angles, dia {diameter:.1f}mm): "
          f"{'ALL CLEAR' if ok else f'FAILS at angles {edge_fail}'}")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rays", type=int, nargs="+", default=[2, 3, 4],
                     help="ray indices to pin (1=2nd toe .. 4=5th toe); "
                          "default is the three NOT already pinned")
    ap.add_argument("--diameter", type=float, default=2.5,
                     help="default matches ray1's validated clean value; "
                          "reduce/lengthen per-ray if the edge check fails")
    ap.add_argument("--length", type=float, default=8.0)
    ap.add_argument("--metatarsal-r", type=float, default=6.0)
    ap.add_argument("--phalanx-r", type=float, default=7.0)
    ap.add_argument("--recenter-scan", type=float, default=16.0)
    ap.add_argument("--src", default=str(SRC))
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    mesh = trimesh.load(args.src)
    print(f"source {Path(args.src).name}  {len(mesh.faces)} faces  "
          f"vol {mesh.volume/1000:.3f} cm3")

    parts = forefoot_components(mesh)
    pins = []
    any_fail = False

    for ray_idx in args.rays:
        name = RAY_NAMES.get(ray_idx, f"ray {ray_idx}")
        print(f"\n{'='*60}\n{name} MTP joint (ray {ray_idx})\n{'='*60}")
        ray_mesh = parts[ray_idx]
        y_all = ray_mesh.vertices[:, 1]
        y_min, y_max = float(y_all.min()), float(y_all.max())
        print(f"  ray {ray_idx} bbox: {len(ray_mesh.faces)} faces, "
              f"Y in [{y_min:.2f}, {y_max:.2f}]")
        # ray extends from FOREFOOT_Y (proximal, fused to the tarsal mass,
        # Y=-85, the MINIMUM) out to the distal toe tip (the MAXIMUM Y --
        # confirmed directly: ray 2's tip prints at Y=-38.76, its cut edge
        # at Y=-85.00, i.e. tip = max, not min. An earlier version of this
        # comment had this backwards and it silently produced a zero-width
        # scan window every time.)
        y_tip = y_max
        y_hi = FOREFOOT_Y  # == y_min, the proximal cut plane
        if y_tip - y_hi < 5.0:
            raise RuntimeError(
                f"ray {ray_idx} bbox is degenerate (Y span {y_tip - y_hi:.3f} mm) -- "
                f"parts[{ray_idx}] is not a real toe ray; check --rays and the "
                f"forefoot_components() split/ordering on this source mesh")
        # search only the distal ~60% of the ray for the joint waist -- the
        # proximal ~40% near FOREFOOT_Y is tarsal-adjacent bulk, not the MTP joint
        scan_lo = y_hi + 0.4 * (y_tip - y_hi)
        cut_y = find_joint_waist(ray_mesh, scan_lo, y_tip)
        print(f"  joint waist found at Y={cut_y:.1f} (scanned Y in "
              f"[{scan_lo:.1f}, {y_tip:.1f}])")

        P, D = split_at_y(ray_mesh, cut_y)
        Pn, Dn = len(P.split(only_watertight=False)), len(D.split(only_watertight=False))
        print(f"  metatarsal-head side: {Pn} component(s), phalanx side: {Dn} component(s)")
        if Pn != 1 or Dn != 1:
            print("  WARNING: cut did not cleanly isolate one bone on each side -- skipping")
            any_fail = True
            continue

        mid_raw, axis_raw, gap = joint_axis(P, D)
        print(f"  closest approach {gap:.3f} mm at "
              f"({mid_raw[0]:.2f}, {mid_raw[1]:.2f}, {mid_raw[2]:.2f})")

        a = near(P, mid_raw, args.metatarsal_r)
        b = near(D, mid_raw, args.phalanx_r)
        if len(a) == 0 or len(b) == 0:
            print("  WARNING: local radius too small to find bone on one side -- skipping")
            any_fail = True
            continue
        ray_axis = b.mean(0) - a.mean(0)
        ray_axis /= np.linalg.norm(ray_axis)
        base_mid = (a.mean(0) + b.mean(0)) / 2.0
        print(f"  local axis ({ray_axis[0]:.3f}, {ray_axis[1]:.3f}, {ray_axis[2]:.3f})")

        try:
            mid = recentre_pin(mesh, base_mid, ray_axis, args.recenter_scan)
        except RuntimeError as e:
            print(f"  WARNING: {e} -- skipping this ray")
            any_fail = True
            continue
        print(f"  pin centre ({mid[0]:.2f}, {mid[1]:.2f}, {mid[2]:.2f})")

        ok = pin_edge_checks(mesh, mid, ray_axis, args.diameter, args.length)
        if not ok:
            print(f"  NOT ADDING pin for {name} -- surface edge check failed at "
                  f"{args.diameter}mm/{args.length}mm; re-run with different "
                  f"--diameter/--length for this ray alone")
            any_fail = True
            continue

        pin = trimesh.creation.cylinder(radius=args.diameter / 2.0,
                                         height=args.length, sections=48)
        R = trimesh.geometry.align_vectors([0, 0, 1], ray_axis)
        pin.apply_transform(R)
        pin.apply_translation(mid)
        pins.append(pin)
        print(f"  pin added: {args.diameter:.1f}mm dia x {args.length:.1f}mm")

    if not pins:
        print("\nNo pins passed all checks -- nothing written.")
        return 1

    print(f"\n{'='*60}\nUnioning {len(pins)} pin(s) into the model\n{'='*60}")
    out = trimesh.util.concatenate([mesh] + pins)
    print(f"concatenate: {len(out.faces)} faces")
    try:
        merged = mesh
        for p in pins:
            merged = merged.union(p)
        print(f"boolean union: {len(merged.faces)} faces  "
              f"watertight {merged.is_watertight}  "
              f"bodies {len(merged.split(only_watertight=False))}")
        out = merged
    except Exception as e:  # noqa: BLE001
        print(f"boolean union unavailable ({e}); keeping overlapping concatenation")

    euler = out.euler_number
    genus = (2 - euler) // 2
    print(f"\nRESULT vol {out.volume/1000:.3f} cm3  watertight {out.is_watertight}  "
          f"bodies {len(out.split(only_watertight=False))}  genus {genus}")
    if any_fail:
        print("NOTE: one or more rays were skipped -- see WARNINGs above.")

    if args.out:
        out.export(args.out)
        print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
