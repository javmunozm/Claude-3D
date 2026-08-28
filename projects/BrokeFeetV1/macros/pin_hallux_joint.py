"""Pin the hallux proximal phalanx to the 1st metatarsal head.

THE PROBLEM
-----------
In the operator's sculpt the 1st MTP joint (big toe) is connected by a bridge
0.295 mm across at its narrowest. Measured on BrokeFeetV2_sculpted.stl:

    closest approach   0.295 mm   at (-89.51, -55.06, 35.38)
    verts within 1 mm  107
    verts within 2 mm  241

The mesh is one connected body, so every topology gate passes -- but 0.295 mm is
under a single 0.4 mm extrusion width. The slicer renders it as a thread or
drops it entirely, the phalanx reads as floating, and it snaps on handling.

THE FIX
-------
An internal cylinder spanning the joint, sunk into both bones so it is hidden
inside the anatomy rather than sitting on the surface as a visible strut. This
is a PRINTABILITY reinforcement, not an anatomical correction -- the joint space
is real and stays visible from outside; only the interior is bridged.

Default is a 3.0 mm diameter pin. On PETG at 0.2 mm layers that is ~7 extrusion
widths across, strong enough to survive handling, and it sits entirely within
the ~13 mm wide metatarsal head and ~15 mm phalanx base.

DIRECTION
---------
The pin runs along the joint axis -- the line between the two closest surface
points -- not along a global axis, so it enters both bones perpendicular to
their facing articular surfaces and stays buried.

Usage:
  python macros/pin_hallux_joint.py [--diameter MM] [--length MM] [--out FILE]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import trimesh
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SRC = ROOT / "BrokeFeetV2_sculpted.stl"

# Split plane between 1st metatarsal head and proximal phalanx, from the
# vertex-density waist along the ray (minimum at Y = -54.9).
JOINT_CUT_Y = -55.0
FOREFOOT_Y = -85.0          # isolates the toe rays from the midfoot


def hallux_parts(mesh):
    """Return (metatarsal-head submesh, phalanx submesh) for the 1st ray."""
    V, F = mesh.vertices, mesh.faces
    fore = (V[F][:, :, 1] > FOREFOOT_Y).all(1)
    sub = trimesh.Trimesh(vertices=V, faces=F[fore], process=False)
    sub.remove_unreferenced_vertices()
    # largest forefoot component is the hallux ray (most medial, most massive)
    ray = sorted(sub.split(only_watertight=False),
                 key=lambda x: -len(x.faces))[0]
    rv, rf = ray.vertices, ray.faces
    prox = (rv[rf][:, :, 1] < JOINT_CUT_Y).all(1)
    dist = (rv[rf][:, :, 1] >= JOINT_CUT_Y).all(1)
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
    ap.add_argument("--diameter", type=float, default=3.0)
    ap.add_argument("--length", type=float, default=10.0,
                    help="total pin length, centred on the joint")
    ap.add_argument("--local-r", type=float, default=9.0,
                    help="radius of bone around the joint used to fit the axis")
    ap.add_argument("--src", default=str(SRC))
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    mesh = trimesh.load(args.src)
    print(f"source {Path(args.src).name}  {len(mesh.faces)} faces  "
          f"vol {mesh.volume/1000:.3f} cm3")

    P, D = hallux_parts(mesh)
    mid, axis, gap = joint_axis(P, D)
    print(f"\n1st MTP joint")
    print(f"  metatarsal head  {len(P.vertices)} verts")
    print(f"  proximal phalanx {len(D.vertices)} verts")
    print(f"  closest approach {gap:.3f} mm at "
          f"({mid[0]:.2f}, {mid[1]:.2f}, {mid[2]:.2f})")
    print(f"  joint axis       ({axis[0]:.3f}, {axis[1]:.3f}, {axis[2]:.3f})")

    # Axis fitting. The closest-approach direction is a local surface artefact,
    # and a full centroid-to-centroid ray is no better: both bones curve away
    # from the joint, so the far ends drag the line off-axis and the pin exits
    # through the side. Measured, only 58 % of such a pin sits inside bone.
    #
    # Using only material within LOCAL_R of the joint gives an axis aligned with
    # the bones where the pin actually passes: 90 % inside, and the sole gap is
    # the joint space itself.
    def near(sm, pt, r):
        return sm.vertices[np.linalg.norm(sm.vertices - pt, axis=1) < r]

    a = near(P, mid, args.local_r)
    b = near(D, mid, args.local_r)
    ray_axis = b.mean(0) - a.mean(0)
    ray_axis /= np.linalg.norm(ray_axis)
    print(f"  local axis (r={args.local_r:.0f}mm) "
          f"({ray_axis[0]:.3f}, {ray_axis[1]:.3f}, {ray_axis[2]:.3f})"
          f"  <- pin follows this")

    pin = trimesh.creation.cylinder(radius=args.diameter / 2.0,
                                    height=args.length, sections=48)
    # orient +Z onto the ray axis, then move to the joint centre
    R = trimesh.geometry.align_vectors([0, 0, 1], ray_axis)
    pin.apply_transform(R)
    pin.apply_translation(mid)
    print(f"\npin: {args.diameter:.1f} mm dia x {args.length:.1f} mm, "
          f"centred on the joint")

    # Where does the pin leave bone? A pin that pokes out is a visible strut,
    # which is not what was asked for. Sampling along the axis says exactly
    # where any exposure is -- the expected result is one open span at the
    # joint gap and nothing else.
    ts = np.linspace(-args.length / 2, args.length / 2, 80)
    samples = mid[None, :] + ts[:, None] * ray_axis[None, :]
    ins = mesh.contains(samples)
    print("  axial profile (I = inside bone, . = open space):")
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
    if spans and (abs(spans[0][0]) > args.length / 2 - 0.4
                  or abs(spans[-1][1]) > args.length / 2 - 0.4):
        print("    WARNING: open span reaches a pin end -- it protrudes. "
              "Shorten --length or re-fit --local-r.")

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

    print(f"\nRESULT vol {out.volume/1000:.3f} cm3  "
          f"watertight {out.is_watertight}  "
          f"bodies {len(out.split(only_watertight=False))}")

    if args.out:
        out.export(args.out)
        print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
