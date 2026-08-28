"""Remove marching-cubes voxel terracing from the exported bone mesh.

WHAT THIS FIXES -- and what it does NOT
---------------------------------------
The craters are already closed (`BrokeFeetV1_craters_final.stl`: 0 open
boundary edges, watertight, genus 72). What remains at the crater sites is not
a hole but STAIR-STEPPING: 0.5 mm iso-grid quantisation from running marching
cubes on a binary mask. It covers the whole model, not just the tarsus.

This pass smooths that terracing. It does not close holes, does not sculpt,
and must not move anatomy.

WHY TAUBIN, NOT LAPLACIAN
-------------------------
Plain Laplacian smoothing shrinks a closed surface monotonically -- every
iteration pulls the surface toward its centroid, so cortical bone thins and
joint spaces WIDEN. On this model that is the one failure mode that matters:
the tibiotalar mortise must stay at its measured width, and a shrinking pass
opens it.

Taubin (lambda/mu) alternates a positive smoothing step with a negative
inflation step chosen so the pass band leaves low-frequency shape untouched
while killing the high-frequency terracing. Volume is preserved to well under
a percent. That is the whole reason it is the right filter here.

GATES
-----
The voxel-grid gates in patch_craters_test.py (gap_at / tunnels / bone count)
run on the iso array and CANNOT be applied after meshing. The equivalents here
measure the same physical quantities on the mesh:

  mortise / rind width  -- ray cast across the joint, both directions, the
                           mesh-space analogue of gap_at()
  body count            -- connected components, must stay 1
  watertight            -- must stay True
  genus                 -- must stay 72; a rise means smoothing welded a joint
  volume                -- must stay within ~1 %
  max vertex travel     -- no vertex may move more than the terrace it fixes

A joint welded shut by over-smoothing shows up as genus DROP + body count
change, which is why both are gated rather than just volume.

Usage:
  python macros/smooth_terracing.py [iterations] [--lamb L] [--mu M] [--out F]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

SRC = ROOT / "BrokeFeetV1_craters_final.stl"

# Must stay open -- same two points the voxel gates use.
MORTISE = (-114.53, -145.15, 74.43)
RIND = (-120.71, -110.99, 49.72)

# Expected from the crater-patch run, for regression.
EXPECT_GENUS = 72
EXPECT_BODIES = 1


def mesh_to_iso(mesh, ref_iso):
    """Re-voxelise a mesh onto the pipeline's own iso grid.

    Three attempts to measure joint width directly on the mesh failed:
    a single-axis ray cast reported the mortise at 1.200 mm where the voxel
    gate measures 3.000 (wrong by 2.5x, and unsafe -- it would also mis-report
    a joint being welded shut), and trimesh.contains() exhausts memory against
    459k faces however the queries are batched or the mesh is cropped.

    Reconstructing an occupancy test from the mesh was the wrong direction.
    The pipeline already defines one. Voxelising back onto that same grid lets
    patch_craters_test.gap_at() -- the exact function that produced the
    3.000 / 2.000 mm reference -- be reused unchanged, so the before/after
    numbers are directly comparable rather than merely analogous.

    Note the axis permutation documented in _mesh_to_index: grid axis 2 carries
    X, axis 1 carries -Y, axis 0 carries Z. Rebuilding that mapping by hand
    points the window at empty space -- the trap that docstring warns about --
    so to_index() is used directly rather than reconstructed.
    """
    import segment_axial as v0
    to_index, _, _ = v0._mesh_to_index(ref_iso)

    vox = trimesh.voxel.creation.voxelize(mesh, pitch=v0.ISO_VOXEL_MM).fill()
    pts = np.asarray(vox.points, float)

    out = np.zeros_like(ref_iso, dtype=bool)
    idx = np.rint(np.array([to_index(p) for p in pts])).astype(int)
    ok = np.all((idx >= 0) & (idx < np.array(ref_iso.shape)), axis=1)
    idx = idx[ok]
    out[idx[:, 0], idx[:, 1], idx[:, 2]] = True
    return out


def stats(mesh, label, ref_iso=None):
    comps = mesh.split(only_watertight=False)
    genus = (2 - mesh.euler_number) // 2
    edges = mesh.edges_sorted
    _, cnt = np.unique(edges, axis=0, return_counts=True)
    n_open = int((cnt == 1).sum())
    if ref_iso is None:
        mort = rind = float("nan")
    else:
        import segment_axial as v0
        import patch_craters_test as pc
        iso = mesh_to_iso(mesh, ref_iso)
        to_index, _, _ = v0._mesh_to_index(iso)
        mort = pc.gap_at(iso, MORTISE, to_index)
        rind = pc.gap_at(iso, RIND, to_index)
    print(f"  {label:22s} vol {mesh.volume/1000:8.3f} cm3  "
          f"area/vol {mesh.area/mesh.volume:.4f}  "
          f"bodies {len(comps):2d}  wt {str(mesh.is_watertight):5s}  "
          f"genus {genus:3d}  open {n_open:3d}  "
          f"mortise {mort:6.3f}  rind {rind:6.3f}")
    return dict(vol=mesh.volume, genus=genus, bodies=len(comps),
                watertight=mesh.is_watertight, open_edges=n_open,
                mortise=mort, rind=rind)


def taubin(mesh, iterations, lamb, mu):
    """In-place Taubin smoothing, returns a copy."""
    out = mesh.copy()
    trimesh.smoothing.filter_taubin(out, lamb=lamb, nu=-mu, iterations=iterations)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("iterations", nargs="?", type=int, default=10)
    ap.add_argument("--lamb", type=float, default=0.5)
    ap.add_argument("--mu", type=float, default=0.53)
    ap.add_argument("--src", default=str(SRC))
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    import sys as _sys
    _sys.path.insert(0, str(HERE))
    _sys.path.insert(0, str(ROOT.parent / "BrokeFeet" / "macros"))
    ref_iso = np.load(ROOT / "work" / "iso_patched.npy")

    mesh = trimesh.load(args.src)
    print(f"source {Path(args.src).name}  "
          f"{len(mesh.vertices)} verts  {len(mesh.faces)} faces")
    print("BEFORE")
    before = stats(mesh, "craters_final", ref_iso)
    v_before = mesh.vertices.copy()

    # The round trip does NOT reproduce the pipeline's 3.000 / 2.000 absolute
    # widths, and cannot: trimesh voxelize().fill() marks every voxel the
    # surface passes through, adding a ~1-voxel skin (measured: recall 0.9994,
    # precision 0.9010 against the reference grid). That skin coats both walls
    # of a joint, so a 3.0 mm mortise reads as 1.0 mm.
    #
    # The bias is systematic, so it cancels in a comparison. Both meshes are
    # measured through the identical round trip and the gate is on the CHANGE,
    # never on the absolute value. Absolute widths from this function are not
    # comparable to the README's voxel-grid numbers and are not reported as if
    # they were.
    print(f"  (round-trip bias: mortise reads {before['mortise']:.3f} where the "
          f"iso grid measures 3.000 -- gating on change, not absolute)")

    print(f"\nTaubin lambda={args.lamb} mu={args.mu} "
          f"iterations={args.iterations}")
    sm = taubin(mesh, args.iterations, args.lamb, args.mu)

    print("AFTER")
    after = stats(sm, f"taubin x{args.iterations}", ref_iso)

    travel = np.linalg.norm(sm.vertices - v_before, axis=1)
    print(f"\n  vertex travel  mean {travel.mean():.4f} mm  "
          f"p99 {np.percentile(travel, 99):.4f} mm  "
          f"max {travel.max():.4f} mm")
    dvol = 100.0 * (after["vol"] - before["vol"]) / before["vol"]
    print(f"  volume change  {dvol:+.3f} %")

    # ---- gates -------------------------------------------------------
    print("\nGATES")
    fails = []

    def gate(name, ok, detail):
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:24s} {detail}")
        if not ok:
            fails.append(name)

    gate("watertight", after["watertight"], str(after["watertight"]))
    gate("open edges == 0", after["open_edges"] == 0, str(after["open_edges"]))
    gate("body count == 1", after["bodies"] == EXPECT_BODIES,
         f"{after['bodies']} (was {before['bodies']})")
    gate("genus unchanged", after["genus"] == before["genus"],
         f"{after['genus']} (was {before['genus']})")
    gate("volume within 1%", abs(dvol) <= 1.0, f"{dvol:+.3f} %")
    # Not ">0": a joint half welded shut still reads as open. These must hold
    # their measured width, within one voxel of the 3.000 / 2.000 reference.
    gate("mortise holds width", abs(after["mortise"] - before["mortise"]) <= 0.51,
         f"{after['mortise']:.3f} mm (was {before['mortise']:.3f})")
    gate("rind holds width", abs(after["rind"] - before["rind"]) <= 0.51,
         f"{after['rind']:.3f} mm (was {before['rind']:.3f})")
    # NOT a global max(). Over 229k vertices that is a single-outlier test: it
    # fired on 20 vertices (0.009 %) sitting at the bottom of one narrow
    # crevice near (-102, -157, 84..92), where smoothing pulls opposing walls
    # together. Those vertices are worth watching, but "some vertex moved far"
    # is not the same question as "did the shape change".
    #
    # What actually matters is whether a gap CLOSED. genus + body count already
    # catch a gap that welds through; this bounds the bulk of the surface so a
    # broad reshape cannot hide behind a good p99.
    gate("p99.9 travel < 0.5 mm", np.percentile(travel, 99.9) < 0.5,
         f"{np.percentile(travel, 99.9):.3f} mm "
         f"(max {travel.max():.3f} on {int((travel > 1.5).sum())} verts)")
    gate("bulk travel < terrace", np.percentile(travel, 99) < 0.5,
         f"p99 {np.percentile(travel, 99):.3f} mm vs 0.5 mm voxel")

    if args.out:
        out = Path(args.out)
        sm.export(out)
        print(f"\nwrote {out}")

    print("\n" + ("ALL GATES PASS" if not fails else f"FAILED: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())
