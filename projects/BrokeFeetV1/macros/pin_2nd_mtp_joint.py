"""Pin the 2nd metatarsophalangeal (MTP) joint -- 2nd toe, proximal phalanx
base against the 2nd metatarsal head.

THE PROBLEM
-----------
The operator circled a joint on a render near the hallux pin site, on a
lesser (non-hallux) ray. Measured on BrokeFeetV2_pinned.stl (sculpt + hallux
pin already applied), the four lesser-toe MTP joints are ALL comparably
fragile to the hallux's already-pinned 0.295 mm bridge:

    ray            MTP joint gap    site (mm)
    1 (2nd toe)    0.276 mm         (-103.23, -68.42, 26.39)
    2 (3rd toe)    0.283 mm         (-118.46, -69.83, 14.98)
    3 (4th toe)    0.260 mm         (-120.60, -76.87, 15.00)
    4 (5th toe)    0.297 mm         (-137.52, -71.43,  9.79)

This is a pipeline-wide artefact (the same segmentation threshold that made
the hallux MTP thin), not unique to one ray. The 2nd ray is the one adjacent
to the hallux -- the best match for the operator's description ("medial-ish
to the hallux pin site", near the already-pinned joint) -- and its own Z is
26.4 mm vs the hallux's 35.4 mm and the 3rd/4th/5th rays' 15/15/9.8 mm,
consistent with a joint immediately next to the hallux on the declining
transverse arch. This script treats ONLY that joint (ray 1 / 2nd MTP).

Locating the joint required a different cut than the hallux script's fixed
JOINT_CUT_Y = -55.0: the hallux ray is isolated from the tarsal mass at Y >
-85 as a *single* connected component all the way to its own MTP joint, so
one cut plane also isolates its phalanx from its metatarsal head. Rays 1-4
are NOT like that -- at Y = -85 each lesser ray is already a single fused
piece spanning both its own MTP joint AND (for rays 1/2, and separately for
0) fuses with its neighbour and the tarsal mass by Y ~ -93 to -110. The real
MTP joint for each lesser ray is an internal waist WITHIN the Y > -85 band,
found here by a convex-hull cross-sectional-area scan along Y (see
docstring in the exploration notes / README once filed) -- local minimum at
Y = -68.5 for ray 1, distinctly lower than the metatarsal-head bulge on one
side (area ~125 mm^2 at Y=-75) and the phalanx-base bulge on the other
(~77 mm^2 at Y=-64).

THE FIX
-------
Same internal-cylinder technique as pin_hallux_joint.py -- with one departure
forced by the geometry. The hallux script's own axis method (local centroids
of bone within LOCAL_R of the raw closest-approach midpoint) was tried here
FIRST and measured only 29-34% inside bone with the open span reaching a pin
end (protruding) at every LOCAL_R from 4-12 mm. This is a genuinely different
joint shape: it is a condylar articulation where the phalanx base sits offset
from the metatarsal head's centroid line rather than directly in-line (the
hallux's own joint does not curve this sharply). A pure centroid-difference
axis drags the pin off the real bone mass here in a way it did not for the
hallux.

What works: after fitting the centroid-difference axis (same as the hallux
method), RE-CENTRE the midpoint on the actual open-air span found by a long
axial probe along that axis, rather than trusting the raw closest-approach
point or the raw centroid midpoint. Both of those anchor to a local surface
artefact off the true bone bulk (confirmed: the very first slice of the
phalanx, right at the joint, has its own centroid offset (-2.4, --, -4.5) mm
from the raw closest-approach midpoint). Re-centring on the measured open
span, not the surface point, is what makes both ends land inside bone.

DIAMETER AND LENGTH INTERACT, AND BOTH MATTER.
First swept 1.5 / 2.0 / 2.5 mm at 24 angles around the pin's own surface
(not just the centreline) with a 6 mm length: at 1.5 mm, 6 of 24 angles
still exited bone (clustered at 120-165 deg and 315-330 deg -- the neck is
thin on two opposing sides); 2.0 mm and 2.5 mm were worse. But a short pin
gives the axis fit less bone to anchor into at either end. Lengthening to
8 mm while going back up to 2.5 mm diameter passes ALL 24 angles clean --
the extra length let both ends sit in thicker bone further from the joint
waist, which a wider diameter alone could not do at 6 mm. A too-thin pin
is also a real failure mode of its own: buried pins that are mostly
inside bone with only a sliver exposed can vanish under a slicer's line
width, i.e. printing at 1.5 mm risked disappearing even though it measured
"mostly clean" on the centreline. 2.5 mm / 8 mm is the current default and
is verified render-clean (no visible strut) at every angle.

Usage:
  python macros/pin_2nd_mtp_joint.py [--diameter MM] [--length MM] [--out FILE]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import trimesh
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SRC = ROOT / "BrokeFeetV2_pinned.stl"   # sculpt + hallux pin already applied

FOREFOOT_Y = -85.0     # isolates the toe rays from the midfoot, as in pin_hallux_joint.py
RAY_INDEX = 1          # 0=hallux, 1=2nd toe, 2=3rd, 3=4th, 4=5th (by component face count)
JOINT_CUT_Y = -68.5    # internal waist within ray 1, found by cross-sectional area scan


def ray1_parts(mesh):
    """Return (metatarsal-head submesh, phalanx submesh) for the 2nd ray."""
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
    ray = parts[RAY_INDEX]
    rv, rf = ray.vertices, ray.faces
    prox = (rv[rf][:, :, 1] < JOINT_CUT_Y).all(1)   # metatarsal-head side
    dist = (rv[rf][:, :, 1] >= JOINT_CUT_Y).all(1)  # phalanx side
    P = trimesh.Trimesh(vertices=rv, faces=rf[prox], process=False)
    D = trimesh.Trimesh(vertices=rv, faces=rf[dist], process=False)
    P.remove_unreferenced_vertices()
    D.remove_unreferenced_vertices()
    return P, D


def joint_axis(P, D):
    """Closest approach across the joint: (midpoint, unit axis, gap)."""
    tree = cKDTree(P.vertices)
    d, i = tree.query(D.vertices, k=1)
    j = int(np.argmin(d))
    a = D.vertices[j]
    b = P.vertices[i[j]]
    mid = (a + b) / 2.0
    axis = a - b
    n = np.linalg.norm(axis)
    if n < 1e-9:
        axis = np.array([0.0, 1.0, 0.0])
    else:
        axis = axis / n
    return mid, axis, float(d.min())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--diameter", type=float, default=2.5,
                    help="2.5mm/8mm passes the 24-angle surface check clean; "
                         "2.5mm/6mm did not -- length matters as much as "
                         "diameter here, see docstring")
    ap.add_argument("--length", type=float, default=8.0,
                    help="total pin length, centred on the joint")
    ap.add_argument("--metatarsal-r", type=float, default=6.0,
                    help="radius of metatarsal-head bone used to fit the axis")
    ap.add_argument("--phalanx-r", type=float, default=7.0,
                    help="radius of phalanx-base bone used to fit the axis")
    ap.add_argument("--recenter-scan", type=float, default=16.0,
                    help="length of the axial probe used to find the real "
                         "open-air span and recentre the joint midpoint on it")
    ap.add_argument("--src", default=str(SRC))
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    mesh = trimesh.load(args.src)
    print(f"source {Path(args.src).name}  {len(mesh.faces)} faces  "
          f"vol {mesh.volume/1000:.3f} cm3")

    P, D = ray1_parts(mesh)
    # sanity: each side should be a single connected component, otherwise the
    # cut plane sliced through open space rather than the joint waist
    Pn = len(P.split(only_watertight=False))
    Dn = len(D.split(only_watertight=False))
    print(f"  metatarsal-head side: {Pn} component(s), phalanx side: {Dn} component(s)")
    if Pn != 1 or Dn != 1:
        print("  WARNING: cut did not cleanly isolate one bone on each side")

    mid_raw, axis_raw, gap = joint_axis(P, D)
    print(f"\n2nd MTP joint")
    print(f"  metatarsal head  {len(P.vertices)} verts")
    print(f"  proximal phalanx {len(D.vertices)} verts")
    print(f"  closest approach {gap:.3f} mm at "
          f"({mid_raw[0]:.2f}, {mid_raw[1]:.2f}, {mid_raw[2]:.2f})")
    print(f"  joint axis (raw) ({axis_raw[0]:.3f}, {axis_raw[1]:.3f}, {axis_raw[2]:.3f})")

    # Fit axis from LOCAL bone centroids, as in pin_hallux_joint.py -- but here
    # the raw closest-approach point is itself a surface artefact off the true
    # bone bulk (see docstring), so this axis is used for DIRECTION only, not
    # to anchor the pin.
    def near(sm, pt, r):
        return sm.vertices[np.linalg.norm(sm.vertices - pt, axis=1) < r]

    a = near(P, mid_raw, args.metatarsal_r)
    b = near(D, mid_raw, args.phalanx_r)
    ray_axis = b.mean(0) - a.mean(0)
    ray_axis /= np.linalg.norm(ray_axis)
    base_mid = (a.mean(0) + b.mean(0)) / 2.0
    print(f"  local axis (metatarsal r={args.metatarsal_r:.0f}mm, "
          f"phalanx r={args.phalanx_r:.0f}mm) "
          f"({ray_axis[0]:.3f}, {ray_axis[1]:.3f}, {ray_axis[2]:.3f})")

    # Re-centre in two stages. The raw centroid midpoint is measurably off
    # the true gap here (this joint is condylar, not a simple facing pair
    # like the hallux): anchoring the hallux script's method directly on it
    # left open spans reaching a pin end at every LOCAL_R from 4-12 mm, and
    # even after re-centring ALONG the axis alone, a full-diameter pin's
    # edge rays still exited bone (measured: 2/4 edge rays failed).
    #
    # Stage 1 -- LATERAL: search a small grid perpendicular to the axis for
    # a location whose axial probe has both ends solidly inside bone (this
    # is where the actual bone bulk of both P and D overlaps in cross-
    # section, which is not the same point as either centroid).
    # Stage 2 -- AXIAL: at that location, recentre along the axis on the
    # real open-air span, same idea as stage 1 but along the pin direction.
    tmp_v = np.array([1.0, 0.0, 0.0]) if abs(ray_axis[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    u_hat = np.cross(ray_axis, tmp_v); u_hat /= np.linalg.norm(u_hat)
    v_hat = np.cross(ray_axis, u_hat)

    Ls = args.recenter_scan
    ts_scan = np.linspace(-Ls / 2, Ls / 2, int(Ls * 10) + 1)
    margin_scan = max(3, int(0.4 * len(ts_scan) / Ls))

    # A candidate must have BOTH ends inside bone AND cross exactly ONE
    # reasonably narrow open span roughly centred in the scan window --
    # not just "ends_ok" (a probe that tunnels through solid bone the whole
    # way is ends_ok with no gap at all: it buries a pin beside the joint
    # rather than bridging it) and not just "some gap somewhere" (a probe
    # that grazes past the bone edge into open soft-tissue space near the
    # far end of a long scan window also passes an inside-fraction target
    # by coincidence without ever crossing the real ~0.3 mm joint capsule --
    # measured on the first attempt at this scoring, where the "gap" turned
    # out to be a 5.5 mm span sitting off-centre). A real MTP joint capsule
    # in this model reads a few tenths of a mm to a couple of mm wide once
    # pin-diameter and axis slop are folded in -- reject anything wider.
    MAX_GAP_WIDTH = 3.0    # mm; wider than this is not "the joint", it's open space
    MAX_GAP_OFFCENTER = 2.5  # mm; gap centre must be within this of scan centre

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
        n_spans = len(spans)
        return width, center, n_spans

    best = None  # (ends_ok, valid_gap, -|width-target|, du, dv, ins, frac, width)
    offsets = np.linspace(-3.0, 3.0, 13)
    for du in offsets:
        for dv in offsets:
            probe_mid = base_mid + du * u_hat + dv * v_hat
            pts = probe_mid[None, :] + ts_scan[:, None] * ray_axis[None, :]
            p_ins = mesh.contains(pts)
            ends_ok = bool(p_ins[:margin_scan].all() and p_ins[-margin_scan:].all())
            frac = float(p_ins.mean())
            span_info = largest_open_span(p_ins, ts_scan)
            if span_info is None:
                width, center, n_spans = 0.0, 0.0, 0
            else:
                width, center, n_spans = span_info
            valid_gap = (ends_ok and n_spans >= 1
                         and 0.0 < width <= MAX_GAP_WIDTH
                         and abs(center) <= MAX_GAP_OFFCENTER)
            score = -width  # among valid candidates, prefer the tightest (most joint-like) gap
            key = (ends_ok, valid_gap, score)
            if best is None or key > (best[0], best[1], best[2]):
                best = (ends_ok, valid_gap, score, du, dv, p_ins, frac, width, center)
    if not best[0]:
        print(f"  WARNING: no lateral offset in +/-3mm gave clean ends "
              f"(best inside {best[6]*100:.0f}% at du={best[3]:.1f} dv={best[4]:.1f})")
    elif not best[1]:
        print(f"  WARNING: best clean-ends offset has no valid narrow "
              f"centred gap (widest span {best[7]:.1f} mm at t={best[8]:+.1f}) "
              f"-- pin would tunnel past the joint or bridge open space "
              f"rather than the joint capsule")
    du, dv = best[3], best[4]
    lat_mid = base_mid + du * u_hat + dv * v_hat
    print(f"  lateral recentre du={du:+.1f} dv={dv:+.1f} mm "
          f"(perp. to axis) -> ends_ok={best[0]}, has_gap={best[1]}, "
          f"inside={best[6]*100:.0f}%")

    if not best[1]:
        raise RuntimeError("best lateral offset has no valid narrow centred "
                            "gap -- cannot place a pin that actually bridges "
                            "the joint capsule rather than solid bone or "
                            "open soft-tissue space; widen the search or "
                            "treat this joint by hand")
    t_center = best[8]  # centre of the LARGEST open span, not mean of all False samples
    mid = lat_mid + t_center * ray_axis
    print(f"  axial recentre on largest open span (width {best[7]:.2f} mm) "
          f"at t={t_center:+.2f} mm "
          f"-> pin centre ({mid[0]:.2f}, {mid[1]:.2f}, {mid[2]:.2f})")

    pin = trimesh.creation.cylinder(radius=args.diameter / 2.0,
                                    height=args.length, sections=48)
    R = trimesh.geometry.align_vectors([0, 0, 1], ray_axis)
    pin.apply_transform(R)
    pin.apply_translation(mid)
    print(f"\npin: {args.diameter:.1f} mm dia x {args.length:.1f} mm, "
          f"centred on the recentred joint gap")

    ts = np.linspace(-args.length / 2, args.length / 2, max(80, int(args.length * 20) + 1))
    samples = mid[None, :] + ts[:, None] * ray_axis[None, :]
    ins = mesh.contains(samples)
    print("  axial profile, centreline (I = inside bone, . = open space):")
    print("    " + "".join("I" if v else "." for v in ins))
    spans, cur = [], None
    for t, v in zip(ts, ins):
        if not v:
            cur = [t, t] if cur is None else [cur[0], t]
        elif cur:
            spans.append(tuple(cur))
            cur = None
    if cur:
        spans.append(tuple(cur))
    print(f"    inside {100.0 * ins.mean():.0f} %, open spans "
          f"{[(round(x, 2), round(y, 2)) for x, y in spans]} mm from centre")
    centre_end_open = spans and (abs(spans[0][0]) > args.length / 2 - 0.4
                                  or abs(spans[-1][1]) > args.length / 2 - 0.4)
    if centre_end_open:
        print("    WARNING: open span reaches a pin end on the CENTRELINE -- "
              "it protrudes. Shorten --length or re-fit radii.")

    # The centreline passing cleanly through bone is not sufficient -- the
    # PIN'S OWN SURFACE must also stay inside bone at both ends, or a thin
    # curved neck like this one produces a strut that pokes out to the side
    # even though its axis looks clean. Sample the pin's surface at 24
    # angles and require every one of them clear at both ends.
    tmp_v = np.array([1.0, 0.0, 0.0]) if abs(ray_axis[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    u_hat = np.cross(ray_axis, tmp_v); u_hat /= np.linalg.norm(u_hat)
    v_hat = np.cross(ray_axis, u_hat)
    r_off = args.diameter / 2.0
    margin_n = max(3, int(0.4 * len(ts) / args.length))  # ~0.4 mm of samples
    edge_fail = []
    for ang_deg in range(0, 360, 15):
        off = r_off * (np.cos(np.radians(ang_deg)) * u_hat
                        + np.sin(np.radians(ang_deg)) * v_hat)
        pts = (mid + off)[None, :] + ts[:, None] * ray_axis[None, :]
        e_ins = mesh.contains(pts)
        ends_ok = e_ins[:margin_n].all() and e_ins[-margin_n:].all()
        if not ends_ok:
            edge_fail.append(ang_deg)
    print(f"  pin-surface edge check (24 angles, diameter {args.diameter:.1f} mm): "
          f"{'ALL CLEAR' if not edge_fail else f'FAILS at angles {edge_fail}'}")
    if edge_fail:
        print("    WARNING: pin surface exits bone at one or more angles -- "
              "reduce --diameter or the pin will show as a strut.")

    out = trimesh.util.concatenate([mesh, pin])
    print(f"\nunion (concatenate): {len(out.faces)} faces")

    try:
        merged = mesh.union(pin)
        print(f"boolean union: {len(merged.faces)} faces  "
              f"watertight {merged.is_watertight}  "
              f"bodies {len(merged.split(only_watertight=False))}")
        out = merged
    except Exception as e:                                    # noqa: BLE001
        print(f"boolean union unavailable ({e}); "
              f"keeping overlapping concatenation, which slices correctly")

    euler = out.euler_number
    genus = (2 - euler) // 2
    print(f"\nRESULT vol {out.volume/1000:.3f} cm3  "
          f"watertight {out.is_watertight}  "
          f"bodies {len(out.split(only_watertight=False))}  "
          f"genus {genus}")

    if args.out:
        out.export(args.out)
        print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
