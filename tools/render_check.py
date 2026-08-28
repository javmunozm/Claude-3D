"""
render_check.py — geometry verification gate
=============================================
Catches the two classes of modelling bug that dimension checks miss:

  1. TOPOLOGY  — a part that looks right but is two disconnected bodies,
                 or is not watertight, and so cannot be printed as one piece.
  2. FORM      — a part whose bounding box and dimensions are all correct
                 but whose actual shape is wrong (e.g. a solid slab spanning
                 a span that should be open).

Both classes really shipped in this repo. VitaGrip revision 2 built a bridge
across ~97% of the grip's width and revision 3 exported two disconnected
bodies; neither was visible in a wireframe view or in any bounding-box check.
Only a SHADED render made them obvious. That is why this script renders
shaded by default and refuses to render wireframe.

Usage
-----
    # Topology gate only (fast, no display needed)
    python tools/render_check.py VitaGrip/VitaGrip.stl

    # Topology gate + shaded renders from standard cameras
    python tools/render_check.py VitaGrip/VitaGrip.stl --views front back

    # Expect a multi-piece file (suppresses the single-body failure)
    python tools/render_check.py part.stl --expect-bodies 2

Exit code is 0 only if every gate passes, so this can be used as a
pre-export or CI check.

Requirements:
    pip install trimesh matplotlib numpy
"""

import argparse
import pathlib
import sys

import numpy as np
import trimesh


def silhouette_profile(mask, n=16):
    """Width-vs-height profile of a boolean silhouette mask, normalized.

    Returns a list of (t, width_fraction) where t runs 0 (top) to 1 (bottom)
    and width_fraction is that row's width as a fraction of the widest row.
    Shape-only: independent of absolute scale, so a render and a photo of a
    differently-sized object are still directly comparable.
    """
    rows = np.where(mask.any(axis=1))[0]
    if len(rows) == 0:
        return []
    y0, y1 = rows.min(), rows.max()
    widths = []
    for i in range(n):
        y = int(y0 + (y1 - y0) * i / (n - 1))
        xs = np.where(mask[y])[0]
        widths.append(0.0 if len(xs) == 0 else float(xs.max() - xs.min() + 1))
    peak = max(widths) or 1.0
    return [(i / (n - 1), w / peak) for i, w in enumerate(widths)]


# ── Standard camera angles ────────────────────────────────────────────────────
# These are the conventions established during VitaGrip development and
# confirmed correct there — front is the view that exposed both bugs.
VIEWS = {
    "front": (90, -90),
    "back": (90, 90),
    "right": (0, 0),
    "left": (0, 180),
    "top": (90, 0),
    "iso": (30, -60),
}


def check_topology(mesh, expect_bodies=1):
    """Structural integrity gates. Returns (all_passed, list_of_result_rows).

    body_count is the gate that catches "the two halves are not actually
    connected" — a part can be geometrically perfect and still export as
    several disjoint solids, which no slicer will treat as one object.
    """
    results = []

    n_bodies = mesh.body_count
    ok_bodies = n_bodies == expect_bodies
    results.append((
        ok_bodies,
        "body_count",
        f"{n_bodies} (expected {expect_bodies})",
        "" if ok_bodies else "part is not a single connected solid — not printable as one piece",
    ))

    ok_wt = bool(mesh.is_watertight)
    results.append((
        ok_wt,
        "is_watertight",
        str(ok_wt),
        "" if ok_wt else "open mesh — slicers may fill or drop regions unpredictably",
    ))

    ok_winding = bool(mesh.is_winding_consistent)
    results.append((
        ok_winding,
        "winding_consistent",
        str(ok_winding),
        "" if ok_winding else "inconsistent face normals",
    ))

    # Negative volume means normals point inward — the solid is inside-out.
    vol = mesh.volume
    ok_vol = vol > 0
    results.append((
        ok_vol,
        "volume",
        f"{vol / 1000.0:.2f} cm3",
        "" if ok_vol else "non-positive volume — normals likely inverted",
    ))

    ext = mesh.extents
    results.append((
        True,
        "bounding_box",
        f"{ext[0]:.1f} x {ext[1]:.1f} x {ext[2]:.1f} mm",
        "",
    ))

    return all(r[0] for r in results), results


def render_shaded(mesh, out_path, view="front", size=900):
    """Render a SHADED (never wireframe) view of the mesh.

    Wireframe is deliberately not offered. Both historical bugs in this repo
    were invisible in wireframe — a slab and an open span look identical when
    you can see through both.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    if view not in VIEWS:
        raise ValueError(f"unknown view {view!r}; choose from {sorted(VIEWS)}")
    elev, azim = VIEWS[view]

    fig = plt.figure(figsize=(size / 100.0, size / 100.0), dpi=100)
    ax = fig.add_subplot(111, projection="3d")

    tris = mesh.vertices[mesh.faces]
    coll = Poly3DCollection(
        tris, facecolor="#8fa9c4", edgecolor="none", linewidths=0, alpha=1.0
    )
    coll.set_sort_zpos(0)
    ax.add_collection3d(coll)

    # Equal aspect so proportions are readable and comparable to a photo.
    bounds = mesh.bounds
    center = bounds.mean(axis=0)
    span = float((bounds[1] - bounds[0]).max()) / 2.0 * 1.1
    ax.set_xlim(center[0] - span, center[0] + span)
    ax.set_ylim(center[1] - span, center[1] + span)
    ax.set_zlim(center[2] - span, center[2] + span)
    try:
        ax.set_box_aspect((1, 1, 1))
    except Exception:
        pass

    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    fig.tight_layout(pad=0)
    fig.savefig(out_path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out_path


def compare_to_reference(render_path, reference_path, out_path):
    """Build a side-by-side render|reference image and compare silhouettes.

    This is the check that four VitaGrip revisions never ran. Each revision
    verified a local property (is this span open? is it one body? is this band
    thick?) and each passed, while the part as a whole looked nothing like the
    reference: its handle horns TAPERED to a 13 mm point where the reference
    horns SWELL to a ~53 mm teardrop. No local check can catch a whole-form
    mismatch. Only looking at both images together can.

    Returns a profile table. The table is a prompt to look, not a verdict —
    a human (or an agent with vision) must read the output image.
    """
    from PIL import Image

    ren = Image.open(render_path).convert("RGB")
    ref = Image.open(reference_path).convert("RGB")

    h = 700
    ren = ren.resize((int(ren.width * h / ren.height), h))
    ref = ref.resize((int(ref.width * h / ref.height), h))
    canvas = Image.new("RGB", (ren.width + ref.width + 30, h), "white")
    canvas.paste(ren, (0, 0))
    canvas.paste(ref, (ren.width + 30, 0))
    canvas.save(out_path)

    def mask_of(img):
        a = np.asarray(img).astype(int)
        # Anything meaningfully darker/more saturated than the white backdrop.
        bright = a.max(axis=2)
        sat = a.max(axis=2) - a.min(axis=2)
        return (bright < 240) & ((sat > 25) | (bright < 200))

    m_ren, m_ref = mask_of(ren), mask_of(ref)
    p_ren = silhouette_profile(m_ren)
    p_ref = silhouette_profile(m_ref)

    def fill(mask):
        rows = np.where(mask.any(axis=1))[0]
        cols = np.where(mask.any(axis=0))[0]
        if len(rows) == 0 or len(cols) == 0:
            return 0.0
        bbox = (rows.max() - rows.min() + 1) * (cols.max() - cols.min() + 1)
        return float(mask.sum()) / bbox

    return p_ren, p_ref, out_path, fill(m_ren), fill(m_ref)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stl", help="path to the STL to check")
    ap.add_argument("--views", nargs="*", default=[],
                    help=f"shaded views to render: {' '.join(sorted(VIEWS))}")
    ap.add_argument("--out-dir", default=None,
                    help="where to write renders (default: alongside the STL)")
    ap.add_argument("--expect-bodies", type=int, default=1,
                    help="expected body_count (default 1; raise for multi-piece files)")
    ap.add_argument("--reference", default=None,
                    help="reference image to compare the first rendered view against "
                         "(builds a side-by-side image you must then open and read)")
    args = ap.parse_args()

    stl_path = pathlib.Path(args.stl).resolve()
    if not stl_path.exists():
        print(f"ERROR: no such file: {stl_path}")
        return 2

    mesh = trimesh.load(str(stl_path))
    if isinstance(mesh, trimesh.Scene):
        mesh = trimesh.util.concatenate(tuple(mesh.geometry.values()))

    print("=" * 70)
    print(f"render_check — {stl_path.name}")
    print("=" * 70)

    passed, results = check_topology(mesh, expect_bodies=args.expect_bodies)
    for ok, label, value, note in results:
        tag = "PASS" if ok else "FAIL"
        line = f"  [{tag}]  {label:<20} {value}"
        if note:
            line += f"\n           -> {note}"
        print(line)
    print()

    if args.views:
        out_dir = pathlib.Path(args.out_dir) if args.out_dir else stl_path.parent
        out_dir.mkdir(parents=True, exist_ok=True)
        for view in args.views:
            out = out_dir / f"{stl_path.stem}_{view}.png"
            render_shaded(mesh, str(out), view=view)
            print(f"  Rendered [{view:<5}] -> {out}")
        print()
        print("  NOTE: renders are not self-verifying. Open each one and confirm")
        print("        the SHAPE matches intent — spans that should be open are")
        print("        open, curves read as curves. Dimension checks cannot do this.")
        print()

        if args.reference:
            first = out_dir / f"{stl_path.stem}_{args.views[0]}.png"
            side = out_dir / f"{stl_path.stem}_vs_reference.png"
            p_ren, p_ref, _, fill_ren, fill_ref = compare_to_reference(
                str(first), args.reference, str(side))
            print("-" * 70)
            print("Silhouette profile — width by height, normalized to each shape's")
            print("widest row. Compares outer BOUNDS only, so it stays valid across")
            print("different absolute sizes.")
            print()
            print("  WEAK SIGNAL — read this table as a hint, never as a verdict.")
            print("  It measures each row's outer width, so a hollow skeletal frame")
            print("  and a solid body of the same outline score IDENTICALLY. On the")
            print("  known-bad VitaGrip case this table showed near-perfect agreement")
            print("  while the side-by-side image showed a thin bracket next to a fat")
            print("  controller grip. Agreement here proves nothing. Only the image does.")
            print()
            print("    t (top->bottom)    render     reference    ")
            for (t, wr), (_, wf) in zip(p_ren, p_ref):
                bar_r = "#" * int(wr * 20)
                bar_f = "#" * int(wf * 20)
                flag = "   <-- differs" if abs(wr - wf) > 0.25 else ""
                print(f"      {t:4.2f}          {bar_r:<20} {bar_f:<20}{flag}")
            print()
            print(f"  Silhouette fill of own bounding box:")
            print(f"      render     {fill_ren * 100:5.1f} %")
            print(f"      reference  {fill_ref * 100:5.1f} %")
            gap = fill_ref - fill_ren
            if abs(gap) > 0.08:
                lean = "LESS" if gap > 0 else "MORE"
                print(f"      -> the render carries substantially {lean} mass than the")
                print(f"         reference. A slab and a rounded teardrop project the same")
                print(f"         outline, so this gap means the cross-sections need depth")
                print(f"         variation — not another width tweak.")
            print()
            print(f"  Side-by-side -> {side}")
            print()
            print("  *** OPEN THAT IMAGE AND ANSWER ONE QUESTION: is this the same")
            print("      object as the reference? Not 'are the dimensions right' —")
            print("      is the FORM the same. A part can pass every dimensional and")
            print("      topological gate above and still be the wrong shape. ***")
            print()

    print("=" * 70)
    if passed:
        print("VERDICT: topology gates PASS")
    else:
        print("VERDICT: topology gates FAILED — see [FAIL] lines above")
    print("=" * 70)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
