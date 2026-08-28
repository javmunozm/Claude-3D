"""Blend the hand-sculpted crater fills into the surrounding bone.

THE PROBLEM THIS SOLVES
-----------------------
The Blender fills are smooth. The bone around them is still terraced at the
0.5 mm iso pitch. So each fill reads as a smooth blob sitting on a stair-stepped
surface, with a hard rim where the two meet -- most visible at sites 6 and 7 on
the calcaneus. It is the SEAM that looks wrong, not the fill.

WHY NOT ANOTHER GLOBAL SMOOTHING PASS
-------------------------------------
Because it was already tried and rejected. `smooth_terracing.py` at
lambda=0.20 mu=0.21 x5 was judged insufficient by the operator, and stronger
settings do not help: lambda=0.5 mu=0.53 x10 widened the mortise 1.000 -> 2.000,
i.e. it opens joints before it finishes de-terracing. A global pass also has no
reason to concentrate effort where the seams actually are.

WHAT THIS DOES INSTEAD
----------------------
Taubin smoothing applied ONLY to a band around the sculpted regions, with a
cosine falloff so the correction fades to zero before it reaches untouched
anatomy. Vertices are selected by distance to the triangles that the sculpt
actually changed (found by diffing the pre/post Blender STLs), so the band
follows the operator's own strokes rather than a guessed box.

  RADIUS_MM      full-strength core, covers the fill and its rim
  FALLOFF_MM     fades to zero over this distance beyond the core

Everything outside RADIUS + FALLOFF is bit-identical to the input.

GATES
-----
Same set as smooth_terracing.py -- watertight, 1 body, genus 72, joint widths
via the re-voxelise round trip (change-based, see that module for why the
absolute numbers are not comparable to the README's), plus a check that no
vertex outside the band moved at all.

Usage:
  python macros/blend_sculpt_seams.py [--iters N] [--lamb L] [--mu M]
                                      [--radius MM] [--falloff MM] [--out F]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import trimesh
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

SRC = ROOT / "BrokeFeetV2_sculpted.stl"
PRE = ROOT / "blender" / "BrokeFeetV1_sculpt.stl"     # handed to Blender
POST = ROOT / "blender" / "BrokeFeetV2_sculpt.stl"    # returned from Blender
TJ = ROOT / "blender" / "TRANSFORM.json"

MORTISE = (-114.53, -145.15, 74.43)
RIND = (-120.71, -110.99, 49.72)


def sculpted_points():
    """Centroids of the triangles the operator actually changed, in mm."""
    t = json.loads(TJ.read_text())
    centre = np.array(t["centre_mm"], float)
    k = float(t["mm_per_blender_unit"])
    a = trimesh.load(PRE)
    b = trimesh.load(POST)
    fa = a.triangles.reshape(-1, 9)
    fb = b.triangles.reshape(-1, 9)
    if fa.shape != fb.shape:
        raise SystemExit("pre/post triangle counts differ -- cannot diff")
    changed = np.abs(fa - fb).max(1) > 0
    pts = fb[changed].reshape(-1, 3, 3).mean(1) * k + centre
    return pts, int(changed.sum())


def weights(mesh, pts, radius, falloff):
    """Per-vertex blend weight: 1 in the core, cosine fade to 0 at radius+falloff."""
    tree = cKDTree(pts)
    d, _ = tree.query(mesh.vertices, k=1)
    w = np.zeros(len(mesh.vertices))
    w[d <= radius] = 1.0
    band = (d > radius) & (d < radius + falloff)
    x = (d[band] - radius) / falloff
    w[band] = 0.5 * (1.0 + np.cos(np.pi * x))
    return w, d


def stats(mesh, label, ref_iso):
    import smooth_terracing as st
    import segment_axial as v0
    import patch_craters_test as pc
    bodies = len(mesh.split(only_watertight=False))
    genus = (2 - mesh.euler_number) // 2
    _, cnt = np.unique(mesh.edges_sorted, axis=0, return_counts=True)
    open_e = int((cnt == 1).sum())
    iso = st.mesh_to_iso(mesh, ref_iso)
    ti, _, _ = v0._mesh_to_index(iso)
    mort = pc.gap_at(iso, MORTISE, ti)
    rind = pc.gap_at(iso, RIND, ti)
    print(f"  {label:20s} vol {mesh.volume/1000:8.3f} cm3  "
          f"area/vol {mesh.area/mesh.volume:.4f}  bodies {bodies:2d}  "
          f"wt {str(mesh.is_watertight):5s}  genus {genus:3d}  open {open_e:3d}  "
          f"mortise {mort:.3f}  rind {rind:.3f}")
    return dict(vol=mesh.volume, genus=genus, bodies=bodies, open_edges=open_e,
                watertight=mesh.is_watertight, mortise=mort, rind=rind)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iters", type=int, default=12)
    ap.add_argument("--lamb", type=float, default=0.35)
    ap.add_argument("--mu", type=float, default=0.36)
    ap.add_argument("--radius", type=float, default=1.0)
    ap.add_argument("--falloff", type=float, default=1.5)
    ap.add_argument("--allow-inward", action="store_true",
                    help="permit inward motion (reopens filled craters -- "
                         "only for reproducing the rejected first attempt)")
    ap.add_argument("--src", default=str(SRC))
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    import sys
    sys.path.insert(0, str(HERE))
    sys.path.insert(0, str(ROOT.parent / "BrokeFeet" / "macros"))
    ref_iso = np.load(ROOT / "work" / "iso_patched.npy")

    mesh = trimesh.load(args.src)
    pts, n_changed = sculpted_points()
    print(f"source {Path(args.src).name}  {len(mesh.vertices)} verts")
    print(f"sculpted region: {n_changed} changed triangles from the Blender diff")

    w, dist = weights(mesh, pts, args.radius, args.falloff)
    n_core = int((w >= 0.999).sum())
    n_band = int(((w > 0) & (w < 0.999)).sum())
    print(f"blend band: {n_core} verts at full strength, {n_band} in falloff, "
          f"{len(w) - n_core - n_band} untouched "
          f"({100.0 * (n_core + n_band) / len(w):.1f} % of mesh affected)")

    print("\nBEFORE")
    before = stats(mesh, "sculpted", ref_iso)
    v0_pos = mesh.vertices.copy()

    # Taubin on the whole mesh, then re-blend by weight. Smoothing the full
    # surface and masking afterwards keeps the filter's neighbourhood intact at
    # the band edge; masking first would make the boundary itself a feature.
    sm = mesh.copy()
    trimesh.smoothing.filter_taubin(sm, lamb=args.lamb, nu=-args.mu,
                                    iterations=args.iters)
    delta = (sm.vertices - v0_pos) * w[:, None]

    # OUTWARD-ONLY CLAMP.
    #
    # Without this the blend REOPENS the craters the operator filled by hand.
    # Measured on the first attempt: 304 vertices pulled inward past 0.5 mm,
    # 84 past 1.0 mm, worst 3.61 mm, and net volume fell 0.093 cm3 -- material
    # the operator added, taken back out. Two clusters sat right on filled
    # craters: 98 verts sinking 3.39 mm at 3.0 mm from op1, and 180 verts
    # sinking 3.61 mm near the ankle.
    #
    # The cause is intrinsic to smoothing, not to the radius: a Taubin pass
    # pulls a convex fill DOWN toward its concave surroundings, which is
    # exactly a crater coming back. Shrinking the band cannot fix it.
    #
    # A seam blend should only ever shave a proud rim, never restore a cavity,
    # so the component of motion along the inward normal is dropped and only
    # outward (and tangential) motion survives.
    if not args.allow_inward:
        nrm = mesh.vertex_normals
        along = (delta * nrm).sum(1)
        delta = delta - np.minimum(along, 0.0)[:, None] * nrm

    out = mesh.copy()
    out.vertices = v0_pos + delta

    print("AFTER")
    after = stats(out, f"blended x{args.iters}", ref_iso)

    travel = np.linalg.norm(out.vertices - v0_pos, axis=1)
    outside = w <= 0
    print(f"\n  travel in band   mean {travel[w > 0].mean():.4f} mm  "
          f"p99 {np.percentile(travel[w > 0], 99):.4f} mm  "
          f"max {travel.max():.4f} mm")
    print(f"  travel outside   max {travel[outside].max():.9f} mm "
          f"(must be 0)")
    dvol = 100.0 * (after["vol"] - before["vol"]) / before["vol"]
    print(f"  volume change    {dvol:+.3f} %")

    print("\nGATES")
    fails = []

    def gate(name, ok, detail):
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:26s} {detail}")
        if not ok:
            fails.append(name)

    gate("watertight", after["watertight"], str(after["watertight"]))
    gate("open edges == 0", after["open_edges"] == 0, str(after["open_edges"]))
    gate("body count == 1", after["bodies"] == 1,
         f"{after['bodies']} (was {before['bodies']})")
    gate("genus unchanged", after["genus"] == before["genus"],
         f"{after['genus']} (was {before['genus']})")
    gate("volume within 0.5%", abs(dvol) <= 0.5, f"{dvol:+.3f} %")
    gate("mortise holds", abs(after["mortise"] - before["mortise"]) <= 0.51,
         f"{after['mortise']:.3f} (was {before['mortise']:.3f})")
    gate("rind holds", abs(after["rind"] - before["rind"]) <= 0.51,
         f"{after['rind']:.3f} (was {before['rind']:.3f})")
    gate("nothing moved outside band", travel[outside].max() == 0.0,
         f"{travel[outside].max():.9f} mm")

    # The gate the first attempt lacked. Every other check here passed while
    # the blend was quietly undoing the operator's crater fills -- watertight,
    # 1 body, genus 72, volume -0.076 %. Volume is far too coarse: refilling a
    # crater costs a few mm3 against 122 000. Only signed normal travel sees it.
    nrm = mesh.vertex_normals
    inward = ((out.vertices - v0_pos) * nrm).sum(1)
    worst_in = float(inward.min())
    n_in = int((inward < -0.05).sum())
    gate("no crater reopened", worst_in >= -0.05,
         f"worst inward {worst_in:.4f} mm on {n_in} verts "
         f"(first attempt: -3.61 mm on 304)")

    if args.out:
        out.export(args.out)
        print(f"\nwrote {args.out}")

    print("\n" + ("ALL GATES PASS" if not fails else f"FAILED: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())
